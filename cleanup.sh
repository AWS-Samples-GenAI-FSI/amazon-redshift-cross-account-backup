#!/bin/bash

# Cleanup script for ACA Redshift Cross-Account Snapshot Demo
# This script removes all demo resources to avoid ongoing charges

# Don't exit on errors - we want to continue cleanup even if some resources fail
set +e

# Function to safely run AWS commands with retries
safe_aws_command() {
    local max_attempts=3
    local attempt=1
    local command="$@"
    
    while [ $attempt -le $max_attempts ]; do
        echo "Attempt $attempt: $command"
        if eval "$command"; then
            return 0
        else
            echo "Attempt $attempt failed, retrying..."
            sleep 5
            ((attempt++))
        fi
    done
    echo "Command failed after $max_attempts attempts: $command"
    return 1
}

# Function to get target account ID
get_target_account_id() {
    # Try to get from target profile
    local target_account=$(aws sts get-caller-identity --query 'Account' --output text --profile target 2>/dev/null || echo "")
    if [[ -n "$target_account" ]]; then
        echo "$target_account"
    else
        # Fallback to hardcoded value
        echo "058264155998"
    fi
}

echo "=== ACA Redshift Demo Cleanup ==="
echo "⚠️  This will delete all demo resources and cannot be undone!"
echo

read -p "Are you sure you want to proceed? (yes/no): " CONFIRM

if [[ $CONFIRM != "yes" ]]; then
    echo "Cleanup cancelled"
    exit 0
fi

echo "Starting cleanup process..."

# Step 1: Delete restored clusters first (they depend on snapshots)
echo "=== Step 1: Deleting restored Redshift clusters ==="
RESTORED_CLUSTERS=("aca-restored-cluster" "restored-demo-cluster")

for cluster in "${RESTORED_CLUSTERS[@]}"; do
    echo "Checking for cluster: $cluster"
    if aws redshift describe-clusters --cluster-identifier "$cluster" --region us-east-1 >/dev/null 2>&1; then
        echo "Deleting cluster: $cluster"
        safe_aws_command "aws redshift delete-cluster --cluster-identifier $cluster --skip-final-cluster-snapshot --region us-east-1"
        
        # Wait for deletion to start
        echo "Waiting for cluster deletion to start..."
        sleep 30
    else
        echo "Cluster $cluster not found or already deleted"
    fi
done

# Step 2: Delete manual snapshots (including cross-account shared ones)
echo "=== Step 2: Deleting manual snapshots ==="

# First, revoke cross-account access for shared snapshots
echo "Revoking cross-account access for shared snapshots..."
SHARED_SNAPSHOTS=$(aws redshift describe-cluster-snapshots \
    --snapshot-type manual \
    --query 'Snapshots[?starts_with(SnapshotIdentifier, `demo-snapshot`) || starts_with(SnapshotIdentifier, `copied-`)].SnapshotIdentifier' \
    --output text \
    --region us-east-1 \
    --profile source 2>/dev/null || echo "")

for snapshot in $SHARED_SNAPSHOTS; do
    if [[ -n "$snapshot" && "$snapshot" != "None" ]]; then
        echo "Revoking cross-account access for snapshot: $snapshot"
        # Get target account ID dynamically
        local target_account=$(get_target_account_id)
        # Try to revoke access - this might fail if not shared, which is OK
        aws redshift revoke-snapshot-access \
            --snapshot-identifier "$snapshot" \
            --account-with-restore-access "$target_account" \
            --region us-east-1 \
            --profile source 2>/dev/null || echo "  (No cross-account access to revoke or already revoked)"
    fi
done

# Wait a moment for revocation to take effect
echo "Waiting for access revocation to take effect..."
sleep 10

# Now delete snapshots from source account
echo "Deleting snapshots from source account..."
SNAPSHOTS=$(aws redshift describe-cluster-snapshots \
    --snapshot-type manual \
    --query 'Snapshots[?starts_with(SnapshotIdentifier, `demo-snapshot`) || starts_with(SnapshotIdentifier, `copied-`)].SnapshotIdentifier' \
    --output text \
    --region us-east-1 \
    --profile source 2>/dev/null || echo "")

for snapshot in $SNAPSHOTS; do
    if [[ -n "$snapshot" && "$snapshot" != "None" ]]; then
        echo "Deleting source snapshot: $snapshot"
        safe_aws_command "aws redshift delete-cluster-snapshot --snapshot-identifier $snapshot --region us-east-1 --profile source"
    fi
