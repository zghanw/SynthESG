from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import boto3
import json
import os
from datetime import datetime

app = FastAPI(title="ESG Reporting API", version="1.0.0")
security = HTTPBearer()

# Get region from environment or default to ap-southeast-5
region = os.environ.get('AWS_DEFAULT_REGION', 'ap-southeast-5')

# AWS clients
lambda_client = boto3.client('lambda', region_name=region)
s3_client = boto3.client('s3', region_name=region)

class ESGDataInput(BaseModel):
    source_type: str
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class ReportRequest(BaseModel):
    framework: str = "GRI"  # GRI, SASB, TCFD
    date_range: int = 30
    report_type: str = "comprehensive"

class DocumentUpload(BaseModel):
    bucket_name: str
    object_key: str
    document_type: str = "sustainability_report"

@app.post("/api/v1/ingest")
async def ingest_esg_data(
    data: ESGDataInput,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Ingest ESG data from various sources
    """
    try:
        # Prepare payload for Lambda
        payload = {
            "source_type": data.source_type,
            "api_data": data.data,
            "metadata": data.metadata or {}
        }
        
        # Invoke data ingestion Lambda
        response = lambda_client.invoke(
            FunctionName='DataIngestionFunction',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            return {"message": "Data ingested successfully", "result": json.loads(result['body'])}
        else:
            raise HTTPException(status_code=500, detail=json.loads(result['body']))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/process-document")
async def process_document(
    document: DocumentUpload,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Process uploaded ESG documents
    """
    try:
        payload = {
            "source_type": "document",
            "bucket_name": document.bucket_name,
            "object_key": document.object_key
        }
        
        response = lambda_client.invoke(
            FunctionName='DataIngestionFunction',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            return {"message": "Document processing started", "result": json.loads(result['body'])}
        else:
            raise HTTPException(status_code=500, detail=json.loads(result['body']))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/generate-report")
async def generate_report(
    request: ReportRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """
    Generate ESG report
    """
    try:
        payload = {
            "framework": request.framework,
            "date_range": request.date_range,
            "report_type": request.report_type
        }
        
        response = lambda_client.invoke(
            FunctionName='ReportGenerationFunction',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            return {"message": "Report generated successfully", "result": json.loads(result['body'])}
        else:
            raise HTTPException(status_code=500, detail=json.loads(result['body']))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/v1/frameworks")
async def get_supported_frameworks():
    """
    Get list of supported ESG frameworks
    """
    return {
        "frameworks": [
            {
                "code": "GRI",
                "name": "Global Reporting Initiative",
                "description": "Comprehensive sustainability reporting standard"
            },
            {
                "code": "SASB",
                "name": "Sustainability Accounting Standards Board",
                "description": "Industry-specific sustainability standards"
            },
            {
                "code": "TCFD",
                "name": "Task Force on Climate-related Financial Disclosures",
                "description": "Climate-related financial risk disclosure framework"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
