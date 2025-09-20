#!/bin/bash

# ESG Reporting Automation System Deployment Script
# For Great Malaysia AI Hackathon 2025

set -e

echo "🚀 Starting ESG Reporting System Deployment..."

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

# Check CDK
if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK not found. Installing..."
    npm install -g aws-cdk
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.12+."
    exit 1
fi

# Verify AWS region configuration
REGION=$(aws configure get region)
if [ "$REGION" != "ap-southeast-5" ]; then
    echo "⚠️  Setting AWS region to ap-southeast-5 (Malaysia)"
    aws configure set region ap-southeast-5
fi

echo "✅ Prerequisites check completed"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Verify Bedrock model access
echo "🤖 Checking Bedrock model access..."
aws bedrock list-foundation-models --region ap-southeast-5 > /dev/null 2>&1 || {
    echo "⚠️  Bedrock models may not be available in ap-southeast-5"
    echo "    You may need to request access to foundation models"
}

# Bootstrap CDK (if needed)
echo "🏗️  Bootstrapping CDK..."
cdk bootstrap --region ap-southeast-5

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ -v

# Deploy infrastructure
echo "🚀 Deploying infrastructure..."
cdk deploy ESGReportingStack --require-approval never

echo "✅ Deployment completed successfully!"
echo ""
echo "📊 ESG Reporting System is now deployed in ap-southeast-5"
echo ""
echo "🔗 Next steps:"
echo "   1. Upload test documents to the S3 bucket"
echo "   2. Test API endpoints"
echo "   3. Generate your first ESG report"
echo ""
echo "📚 Check the README.md for usage examples and API documentation"
