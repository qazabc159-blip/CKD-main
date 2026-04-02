# AWS Architecture Description

## Architecture Goal
To provide a cloud-native platform for CKD risk prediction that supports:
- user-facing web access
- API-based inference
- model training and versioning
- future deployment automation

## User Roles
### Clinician / Staff
Uses the web UI to submit patient information and receive risk prediction results.

### System Admin / ML Engineer
Manages model training, deployment workflow, monitoring, and platform maintenance.

## Request Flow
1. User accesses the web UI via HTTPS
2. Route 53 directs traffic to CloudFront
3. CloudFront serves the web UI from S3 static hosting
4. Web UI sends prediction requests to API Gateway
5. API Gateway invokes Lambda
6. Lambda loads the latest model information from the model bucket
7. Lambda returns the prediction result to the frontend

## Training Flow
1. Training data is stored in the S3 data bucket
2. SageMaker Training Job reads the dataset
3. AutoPrognosis 2.0 trains a CKD prediction model
4. Trained artifacts are written to the S3 model bucket
5. model_registry.json is updated to point to the latest model version
6. Lambda uses the latest registry info on future invocations

## Storage Design
### ckd-data-bucket
Stores:
- raw dataset
- preprocessed dataset
- future training input data

### ckd-model-bucket
Stores:
- trained model artifacts
- registry metadata
- model evaluation summaries

## Monitoring and Security
- CloudWatch collects logs and metrics
- IAM controls role-based permissions
- Lambda and SageMaker are intended to run under least-privilege access
