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

Native Redshift Snapshot Sharing Demo
Demonstrates cross-account snapshot sharing using native Redshift capabilities
"""

import boto3
import json
import time
from datetime import datetime
from typing import Dict, Any

class RedshiftSnapshotDemo:
    def __init__(self, source_profile: str = None, target_profile: str = None):
        """Initialize with AWS profiles for source and target accounts"""
        self.source_session = boto3.Session(profile_name=source_profile) if source_profile else boto3.Session()
        self.target_session = boto3.Session(profile_name=target_profile) if target_profile else boto3.Session()
        
        self.source_redshift = self.source_session.client('redshift')
        self.target_redshift = self.target_session.client('redshift')
        
        self.source_account_id = self.source_session.client('sts').get_caller_identity()['Account']
        self.target_account_id = self.target_session.client('sts').get_caller_identity()['Account']
        
        print(f"Source Account: {self.source_account_id}")
        print(f"Target Account: {self.target_account_id}")

    def create_manual_snapshot(self, cluster_identifier: str) -> str:
        """Create a manual snapshot of the Redshift cluster"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        snapshot_identifier = f"demo-snapshot-{timestamp}"
        
        print(f"Creating manual snapshot: {snapshot_identifier}")
        
        try:
            response = self.source_redshift.create_cluster_snapshot(
                SnapshotIdentifier=snapshot_identifier,
                ClusterIdentifier=cluster_identifier,
                Tags=[
                    {'Key': 'Purpose', 'Value': 'CrossAccountDemo'},
                    {'Key': 'CreatedBy', 'Value': 'RedshiftSnapshotDemo'}
                ]
            )
            
            # Wait for snapshot to complete
            self._wait_for_snapshot_completion(snapshot_identifier)
            
            print(f"Snapshot created successfully: {snapshot_identifier}")
            return snapshot_identifier
            
        except Exception as e:
            print(f"Error creating snapshot: {str(e)}")
            raise

    def _wait_for_snapshot_completion(self, snapshot_identifier: str, timeout: int = 1800):
        """Wait for snapshot to complete (up to 30 minutes)"""
        print("Waiting for snapshot to complete...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.source_redshift.describe_cluster_snapshots(
                    SnapshotIdentifier=snapshot_identifier
                )
                
                if response['Snapshots']:
                    status = response['Snapshots'][0]['Status']
                    print(f"Snapshot status: {status}")
                    
                    if status == 'available':
                        return True
                    elif status == 'failed':
                        raise Exception("Snapshot creation failed")
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"Error checking snapshot status: {str(e)}")
                time.sleep(30)
        
        raise Exception("Timeout waiting for snapshot completion")

    def share_snapshot_with_account(self, snapshot_identifier: str) -> bool:
        """Share snapshot with target account"""
        print(f"Sharing snapshot {snapshot_identifier} with account {self.target_account_id}")
        
        try:
            response = self.source_redshift.authorize_snapshot_access(
                SnapshotIdentifier=snapshot_identifier,
                AccountWithRestoreAccess=self.target_account_id
            )
            
            print("Snapshot shared successfully")
            return True
            
        except Exception as e:
            print(f"Error sharing snapshot: {str(e)}")
            return False

    def list_shared_snapshots(self) -> list:
        """List snapshots shared with target account"""
        print("Listing shared snapshots in target account...")
        
        try:
            response = self.target_redshift.describe_cluster_snapshots(
                SnapshotType='manual',
                OwnerAccount=self.source_account_id
            )
            
            snapshots = response.get('Snapshots', [])
            print(f"Found {len(snapshots)} shared snapshots")
            
            for snapshot in snapshots:
                print(f"  - {snapshot['SnapshotIdentifier']} ({snapshot['Status']})")
            
            return snapshots
            
        except Exception as e:
            print(f"Error listing shared snapshots: {str(e)}")
            return []

    def copy_snapshot_to_target(self, source_snapshot_identifier: str, target_cluster_identifier: str) -> str:
        """Copy shared snapshot in target account"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target_snapshot_identifier = f"copied-{source_snapshot_identifier}-{timestamp}"
        
        print(f"Copying snapshot to target account: {target_snapshot_identifier}")
        
        try:
            # For cross-account snapshots, we need to specify the source account
            full_source_snapshot_id = f"{self.source_account_id}:{source_snapshot_identifier}"
            response = self.target_redshift.copy_cluster_snapshot(
                SourceSnapshotIdentifier=full_source_snapshot_id,
                SourceSnapshotClusterIdentifier=source_cluster_identifier,
                TargetSnapshotIdentifier=target_snapshot_identifier
            )
            
            print(f"Snapshot copy initiated: {target_snapshot_identifier}")
            return target_snapshot_identifier
            
        except Exception as e:
            print(f"Error copying snapshot: {str(e)}")
            raise

    def restore_cluster_from_snapshot(self, snapshot_identifier: str, new_cluster_identifier: str, 
                                    subnet_group_name: str) -> bool:
        """Restore Redshift cluster from snapshot in target account"""
        print(f"Restoring cluster {new_cluster_identifier} from snapshot {snapshot_identifier}")
        
        try:
            response = self.target_redshift.restore_from_cluster_snapshot(
                ClusterIdentifier=new_cluster_identifier,
                SnapshotIdentifier=snapshot_identifier,
                OwnerAccount=self.source_account_id,
                ClusterSubnetGroupName=subnet_group_name,
                PubliclyAccessible=False
            )
            
            print(f"Cluster restore initiated: {new_cluster_identifier}")
            return True
            
        except Exception as e:
            print(f"Error restoring cluster: {str(e)}")
            return False

    def cleanup_snapshots(self, snapshot_identifiers: list):
        """Clean up demo snapshots"""
        print("Cleaning up snapshots...")
        
        for snapshot_id in snapshot_identifiers:
            try:
                # Try to delete from source account first
                self.source_redshift.delete_cluster_snapshot(
                    SnapshotIdentifier=snapshot_id
                )
                print(f"Deleted snapshot from source: {snapshot_id}")
            except:
                try:
                    # Try target account
                    self.target_redshift.delete_cluster_snapshot(
                        SnapshotIdentifier=snapshot_id
                    )
                    print(f"Deleted snapshot from target: {snapshot_id}")
                except Exception as e:
                    print(f"Could not delete snapshot {snapshot_id}: {str(e)}")

def main():
    """Run the complete demo"""
    print("=== Redshift Native Snapshot Sharing Demo ===\n")
    
    # Initialize demo with your account configuration
    # Using your configured AWS profiles
    demo = RedshiftSnapshotDemo(source_profile='source', target_profile='target')
    
    # Verify we're using the correct accounts
    expected_source = "164543933824"
    expected_target = "058264155998"
    
    if demo.source_account_id != expected_source:
        print(f"❌ Warning: Expected source account {expected_source}, got {demo.source_account_id}")
        print("Make sure your AWS credentials are configured for the source account")
    
    if demo.target_account_id != expected_target:
        print(f"❌ Warning: Expected target account {expected_target}, got {demo.target_account_id}")
        print("You'll need to configure target account credentials separately")
    
    # Configuration
    source_cluster_id = "aca-redshift-cluster"
    target_cluster_id = "aca-restored-cluster"
    
    # Get the actual subnet group name from CloudFormation
    try:
        cf_client = demo.target_session.client('cloudformation')
        response = cf_client.describe_stacks(StackName='aca-redshift-target')
        outputs = response['Stacks'][0]['Outputs']
        target_subnet_group = next(
            output['OutputValue'] for output in outputs 
            if output['OutputKey'] == 'TargetSubnetGroupName'
        )
        print(f"Using target subnet group: {target_subnet_group}")
    except Exception as e:
        print(f"Could not get subnet group from CloudFormation: {str(e)}")
        target_subnet_group = "aca-redshift-target-subnet-group"  # fallback
    
    snapshots_created = []
    
    try:
        # Step 1: Create manual snapshot
        snapshot_id = demo.create_manual_snapshot(source_cluster_id)
        snapshots_created.append(snapshot_id)
        
        # Step 2: Share snapshot with target account
        demo.share_snapshot_with_account(snapshot_id)
        
        # Step 3: List shared snapshots in target account
        shared_snapshots = demo.list_shared_snapshots()
        
        # Step 4: Copy snapshot in target account (optional - skipping for demo)
        print("Note: Skipping snapshot copy step - proceeding directly to restore")
        
        # Step 5: Restore cluster from snapshot using shared snapshot
        if shared_snapshots:
            # Use the shared snapshot directly for restore (without account prefix)
            demo.restore_cluster_from_snapshot(snapshot_id, target_cluster_id, target_subnet_group)
        
        print("\n=== Demo completed successfully! ===")
        print(f"Restored cluster: {target_cluster_id}")
        print("Check the AWS console to verify the restored cluster.")
        
    except Exception as e:
        print(f"\nDemo failed: {str(e)}")
    
    finally:
        # Cleanup (uncomment if you want automatic cleanup)
        # demo.cleanup_snapshots(snapshots_created)
        pass

if __name__ == "__main__":
    main()