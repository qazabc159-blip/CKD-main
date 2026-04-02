# Experiment Plan

## Objective
To compare baseline models and AutoPrognosis 2.0 for CKD risk prediction, and later evaluate platform-level deployment behavior.

## Stage 1: Local Modeling
- dataset loading
- preprocessing
- missingness analysis
- baseline model training
- AutoPrognosis training
- model comparison

## Stage 2: Local Service Integration
- define input/output API schema
- connect UI to local backend
- return prediction results to frontend

## Stage 3: Cloud Deployment
- upload data/model artifacts to S3
- deploy Lambda inference
- configure API Gateway
- test end-to-end latency

## Stage 4: Thesis Evaluation
- predictive performance
- calibration
- interpretability
- system latency
- deployment cost estimation
