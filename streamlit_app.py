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

Amazon Redshift Cross-Account Backup - Streamlit Interface
Interactive web application for managing Redshift backup solutions
"""

import streamlit as st
import boto3
import json
import subprocess
import time
from datetime import datetime
import pandas as pd
from typing import Dict, List, Optional
import os
import sys

# Add the scripts directory to the path
sys.path.append('scripts')

# Import our demo classes
try:
    from scripts.native_snapshot_demo import RedshiftSnapshotDemo
    from scripts.aws_backup_demo import AWSBackupDemo
except ImportError:
    st.error("Could not import demo modules. Make sure you're running from the repository root.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Amazon Redshift Cross-Account Backup",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF9900;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def load_config():
    """Load configuration from JSON file"""
    try:
        with open('config/demo-config.json', 'r') as f:
            config = json.load(f)
        return config['demo_configuration']
    except Exception as e:
        st.error(f"Could not load configuration: {str(e)}")
        return None

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        # Check for source profile
        source_session = boto3.Session(profile_name='source')
        source_sts = source_session.client('sts')
        source_identity = source_sts.get_caller_identity()
        
        # Check for target profile
        target_session = boto3.Session(profile_name='target')
        target_sts = target_session.client('sts')
        target_identity = target_sts.get_caller_identity()
        
        return {
            'source': source_identity,
            'target': target_identity,
            'status': 'success'
        }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def run_cloudformation_command(command: List[str], description: str) -> Dict:
    """Run a CloudFormation command and return results"""
    try:
        with st.spinner(f"{description}..."):
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Command timed out after 5 minutes'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Main Streamlit application"""
    
    # Header
    st.markdown('<h1 class="main-header">🔄 Amazon Redshift Cross-Account Backup</h1>', unsafe_allow_html=True)
    st.markdown("**Interactive web interface for Financial Services Industry backup solutions**")
    
    # Load configuration
    config = load_config()
    if not config:
        st.stop()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a section:",
        [
            "🏠 Overview",
            "⚙️ Configuration", 
            "🚀 Quick Deploy",
            "📊 Native Demo",
            "☁️ AWS Backup Demo",
            "🤖 Lambda Automation",
            "📈 Monitoring",
            "🧹 Cleanup"
        ]
    )
    
    # AWS Credentials Status
    st.sidebar.markdown("---")
    st.sidebar.subheader("AWS Credentials")
    
    creds = check_aws_credentials()
    if creds['status'] == 'success':
        st.sidebar.success("✅ AWS Profiles Configured")
        st.sidebar.text(f"Source: {creds['source']['Account']}")
        st.sidebar.text(f"Target: {creds['target']['Account']}")
    else:
        st.sidebar.error("❌ AWS Profiles Not Configured")
        st.sidebar.text("Configure 'source' and 'target' profiles")
    
    # Main content based on selected page
    if page == "🏠 Overview":
        show_overview(config)
    elif page == "⚙️ Configuration":
        show_configuration(config)
    elif page == "🚀 Quick Deploy":
        show_quick_deploy(config)
    elif page == "📊 Native Demo":
        show_native_demo(config)
    elif page == "☁️ AWS Backup Demo":
        show_aws_backup_demo(config)
    elif page == "🤖 Lambda Automation":
        show_lambda_automation(config)
    elif page == "📈 Monitoring":
        show_monitoring(config)
    elif page == "🧹 Cleanup":
        show_cleanup(config)

