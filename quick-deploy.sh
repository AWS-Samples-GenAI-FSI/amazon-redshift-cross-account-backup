#!/bin/bash

# Quick deployment script for your specific accounts
# Source: 164543933824, Target: 058264155998

set -e

SOURCE_ACCOUNT="164543933824"
TARGET_ACCOUNT="058264155998"
REGION="us-east-1"

echo "=== Quick Deploy for Redshift Cross-Account Demo ==="
echo "Source Account: $SOURCE_ACCOUNT"
echo "Target Account: $TARGET_ACCOUNT"
echo "Region: $REGION"
echo

# Get Redshift password
read -s -p "Enter Redshift master password (min 8 chars): " REDSHIFT_PASSWORD
echo
echo

if [[ ${#REDSHIFT_PASSWORD} -lt 8 ]]; then
    echo "❌ Password must be at least 8 characters"
    exit 1
fi

echo "=== Deploying ACA Source Account Infrastructure ==="
aws cloudformation create-stack \
    --stack-name aca-redshift-source \
    --template-body file://cloudformation/source-account-setup.yaml \
    --parameters ParameterKey=TargetAccountId,ParameterValue=$TARGET_ACCOUNT \
                 ParameterKey=RedshiftMasterPassword,ParameterValue="$REDSHIFT_PASSWORD" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $REGION \
    --profile source

echo "✅ ACA source stack deployment initiated"

echo "=== Deploying ACA Target Account Infrastructure ==="
aws cloudformation create-stack \
    --stack-name aca-redshift-target \
    --template-body file://cloudformation/target-account-setup.yaml \
    --parameters ParameterKey=SourceAccountId,ParameterValue=$SOURCE_ACCOUNT \
    --capabilities CAPABILITY_IAM \
    --region $REGION \
    --profile target

echo "✅ Target stack deployment initiated"
echo

echo "=== Waiting for Deployments ==="
echo "This will take 10-15 minutes. Monitoring progress..."

echo "Monitoring ACA source account stack..."
aws cloudformation wait stack-create-complete \
    --stack-name aca-redshift-source \
    --region $REGION \
    --profile source

echo "✅ ACA source account deployment completed"

echo "Monitoring ACA target account stack..."
aws cloudformation wait stack-create-complete \
    --stack-name aca-redshift-target \
    --region $REGION \
    --profile target

echo "✅ ACA target account deployment completed"

echo "Waiting for ACA Redshift cluster to be available..."
aws redshift wait cluster-available \
    --cluster-identifier aca-redshift-cluster \
    --region $REGION \
    --profile source

echo "✅ Redshift cluster is ready!"
echo

echo "=== ACA Deployment Summary ==="
echo "✅ ACA source account ($SOURCE_ACCOUNT) - Infrastructure deployed"
echo "✅ ACA target account ($TARGET_ACCOUNT) - Infrastructure deployed"
echo "✅ ACA Redshift cluster - Available and ready"
echo
echo "Next steps:"
echo "1. Run native demo: python3 scripts/native_snapshot_demo.py"
echo "2. Run backup demo: python3 scripts/aws_backup_demo.py"
echo "3. Check AWS console to verify resources"
echo
echo "Remember to run ./cleanup.sh when done to avoid charges!"