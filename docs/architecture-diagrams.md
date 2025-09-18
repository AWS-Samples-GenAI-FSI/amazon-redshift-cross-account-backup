# Architecture Diagrams

This document provides detailed architecture diagrams for all three Amazon Redshift cross-account backup approaches.

## Overview Architecture

```mermaid
graph TB
    subgraph "Production Account (Source)"
        RC[Amazon Redshift Cluster]
        KMS1[KMS Key]
        VPC1[VPC & Subnets]
    end
    
    subgraph "Disaster Recovery Account (Target)"
        VPC2[VPC & Subnets]
        SG[Subnet Groups]
        KMS2[KMS Key]
        RRC[Restored Clusters<br/>On-Demand]
    end
    
    subgraph "Backup Approaches"
        A1[1. Native Manual Scripts]
        A2[2. Lambda Automation]
        A3[3. AWS Backup]
    end
    
    RC --> A1
    RC --> A2
    RC --> A3
    
    A1 -.-> RRC
    A2 -.-> RRC
    A3 -.-> RRC
    
    KMS1 -.-> KMS2
```

## 1. Native Manual Scripts Architecture

```mermaid
graph TB
    subgraph "Production Account"
        subgraph "VPC (10.0.0.0/16)"
            subgraph "Private Subnets"
                RC[Amazon Redshift Cluster<br/>aca-redshift-cluster]
            end
        end
        
        KMS1[KMS Customer Key<br/>alias/aca-redshift-key]
        MS[Manual Snapshots<br/>demo-snapshot-*]
        
        RC --> MS
        KMS1 --> RC
    end
    
    subgraph "Target Account"
        subgraph "VPC (10.1.0.0/16)"
            subgraph "Private Subnets"
                RSG[Redshift Subnet Group<br/>aca-target-subnet-group]
                RRC[Restored Cluster<br/>aca-restored-cluster]
            end
        end
        
        KMS2[KMS Customer Key<br/>alias/aca-backup-key]
        SS[Shared Snapshots<br/>Cross-Account Access]
        
        RSG --> RRC
        KMS2 --> RRC
    end
    
    subgraph "Manual Process"
        DEV[Developer/Operator]
        SCRIPT[Python Script<br/>native_snapshot_demo.py]
        
        DEV --> SCRIPT
    end
    
    SCRIPT --> RC
    MS -.->|Cross-Account Share| SS
    SS --> RRC
    
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef manual fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
    
    class RC,KMS1,MS,RSG,RRC,KMS2,SS aws
    class DEV,SCRIPT manual
```

## 2. Lambda-Based Automation Architecture

```mermaid
graph TB
    subgraph "Production Account"
        subgraph "VPC (10.0.0.0/16)"
            subgraph "Private Subnets"
                RC[Amazon Redshift Cluster<br/>aca-redshift-cluster]
            end
        end
        
        subgraph "Serverless Automation"
            EB[Amazon EventBridge<br/>Schedule Rule]
            LF[AWS Lambda Function<br/>aca-redshift-backup]
            CW[CloudWatch Logs<br/>& Metrics]
            SNS[Amazon SNS<br/>Notifications]
        end
        
        KMS1[KMS Customer Key<br/>alias/aca-redshift-key]
        AS[Automated Snapshots<br/>aca-lambda-snapshot-*]
        IAM1[IAM Execution Role<br/>AcaRedshiftBackupLambdaRole]
        
        EB -->|Trigger| LF
        LF --> RC
        LF --> CW
        LF --> SNS
        LF --> AS
        RC --> AS
        KMS1 --> RC
        IAM1 --> LF
    end
    
    subgraph "Target Account"
        subgraph "VPC (10.1.0.0/16)"
            subgraph "Private Subnets"
                RSG[Redshift Subnet Group<br/>aca-target-subnet-group]
                RRC[Restored Cluster<br/>On-Demand]
            end
        end
        
        KMS2[KMS Customer Key<br/>alias/aca-backup-key]
        SS[Shared Snapshots<br/>Cross-Account Access]
        
        RSG --> RRC
        KMS2 --> RRC
    end
    
    subgraph "Monitoring & Alerts"
        EMAIL[Email Notifications]
        DASH[CloudWatch Dashboard]
        ALARM[CloudWatch Alarms]
        
        SNS --> EMAIL
        CW --> DASH
        CW --> ALARM
        ALARM --> SNS
    end
    
    AS -.->|Auto-Share| SS
    SS --> RRC
    
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef serverless fill:#9C27B0,stroke:#4A148C,stroke-width:2px,color:#fff
    classDef monitoring fill:#2196F3,stroke:#0D47A1,stroke-width:2px,color:#fff
    
    class RC,KMS1,AS,RSG,RRC,KMS2,SS,IAM1 aws
    class EB,LF,SNS serverless
    class CW,EMAIL,DASH,ALARM monitoring
```

