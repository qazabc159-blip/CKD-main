# Chapter 4 System Design Notes

## Purpose
This chapter describes the design and implementation of the AWS-based CKD risk prediction platform.

## Core Components
- Route 53
- CloudFront
- S3 static web UI
- API Gateway
- Lambda inference function
- SageMaker training job
- S3 data bucket
- S3 model bucket
- CloudWatch
- IAM

## Current Status
- architecture concept completed
- system implementation not started

## Main Design Principle
- decouple frontend, training, and inference
- keep inference lightweight and serverless
- store model artifacts and registry in S3
- support future retraining and model version switching
