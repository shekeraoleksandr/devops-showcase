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

import grpc

import demo_pb2
import demo_pb2_grpc

from logger import getJSONLogger
logger = getJSONLogger('emailservice-client')

def send_confirmation_email(email, order):
  channel = grpc.insecure_channel('[::]:8080')
  stub = demo_pb2_grpc.EmailServiceStub(channel)
  try:
    response = stub.SendOrderConfirmation(demo_pb2.SendOrderConfirmationRequest(
      email = email,
      order = order
    ))
    logger.info('Request sent.')
  except grpc.RpcError as err:
    logger.error(err.details())
    logger.error('{}, {}'.format(err.code().name, err.code().value))

if __name__ == '__main__':
  logger.info('Client for email service.')

  # Create a test order
  test_order = demo_pb2.OrderResult(
    order_id='test-order-123',
    shipping_tracking_id='tracking-456',
    shipping_cost=demo_pb2.Money(currency_code='USD', units=5, nanos=990000000),
    shipping_address=demo_pb2.Address(
      street_address='123 Main St',
      city='San Francisco',
      state='CA',
      country='USA',
      zip_code=94105
    ),
    items=[
      demo_pb2.OrderItem(
        item=demo_pb2.CartItem(
          product_id='OLJCESPC7Z',
          quantity=1
        ),
        cost=demo_pb2.Money(currency_code='USD', units=35, nanos=0)
      )
    ]
  )

  # Send test email
  logger.info('Sending test order confirmation email...')
  send_confirmation_email('test@example.com', test_order)
