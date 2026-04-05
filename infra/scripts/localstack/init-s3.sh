#!/bin/bash
echo "Creating S3 bucket..."
awslocal s3 mb s3://archlens-diagramas
awslocal s3api put-bucket-cors --bucket archlens-diagramas --cors-configuration '{
  "CORSRules": [
    {
      "AllowedOrigins": ["*"],
      "AllowedMethods": ["GET", "PUT", "POST"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3600
    }
  ]
}'
echo "S3 bucket 'archlens-diagramas' created."

# Listar para confirmar
awslocal s3 ls