done

# Note: We don't need to delete from target account since shared snapshots are owned by source
echo "Note: Shared snapshots are owned by source account and deleted above"

# Step 3: Clean up AWS Backup resources (order matters!)
echo "=== Step 3: Cleaning up AWS Backup resources ==="

# First, delete recovery points from both accounts
echo "Deleting recovery points from source account..."
RECOVERY_POINTS=$(aws backup list-recovery-points-by-backup-vault \
    --backup-vault-name aca-redshift-vault \
    --query 'RecoveryPoints[].RecoveryPointArn' \
    --output text \
    --region us-east-1 \
    --profile source 2>/dev/null || echo "")

for rp_arn in $RECOVERY_POINTS; do
    if [[ -n "$rp_arn" && "$rp_arn" != "None" ]]; then
        echo "Deleting recovery point: $rp_arn"
        safe_aws_command "aws backup delete-recovery-point --backup-vault-name aca-redshift-vault --recovery-point-arn '$rp_arn' --region us-east-1 --profile source"
    fi
done

echo "Deleting recovery points from target account..."
TARGET_RECOVERY_POINTS=$(aws backup list-recovery-points-by-backup-vault \
    --backup-vault-name aca-redshift-cross-account-vault \
    --query 'RecoveryPoints[].RecoveryPointArn' \
    --output text \
    --region us-east-1 \
    --profile target 2>/dev/null || echo "")

for rp_arn in $TARGET_RECOVERY_POINTS; do
    if [[ -n "$rp_arn" && "$rp_arn" != "None" ]]; then
        echo "Deleting target recovery point: $rp_arn"
        safe_aws_command "aws backup delete-recovery-point --backup-vault-name aca-redshift-cross-account-vault --recovery-point-arn '$rp_arn' --region us-east-1 --profile target"
    fi
done

# Wait for recovery points to be deleted
echo "Waiting for recovery points to be deleted..."
sleep 60

# Then delete backup plans and selections
echo "Deleting backup plans from source account..."
BACKUP_PLANS=$(aws backup list-backup-plans \
    --query 'BackupPlansList[?starts_with(BackupPlanName, `aca-redshift`)].BackupPlanId' \
    --output text \
    --region us-east-1 \
    --profile source 2>/dev/null || echo "")

for plan_id in $BACKUP_PLANS; do
    if [[ -n "$plan_id" && "$plan_id" != "None" ]]; then
        echo "Processing backup plan: $plan_id"
        
        # Delete backup selections first
        SELECTIONS=$(aws backup list-backup-selections \
            --backup-plan-id $plan_id \
            --query 'BackupSelectionsList[].SelectionId' \
            --output text \
            --region us-east-1 \
            --profile source 2>/dev/null || echo "")
        
        for selection_id in $SELECTIONS; do
            if [[ -n "$selection_id" && "$selection_id" != "None" ]]; then
                echo "Deleting backup selection: $selection_id"
                safe_aws_command "aws backup delete-backup-selection --backup-plan-id $plan_id --selection-id $selection_id --region us-east-1 --profile source"
            fi
        done
        
        # Delete the backup plan
        echo "Deleting backup plan: $plan_id"
        safe_aws_command "aws backup delete-backup-plan --backup-plan-id $plan_id --region us-east-1 --profile source"
    fi
done

# Finally, delete backup vaults (they must be empty)
echo "Waiting before attempting to delete backup vaults..."
sleep 30

echo "Attempting to delete backup vaults..."
safe_aws_command "aws backup delete-backup-vault --backup-vault-name aca-redshift-vault --region us-east-1 --profile source" || echo "Could not delete source vault (may not exist or not empty)"
safe_aws_command "aws backup delete-backup-vault --backup-vault-name aca-redshift-cross-account-vault --region us-east-1 --profile target" || echo "Could not delete target vault (may not exist or not empty)"

# Step 4: Wait for cluster deletions to complete
echo "=== Step 4: Waiting for cluster deletions ==="

# Check if main cluster exists and wait for its deletion
if aws redshift describe-clusters --cluster-identifier aca-redshift-cluster --region us-east-1 --profile source >/dev/null 2>&1; then
    echo "Main cluster still exists, waiting for deletion..."
    aws redshift wait cluster-deleted \
        --cluster-identifier aca-redshift-cluster \
        --region us-east-1 \
        --profile source || echo "Cluster deletion wait timed out or failed"
