#!/bin/bash

# Redshift Cross-Account Snapshot Demo Runner
# This script helps you run the complete demo with proper setup

set -e

echo "=== ACA Redshift Cross-Account Snapshot Demo ==="
echo

# Check prerequisites
echo "Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.7+ first."
    exit 1
fi

# Check boto3
if ! python3 -c "import boto3" &> /dev/null; then
    echo "❌ boto3 not found. Installing requirements..."
    pip3 install -r requirements.txt
fi

echo "✅ Prerequisites check passed"
echo

# Configuration - Your specific accounts
SOURCE_ACCOUNT_ID="164543933824"
TARGET_ACCOUNT_ID="058264155998"

echo "Using your configured accounts:"
echo "  Source Account: $SOURCE_ACCOUNT_ID"
echo "  Target Account: $TARGET_ACCOUNT_ID"
echo

read -s -p "Enter Redshift master password (min 8 chars): " REDSHIFT_PASSWORD
echo
echo

if [[ ${#REDSHIFT_PASSWORD} -lt 8 ]]; then
    echo "❌ Password must be at least 8 characters"
    exit 1
fi
echo

# Ask for demo type
echo "Select demo type:"
echo "1) Native Redshift Snapshot Sharing"
echo "2) AWS Backup Integration"
echo "3) Both (recommended)"
read -p "Enter choice (1-3): " DEMO_CHOICE

case $DEMO_CHOICE in
    1)
        DEMO_TYPE="native"
        ;;
    2)
        DEMO_TYPE="backup"
        ;;
    3)
        DEMO_TYPE="both"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo "Selected demo type: $DEMO_TYPE"
echo

# Deploy infrastructure
echo "=== Deploying ACA Infrastructure ==="

echo "Deploying ACA source account infrastructure..."
aws cloudformation create-stack \
    --stack-name aca-redshift-source \
    --template-body file://cloudformation/source-account-setup.yaml \
    --parameters ParameterKey=TargetAccountId,ParameterValue=$TARGET_ACCOUNT_ID \
                 ParameterKey=RedshiftMasterPassword,ParameterValue=$REDSHIFT_PASSWORD \
    --capabilities CAPABILITY_NAMED_IAM \
    --region us-east-1 \
    --profile source

echo "Deploying ACA target account infrastructure..."
aws cloudformation create-stack \
    --stack-name aca-redshift-target \
    --template-body file://cloudformation/target-account-setup.yaml \
    --parameters ParameterKey=SourceAccountId,ParameterValue=$SOURCE_ACCOUNT_ID \
    --capabilities CAPABILITY_IAM \
    --region us-east-1 \
    --profile target

echo "Waiting for stacks to complete (this may take 10-15 minutes)..."

# Wait for source stack
aws cloudformation wait stack-create-complete \
    --stack-name aca-redshift-source \
    --region us-east-1 \
    --profile source

echo "✅ ACA source account stack deployed successfully"

# Wait for target stack  
aws cloudformation wait stack-create-complete \
    --stack-name aca-redshift-target \
    --region us-east-1 \
    --profile target

echo "✅ ACA target account stack deployed successfully"
echo

# Wait for Redshift cluster to be available
echo "Waiting for ACA Redshift cluster to be available..."
aws redshift wait cluster-available \
    --cluster-identifier aca-redshift-cluster \
    --region us-east-1 \
    --profile source

echo "✅ ACA Redshift cluster is ready"
echo

# Run demos
echo "=== Running Demos ==="

if [[ $DEMO_TYPE == "native" || $DEMO_TYPE == "both" ]]; then
    echo "Running Native Redshift Snapshot Sharing Demo..."
    python3 scripts/native_snapshot_demo.py
    echo "✅ Native demo completed"
    echo
fi

if [[ $DEMO_TYPE == "backup" || $DEMO_TYPE == "both" ]]; then
    echo "Running AWS Backup Integration Demo..."
    python3 scripts/aws_backup_demo.py
    echo "✅ AWS Backup demo completed"
    echo
fi

echo "=== Demo Summary ==="
echo "✅ All demos completed successfully!"
echo
echo "Next steps:"
echo "1. Check the AWS console to verify resources"
echo "2. Review the restored clusters and backups"
echo "3. Run cleanup when ready: ./cleanup.sh"
echo
echo "For detailed analysis, see docs/comparison-analysis.md"