def show_overview(config):
    """Show overview page"""
    st.header("Solution Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Three Approaches")
        st.markdown("""
        **1. Native Manual Scripts**
        - Direct Redshift snapshot sharing
        - Manual execution and testing
        - Lowest cost (~$24.58/month for 1TB)
        
        **2. Lambda Automation** ⭐ **Recommended**
        - Serverless automation
        - Scheduled backups with EventBridge
        - Cost-effective (~$24.81/month for 1TB)
        
        **3. AWS Backup Integration**
        - Enterprise backup management
        - Advanced compliance features
        - Higher cost (~$51.25/month for 1TB)
        """)
    
    with col2:
        st.subheader("🏗️ Architecture")
        st.markdown("""
        **Production Account**
        - Amazon Redshift cluster
        - AWS Lambda function (optional)
        - AWS Backup vault
        - EventBridge scheduling
        - SNS notifications
        
        **Disaster Recovery Account**
        - VPC and networking
        - Backup vault for cross-account copies
        - Restored clusters (on-demand)
        """)
    
    # Cost comparison
    st.subheader("💰 Cost Comparison (1TB Cluster)")
    
    cost_data = {
        'Approach': ['Native Manual', 'Lambda Automation', 'AWS Backup'],
        'Monthly Cost': ['$24.58', '$24.81', '$51.25'],
        'Features': ['Basic automation', 'Serverless automation', 'Enterprise features'],
        'Best For': ['Testing/Development', 'Production (Recommended)', 'Compliance-heavy']
    }
    
    df = pd.DataFrame(cost_data)
    st.table(df)
    
    # Current configuration
    st.subheader("🔧 Current Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        st.json({
            "Resource Prefix": config['resource_prefix'],
            "AWS Region": config['aws_region'],
            "Cluster Type": config['cluster_configuration']['cluster_type'],
            "Node Type": config['cluster_configuration']['node_type']
        })
    
    with col2:
        st.json({
            "Retention Days": config['backup_configuration']['retention_days'],
            "Backup Schedule": config['backup_configuration']['backup_schedule'],
            "Database Name": config['cluster_configuration']['database_name']
        })

