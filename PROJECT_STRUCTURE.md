# ACA Redshift Cross-Account Backup Demo - Project Structure

This document provides a comprehensive overview of the project structure and organization.

## Repository Structure

```
aca-redshift-backup-demo/
├── .github/                          # GitHub configuration
│   └── workflows/
│       └── validate.yml              # CI/CD pipeline for validation
├── cloudformation/                   # Infrastructure as Code
│   ├── source-account-setup.yaml     # Source account infrastructure
│   ├── target-account-setup.yaml     # Target account infrastructure
│   └── aca-lambda-backup-setup.yaml  # Lambda automation infrastructure
├── docs/                            # Documentation
│   ├── setup-guide.md               # Complete setup instructions
│   ├── comparison-analysis.md        # Feature and cost comparison
│   ├── technical-faq.md             # Technical FAQ and troubleshooting
│   └── lambda-automation-guide.md    # Lambda solution deep dive
├── lambda/                          # Lambda function code
│   └── aca_redshift_backup_lambda.py # Serverless backup automation
├── scripts/                         # Demo and testing scripts
│   ├── native_snapshot_demo.py      # Native approach demonstration
│   └── aws_backup_demo.py           # AWS Backup demonstration
├── .gitignore                       # Git ignore patterns
├── CHANGELOG.md                     # Version history and changes
├── CONTRIBUTING.md                  # Contribution guidelines
├── LICENSE                          # Apache 2.0 license
├── PROJECT_STRUCTURE.md             # This file
├── README.md                        # Main project documentation
├── cleanup.sh                       # Resource cleanup automation
├── demo-runner.sh                   # Interactive demo execution
├── deploy-lambda-backup.sh          # Lambda solution deployment
├── quick-deploy.sh                  # Fast infrastructure deployment
└── requirements.txt                 # Python dependencies
```

## File Descriptions

### Infrastructure (CloudFormation)

#### `cloudformation/source-account-setup.yaml`
- **Purpose**: Creates infrastructure in the source AWS account
- **Resources**: 
  - ACA Redshift cluster (`aca-redshift-cluster`)
  - VPC, subnets, and networking
  - KMS keys with cross-account permissions
  - AWS Backup vault and plans
  - IAM roles for backup operations
- **Parameters**: Target account ID, Redshift credentials
- **Outputs**: Cluster ARN, KMS key ID, backup vault details

#### `cloudformation/target-account-setup.yaml`
- **Purpose**: Creates infrastructure in the target AWS account
- **Resources**:
  - VPC and networking for restored clusters
  - Redshift subnet groups
  - AWS Backup vault for cross-account copies
  - KMS keys for backup encryption
- **Parameters**: Source account ID
- **Outputs**: Subnet group names, backup vault ARN

#### `cloudformation/aca-lambda-backup-setup.yaml`
- **Purpose**: Deploys serverless backup automation
- **Resources**:
  - Lambda function with backup logic
  - EventBridge scheduling rules
  - CloudWatch monitoring and alarms
  - SNS notifications
  - IAM roles and permissions
- **Parameters**: Schedule, retention, notification email
- **Outputs**: Lambda function ARN, schedule rule name

### Automation Scripts

#### `quick-deploy.sh`
- **Purpose**: Rapid deployment of complete infrastructure
- **Features**:
  - Deploys both source and target account stacks
  - Waits for completion and validates resources
  - Provides deployment summary and next steps
- **Usage**: `./quick-deploy.sh`
- **Duration**: ~15 minutes

#### `deploy-lambda-backup.sh`
- **Purpose**: Deploys Lambda-based backup automation
- **Features**:
  - Interactive configuration (schedule, retention, email)
  - Deploys Lambda infrastructure
  - Tests function execution
  - Provides operational guidance
- **Usage**: `./deploy-lambda-backup.sh`
- **Duration**: ~5 minutes

#### `demo-runner.sh`
- **Purpose**: Complete interactive demo experience
- **Features**:
  - Prerequisites checking
  - Infrastructure deployment
  - Demo execution (native, backup, or both)
  - Comprehensive logging
- **Usage**: `./demo-runner.sh`
- **Duration**: ~25 minutes

#### `cleanup.sh`
- **Purpose**: Comprehensive resource cleanup
- **Features**:
  - Multi-step cleanup process
  - Cross-account resource removal
  - Dependency-aware deletion order
  - Final verification and reporting
- **Usage**: `./cleanup.sh`
- **Duration**: ~10 minutes

### Demo Scripts

#### `scripts/native_snapshot_demo.py`
- **Purpose**: Demonstrates native Redshift snapshot sharing
- **Features**:
  - Manual snapshot creation
  - Cross-account sharing
  - Cluster restoration in target account
  - Comprehensive logging and error handling
- **Class**: `RedshiftSnapshotDemo`
- **Methods**: `create_manual_snapshot()`, `share_snapshot_with_account()`, `restore_cluster_from_snapshot()`

#### `scripts/aws_backup_demo.py`
- **Purpose**: Demonstrates AWS Backup integration
- **Features**:
  - Uses CloudFormation-deployed backup infrastructure
  - On-demand backup job execution
  - Cross-account backup copying
  - Recovery point management
- **Class**: `AWSBackupDemo`
- **Methods**: `start_backup_job()`, `wait_for_backup_completion()`, `list_recovery_points()`

### Lambda Function

