import boto3
import os
import mimetypes

session = boto3.Session(
    aws_access_key_id='YOUR_AWS_ACCESS_KEY_ID',
    aws_secret_access_key='YOUR_AWS_SECRET_ACCESS_KEY',
    region_name='us-east-1'
)
s3 = session.client('s3')
bucket = 'lorawan-telemetry-stack-webhostingbucket-djy9frtf8y6f'
out_dir = r'C:\Users\nsaty\Documents\Dilip Work\Aqua_feeder\Cloud\frontend\out'

print("Uploading to S3...")
for root, dirs, files in os.walk(out_dir):
    for file in files:
        local_path = os.path.join(root, file)
        s3_key = os.path.relpath(local_path, out_dir).replace('\\', '/')
        content_type, _ = mimetypes.guess_type(local_path)
        if not content_type:
            content_type = 'binary/octet-stream'
        
        print(f"Uploading {s3_key}...")
        s3.upload_file(local_path, bucket, s3_key, ExtraArgs={'ContentType': content_type})

print("Successfully deployed to S3!")
