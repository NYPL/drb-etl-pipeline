#!/bin/bash

awslocal s3 mb s3://drb-files-local
awslocal s3 mb s3://drb-files-limited-local
awslocal s3 mb s3://ump-pdf-repository-local

awslocal s3api put-bucket-cors --bucket drb-files-local --cors-configuration '{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "POST", "PUT", "DELETE", "HEAD"],
      "AllowedHeaders": ["*"]
    }
  ]
}'
