# Email Service - AWS Migration Guide

This email service has been migrated from Google Cloud Platform (GCP) to Amazon Web Services (AWS).

## Changes Made

### 1. Email Service Provider
- **Before**: Google Cloud Mail API (not implemented)
- **After**: AWS Simple Email Service (SES)

### 2. Profiling/Tracing
- **Before**: Google Cloud Profiler
- **After**: AWS X-Ray

### 3. Dependencies
- **Removed**:
  - `google-api-core`
  - `google-cloud-profiler`
  - `google-cloud-trace`
  - `google-auth`

- **Added**:
  - `boto3` (AWS SDK for Python)
  - `aws-xray-sdk` (AWS X-Ray tracing)

## Configuration

### Environment Variables

#### Required for Production Mode:
- `DUMMY_MODE`: Set to `false` to enable actual email sending (default: `true`)
- `AWS_REGION`: AWS region for SES (default: `us-east-1`)
- `SENDER_EMAIL`: Verified sender email address in AWS SES
- `AWS_ACCESS_KEY_ID`: AWS access key (or use IAM roles)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key (or use IAM roles)

#### Optional:
- `PORT`: Service port (default: `8080`)
- `DISABLE_PROFILER`: Set to disable AWS X-Ray tracing
- `ENABLE_TRACING`: Set to `1` to enable OpenTelemetry tracing
- `COLLECTOR_SERVICE_ADDR`: OpenTelemetry collector address

### AWS SES Setup

1. **Verify Sender Email Address**:
   ```bash
   aws ses verify-email-identity --email-address noreply@yourdomain.com
   ```

2. **Move Out of SES Sandbox** (for production):
   - By default, SES is in sandbox mode
   - Request production access via AWS Console
   - In sandbox mode, you can only send to verified email addresses

3. **IAM Permissions**:
   The service needs the following IAM permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "ses:SendEmail",
           "ses:SendRawEmail"
         ],
         "Resource": "*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "xray:PutTraceSegments",
           "xray:PutTelemetryRecords"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

## Running the Service

### Dummy Mode (No emails sent):
```bash
export DUMMY_MODE=true
python email_server.py
```

### Production Mode (AWS SES):
```bash
export DUMMY_MODE=false
export AWS_REGION=us-east-1
export SENDER_EMAIL=noreply@yourdomain.com
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
python email_server.py
```

### Using IAM Roles (Recommended for EC2/ECS):
```bash
export DUMMY_MODE=false
export AWS_REGION=us-east-1
export SENDER_EMAIL=noreply@yourdomain.com
# No need to set AWS credentials - they will be obtained from IAM role
python email_server.py
```

## Testing

### Install Dependencies:
```bash
pip install -r requirements.txt
```

### Run in Dummy Mode:
```bash
python email_server.py
```

### Test with Client:
```bash
python email_client.py
```

## Docker Deployment

When deploying with Docker, ensure:
1. AWS credentials are available (via environment variables or IAM roles)
2. The container has network access to AWS SES endpoints
3. Environment variables are properly configured

## Troubleshooting

### "AWS credentials not configured"
- Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set, OR
- Ensure the service is running with an IAM role that has SES permissions

### "Email address not verified"
- In SES sandbox mode, both sender and recipient must be verified
- Request production access or verify the recipient email address

### "MessageRejected: Email address is not verified"
- Verify your sender email address in AWS SES console
- Check that SENDER_EMAIL environment variable matches the verified address

## Migration Notes

The service maintains backward compatibility with:
- gRPC interface (no changes)
- OpenTelemetry tracing (still supported)
- Health check endpoints (unchanged)

The only breaking changes are:
- Environment variable changes (GCP_PROJECT_ID no longer used)
- New AWS-specific environment variables required
- Different cloud provider credentials needed