## 3. AWS Backup Integration Architecture

```mermaid
graph TB
    subgraph "Production Account"
        subgraph "VPC (10.0.0.0/16)"
            subgraph "Private Subnets"
                RC[Amazon Redshift Cluster<br/>aca-redshift-cluster]
            end
        end
        
        subgraph "AWS Backup Service"
            BV1[AWS Backup Vault<br/>aca-redshift-vault]
            BP[Backup Plan<br/>aca-redshift-plan]
            BS[Backup Selection<br/>AcaRedshiftClusterSelection]
            BJ[Backup Jobs<br/>Scheduled & On-Demand]
        end
        
        KMS1[KMS Customer Key<br/>alias/aca-redshift-key]
        IAM1[IAM Service Role<br/>AcaAWSBackupServiceRole-Redshift]
        RP1[Recovery Points<br/>awsbackup:job-*]
        
        BP --> BS
        BS --> RC
        BJ --> RC
        BJ --> BV1
        BV1 --> RP1
        KMS1 --> RC
        KMS1 --> BV1
        IAM1 --> BJ
    end
    
    subgraph "Target Account"
        subgraph "VPC (10.1.0.0/16)"
            subgraph "Private Subnets"
                RSG[Redshift Subnet Group<br/>aca-target-subnet-group]
                RRC[Restored Cluster<br/>On-Demand]
            end
        end
        
        subgraph "AWS Backup Service"
            BV2[AWS Backup Vault<br/>aca-redshift-cross-account-vault]
            RJ[Restore Jobs<br/>Cross-Account]
        end
        
        KMS2[KMS Customer Key<br/>alias/aca-backup-key]
        RP2[Recovery Points<br/>Cross-Account Copies]
        
        BV2 --> RP2
        RJ --> RSG
        RSG --> RRC
        KMS2 --> RRC
        KMS2 --> BV2
    end
    
    subgraph "Enterprise Features"
        CONFIG[AWS Config<br/>Compliance]
        TRAIL[AWS CloudTrail<br/>Audit Logs]
        REPORT[Backup Reports<br/>& Compliance]
        
        BJ --> CONFIG
        BJ --> TRAIL
        BV1 --> REPORT
        BV2 --> REPORT
    end
    
    RP1 -.->|Cross-Account Copy| RP2
    RP2 --> RRC
    
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef backup fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
    classDef enterprise fill:#9C27B0,stroke:#4A148C,stroke-width:2px,color:#fff
    
    class RC,KMS1,RSG,RRC,KMS2,IAM1 aws
    class BV1,BP,BS,BJ,BV2,RJ,RP1,RP2 backup
    class CONFIG,TRAIL,REPORT enterprise
```

## Data Flow Diagrams

### Native Manual Process Flow

