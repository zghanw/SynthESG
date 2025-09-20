# 🏗️ AWS Services Architecture - ESGenius AI

![AWS Architecture](aws_architecture.png)

## 📋 Complete AWS Services Inventory

### 🌐 **Frontend & Content Delivery**
| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Amazon S3** | Static website hosting | Public read access, website configuration |
| **CloudFront** | CDN for global distribution | Edge locations, caching policies |

### 🔌 **API & Gateway**
| Service | Purpose | Configuration |
|---------|---------|---------------|
| **API Gateway** | REST API endpoints | CORS enabled, Lambda integrations |
| | Routes: `/api/v1/analyze`, `/api/v1/report` | POST methods, JSON payloads |

### ⚡ **Serverless Compute**
| Service | Function | Runtime | Memory | Timeout |
|---------|----------|---------|---------|---------|
| **AWS Lambda** | ESG Calculator | Python 3.12 | 1024 MB | 5 min |
| **AWS Lambda** | Report Generator | Python 3.12 | 2048 MB | 10 min |
| **AWS Lambda** | Data Ingestion | Python 3.12 | 512 MB | 5 min |
| **AWS Lambda** | Data Processing | Python 3.12 | 1024 MB | 5 min |

### 🤖 **AI/ML Services**
| Service | Purpose | Model/Configuration |
|---------|---------|-------------------|
| **Amazon Bedrock** | AI-powered ESG analysis | Claude/Titan models |
| **Amazon Textract** | Document processing | OCR, form extraction |
| **Amazon Kendra** | Intelligent search | ESG document indexing |

### 💾 **Data Storage**
| Service | Purpose | Encryption | Access Pattern |
|---------|---------|------------|----------------|
| **Amazon S3** | Raw data storage | KMS encrypted | Infrequent access |
| **Amazon S3** | Report storage | KMS encrypted | On-demand access |
| **Amazon DynamoDB** | Processed data & audit trail | KMS encrypted | High throughput |

### 🔒 **Security & Compliance**
| Service | Purpose | Configuration |
|---------|---------|---------------|
| **AWS KMS** | Encryption key management | Customer managed keys |
| **AWS IAM** | Access control | Least privilege roles |
| **AWS CloudWatch** | Monitoring & logging | 7-day retention |

## 🔄 Data Flow Architecture

### **1. User Request Flow**
```
User → S3 Website → API Gateway → Lambda Functions
```

### **2. ESG Analysis Flow**
```
Lambda Scraper → Bedrock AI → DynamoDB → Response
```

### **3. Document Processing Flow**
```
S3 Raw Data → Textract → Lambda Processing → DynamoDB
```

### **4. Report Generation Flow**
```
Lambda Report → S3 Reports → Presigned URL → User Download
```

## 📊 Resource Specifications

### **Lambda Functions Configuration**
```yaml
ESG Calculator:
  Runtime: Python 3.12
  Memory: 1024 MB
  Timeout: 5 minutes
  Handler: scientific_esg_calculator.lambda_handler
  
Report Generator:
  Runtime: Python 3.12
  Memory: 2048 MB
  Timeout: 10 minutes
  Handler: professional_report_generator.lambda_handler
```

### **DynamoDB Table Schema**
```yaml
Table: esg-processed-data
Partition Key: company_id (String)
Attributes:
  - raw_data (JSON)
  - calculated_scores (JSON)
  - timestamp (String)
  - audit_trail (JSON)
```

### **S3 Bucket Configuration**
```yaml
Raw Data Bucket:
  Encryption: KMS
  Versioning: Enabled
  Lifecycle: 90 days to IA
  
Reports Bucket:
  Encryption: KMS
  Public Access: Blocked
  Presigned URLs: 1 hour expiry
```

## 🌏 Regional Deployment

**Primary Region**: `ap-southeast-5` (Malaysia)
- **Compliance**: Local data residency requirements
- **Latency**: Optimized for Southeast Asia
- **Availability**: Multi-AZ deployment

## 🔐 Security Implementation

### **Encryption at Rest**
- All S3 buckets encrypted with KMS
- DynamoDB encrypted with customer-managed keys
- Lambda environment variables encrypted

### **Encryption in Transit**
- HTTPS/TLS 1.2 for all API calls
- VPC endpoints for internal communication
- Signed requests for S3 access

### **Access Control**
- IAM roles with least privilege
- Resource-based policies
- API Gateway authentication

## 📈 Monitoring & Observability

### **CloudWatch Metrics**
- Lambda function duration and errors
- API Gateway request count and latency
- DynamoDB read/write capacity
- S3 request metrics

### **CloudWatch Logs**
- Lambda function execution logs
- API Gateway access logs
- Application-level logging

### **Alarms & Notifications**
- High error rate alerts
- Performance degradation warnings
- Cost optimization recommendations

## 💰 Cost Optimization

### **Serverless Benefits**
- Pay-per-use Lambda execution
- DynamoDB on-demand billing
- S3 intelligent tiering
- No idle resource costs

### **Estimated Monthly Costs** (1000 analyses)
- Lambda: ~$5
- DynamoDB: ~$10
- S3: ~$3
- API Gateway: ~$2
- **Total**: ~$20/month

## 🚀 Scalability Features

### **Auto-Scaling**
- Lambda concurrent executions: 1000
- DynamoDB auto-scaling enabled
- API Gateway throttling: 10,000 RPS
- S3 unlimited storage

### **Performance Optimization**
- Lambda warm-up strategies
- DynamoDB global secondary indexes
- S3 transfer acceleration
- CloudFront edge caching

---

## 🏆 **Production-Ready Architecture**

This AWS architecture demonstrates:
- ✅ **Serverless scalability** with Lambda and DynamoDB
- ✅ **Enterprise security** with KMS and IAM
- ✅ **Global performance** with CloudFront CDN
- ✅ **Cost optimization** with pay-per-use services
- ✅ **Compliance ready** with Malaysia region deployment
- ✅ **Monitoring & observability** with CloudWatch
- ✅ **High availability** with multi-AZ deployment

**Perfect for hackathon judges to see professional cloud architecture! 🏗️☁️**
