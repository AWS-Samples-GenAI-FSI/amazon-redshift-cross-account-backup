# ACA Setup Guide: Redshift Cross-Account Snapshot Demo

This guide walks you through setting up the ACA demo environment for all three backup approaches:

1. **Native Manual Scripts** - For testing and development
2. **Lambda-Based Automation** - For production serverless automation  
3. **AWS Backup Integration** - For enterprise backup management

## Prerequisites

- Two AWS accounts (source and target)
- AWS CLI configured with appropriate profiles
- Python 3.7+ with boto3 installed
- CloudFormation deployment permissions

## Quick Setup (Recommended)

### Automated Deployment
```bash
./quick-deploy.sh
```
This script will:
- Deploy both source and target account infrastructure
- Create the ACA Redshift cluster
- Set up all networking, KMS, and backup resources
- Wait for everything to be ready (~15 minutes)

### Manual Account Setup

#### 1. Source Account Setup
```bash
aws cloudformation create-stack \
  --stack-name aca-redshift-source \
  --template-body file://cloudformation/source-account-setup.yaml \
  --parameters ParameterKey=TargetAccountId,ParameterValue=058264155998 \
               ParameterKey=RedshiftMasterPassword,ParameterValue=YourSecurePassword123 \
  --capabilities CAPABILITY_NAMED_IAM \
  --profile source
```

#### 2. Target Account Setup
```bash
aws cloudformation create-stack \
  --stack-name aca-redshift-target \
  --template-body file://cloudformation/target-account-setup.yaml \
  --parameters ParameterKey=SourceAccountId,ParameterValue=164543933824 \
  --capabilities CAPABILITY_IAM \
  --profile target
```

## Deployment Options

### Option 1: Lambda-Based Production Automation (Recommended)

Deploy serverless backup automation:

```bash
./deploy-lambda-backup.sh
```

This will:
- Deploy a Lambda function for automated backups
- Set up EventBridge scheduling (daily, hourly, or custom)
- Configure SNS notifications (optional email alerts)
- Enable automatic snapshot retention management
- Provide production-ready monitoring and alerting

**Benefits:**
- ✅ Serverless - no infrastructure to manage
- ✅ Cost-effective - ~50% savings vs AWS Backup
- ✅ Automated scheduling and retention
- ✅ Built-in monitoring and notifications

### Option 2: Manual Script Testing

Test the native approach with manual scripts:

```bash
# Test native snapshot sharing
python3 scripts/native_snapshot_demo.py

# Test AWS Backup integration  
python3 scripts/aws_backup_demo.py
```

**Native Demo Process:**
1. Creates manual snapshot of ACA Redshift cluster
2. Shares snapshot with target account
3. Lists all shared snapshots
4. Restores new cluster in target account

**AWS Backup Demo Process:**
1. Uses existing AWS Backup infrastructure from CloudFormation
2. Creates on-demand backup job
3. Monitors backup completion
4. Shows cross-account backup copying

### Option 3: Complete Demo Runner

Run the full interactive demo:

```bash
./demo-runner.sh
```

This provides:
- Interactive menu to choose demo type
- Automated infrastructure deployment
- Execution of selected demos
- Comprehensive logging and status updates

## Configuration Options

### AWS Profiles

If you're using named AWS profiles, modify the demo scripts:

```python
# For native snapshot demo
demo = RedshiftSnapshotDemo(
    source_profile='source-account',
    target_profile='target-account'
)

# For AWS Backup demo
demo = AWSBackupDemo(
    source_profile='source-account', 
    target_profile='target-account'
)
```

### Custom Parameters

Update these variables in the demo scripts as needed:

```python
# Cluster identifiers
source_cluster_id = "demo-redshift-cluster"
target_cluster_id = "restored-demo-cluster"

# Subnet group (from CloudFormation output)
target_subnet_group = "redshift-target-subnet-group"

# Backup vault names
vault_name = "redshift-demo-vault"
target_vault_name = "redshift-cross-account-vault"
```

## Monitoring and Verification

### 1. Check Snapshot Status

```bash
# List snapshots in source account
aws redshift describe-cluster-snapshots \
  --cluster-identifier demo-redshift-cluster \
  --profile source-account

# List shared snapshots in target account
aws redshift describe-cluster-snapshots \
  --snapshot-type manual \
  --owner-account SOURCE_ACCOUNT_ID \
  --profile target-account
```

### 2. Monitor AWS Backup Jobs

```bash
# List backup jobs
aws backup list-backup-jobs \
  --profile source-account

# List copy jobs
aws backup list-copy-jobs \
  --profile source-account
```

### 3. Verify Restored Clusters

```bash
# Check restored cluster status
aws redshift describe-clusters \
  --cluster-identifier restored-demo-cluster \
  --profile target-account
```

## Troubleshooting

### Common Issues

1. **KMS Key Permissions**: Ensure the target account has decrypt permissions on the source account's KMS key
2. **Cross-Account Trust**: Verify IAM roles have proper cross-account trust relationships
3. **Region Consistency**: Both accounts must be in the same region for direct sharing
4. **Subnet Groups**: Ensure target account has appropriate subnet groups for cluster restoration

### Error Resolution

- **Access Denied**: Check IAM permissions and cross-account policies
- **Snapshot Not Found**: Verify snapshot sharing completed successfully
- **Restore Failures**: Check subnet group configuration and VPC settings
- **Timeout Issues**: Increase timeout values for large clusters

## Cleanup

To avoid ongoing charges, clean up resources after testing:

```bash
# Delete CloudFormation stacks
aws cloudformation delete-stack \
  --stack-name redshift-demo-source \
  --profile source-account

aws cloudformation delete-stack \
  --stack-name redshift-demo-target \
  --profile target-account

# Delete any remaining snapshots manually if needed
```

## Security Considerations

- Use least-privilege IAM policies
- Enable encryption for all snapshots and backups
- Regularly rotate KMS keys
- Monitor cross-account access with CloudTrail
- Implement backup retention policies