#!/usr/bin/python
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from concurrent import futures
import argparse
import os
import sys
import time
import grpc
import traceback
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateError
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

import demo_pb2
import demo_pb2_grpc
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc

from opentelemetry import trace
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from aws_xray_sdk.core import xray_recorder

from logger import getJSONLogger
logger = getJSONLogger('emailservice-server')

# Loads confirmation email template from file
env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['html', 'xml'])
)
template = env.get_template('confirmation.html')

class BaseEmailService(demo_pb2_grpc.EmailServiceServicer):
  def Check(self, request, context):
    return health_pb2.HealthCheckResponse(
      status=health_pb2.HealthCheckResponse.SERVING)
  
  def Watch(self, request, context):
    return health_pb2.HealthCheckResponse(
      status=health_pb2.HealthCheckResponse.UNIMPLEMENTED)

class EmailService(BaseEmailService):
  def __init__(self):
    super().__init__()
    # Initialize AWS SES client
    aws_region = os.environ.get('AWS_REGION', 'us-east-1')
    self.ses_client = boto3.client('ses', region_name=aws_region)
    # Get sender email from environment variable
    self.sender_email = os.environ.get('SENDER_EMAIL', 'noreply@example.com')

  def send_email(self, email_address, content):
    """Send email using AWS SES"""
    try:
      response = self.ses_client.send_email(
        Source=self.sender_email,
        Destination={
          'ToAddresses': [email_address]
        },
        Message={
          'Subject': {
            'Data': 'Your Order Confirmation',
            'Charset': 'UTF-8'
          },
          'Body': {
            'Html': {
              'Data': content,
              'Charset': 'UTF-8'
            }
          }
        }
      )
      logger.info("Email sent to {} with MessageId: {}".format(
        email_address, response['MessageId']))
      return response
    except ClientError as e:
      logger.error("Failed to send email: {}".format(e.response['Error']['Message']))
      raise

  def SendOrderConfirmation(self, request, context):
    email = request.email
    order = request.order

    try:
      confirmation = template.render(order = order)
    except TemplateError as err:
      context.set_details("An error occurred when preparing the confirmation mail.")
      logger.error(str(err))
      context.set_code(grpc.StatusCode.INTERNAL)
      return demo_pb2.Empty()

    try:
      self.send_email(email, confirmation)
    except ClientError as err:
      context.set_details("An error occurred when sending the email.")
      logger.error(str(err))
      context.set_code(grpc.StatusCode.INTERNAL)
      return demo_pb2.Empty()
    except NoCredentialsError:
      context.set_details("AWS credentials not configured.")
      logger.error("AWS credentials not found")
      context.set_code(grpc.StatusCode.INTERNAL)
      return demo_pb2.Empty()

    return demo_pb2.Empty()

class DummyEmailService(BaseEmailService):
  def SendOrderConfirmation(self, request, context):
    logger.info('A request to send order confirmation email to {} has been received.'.format(request.email))
    return demo_pb2.Empty()

class HealthCheck():
  def Check(self, request, context):
    return health_pb2.HealthCheckResponse(
      status=health_pb2.HealthCheckResponse.SERVING)

def start(dummy_mode):
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=10),)
  service = None
  if dummy_mode:
    service = DummyEmailService()
    logger.info("Starting email service in DUMMY mode (emails will not be sent)")
  else:
    service = EmailService()
    logger.info("Starting email service with AWS SES")

  demo_pb2_grpc.add_EmailServiceServicer_to_server(service, server)
  health_pb2_grpc.add_HealthServicer_to_server(service, server)

  port = os.environ.get('PORT', "8080")
  logger.info("listening on port: "+port)
  server.add_insecure_port('[::]:'+port)
  server.start()
  try:
    while True:
      time.sleep(3600)
  except KeyboardInterrupt:
    server.stop(0)

def initAWSXRay():
  """Initialize AWS X-Ray tracing"""
  try:
    # Configure X-Ray recorder
    xray_recorder.configure(
      service='email_server',
      sampling=True,
      context_missing='LOG_ERROR'
    )
    logger.info("Successfully initialized AWS X-Ray.")
  except Exception as exc:
    logger.warning("Unable to initialize AWS X-Ray: " + str(exc))
  return


if __name__ == '__main__':
  # Determine mode from environment variable
  dummy_mode = os.environ.get('DUMMY_MODE', 'true').lower() == 'true'

  if dummy_mode:
    logger.info('starting the email service in dummy mode.')
  else:
    logger.info('starting the email service with AWS SES.')

  # AWS X-Ray Profiler/Tracing
  try:
    if "DISABLE_PROFILER" in os.environ:
      logger.info("AWS X-Ray disabled.")
    else:
      logger.info("AWS X-Ray enabled.")
      initAWSXRay()
  except Exception as e:
      logger.info(f"AWS X-Ray initialization failed: {e}")

  # OpenTelemetry Tracing
  try:
    if os.environ.get("ENABLE_TRACING") == "1":
      otel_endpoint = os.getenv("COLLECTOR_SERVICE_ADDR", "localhost:4317")
      trace.set_tracer_provider(TracerProvider())
      trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
            endpoint = otel_endpoint,
            insecure = True
          )
        )
      )
      logger.info("OpenTelemetry tracing enabled.")
    grpc_server_instrumentor = GrpcInstrumentorServer()
    grpc_server_instrumentor.instrument()

  except KeyError:
      logger.info("OpenTelemetry tracing disabled.")
  except Exception as e:
      logger.warning(f"Exception on tracing setup: {traceback.format_exc()}, tracing disabled.")

  start(dummy_mode = dummy_mode)
