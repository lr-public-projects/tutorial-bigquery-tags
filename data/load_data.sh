#!/bin/bash
echo "Starting data load into BigQuery..."

# Exit script on error
set -e

# Variables (replace with your actual project and dataset IDs if different)
PROJECT_ID=$(gcloud config get-value project)
DATASET_ID="TUTORIAL_DATA"

echo "Loading data into personal_info table..."
bq load --source_format=CSV --skip_leading_rows=1 \
  "${PROJECT_ID}:${DATASET_ID}.PERSONAL_INFO" ./personal_info.csv

echo "Loading data into financial_info table..."
bq load --source_format=CSV --skip_leading_rows=1 \
  "${PROJECT_ID}:${DATASET_ID}.FINANCIAL_INFO" ./financial_info.csv

echo "Data loading complete."
