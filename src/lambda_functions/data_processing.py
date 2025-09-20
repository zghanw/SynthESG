import json
import boto3
import logging
import os
from typing import Dict, Any, List
from datetime import datetime
import re

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get region from environment or default to ap-southeast-5
region = os.environ.get('AWS_DEFAULT_REGION', 'ap-southeast-5')

textract_client = boto3.client('textract', region_name=region)
bedrock_client = boto3.client('bedrock-runtime', region_name=region)
dynamodb = boto3.resource('dynamodb', region_name=region)
s3_client = boto3.client('s3', region_name=region)

# DynamoDB table for processed ESG data
esg_table = dynamodb.Table('esg-processed-data')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Process extracted ESG data using AI services
    """
    try:
        job_id = event.get('job_id')
        if not job_id:
            raise ValueError("Missing Textract job_id")
        
        # Get Textract results
        textract_data = get_textract_results(job_id)
        
        # Extract ESG metrics using AI
        esg_metrics = extract_esg_metrics(textract_data)
        
        # Validate and normalize data
        validated_data = validate_esg_data(esg_metrics)
        
        # Store processed data
        storage_result = store_processed_data(validated_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data processing completed',
                'metrics_extracted': len(validated_data),
                'storage_result': storage_result
            })
        }
        
    except Exception as e:
        logger.error(f"Error in data processing: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_textract_results(job_id: str) -> Dict[str, Any]:
    """Retrieve Textract analysis results"""
    try:
        response = textract_client.get_document_analysis(JobId=job_id)
        
        if response['JobStatus'] != 'SUCCEEDED':
            raise ValueError(f"Textract job not completed. Status: {response['JobStatus']}")
        
        # Extract text and table data
        blocks = response['Blocks']
        extracted_data = {
            'text': extract_text_from_blocks(blocks),
            'tables': extract_tables_from_blocks(blocks)
        }
        
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error retrieving Textract results: {str(e)}")
        raise

def extract_text_from_blocks(blocks: List[Dict]) -> str:
    """Extract plain text from Textract blocks"""
    text_blocks = [block for block in blocks if block['BlockType'] == 'LINE']
    return '\n'.join([block.get('Text', '') for block in text_blocks])

def extract_tables_from_blocks(blocks: List[Dict]) -> List[Dict]:
    """Extract table data from Textract blocks"""
    tables = []
    table_blocks = [block for block in blocks if block['BlockType'] == 'TABLE']
    
    for table_block in table_blocks:
        # Simplified table extraction
        table_data = {
            'id': table_block['Id'],
            'confidence': table_block.get('Confidence', 0)
        }
        tables.append(table_data)
    
    return tables

def extract_esg_metrics(textract_data: Dict[str, Any]) -> Dict[str, Any]:
    """Use Bedrock to extract ESG metrics from text"""
    try:
        text_content = textract_data['text']
        
        prompt = f"""
        Extract ESG (Environmental, Social, Governance) metrics from the following text.
        Focus on quantitative data like emissions, energy consumption, waste, employee metrics, etc.
        
        Text: {text_content[:3000]}  # Limit text length
        
        Return a JSON object with the following structure:
        {{
            "environmental": {{"co2_emissions": value, "energy_consumption": value, "waste_generated": value}},
            "social": {{"employee_count": value, "diversity_ratio": value, "training_hours": value}},
            "governance": {{"board_independence": value, "audit_frequency": value}}
        }}
        """
        
        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1000,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        content = result['content'][0]['text']
        
        # Parse JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        
        return {}
        
    except Exception as e:
        logger.error(f"Error extracting ESG metrics: {str(e)}")
        return {}

def validate_esg_data(esg_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize ESG data"""
    validated_data = {
        'environmental': {},
        'social': {},
        'governance': {},
        'validation_timestamp': datetime.utcnow().isoformat()
    }
    
    # Validate environmental metrics
    env_data = esg_metrics.get('environmental', {})
    for metric, value in env_data.items():
        if isinstance(value, (int, float)) and value >= 0:
            validated_data['environmental'][metric] = value
    
    # Validate social metrics
    social_data = esg_metrics.get('social', {})
    for metric, value in social_data.items():
        if isinstance(value, (int, float)) and value >= 0:
            validated_data['social'][metric] = value
    
    # Validate governance metrics
    gov_data = esg_metrics.get('governance', {})
    for metric, value in gov_data.items():
        if isinstance(value, (int, float)) and 0 <= value <= 100:
            validated_data['governance'][metric] = value
    
    return validated_data

def store_processed_data(validated_data: Dict[str, Any]) -> Dict[str, Any]:
    """Store processed ESG data in DynamoDB"""
    try:
        item = {
            'id': f"esg-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'timestamp': datetime.utcnow().isoformat(),
            'data': validated_data
        }
        
        esg_table.put_item(Item=item)
        
        return {
            'stored_id': item['id'],
            'timestamp': item['timestamp']
        }
        
    except Exception as e:
        logger.error(f"Error storing processed data: {str(e)}")
        raise
