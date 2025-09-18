#!/bin/bash

# Deploy ACA Lambda-based Redshift backup solution
# This script deploys the serverless backup automation

set -e

SOURCE_ACCOUNT="164543933824"
TARGET_ACCOUNT="058264155998"
REGION="us-east-1"

echo "=== ACA Lambda Backup Deployment ==="
echo "Source Account: $SOURCE_ACCOUNT"
echo "Target Account: $TARGET_ACCOUNT"
echo "Region: $REGION"
echo

# Configuration options
echo "Backup Configuration Options:"
echo "1. Daily backups at 2 AM (recommended)"
echo "2. Every 12 hours"
echo "3. Every 6 hours"
echo "4. Custom schedule"
read -p "Select backup frequency (1-4): " SCHEDULE_CHOICE

case $SCHEDULE_CHOICE in
    1)
        SCHEDULE_EXPRESSION="cron(0 2 * * ? *)"
        SCHEDULE_DESC="Daily at 2 AM UTC"
        ;;
    2)
        SCHEDULE_EXPRESSION="rate(12 hours)"
        SCHEDULE_DESC="Every 12 hours"
        ;;
    3)
        SCHEDULE_EXPRESSION="rate(6 hours)"
        SCHEDULE_DESC="Every 6 hours"
        ;;
    4)
        read -p "Enter custom schedule expression (e.g., 'cron(0 */4 * * ? *)'): " SCHEDULE_EXPRESSION
        SCHEDULE_DESC="Custom: $SCHEDULE_EXPRESSION"
        ;;
    *)
        echo "Invalid choice, using daily backup"
        SCHEDULE_EXPRESSION="cron(0 2 * * ? *)"
        SCHEDULE_DESC="Daily at 2 AM UTC"
        ;;
esac

read -p "Enter retention days (default 7): " RETENTION_DAYS
RETENTION_DAYS=${RETENTION_DAYS:-7}

read -p "Enter email for notifications (optional, press Enter to skip): " NOTIFICATION_EMAIL

echo
echo "Configuration Summary:"
echo "  Schedule: $SCHEDULE_DESC"
echo "  Retention: $RETENTION_DAYS days"
echo "  Cluster: aca-redshift-cluster"
if [[ -n "$NOTIFICATION_EMAIL" ]]; then
    echo "  Notifications: $NOTIFICATION_EMAIL"
else
    echo "  Notifications: None configured"
fi
echo

read -p "Proceed with deployment? (yes/no): " CONFIRM
if [[ $CONFIRM != "yes" ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo "=== Deploying Lambda Backup Solution ==="

# Build parameters array
PARAMETERS="ParameterKey=TargetAccountId,ParameterValue=$TARGET_ACCOUNT ParameterKey=ClusterIdentifier,ParameterValue=aca-redshift-cluster ParameterKey=BackupSchedule,ParameterValue=\"$SCHEDULE_EXPRESSION\" ParameterKey=RetentionDays,ParameterValue=$RETENTION_DAYS"

# Add email parameter if provided
if [[ -n "$NOTIFICATION_EMAIL" ]]; then
    PARAMETERS="$PARAMETERS ParameterKey=NotificationEmail,ParameterValue=$NOTIFICATION_EMAIL"
fi

# Deploy the Lambda backup stack
aws cloudformation create-stack \
    --stack-name aca-lambda-backup \
    --template-body file://cloudformation/aca-lambda-backup-setup.yaml \
    --parameters $PARAMETERS \
    --capabilities CAPABILITY_NAMED_IAM \
    --region $REGION \
    --profile source

echo "✅ Lambda backup stack deployment initiated"

echo "Waiting for deployment to complete..."
aws cloudformation wait stack-create-complete \
    --stack-name aca-lambda-backup \
    --region $REGION \
    --profile source

echo "✅ Lambda backup deployment completed"

# Get the Lambda function name
LAMBDA_FUNCTION=$(aws cloudformation describe-stacks \
    --stack-name aca-lambda-backup \
    --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionName`].OutputValue' \
    --output text \
    --region $REGION \
    --profile source)

echo
echo "=== Testing Lambda Function ==="
echo "Running test backup..."

# Test the Lambda function
aws lambda invoke \
    --function-name $LAMBDA_FUNCTION \
    --payload '{"cluster_identifier":"aca-redshift-cluster","target_account_id":"'$TARGET_ACCOUNT'","retention_days":'$RETENTION_DAYS'}' \
    --region $REGION \
    --profile source \
    lambda-test-output.json

echo "Lambda test completed. Output:"
cat lambda-test-output.json | python3 -m json.tool
echo

# Clean up test output
rm -f lambda-test-output.json

echo "=== Deployment Summary ==="
echo "✅ Lambda function deployed: $LAMBDA_FUNCTION"
echo "✅ EventBridge schedule configured: $SCHEDULE_DESC"
echo "✅ Retention policy: $RETENTION_DAYS days"
echo "✅ CloudWatch monitoring enabled"
echo "✅ SNS notifications configured"
echo
echo "Your ACA Redshift backup automation is now active!"
echo
echo "Next steps:"
if [[ -n "$NOTIFICATION_EMAIL" ]]; then
    echo "1. Check your email ($NOTIFICATION_EMAIL) and confirm SNS subscription"
    echo "2. Monitor CloudWatch logs: /aws/lambda/$LAMBDA_FUNCTION"
    echo "3. Check EventBridge rule: aca-redshift-backup-schedule"
else
    echo "1. Optionally subscribe to SNS topic for notifications"
    echo "2. Monitor CloudWatch logs: /aws/lambda/$LAMBDA_FUNCTION"
    echo "3. Check EventBridge rule: aca-redshift-backup-schedule"
fi
echo
echo "To manually trigger a backup:"
echo "aws lambda invoke --function-name $LAMBDA_FUNCTION --region $REGION --profile source lambda-output.json"
echo
echo "To clean up: aws cloudformation delete-stack --stack-name aca-lambda-backup --region $REGION --profile source"