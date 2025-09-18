#!/bin/bash

# Copyright 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Apache License, Version 2.0

# Streamlit App Launcher for Amazon Redshift Cross-Account Backup

echo "🔄 Amazon Redshift Cross-Account Backup - Streamlit Interface"
echo "============================================================"
echo

# Check if Streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "📦 Installing Streamlit requirements..."
    pip install -r requirements-streamlit.txt
fi

# Check AWS credentials
echo "🔐 Checking AWS credentials..."
if ! aws sts get-caller-identity --profile source &> /dev/null; then
    echo "⚠️  Warning: 'source' AWS profile not configured"
    echo "   Configure with: aws configure --profile source"
fi

if ! aws sts get-caller-identity --profile target &> /dev/null; then
    echo "⚠️  Warning: 'target' AWS profile not configured"
    echo "   Configure with: aws configure --profile target"
fi

echo
echo "🚀 Starting Streamlit application..."
echo "   Access the app at: http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo

# Start Streamlit
streamlit run streamlit_app.py \
    --server.port 8501 \
    --server.address localhost \
    --server.headless false \
    --browser.gatherUsageStats false