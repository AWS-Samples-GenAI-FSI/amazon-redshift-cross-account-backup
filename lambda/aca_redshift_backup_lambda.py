#!/usr/bin/env python3
"""
ACA Redshift Lambda Backup Function
Serverless implementation of native Redshift snapshot sharing
"""

import json
import boto3
import time
from datetime import datetime
from typing import Dict, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class AcaRedshiftBackupLambda:
    def __init__(self):
        """Initialize with Lambda execution role credentials"""
        self.source_redshift = boto3.client('redshift')
        self.target_redshift = boto3.client('redshift', region_name='us-east-1')  # Cross-account client
        
        # Get account info from STS
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        self.source_account_id = identity['Account']
        
        logger.info(f"Lambda initialized for source account: {self.source_account_id}")

    def create_manual_snapshot(self, cluster_identifier: str, target_account_id: str) -> str:
        """Create a manual snapshot of the Redshift cluster"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        snapshot_identifier = f"aca-lambda-snapshot-{timestamp}"
        
        logger.info(f"Creating manual snapshot: {snapshot_identifier}")
        
        try:
            response = self.source_redshift.create_cluster_snapshot(
                SnapshotIdentifier=snapshot_identifier,
                ClusterIdentifier=cluster_identifier,
                Tags=[
                    {'Key': 'Purpose', 'Value': 'AcaCrossAccountBackup'},
                    {'Key': 'CreatedBy', 'Value': 'AcaLambdaFunction'},
                    {'Key': 'TargetAccount', 'Value': target_account_id},
                    {'Key': 'Timestamp', 'Value': timestamp}
                ]
            )
            
            logger.info(f"Snapshot creation initiated: {snapshot_identifier}")
            return snapshot_identifier
            
        except Exception as e:
            logger.error(f"Error creating snapshot: {str(e)}")
            raise

    def wait_for_snapshot_completion(self, snapshot_identifier: str, max_wait_minutes: int = 15) -> bool:
        """Wait for snapshot to complete (with Lambda timeout considerations)"""
        logger.info(f"Waiting for snapshot completion: {snapshot_identifier}")
        start_time = time.time()
        max_wait_seconds = max_wait_minutes * 60
        
        while time.time() - start_time < max_wait_seconds:
            try:
                response = self.source_redshift.describe_cluster_snapshots(
                    SnapshotIdentifier=snapshot_identifier
                )
                
                if response['Snapshots']:
                    status = response['Snapshots'][0]['Status']
                    logger.info(f"Snapshot status: {status}")
                    
                    if status == 'available':
                        logger.info(f"Snapshot completed successfully: {snapshot_identifier}")
                        return True
                    elif status == 'failed':
                        logger.error("Snapshot creation failed")
                        raise Exception("Snapshot creation failed")
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error checking snapshot status: {str(e)}")
                time.sleep(30)
        
        # If we reach here, snapshot is still in progress
        logger.warning(f"Snapshot still in progress after {max_wait_minutes} minutes")
        return False

    def share_snapshot_with_account(self, snapshot_identifier: str, target_account_id: str) -> bool:
        """Share snapshot with target account"""
        logger.info(f"Sharing snapshot {snapshot_identifier} with account {target_account_id}")
        
        try:
            response = self.source_redshift.authorize_snapshot_access(
                SnapshotIdentifier=snapshot_identifier,
                AccountWithRestoreAccess=target_account_id
            )
            
            logger.info("Snapshot shared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error sharing snapshot: {str(e)}")
            return False

    def cleanup_old_snapshots(self, cluster_identifier: str, retention_days: int = 7) -> int:
        """Clean up old snapshots based on retention policy"""
        logger.info(f"Cleaning up snapshots older than {retention_days} days")
        
        try:
            # Get all manual snapshots for this cluster
            response = self.source_redshift.describe_cluster_snapshots(
                ClusterIdentifier=cluster_identifier,
                SnapshotType='manual'
            )
            
            deleted_count = 0
            cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 3600)
            
            for snapshot in response.get('Snapshots', []):
                snapshot_id = snapshot['SnapshotIdentifier']
                
                # Only delete our Lambda-created snapshots
                if snapshot_id.startswith('aca-lambda-snapshot-'):
                    snapshot_time = snapshot['SnapshotCreateTime'].timestamp()
                    
                    if snapshot_time < cutoff_time:
                        logger.info(f"Deleting old snapshot: {snapshot_id}")
                        try:
                            self.source_redshift.delete_cluster_snapshot(
                                SnapshotIdentifier=snapshot_id
                            )
                            deleted_count += 1
                        except Exception as e:
                            logger.warning(f"Could not delete snapshot {snapshot_id}: {str(e)}")
            
            logger.info(f"Cleaned up {deleted_count} old snapshots")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return 0

def lambda_handler(event, context):
    """
    Lambda handler for ACA Redshift backup
    
    Expected event format:
    {
        "cluster_identifier": "aca-redshift-cluster",
        "target_account_id": "058264155998",
        "retention_days": 7,
        "wait_for_completion": false
    }
    """
    
    logger.info(f"Lambda invoked with event: {json.dumps(event)}")
    
    try:
        # Parse event parameters
        cluster_identifier = event.get('cluster_identifier', 'aca-redshift-cluster')
        target_account_id = event.get('target_account_id')
        retention_days = event.get('retention_days', 7)
        wait_for_completion = event.get('wait_for_completion', False)
        
        if not target_account_id:
            raise ValueError("target_account_id is required")
        
        # Initialize backup handler
        backup_handler = AcaRedshiftBackupLambda()
        
        # Create snapshot
        snapshot_id = backup_handler.create_manual_snapshot(cluster_identifier, target_account_id)
        
        result = {
            'statusCode': 200,
            'snapshot_id': snapshot_id,
            'cluster_identifier': cluster_identifier,
            'target_account_id': target_account_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'snapshot_initiated'
        }
        
        # Optionally wait for completion (for smaller snapshots)
        if wait_for_completion:
            completed = backup_handler.wait_for_snapshot_completion(snapshot_id, max_wait_minutes=10)
            if completed:
                # Share the snapshot
                shared = backup_handler.share_snapshot_with_account(snapshot_id, target_account_id)
                result['shared'] = shared
                result['status'] = 'completed_and_shared' if shared else 'completed_not_shared'
            else:
                result['status'] = 'snapshot_in_progress'
        else:
            # For async operation, trigger sharing via another Lambda or Step Function
            result['status'] = 'snapshot_initiated_async'
        
        # Clean up old snapshots
        deleted_count = backup_handler.cleanup_old_snapshots(cluster_identifier, retention_days)
        result['cleaned_up_snapshots'] = deleted_count
        
        logger.info(f"Lambda completed successfully: {json.dumps(result)}")
        return result
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {
        "cluster_identifier": "aca-redshift-cluster",
        "target_account_id": "058264155998",
        "retention_days": 7,
        "wait_for_completion": True
    }
    
    class MockContext:
        def __init__(self):
            self.function_name = "aca-redshift-backup"
            self.memory_limit_in_mb = 512
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:aca-redshift-backup"
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))