import json
import boto3
import logging
import os
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get region from environment or default to ap-southeast-5
region = os.environ.get('AWS_DEFAULT_REGION', 'ap-southeast-5')

s3_client = boto3.client('s3', region_name=region)
textract_client = boto3.client('textract', region_name=region)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main handler for ESG data ingestion from various sources
    """
    try:
        # Parse incoming event
        source_type = event.get('source_type', 'document')
        bucket_name = event.get('bucket_name')
        object_key = event.get('object_key')
        
        if not bucket_name or not object_key:
            raise ValueError("Missing required parameters: bucket_name or object_key")
        
        # Process based on source type
        if source_type == 'document':
            result = process_document(bucket_name, object_key)
        elif source_type == 'api':
            result = process_api_data(event.get('api_data', {}))
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data ingestion completed successfully',
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error in data ingestion: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def process_document(bucket_name: str, object_key: str) -> Dict[str, Any]:
    """Process document using Amazon Textract"""
    try:
        # Start Textract job for document analysis
        response = textract_client.start_document_analysis(
            DocumentLocation={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': object_key
                }
            },
            FeatureTypes=['TABLES', 'FORMS']
        )
        
        job_id = response['JobId']
        
        # Store job metadata
        metadata = {
            'job_id': job_id,
            'bucket': bucket_name,
            'key': object_key,
            'status': 'IN_PROGRESS',
            'created_at': datetime.utcnow().isoformat()
        }
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise

def process_api_data(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process API-based ESG data"""
    try:
        # Validate and normalize API data
        processed_data = {
            'data_type': api_data.get('type', 'unknown'),
            'metrics': api_data.get('metrics', {}),
            'timestamp': datetime.utcnow().isoformat(),
            'source': api_data.get('source', 'api')
        }
        
        # Store in S3 for further processing
        s3_key = f"api-data/{datetime.utcnow().strftime('%Y/%m/%d')}/{processed_data['data_type']}.json"
        
        s3_client.put_object(
            Bucket='esg-raw-data-bucket',
            Key=s3_key,
            Body=json.dumps(processed_data),
            ContentType='application/json'
        )
        
        return {
            'stored_location': s3_key,
            'data_type': processed_data['data_type']
        }
        
    except Exception as e:
        logger.error(f"Error processing API data: {str(e)}")
        raise
