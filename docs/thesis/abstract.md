# Abstract Draft

This folder stores the current abstract draft used for the thesis.

## Design and Implementation of an AWS-Based AutoML Platform for Chronic Kidney Disease Risk Prediction Using AutoPrognosis 2.0
## Yang, Jun-Xiang
Department of Bioinformatics and Medical Engineering
Asia University, Taiwan
 Advisor: Charles C. N. Wang, Ph.D.
# Abstract
Chronic Kidney Disease (CKD) is a major public health problem worldwide, and its
impact is particularly evident in Taiwan, where dialysis rates and related healthcare
expenditures remain among the highest globally. The ability to identify high-risk individuals
at an early stage is critical for delaying disease progression, yet many existing CKD
prediction models rely on conventional statistical approaches that often struggle to handle the
complexity and variability of real-world clinical data. Recent advances in automated machine
learning (AutoML) offer an opportunity to improve predictive performance while reducing
manual development effort, but most prior studies focus only on model accuracy and rarely
address how such models can be deployed in a practical, sustainable manner.
This thesis develops an online CKD risk prediction platform by integrating
AutoPrognosis 2.0—an AutoML framework designed for clinical data—with a set of cloud-
based services provided by Amazon Web Services (AWS). The platform automates the key
steps of the modeling workflow, including data processing, model training, deployment, and
real-time inference. Data and model artifacts are stored in Amazon S3, model training is
handled through Amazon SageMaker, and predictions are delivered through a serverless setup
using AWS Lambda and API Gateway. A simple web interface hosted on S3 allows users to
upload patient information and receive risk predictions immediately.
The goals of this study are threefold:
(1) to evaluate whether AutoPrognosis 2.0 can produce reliable CKD risk prediction
models using structured clinical data;
(2) to establish a reproducible AWS-based architecture capable of automating model
training, version tracking, and service updates with minimal manual intervention; and
(3) to conduct preliminary tests to verify that the system operates reliably and responds
efficiently under controlled conditions.
Overall, this work aims to demonstrate a practical and workable example of how a
modern AutoML tool can be deployed on a cloud platform using standard AWS services,
without requiring integration into hospital information systems at this stage.
