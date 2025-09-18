#!/usr/bin/env python3
"""
Copyright 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

AWS Backup Cross-Account Demo
Demonstrates cross-account Redshift backup using AWS Backup service
"""

import boto3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

class AWSBackupDemo:
    def __init__(self, source_profile: str = None, target_profile: str = None):
        """Initialize with AWS profiles for source and target accounts"""
        self.source_session = boto3.Session(profile_name=source_profile) if source_profile else boto3.Session()
        self.target_session = boto3.Session(profile_name=target_profile) if target_profile else boto3.Session()
        
        self.source_backup = self.source_session.client('backup')
        self.target_backup = self.target_session.client('backup')
        self.source_iam = self.source_session.client('iam')
        
        self.source_account_id = self.source_session.client('sts').get_caller_identity()['Account']
        self.target_account_id = self.target_session.client('sts').get_caller_identity()['Account']
        
        print(f"Source Account: {self.source_account_id}")
        print(f"Target Account: {self.target_account_id}")

    def create_backup_role(self) -> str:
        """Create IAM role for AWS Backup service"""
        role_name = "AWSBackupServiceRole-RedshiftDemo"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "backup.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Check if role already exists
            self.source_iam.get_role(RoleName=role_name)
            print(f"IAM role {role_name} already exists")
        except self.source_iam.exceptions.NoSuchEntityException:
            # Create the role
            print(f"Creating IAM role: {role_name}")
            self.source_iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Service role for AWS Backup to access Redshift"
            )
            
            # Attach AWS managed policy
            self.source_iam.attach_role_policy(
                RoleName=role_name,
                PolicyArn="arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
            )
            
            # Wait for role to be available
            time.sleep(10)
        
        role_arn = f"arn:aws:iam::{self.source_account_id}:role/{role_name}"
        print(f"Using IAM role: {role_arn}")
        return role_arn

    def create_backup_vault(self, vault_name: str) -> str:
        """Create backup vault in source account"""
        print(f"Creating backup vault: {vault_name}")
        
        try:
            response = self.source_backup.create_backup_vault(
                BackupVaultName=vault_name,
                BackupVaultTags={
                    'Purpose': 'RedshiftCrossAccountDemo',
                    'CreatedBy': 'AWSBackupDemo'
                }
            )
            
            vault_arn = response['BackupVaultArn']
            print(f"Backup vault created: {vault_arn}")
            return vault_arn
            
        except self.source_backup.exceptions.AlreadyExistsException:
            print(f"Backup vault {vault_name} already exists")
            response = self.source_backup.describe_backup_vault(BackupVaultName=vault_name)
            return response['BackupVaultArn']

    def create_backup_plan(self, plan_name: str, vault_name: str, role_arn: str) -> str:
        """Create backup plan for Redshift"""
        print(f"Creating backup plan: {plan_name}")
        
        backup_plan = {
            "BackupPlanName": plan_name,
            "Rules": [
                {
                    "RuleName": "RedshiftDailyBackup",
                    "TargetBackupVaultName": vault_name,
                    "ScheduleExpression": "cron(0 2 * * ? *)",  # Daily at 2 AM
                    "StartWindowMinutes": 60,
                    "CompletionWindowMinutes": 120,
                    "Lifecycle": {
                        "DeleteAfterDays": 30
                    },
                    "RecoveryPointTags": {
                        "Purpose": "RedshiftDemo",
                        "AutomatedBackup": "true"
                    }
                }
            ]
        }
        
        try:
            response = self.source_backup.create_backup_plan(
                BackupPlan=backup_plan,
                BackupPlanTags={
                    'Purpose': 'RedshiftCrossAccountDemo'
                }
            )
            
            plan_id = response['BackupPlanId']
            print(f"Backup plan created: {plan_id}")
            return plan_id
            
        except self.source_backup.exceptions.AlreadyExistsException:
            print(f"Backup plan {plan_name} already exists, finding existing plan...")
            # Find existing plan
            plans = self.source_backup.list_backup_plans()
            for plan in plans['BackupPlansList']:
                if plan['BackupPlanName'] == plan_name:
                    plan_id = plan['BackupPlanId']
                    print(f"Using existing backup plan: {plan_id}")
                    return plan_id
            raise Exception("Could not find existing backup plan")
        except Exception as e:
            print(f"Error creating backup plan: {str(e)}")
            raise

    def create_backup_selection(self, plan_id: str, cluster_arn: str, role_arn: str) -> str:
        """Create backup selection for Redshift cluster"""
        selection_name = "RedshiftClusterSelection"
        
        print(f"Creating backup selection: {selection_name}")
        
        backup_selection = {
            "SelectionName": selection_name,
            "IamRoleArn": role_arn,
            "Resources": [cluster_arn]
        }
        
        try:
            response = self.source_backup.create_backup_selection(
                BackupPlanId=plan_id,
                BackupSelection=backup_selection
            )
            
            selection_id = response['SelectionId']
            print(f"Backup selection created: {selection_id}")
            return selection_id
            
        except self.source_backup.exceptions.AlreadyExistsException:
            print(f"Backup selection {selection_name} already exists, finding existing selection...")
            # Find existing selection
            selections = self.source_backup.list_backup_selections(BackupPlanId=plan_id)
            for selection in selections['BackupSelectionsList']:
                if selection['SelectionName'] == selection_name:
                    selection_id = selection['SelectionId']
                    print(f"Using existing backup selection: {selection_id}")
                    return selection_id
            raise Exception("Could not find existing backup selection")
        except Exception as e:
            print(f"Error creating backup selection: {str(e)}")
            raise

    def start_backup_job(self, vault_name: str, resource_arn: str, role_arn: str) -> str:
        """Start an on-demand backup job"""
        print("Starting on-demand backup job...")
        
        try:
            response = self.source_backup.start_backup_job(
                BackupVaultName=vault_name,
                ResourceArn=resource_arn,
                IamRoleArn=role_arn,
                IdempotencyToken=str(int(time.time()))
            )
            
            job_id = response['BackupJobId']
            print(f"Backup job started: {job_id}")
            return job_id
            
        except Exception as e:
            print(f"Error starting backup job: {str(e)}")
            raise

    def wait_for_backup_completion(self, job_id: str, timeout: int = 3600):
        """Wait for backup job to complete"""
        print("Waiting for backup to complete...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.source_backup.describe_backup_job(BackupJobId=job_id)
                status = response['State']
                
                print(f"Backup job status: {status}")
                
                if status == 'COMPLETED':
                    recovery_point_arn = response['RecoveryPointArn']
                    print(f"Backup completed successfully: {recovery_point_arn}")
                    return recovery_point_arn
                elif status in ['FAILED', 'ABORTED', 'EXPIRED']:
                    raise Exception(f"Backup job failed with status: {status}")
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error checking backup status: {str(e)}")
                time.sleep(60)
        
        raise Exception("Timeout waiting for backup completion")

    def copy_backup_to_target_account(self, source_recovery_point_arn: str, 
                                    target_vault_name: str) -> str:
        """Copy backup to target account vault"""
        print(f"Copying backup to target account vault: {target_vault_name}")
        
        try:
            response = self.source_backup.start_copy_job(
                RecoveryPointArn=source_recovery_point_arn,
                SourceBackupVaultName=source_recovery_point_arn.split('/')[-2],
                DestinationBackupVaultArn=f"arn:aws:backup:us-east-1:{self.target_account_id}:backup-vault:{target_vault_name}",
                IamRoleArn=f"arn:aws:iam::{self.source_account_id}:role/AWSBackupServiceRole-RedshiftDemo"
            )
            
            copy_job_id = response['CopyJobId']
            print(f"Copy job started: {copy_job_id}")
            return copy_job_id
            
        except Exception as e:
            print(f"Error copying backup: {str(e)}")
            raise

    def list_recovery_points(self, vault_name: str) -> list:
        """List recovery points in backup vault"""
        print(f"Listing recovery points in vault: {vault_name}")
        
        try:
            response = self.source_backup.list_recovery_points_by_backup_vault(
                BackupVaultName=vault_name
            )
            
            recovery_points = response.get('RecoveryPoints', [])
            print(f"Found {len(recovery_points)} recovery points")
            
            for rp in recovery_points:
                print(f"  - {rp['RecoveryPointArn']} ({rp['Status']})")
            
            return recovery_points
            
        except Exception as e:
            print(f"Error listing recovery points: {str(e)}")
            return []

    def restore_from_backup(self, recovery_point_arn: str, new_cluster_id: str, 
                          subnet_group_name: str) -> str:
        """Restore Redshift cluster from backup"""
        print(f"Restoring cluster {new_cluster_id} from backup")
        
        metadata = {
            "ClusterIdentifier": new_cluster_id,
            "ClusterSubnetGroupName": subnet_group_name,
            "PubliclyAccessible": "false"
        }
        
        try:
            response = self.target_backup.start_restore_job(
                RecoveryPointArn=recovery_point_arn,
                Metadata=metadata,
                IamRoleArn=f"arn:aws:iam::{self.target_account_id}:role/AWSBackupServiceRole-RedshiftDemo"
            )
            
            restore_job_id = response['RestoreJobId']
            print(f"Restore job started: {restore_job_id}")
            return restore_job_id
            
        except Exception as e:
            print(f"Error starting restore job: {str(e)}")
            raise

def main():
    """Run the complete AWS Backup demo"""
    print("=== AWS Backup Cross-Account Demo ===\n")
    
    # Initialize demo with your account configuration
    # Using your configured AWS profiles
    demo = AWSBackupDemo(source_profile='source', target_profile='target')
    
    # Verify we're using the correct accounts
    expected_source = "164543933824"
    expected_target = "058264155998"
    
    if demo.source_account_id != expected_source:
        print(f"❌ Warning: Expected source account {expected_source}, got {demo.source_account_id}")
        print("Make sure your AWS credentials are configured for the source account")
    
    if demo.target_account_id != expected_target:
        print(f"❌ Warning: Expected target account {expected_target}, got {demo.target_account_id}")
        print("You'll need to configure target account credentials separately")
    
    # Get configuration from CloudFormation stacks
    try:
        cf_client = demo.source_session.client('cloudformation')
        source_stack = cf_client.describe_stacks(StackName='aca-redshift-source')
        source_outputs = {output['OutputKey']: output['OutputValue'] 
                         for output in source_stack['Stacks'][0]['Outputs']}
        
        vault_name = source_outputs['BackupVaultName']
        cluster_arn = source_outputs['ClusterArn']
        role_arn = source_outputs['BackupRoleArn']
        target_vault_name = "aca-redshift-cross-account-vault"
        
        print(f"Using CloudFormation resources:")
        print(f"  Backup Vault: {vault_name}")
        print(f"  Cluster ARN: {cluster_arn}")
        print(f"  Service Role: {role_arn}")
        
    except Exception as e:
        print(f"Could not get CloudFormation outputs: {str(e)}")
        print("Make sure the CloudFormation stack 'aca-redshift-source' is deployed")
        return 1
    
    try:
        # Step 1: Start on-demand backup (resources already exist from CloudFormation)
        job_id = demo.start_backup_job(vault_name, cluster_arn, role_arn)
        
        # Step 2: Wait for backup completion
        recovery_point_arn = demo.wait_for_backup_completion(job_id)
        
        # Step 3: List recovery points
        demo.list_recovery_points(vault_name)
        
        # Note: Cross-account copy is handled automatically by the backup plan
        print("\nNote: Cross-account backup copy is configured in the backup plan")
        print("Check the target account backup vault for copied recovery points")
        
        print("\n=== AWS Backup demo completed successfully! ===")
        print("Check the AWS Backup console to monitor backup and copy jobs.")
        
    except Exception as e:
        print(f"\nDemo failed: {str(e)}")

if __name__ == "__main__":
    main()