```mermaid
sequenceDiagram
    participant O as Operator
    participant S as Python Script
    participant RC as Redshift Cluster
    participant SA as Source Account
    participant TA as Target Account
    participant TR as Target Redshift
    
    O->>S: Execute native_snapshot_demo.py
    S->>RC: Create manual snapshot
    RC-->>S: Snapshot ID
    S->>S: Wait for completion (30 min)
    S->>SA: Authorize cross-account access
    SA-->>TA: Share snapshot
    S->>TA: List shared snapshots
    S->>TR: Restore cluster from snapshot
    TR-->>S: Cluster restoration initiated
    S-->>O: Demo completed
```

### Lambda Automation Flow

```mermaid
sequenceDiagram
    participant EB as EventBridge
    participant LF as Lambda Function
    participant RC as Redshift Cluster
    participant SA as Source Account
    participant TA as Target Account
    participant CW as CloudWatch
    participant SNS as SNS Topic
    
    EB->>LF: Scheduled trigger (cron)
    LF->>RC: Create snapshot
    RC-->>LF: Snapshot ID
    LF->>SA: Share with target account
    SA-->>TA: Cross-account access granted
    LF->>LF: Cleanup old snapshots
    LF->>CW: Log execution details
    LF->>SNS: Send success notification
    SNS-->>LF: Email sent (if configured)
```

### AWS Backup Process Flow

```mermaid
sequenceDiagram
    participant BP as Backup Plan
    participant BJ as Backup Job
    participant RC as Redshift Cluster
    participant BV1 as Source Vault
    participant BV2 as Target Vault
    participant CJ as Copy Job
    participant RJ as Restore Job
    
    BP->>BJ: Scheduled backup
    BJ->>RC: Create backup
    RC-->>BV1: Store recovery point
    BV1->>CJ: Initiate cross-account copy
    CJ->>BV2: Copy to target vault
    BV2-->>RJ: Recovery point available
    Note over RJ: Restore when needed
    RJ->>RC: Restore cluster in target
```

## Security Architecture

```mermaid
graph TB
    subgraph "Security Controls"
        subgraph "Encryption"
            KMS1[Source KMS Key<br/>Customer Managed]
            KMS2[Target KMS Key<br/>Customer Managed]
            EAR[Encryption at Rest<br/>All Snapshots/Backups]
            EIT[Encryption in Transit<br/>TLS 1.2+]
        end
        
        subgraph "Access Control"
            IAM1[Source IAM Roles<br/>Least Privilege]
            IAM2[Target IAM Roles<br/>Least Privilege]
            XA[Cross-Account Trust<br/>Specific Account Only]
            MFA[MFA Required<br/>Administrative Access]
        end
        
        subgraph "Network Security"
            VPC1[Source VPC<br/>Private Subnets]
            VPC2[Target VPC<br/>Private Subnets]
            SG[Security Groups<br/>Restrictive Rules]
            NACL[Network ACLs<br/>Additional Layer]
        end
        
        subgraph "Audit & Compliance"
            CT[AWS CloudTrail<br/>API Logging]
            CW[CloudWatch Logs<br/>Application Logging]
            CONFIG[AWS Config<br/>Compliance Rules]
            GUARD[GuardDuty<br/>Threat Detection]
        end
    end
    
    subgraph "Data Protection"
        BACKUP[Backup Data]
        SNAPSHOT[Snapshot Data]
        RESTORE[Restored Data]
        
        KMS1 --> BACKUP
        KMS1 --> SNAPSHOT
        KMS2 --> RESTORE
        
        EAR --> BACKUP
        EAR --> SNAPSHOT
        EAR --> RESTORE
        
        EIT --> BACKUP
        EIT --> RESTORE
    end
    
    classDef security fill:#F44336,stroke:#B71C1C,stroke-width:2px,color:#fff
    classDef data fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
    
    class KMS1,KMS2,EAR,EIT,IAM1,IAM2,XA,MFA,VPC1,VPC2,SG,NACL,CT,CW,CONFIG,GUARD security
    class BACKUP,SNAPSHOT,RESTORE data
```