#### `lambda/aca_redshift_backup_lambda.py`
- **Purpose**: Production-ready serverless backup automation
- **Features**:
  - Scheduled backup execution
  - Cross-account snapshot sharing
  - Automatic retention management
  - Comprehensive error handling and logging
- **Class**: `AcaRedshiftBackupLambda`
- **Handler**: `lambda_handler(event, context)`
- **Timeout**: 15 minutes
- **Memory**: 512 MB

### Documentation

#### `README.md`
- **Purpose**: Main project overview and quick start
- **Sections**: Architecture, features, cost comparison, quick start options
- **Audience**: All users (developers, operators, decision makers)

#### `docs/setup-guide.md`
- **Purpose**: Detailed setup and deployment instructions
- **Sections**: Prerequisites, deployment options, configuration, troubleshooting
- **Audience**: Technical implementers

#### `docs/comparison-analysis.md`
- **Purpose**: Comprehensive comparison of all three approaches
- **Sections**: Cost analysis, feature comparison, recommendations, decision matrix
- **Audience**: Decision makers and architects

#### `docs/technical-faq.md`
- **Purpose**: Technical FAQ addressing common implementation questions
- **Sections**: Storage architecture, cross-account mechanisms, troubleshooting, best practices
- **Audience**: Technical implementers and DevOps engineers

#### `docs/lambda-automation-guide.md`
- **Purpose**: Deep technical guide for Lambda solution
- **Sections**: Architecture, deployment, monitoring, troubleshooting, best practices
- **Audience**: DevOps engineers and system administrators

### Configuration Files

#### `requirements.txt`
- **Purpose**: Python dependencies for all scripts
- **Dependencies**: boto3, botocore, schedule, python-dateutil
- **Usage**: `pip install -r requirements.txt`

#### `.gitignore`
- **Purpose**: Excludes sensitive and temporary files from version control
- **Patterns**: AWS credentials, logs, temporary files, IDE files, OS files

#### `LICENSE`
- **Purpose**: Apache 2.0 license for open source distribution
- **Permissions**: Commercial use, modification, distribution, private use

### GitHub Configuration

#### `.github/workflows/validate.yml`
- **Purpose**: Continuous integration and validation
- **Jobs**:
  - CloudFormation template validation
  - Python code linting and syntax checking
  - Shell script validation with shellcheck
  - Security scanning
- **Triggers**: Push to main/develop, pull requests

## Resource Naming Conventions

### ACA Branding
All AWS resources use the `aca-` prefix for consistent identification:

- **Redshift Cluster**: `aca-redshift-cluster`
- **VPC**: `aca-redshift-vpc` / `aca-redshift-target-vpc`
- **Subnets**: `aca-redshift-subnet-1`, `aca-redshift-subnet-2`
- **KMS Keys**: `alias/aca-redshift-key`, `alias/aca-backup-key`
- **Backup Vaults**: `aca-redshift-vault`, `aca-redshift-cross-account-vault`
- **Lambda Function**: `aca-redshift-backup`
- **IAM Roles**: `AcaAWSBackupServiceRole-Redshift`, `AcaRedshiftBackupLambdaRole`

### CloudFormation Stacks
- **Source Account**: `aca-redshift-source`
- **Target Account**: `aca-redshift-target`
- **Lambda Automation**: `aca-lambda-backup`

### Snapshot Naming
- **Manual Demo**: `demo-snapshot-YYYYMMDD-HHMMSS`
- **Lambda Automation**: `aca-lambda-snapshot-YYYYMMDD-HHMMSS`
- **AWS Backup**: `awsbackup:job-{job-id}`

## Development Workflow

### Local Development
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure AWS profiles: `source` and `target`
4. Deploy infrastructure: `./quick-deploy.sh`
5. Test changes with demo scripts
6. Clean up resources: `./cleanup.sh`

### Contributing
1. Fork repository
2. Create feature branch
3. Make changes following coding standards
4. Test thoroughly with actual AWS resources
5. Update documentation
6. Submit pull request

### Release Process
1. Update version numbers
2. Update CHANGELOG.md
3. Test all deployment scenarios
4. Create GitHub release
5. Update documentation

## Security Considerations

### Sensitive Information
- AWS credentials never committed to repository
- Account IDs are examples (can be customized)
- KMS keys use customer-managed encryption
- IAM roles follow least-privilege principles

### Access Control
- Cross-account permissions limited to specific operations
- Snapshot sharing restricted to designated target account
- Lambda execution role has minimal required permissions
- All resources support encryption at rest and in transit

## Monitoring and Observability

### CloudWatch Integration
- Lambda function logs: `/aws/lambda/aca-redshift-backup`
- CloudFormation events tracked
- Custom metrics for backup success/failure rates
- Alarms for operational issues

### Notifications
- SNS topics for operational alerts
- Email notifications for backup failures
- CloudWatch alarms for Lambda errors
- Optional integration with external monitoring systems

## Cost Management

### Resource Optimization
- Automatic snapshot retention prevents cost accumulation
- Lambda execution optimized for minimal runtime
- Storage costs tracked and reported
- Regular cleanup of unused resources

### Cost Monitoring
- CloudWatch cost metrics
- Resource tagging for cost allocation
- Regular cost analysis and optimization recommendations
- Comparison reporting between approaches

This project structure supports scalable development, comprehensive testing, and production deployment while maintaining clear separation of concerns and following AWS best practices.