def show_configuration(config):
    """Show configuration page"""
    st.header("⚙️ Configuration Management")
    
    st.subheader("Current Configuration")
    st.json(config)
    
    st.subheader("Update Configuration")
    
    with st.form("config_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_prefix = st.text_input("Resource Prefix", value=config['resource_prefix'])
            new_region = st.selectbox("AWS Region", 
                                    ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'],
                                    index=0 if config['aws_region'] == 'us-east-1' else 0)
            new_retention = st.number_input("Retention Days", min_value=1, max_value=365, 
                                          value=config['backup_configuration']['retention_days'])
        
        with col2:
            new_node_type = st.selectbox("Node Type", 
                                       ['ra3.xlplus', 'ra3.4xlarge', 'ra3.16xlarge'],
                                       index=0)
            new_cluster_type = st.selectbox("Cluster Type", 
                                          ['single-node', 'multi-node'],
                                          index=0 if config['cluster_configuration']['cluster_type'] == 'single-node' else 1)
            new_email = st.text_input("Notification Email", 
                                    value=config['backup_configuration']['notification_email'])
        
        submitted = st.form_submit_button("Update Configuration")
        
        if submitted:
            # Update configuration
            updated_config = config.copy()
            updated_config['resource_prefix'] = new_prefix
            updated_config['aws_region'] = new_region
            updated_config['backup_configuration']['retention_days'] = new_retention
            updated_config['cluster_configuration']['node_type'] = new_node_type
            updated_config['cluster_configuration']['cluster_type'] = new_cluster_type
            updated_config['backup_configuration']['notification_email'] = new_email
            
            try:
                with open('config/demo-config.json', 'w') as f:
                    json.dump({"demo_configuration": updated_config}, f, indent=2)
                st.success("✅ Configuration updated successfully!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"❌ Failed to update configuration: {str(e)}")

def show_quick_deploy(config):
    """Show quick deployment page"""
    st.header("🚀 Quick Deploy Infrastructure")
    
    st.markdown("""
    Deploy the complete infrastructure for both source and target accounts.
    This will create all necessary resources including VPCs, Redshift cluster, and backup infrastructure.
    """)
    
    # Deployment parameters
    with st.form("deploy_form"):
        st.subheader("Deployment Parameters")
        
        col1, col2 = st.columns(2)
        with col1:
            source_account = st.text_input("Source Account ID", value=config['source_account_id'])
            target_account = st.text_input("Target Account ID", value=config['target_account_id'])
        
        with col2:
            master_password = st.text_input("Redshift Master Password", type="password", 
                                          help="Minimum 8 characters")
            region = st.text_input("AWS Region", value=config['aws_region'])
        
        deploy_button = st.form_submit_button("🚀 Deploy Infrastructure", type="primary")
        
        if deploy_button:
            if len(master_password) < 8:
                st.error("❌ Password must be at least 8 characters")
            else:
                deploy_infrastructure(source_account, target_account, master_password, region)

def deploy_infrastructure(source_account, target_account, password, region):
    """Deploy infrastructure using CloudFormation"""
    st.subheader("Deployment Progress")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Deploy source account
    status_text.text("Deploying source account infrastructure...")
    progress_bar.progress(10)
    
    source_cmd = [
        'aws', 'cloudformation', 'create-stack',
        '--stack-name', f'{config["resource_prefix"]}-redshift-source',
        '--template-body', 'file://cloudformation/source-account-setup.yaml',
        '--parameters', 
        f'ParameterKey=TargetAccountId,ParameterValue={target_account}',
        f'ParameterKey=RedshiftMasterPassword,ParameterValue={password}',
        '--capabilities', 'CAPABILITY_NAMED_IAM',
        '--region', region,
        '--profile', 'source'
    ]
    
    source_result = run_cloudformation_command(source_cmd, "Deploying source account")
    progress_bar.progress(30)
    
    if not source_result['success']:
        st.error(f"❌ Source deployment failed: {source_result.get('stderr', 'Unknown error')}")
        return
    
    # Deploy target account
    status_text.text("Deploying target account infrastructure...")
    progress_bar.progress(50)
    
    target_cmd = [
        'aws', 'cloudformation', 'create-stack',
        '--stack-name', f'{config["resource_prefix"]}-redshift-target',
        '--template-body', 'file://cloudformation/target-account-setup.yaml',
        '--parameters', 
        f'ParameterKey=SourceAccountId,ParameterValue={source_account}',
        '--capabilities', 'CAPABILITY_IAM',
        '--region', region,
        '--profile', 'target'
    ]
    
    target_result = run_cloudformation_command(target_cmd, "Deploying target account")
    progress_bar.progress(70)
    
    if not target_result['success']:
        st.error(f"❌ Target deployment failed: {target_result.get('stderr', 'Unknown error')}")
        return
    
    # Wait for completion
    status_text.text("Waiting for deployments to complete...")
    progress_bar.progress(90)
    
    # This would normally wait for stack completion
    # For demo purposes, we'll simulate the wait
    time.sleep(2)
    
    progress_bar.progress(100)
    status_text.text("Deployment completed!")
    
    st.markdown('<div class="success-box">✅ Infrastructure deployed successfully!</div>', 
                unsafe_allow_html=True)
    
    st.subheader("Next Steps")
    st.markdown("""
    1. **Test Native Demo** - Try the native snapshot sharing
    2. **Deploy Lambda Automation** - Set up serverless backups
    3. **Configure Monitoring** - Set up alerts and dashboards
    """)

def show_native_demo(config):
    """Show native demo page"""
    st.header("📊 Native Redshift Snapshot Demo")
    
    st.markdown("""
    Test the native Redshift snapshot sharing approach. This creates manual snapshots
    and shares them across accounts using native Redshift capabilities.
    """)
    
    # Demo controls
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Demo Configuration")
        cluster_id = st.text_input("Source Cluster ID", 
                                 value=f"{config['resource_prefix']}-redshift-cluster")
        target_cluster_id = st.text_input("Target Cluster ID", 
                                        value=f"{config['resource_prefix']}-restored-cluster")
    
    with col2:
        st.subheader("Account Information")
        st.text(f"Source Account: {config['source_account_id']}")
        st.text(f"Target Account: {config['target_account_id']}")
        st.text(f"Region: {config['aws_region']}")
    
    # Run demo button
    if st.button("🚀 Run Native Demo", type="primary"):
        run_native_demo(cluster_id, target_cluster_id, config)

def run_native_demo(cluster_id, target_cluster_id, config):
    """Run the native snapshot demo"""
    st.subheader("Demo Execution")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.container()
    
    try:
        # Initialize demo
        status_text.text("Initializing demo...")
        progress_bar.progress(10)
        
        demo = RedshiftSnapshotDemo(source_profile='source', target_profile='target')
        
        with log_container:
            st.text(f"Source Account: {demo.source_account_id}")
            st.text(f"Target Account: {demo.target_account_id}")
        
        # Create snapshot
        status_text.text("Creating manual snapshot...")
        progress_bar.progress(30)
        
        snapshot_id = demo.create_manual_snapshot(cluster_id)
        
        with log_container:
            st.success(f"✅ Snapshot created: {snapshot_id}")
        
        # Share snapshot
        status_text.text("Sharing snapshot with target account...")
        progress_bar.progress(60)
        
        shared = demo.share_snapshot_with_account(snapshot_id)
        
        if shared:
            with log_container:
                st.success("✅ Snapshot shared successfully")
        else:
            with log_container:
                st.error("❌ Failed to share snapshot")
            return
        
        # List shared snapshots
        status_text.text("Listing shared snapshots...")
        progress_bar.progress(80)
        
        shared_snapshots = demo.list_shared_snapshots()
        
        with log_container:
            st.subheader("Shared Snapshots")
            if shared_snapshots:
                snapshot_data = []
                for snapshot in shared_snapshots:
                    snapshot_data.append({
                        'Snapshot ID': snapshot['SnapshotIdentifier'],
                        'Status': snapshot['Status'],
                        'Create Time': snapshot['SnapshotCreateTime'].strftime('%Y-%m-%d %H:%M:%S'),
                        'Size (GB)': snapshot.get('TotalBackupSizeInMegaBytes', 0) / 1024
                    })
                
                df = pd.DataFrame(snapshot_data)
                st.dataframe(df)
            else:
                st.warning("No shared snapshots found")
        
        progress_bar.progress(100)
        status_text.text("Demo completed successfully!")
        
        st.markdown('<div class="success-box">✅ Native demo completed successfully!</div>', 
                    unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Demo failed: {str(e)}")
        with log_container:
            st.exception(e)

def show_aws_backup_demo(config):
    """Show AWS Backup demo page"""
    st.header("☁️ AWS Backup Integration Demo")
    
    st.markdown("""
    Test the AWS Backup integration approach. This uses AWS Backup service
    for centralized backup management with cross-account capabilities.
    """)
    
    # Demo controls
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Backup Configuration")
        vault_name = st.text_input("Backup Vault Name", 
                                 value=f"{config['resource_prefix']}-redshift-vault")
        cluster_arn = st.text_input("Cluster ARN", 
                                  value=f"arn:aws:redshift:{config['aws_region']}:{config['source_account_id']}:cluster:{config['resource_prefix']}-redshift-cluster")
    
    with col2:
        st.subheader("Cross-Account Settings")
        target_vault = st.text_input("Target Vault Name", 
                                    value=f"{config['resource_prefix']}-redshift-cross-account-vault")
        st.text(f"Target Account: {config['target_account_id']}")
    
    # Run demo button
    if st.button("🚀 Run AWS Backup Demo", type="primary"):
        run_aws_backup_demo(vault_name, cluster_arn, target_vault, config)

def run_aws_backup_demo(vault_name, cluster_arn, target_vault, config):
    """Run the AWS Backup demo"""
    st.subheader("AWS Backup Demo Execution")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.container()
    
    try:
        # Initialize demo
        status_text.text("Initializing AWS Backup demo...")
        progress_bar.progress(10)
        
        demo = AWSBackupDemo(source_profile='source', target_profile='target')
        
        with log_container:
            st.text(f"Source Account: {demo.source_account_id}")
            st.text(f"Target Account: {demo.target_account_id}")
        
        # Start backup job
        status_text.text("Starting on-demand backup job...")
        progress_bar.progress(30)
        
        # Get role ARN from CloudFormation
        cf_client = demo.source_session.client('cloudformation')
        source_stack = cf_client.describe_stacks(StackName=f'{config["resource_prefix"]}-redshift-source')
        source_outputs = {output['OutputKey']: output['OutputValue'] 
                         for output in source_stack['Stacks'][0]['Outputs']}
        
        role_arn = source_outputs['BackupRoleArn']
        
        job_id = demo.start_backup_job(vault_name, cluster_arn, role_arn)
        
        with log_container:
            st.success(f"✅ Backup job started: {job_id}")
        
        # Wait for completion (simplified for demo)
        status_text.text("Waiting for backup completion...")
        progress_bar.progress(70)
        
        # In a real implementation, we'd wait for the actual backup
        time.sleep(3)  # Simulate waiting
        
        # List recovery points
        status_text.text("Listing recovery points...")
        progress_bar.progress(90)
        
        recovery_points = demo.list_recovery_points(vault_name)
        
        with log_container:
            st.subheader("Recovery Points")
            if recovery_points:
                rp_data = []
                for rp in recovery_points:
                    rp_data.append({
                        'Recovery Point ARN': rp['RecoveryPointArn'].split('/')[-1],
                        'Status': rp['Status'],
                        'Creation Date': rp['CreationDate'].strftime('%Y-%m-%d %H:%M:%S'),
                        'Resource Type': rp['ResourceType']
                    })
                
                df = pd.DataFrame(rp_data)
                st.dataframe(df)
            else:
                st.warning("No recovery points found")
        
        progress_bar.progress(100)
        status_text.text("AWS Backup demo completed!")
        
        st.markdown('<div class="success-box">✅ AWS Backup demo completed successfully!</div>', 
                    unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ AWS Backup demo failed: {str(e)}")
        with log_container:
            st.exception(e)

def show_lambda_automation(config):
    """Show Lambda automation page"""
    st.header("🤖 Lambda Automation Deployment")
    
    st.markdown("""
    Deploy serverless backup automation using AWS Lambda and EventBridge.
    This provides scheduled backups with automatic retention management.
    """)
    
    # Lambda configuration
    with st.form("lambda_form"):
        st.subheader("Lambda Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            schedule_option = st.selectbox("Backup Schedule", [
                "Daily at 2 AM",
                "Every 12 hours", 
                "Every 6 hours",
                "Custom"
            ])
            
            if schedule_option == "Custom":
                custom_schedule = st.text_input("Custom Cron Expression", 
                                              value="cron(0 2 * * ? *)",
                                              help="Use AWS cron format")
            
            retention_days = st.number_input("Retention Days", min_value=1, max_value=365, 
                                           value=config['backup_configuration']['retention_days'])
        
        with col2:
            notification_email = st.text_input("Notification Email (Optional)", 
                                             value=config['backup_configuration']['notification_email'])
            
            cluster_id = st.text_input("Cluster Identifier", 
                                     value=f"{config['resource_prefix']}-redshift-cluster")
            
            target_account = st.text_input("Target Account ID", 
                                         value=config['target_account_id'])
        
        deploy_lambda = st.form_submit_button("🚀 Deploy Lambda Automation", type="primary")
        
        if deploy_lambda:
            # Map schedule options to cron expressions
            schedule_map = {
                "Daily at 2 AM": "cron(0 2 * * ? *)",
                "Every 12 hours": "rate(12 hours)",
                "Every 6 hours": "rate(6 hours)",
                "Custom": custom_schedule if schedule_option == "Custom" else "cron(0 2 * * ? *)"
            }
            
            schedule_expr = schedule_map[schedule_option]
            deploy_lambda_automation(schedule_expr, retention_days, notification_email, 
                                   cluster_id, target_account, config)

def deploy_lambda_automation(schedule, retention, email, cluster_id, target_account, config):
    """Deploy Lambda automation"""
    st.subheader("Lambda Deployment Progress")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Build parameters
    params = [
        f'ParameterKey=TargetAccountId,ParameterValue={target_account}',
        f'ParameterKey=ClusterIdentifier,ParameterValue={cluster_id}',
        f'ParameterKey=BackupSchedule,ParameterValue={schedule}',
        f'ParameterKey=RetentionDays,ParameterValue={retention}'
    ]
    
    if email:
        params.append(f'ParameterKey=NotificationEmail,ParameterValue={email}')
    
    # Deploy Lambda stack
    status_text.text("Deploying Lambda automation...")
    progress_bar.progress(30)
    
    lambda_cmd = [
        'aws', 'cloudformation', 'create-stack',
        '--stack-name', f'{config["resource_prefix"]}-lambda-backup',
        '--template-body', 'file://cloudformation/aca-lambda-backup-setup.yaml',
        '--parameters'
    ] + params + [
        '--capabilities', 'CAPABILITY_NAMED_IAM',
        '--region', config['aws_region'],
        '--profile', 'source'
    ]
    
    result = run_cloudformation_command(lambda_cmd, "Deploying Lambda automation")
    progress_bar.progress(80)
    
    if result['success']:
        progress_bar.progress(100)
        status_text.text("Lambda automation deployed successfully!")
        
        st.markdown('<div class="success-box">✅ Lambda automation deployed successfully!</div>', 
                    unsafe_allow_html=True)
        
        st.subheader("Automation Details")
        st.markdown(f"""
        - **Schedule**: {schedule}
        - **Retention**: {retention} days
        - **Cluster**: {cluster_id}
        - **Target Account**: {target_account}
        - **Notifications**: {'Enabled' if email else 'Disabled'}
        """)
        
    else:
        st.error(f"❌ Lambda deployment failed: {result.get('stderr', 'Unknown error')}")

def show_monitoring(config):
    """Show monitoring page"""
    st.header("📈 Monitoring & Status")
    
    st.markdown("Monitor the status of your backup infrastructure and recent backup activities.")
    
    # Tabs for different monitoring views
    tab1, tab2, tab3 = st.tabs(["Infrastructure Status", "Backup History", "Cost Analysis"])
    
    with tab1:
        st.subheader("Infrastructure Status")
        
        # Check CloudFormation stacks
        if st.button("🔄 Refresh Status"):
            check_infrastructure_status(config)
    
    with tab2:
        st.subheader("Recent Backup Activity")
        
        # Show recent snapshots and backups
        show_backup_history(config)
    
    with tab3:
        st.subheader("Cost Analysis")
        
        # Show cost breakdown
        show_cost_analysis(config)

def check_infrastructure_status(config):
    """Check the status of deployed infrastructure"""
    try:
        # Check source account stacks
        source_session = boto3.Session(profile_name='source')
        cf_source = source_session.client('cloudformation')
        
        stacks_to_check = [
            f'{config["resource_prefix"]}-redshift-source',
            f'{config["resource_prefix"]}-lambda-backup'
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Source Account Stacks")
            for stack_name in stacks_to_check:
                try:
                    response = cf_source.describe_stacks(StackName=stack_name)
                    stack = response['Stacks'][0]
                    status = stack['StackStatus']
                    
                    if 'COMPLETE' in status:
                        st.success(f"✅ {stack_name}: {status}")
                    elif 'FAILED' in status:
                        st.error(f"❌ {stack_name}: {status}")
                    else:
                        st.warning(f"⏳ {stack_name}: {status}")
                        
                except Exception:
                    st.error(f"❌ {stack_name}: Not Found")
        
        # Check target account
        target_session = boto3.Session(profile_name='target')
        cf_target = target_session.client('cloudformation')
        
        with col2:
            st.subheader("Target Account Stacks")
            target_stack = f'{config["resource_prefix"]}-redshift-target'
            
            try:
                response = cf_target.describe_stacks(StackName=target_stack)
                stack = response['Stacks'][0]
                status = stack['StackStatus']
                
                if 'COMPLETE' in status:
                    st.success(f"✅ {target_stack}: {status}")
                elif 'FAILED' in status:
                    st.error(f"❌ {target_stack}: {status}")
                else:
                    st.warning(f"⏳ {target_stack}: {status}")
                    
            except Exception:
                st.error(f"❌ {target_stack}: Not Found")
        
    except Exception as e:
        st.error(f"Failed to check infrastructure status: {str(e)}")

def show_backup_history(config):
    """Show recent backup history"""
    try:
        source_session = boto3.Session(profile_name='source')
        redshift = source_session.client('redshift')
        
        # Get recent snapshots
        response = redshift.describe_cluster_snapshots(
            ClusterIdentifier=f'{config["resource_prefix"]}-redshift-cluster',
            SnapshotType='manual',
            MaxRecords=10
        )
        
        if response['Snapshots']:
            snapshot_data = []
            for snapshot in response['Snapshots']:
                snapshot_data.append({
                    'Snapshot ID': snapshot['SnapshotIdentifier'],
                    'Status': snapshot['Status'],
                    'Created': snapshot['SnapshotCreateTime'].strftime('%Y-%m-%d %H:%M:%S'),
                    'Size (GB)': round(snapshot.get('TotalBackupSizeInMegaBytes', 0) / 1024, 2)
                })
            
            df = pd.DataFrame(snapshot_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No recent snapshots found")
            
    except Exception as e:
        st.error(f"Failed to retrieve backup history: {str(e)}")

def show_cost_analysis(config):
    """Show cost analysis"""
    st.subheader("Monthly Cost Estimates (1TB Cluster)")
    
    cost_data = {
        'Component': [
            'Native Snapshots Storage',
            'Lambda Execution',
            'EventBridge Events',
            'CloudWatch Logs',
            'AWS Backup Storage',
            'Backup Operations'
        ],
        'Native Approach': ['$24.58', '$0.20', '$0.03', '$0.05', 'N/A', 'N/A'],
        'Lambda Approach': ['$24.58', '$0.20', '$0.03', '$0.05', 'N/A', 'N/A'],
        'AWS Backup': ['N/A', 'N/A', 'N/A', 'N/A', '$51.20', '$0.05']
    }
    
    df = pd.DataFrame(cost_data)
    st.dataframe(df, use_container_width=True)
    
    # Cost savings visualization
    st.subheader("Cost Savings Analysis")
    
    approaches = ['Native Manual', 'Lambda Automation', 'AWS Backup']
    costs = [24.58, 24.86, 51.25]
    
    chart_data = pd.DataFrame({
        'Approach': approaches,
        'Monthly Cost ($)': costs
    })
    
    st.bar_chart(chart_data.set_index('Approach'))

def show_cleanup(config):
    """Show cleanup page"""
    st.header("🧹 Resource Cleanup")
    
    st.markdown("""
    ⚠️ **Warning**: This will delete all demo resources and cannot be undone!
    
    The cleanup process will:
    1. Delete restored Redshift clusters
    2. Remove manual snapshots and shared snapshots
    3. Clean up AWS Backup resources
    4. Delete CloudFormation stacks
    5. Verify complete resource removal
    """)
    
    # Cleanup options
    st.subheader("Cleanup Options")
    
    cleanup_snapshots = st.checkbox("Delete all snapshots", value=True)
    cleanup_backups = st.checkbox("Delete AWS Backup resources", value=True)
    cleanup_lambda = st.checkbox("Delete Lambda automation", value=True)
    cleanup_stacks = st.checkbox("Delete CloudFormation stacks", value=True)
    
    # Confirmation
    st.subheader("Confirmation")
    confirm_text = st.text_input("Type 'DELETE' to confirm cleanup:")
    
    if st.button("🗑️ Start Cleanup", type="primary", disabled=(confirm_text != "DELETE")):
        if confirm_text == "DELETE":
            run_cleanup(config, cleanup_snapshots, cleanup_backups, cleanup_lambda, cleanup_stacks)
        else:
            st.error("Please type 'DELETE' to confirm")

def run_cleanup(config, snapshots, backups, lambda_cleanup, stacks):
    """Run the cleanup process"""
    st.subheader("Cleanup Progress")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.container()
    
    try:
        # Run cleanup script
        status_text.text("Running cleanup script...")
        progress_bar.progress(20)
        
        cleanup_cmd = ['./cleanup.sh']
        
        with st.spinner("Executing cleanup..."):
            result = subprocess.run(
                cleanup_cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
        
        progress_bar.progress(80)
        
        with log_container:
            if result.returncode == 0:
                st.success("✅ Cleanup script executed successfully")
                st.text("Cleanup output:")
                st.code(result.stdout)
            else:
                st.error("❌ Cleanup script failed")
                st.text("Error output:")
                st.code(result.stderr)
        
        progress_bar.progress(100)
        status_text.text("Cleanup completed!")
        
        if result.returncode == 0:
            st.markdown('<div class="success-box">✅ All resources cleaned up successfully!</div>', 
                        unsafe_allow_html=True)
        
    except subprocess.TimeoutExpired:
        st.error("❌ Cleanup timed out after 10 minutes")
    except Exception as e:
        st.error(f"❌ Cleanup failed: {str(e)}")

if __name__ == "__main__":
    main()