## Cost Optimization Architecture

```mermaid
graph TB
    subgraph "Cost Components"
        subgraph "Storage Costs"
            SS[Snapshot Storage<br/>$0.024/GB/month]
            BS[Backup Storage<br/>$0.05/GB/month]
            CS[Compute Storage<br/>Variable by node type]
        end
        
        subgraph "Compute Costs"
            RC[Running Clusters<br/>Source Account Only]
            LF[Lambda Execution<br/>~$0.20/month]
            BJ[Backup Jobs<br/>$0.05/1000 requests]
        end
        
        subgraph "Data Transfer"
            XR[Cross-Region<br/>$0.02/GB]
            XA[Cross-Account<br/>No additional charge]
            INT[Internet<br/>Not applicable]
        end
    end
    
    subgraph "Optimization Strategies"
        subgraph "Native Approach"
            AR[Automated Retention<br/>Delete old snapshots]
            SC[Smart Scheduling<br/>Off-peak hours]
            IC[Incremental Copies<br/>Redshift native]
        end
        
        subgraph "Lambda Approach"
            SO[Serverless Optimization<br/>No idle compute]
            ER[Efficient Runtime<br/>Minimal execution time]
            BR[Batch Retention<br/>Bulk cleanup]
        end
        
        subgraph "AWS Backup"
            LP[Lifecycle Policies<br/>Automated transitions]
            DD[Data Deduplication<br/>Built-in optimization]
            CR[Cross-Region Rules<br/>Selective copying]
        end
    end
    
    SS --> AR
    LF --> SO
    BS --> LP
    
    classDef cost fill:#FF9900,stroke:#E65100,stroke-width:2px,color:#fff
    classDef optimization fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
    
    class SS,BS,CS,RC,LF,BJ,XR,XA,INT cost
    class AR,SC,IC,SO,ER,BR,LP,DD,CR optimization
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Infrastructure as Code"
        subgraph "CloudFormation Templates"
            CFT1[source-account-setup.yaml<br/>Main Infrastructure]
            CFT2[target-account-setup.yaml<br/>DR Infrastructure]
            CFT3[aca-lambda-backup-setup.yaml<br/>Automation Infrastructure]
        end
        
        subgraph "Deployment Scripts"
            QD[quick-deploy.sh<br/>Full Infrastructure]
            LD[deploy-lambda-backup.sh<br/>Lambda Automation]
            DR[demo-runner.sh<br/>Interactive Demo]
            CU[cleanup.sh<br/>Resource Cleanup]
        end
    end
    
    subgraph "CI/CD Pipeline"
        subgraph "GitHub Actions"
            VAL[Template Validation<br/>CloudFormation Lint]
            TEST[Code Testing<br/>Python Syntax Check]
            SEC[Security Scan<br/>Static Analysis]
            DOC[Documentation<br/>Auto-generation]
        end
    end
    
    subgraph "Deployment Flow"
        DEV[Developer]
        GIT[Git Repository]
        AWS1[Source Account]
        AWS2[Target Account]
        
        DEV --> GIT
        GIT --> VAL
        VAL --> TEST
        TEST --> SEC
        SEC --> CFT1
        CFT1 --> AWS1
        CFT2 --> AWS2
        CFT3 --> AWS1
    end
    
    classDef iac fill:#9C27B0,stroke:#4A148C,stroke-width:2px,color:#fff
    classDef cicd fill:#2196F3,stroke:#0D47A1,stroke-width:2px,color:#fff
    classDef deploy fill:#FF9900,stroke:#E65100,stroke-width:2px,color:#fff
    
    class CFT1,CFT2,CFT3,QD,LD,DR,CU iac
    class VAL,TEST,SEC,DOC cicd
    class DEV,GIT,AWS1,AWS2 deploy
```

These diagrams provide comprehensive visual documentation of the architecture for all three approaches, including security, cost optimization, and deployment considerations.