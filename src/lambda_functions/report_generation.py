import json
import boto3
import logging
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get region from environment or default to ap-southeast-5
region = os.environ.get('AWS_DEFAULT_REGION', 'ap-southeast-5')

dynamodb = boto3.resource('dynamodb', region_name=region)
s3_client = boto3.client('s3', region_name=region)
bedrock_client = boto3.client('bedrock-runtime', region_name=region)

esg_table = dynamodb.Table('esg-processed-data')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Generate ESG reports in multiple formats
    """
    try:
        report_type = event.get('report_type', 'comprehensive')
        framework = event.get('framework', 'GRI')  # GRI, SASB, TCFD
        date_range = event.get('date_range', 30)  # days
        
        # Retrieve ESG data
        esg_data = retrieve_esg_data(date_range)
        
        # Generate report content using AI
        report_content = generate_report_content(esg_data, framework)
        
        # Create PDF report
        pdf_path = create_pdf_report(report_content, framework)
        
        # Upload to S3
        s3_key = upload_report_to_s3(pdf_path, framework)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Report generated successfully',
                'report_location': s3_key,
                'framework': framework,
                'data_points': len(esg_data)
            })
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def retrieve_esg_data(date_range: int) -> List[Dict[str, Any]]:
    """Retrieve ESG data from DynamoDB for specified date range"""
    try:
        cutoff_date = (datetime.utcnow() - timedelta(days=date_range)).isoformat()
        
        response = esg_table.scan(
            FilterExpression='#ts >= :cutoff',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={':cutoff': cutoff_date}
        )
        
        return response.get('Items', [])
        
    except Exception as e:
        logger.error(f"Error retrieving ESG data: {str(e)}")
        return []

def generate_report_content(esg_data: List[Dict], framework: str) -> Dict[str, Any]:
    """Generate report content using Bedrock AI"""
    try:
        # Aggregate data
        aggregated_data = aggregate_esg_metrics(esg_data)
        
        prompt = f"""
        Generate a comprehensive ESG report following the {framework} framework.
        
        Data Summary:
        {json.dumps(aggregated_data, indent=2)}
        
        Please provide:
        1. Executive Summary
        2. Environmental Performance Analysis
        3. Social Impact Assessment
        4. Governance Evaluation
        5. Key Recommendations
        
        Format as structured text with clear sections.
        """
        
        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 2000,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        content = result['content'][0]['text']
        
        return {
            'content': content,
            'data': aggregated_data,
            'framework': framework,
            'generated_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating report content: {str(e)}")
        return {'content': 'Error generating content', 'data': {}}

def aggregate_esg_metrics(esg_data: List[Dict]) -> Dict[str, Any]:
    """Aggregate ESG metrics from multiple data points"""
    aggregated = {
        'environmental': {},
        'social': {},
        'governance': {},
        'total_records': len(esg_data)
    }
    
    for record in esg_data:
        data = record.get('data', {})
        
        # Aggregate environmental metrics
        env_data = data.get('environmental', {})
        for metric, value in env_data.items():
            if metric not in aggregated['environmental']:
                aggregated['environmental'][metric] = []
            aggregated['environmental'][metric].append(value)
        
        # Aggregate social metrics
        social_data = data.get('social', {})
        for metric, value in social_data.items():
            if metric not in aggregated['social']:
                aggregated['social'][metric] = []
            aggregated['social'][metric].append(value)
        
        # Aggregate governance metrics
        gov_data = data.get('governance', {})
        for metric, value in gov_data.items():
            if metric not in aggregated['governance']:
                aggregated['governance'][metric] = []
            aggregated['governance'][metric].append(value)
    
    # Calculate averages - create new dict to avoid iteration issues
    for category in ['environmental', 'social', 'governance']:
        category_data = aggregated[category].copy()  # Create a copy
        for metric, values in category_data.items():
            if values and isinstance(values, list):
                aggregated[category][f"{metric}_avg"] = sum(values) / len(values)
                aggregated[category][f"{metric}_total"] = sum(values)
    
    return aggregated

def create_pdf_report(report_content: Dict[str, Any], framework: str) -> str:
    """Create PDF report using ReportLab"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph(f"ESG Report - {framework} Framework", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Generated date
        date_para = Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles['Normal'])
        story.append(date_para)
        story.append(Spacer(1, 12))
        
        # Content
        content_lines = report_content['content'].split('\n')
        for line in content_lines:
            if line.strip():
                para = Paragraph(line, styles['Normal'])
                story.append(para)
                story.append(Spacer(1, 6))
        
        # Data summary table
        data = report_content.get('data', {})
        if data:
            story.append(Spacer(1, 12))
            story.append(Paragraph("Data Summary", styles['Heading2']))
            
            table_data = [['Category', 'Metric', 'Value']]
            for category, metrics in data.items():
                if isinstance(metrics, dict):
                    for metric, value in metrics.items():
                        if isinstance(value, (int, float)):
                            table_data.append([category.title(), metric, f"{value:.2f}"])
            
            if len(table_data) > 1:
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
        
        doc.build(story)
        
        # Save to temporary file
        pdf_path = f"/tmp/esg_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        return pdf_path
        
    except Exception as e:
        logger.error(f"Error creating PDF report: {str(e)}")
        raise

def upload_report_to_s3(pdf_path: str, framework: str) -> str:
    """Upload generated report to S3"""
    try:
        s3_key = f"reports/{framework}/{datetime.utcnow().strftime('%Y/%m/%d')}/esg_report_{datetime.utcnow().strftime('%H%M%S')}.pdf"
        
        with open(pdf_path, 'rb') as f:
            s3_client.put_object(
                Bucket='esg-reports-bucket',
                Key=s3_key,
                Body=f.read(),
                ContentType='application/pdf'
            )
        
        return s3_key
        
    except Exception as e:
        logger.error(f"Error uploading report to S3: {str(e)}")
        raise