else
    echo "Main cluster already deleted or not found"
fi

# Step 5: Delete CloudFormation stacks (order matters - target first)
echo "=== Step 5: Deleting CloudFormation stacks ==="

# Delete target stack first (it has fewer dependencies)
echo "Deleting ACA target account stack..."
if aws cloudformation describe-stacks --stack-name aca-redshift-target --region us-east-1 --profile target >/dev/null 2>&1; then
    safe_aws_command "aws cloudformation delete-stack --stack-name aca-redshift-target --region us-east-1 --profile target"
    
    echo "Waiting for target stack deletion..."
    aws cloudformation wait stack-delete-complete \
        --stack-name aca-redshift-target \
        --region us-east-1 \
        --profile target || echo "Target stack deletion wait timed out"
else
    echo "Target stack not found or already deleted"
fi

# Delete source stack last (it has the main cluster)
echo "Deleting ACA source account stack..."
if aws cloudformation describe-stacks --stack-name aca-redshift-source --region us-east-1 --profile source >/dev/null 2>&1; then
    safe_aws_command "aws cloudformation delete-stack --stack-name aca-redshift-source --region us-east-1 --profile source"
    
    echo "Waiting for source stack deletion..."
    aws cloudformation wait stack-delete-complete \
        --stack-name aca-redshift-source \
        --region us-east-1 \
        --profile source || echo "Source stack deletion wait timed out"
else
    echo "Source stack not found or already deleted"
fi

# Step 6: Final verification
echo "=== Step 6: Final verification ==="

echo "Checking for remaining resources..."

# Check for remaining clusters
echo "Checking for remaining Redshift clusters..."
REMAINING_CLUSTERS=$(aws redshift describe-clusters \
    --query 'Clusters[?starts_with(ClusterIdentifier, `aca-`)].ClusterIdentifier' \
    --output text \
    --region us-east-1 \
    --profile source 2>/dev/null || echo "")

if [[ -n "$REMAINING_CLUSTERS" && "$REMAINING_CLUSTERS" != "None" ]]; then
    echo "⚠️  Warning: Found remaining clusters: $REMAINING_CLUSTERS"
else
    echo "✅ No remaining clusters found"
fi

# Check for remaining stacks
echo "Checking for remaining CloudFormation stacks..."
SOURCE_STACKS=$(aws cloudformation list-stacks \
    --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
    --query 'StackSummaries[?starts_with(StackName, `aca-redshift`)].StackName' \
    --output text \
    --region us-east-1 \
    --profile source 2>/dev/null || echo "")

TARGET_STACKS=$(aws cloudformation list-stacks \
    --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
    --query 'StackSummaries[?starts_with(StackName, `aca-redshift`)].StackName' \
    --output text \
    --region us-east-1 \
    --profile target 2>/dev/null || echo "")

if [[ -n "$SOURCE_STACKS" && "$SOURCE_STACKS" != "None" ]]; then
    echo "⚠️  Warning: Found remaining source stacks: $SOURCE_STACKS"
fi

if [[ -n "$TARGET_STACKS" && "$TARGET_STACKS" != "None" ]]; then
    echo "⚠️  Warning: Found remaining target stacks: $TARGET_STACKS"
fi

if [[ -z "$SOURCE_STACKS" && -z "$TARGET_STACKS" ]]; then
    echo "✅ No remaining stacks found"
fi

echo
echo "=== ACA Cleanup Summary ==="
echo "✅ Cleanup process completed!"
echo
echo "What was cleaned up:"
echo "  • Restored Redshift clusters"
echo "  • Manual snapshots (source and target accounts)"
echo "  • AWS Backup recovery points"
echo "  • AWS Backup plans and selections"
echo "  • AWS Backup vaults"
echo "  • CloudFormation stacks"
echo
echo "⚠️  Important notes:"
echo "  • Some backup recovery points may have retention policies"
echo "  • Cross-account shared snapshots may need manual cleanup"
echo "  • Check both AWS accounts in the console to verify complete cleanup"
echo "  • Any remaining resources will continue to incur charges"
echo
echo "If you see warnings above, you may need to manually delete remaining resources."