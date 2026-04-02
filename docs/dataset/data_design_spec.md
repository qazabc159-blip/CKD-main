# Data Design Specification v1
## Project
Design and Implementation of an AWS-Based AutoML Platform for Chronic Kidney Disease Risk Prediction Using AutoPrognosis 2.0

## Version
v1.0 (initial planning version)

## Status
Draft for project initialization

---

## 1. Purpose of This Document
This document defines the initial data design specification for the CKD risk prediction thesis project.  
Its purpose is to establish a consistent methodological basis for:

- dataset selection
- cohort definition
- feature schema design
- label definition
- preprocessing rules
- model evaluation
- future backend API alignment
- future AWS deployment alignment

This version is created before actual dataset acquisition and before model experimentation begins.

---

## 2. Research Task Definition

### 2.1 Primary Task
The primary modeling task in the first phase of this study is defined as:

**Binary classification for CKD risk prediction using structured clinical/tabular data.**

### 2.2 Rationale
This task definition is selected because:

1. The thesis abstract already defines the project as a CKD risk prediction platform based on structured clinical data.
2. The initial platform objective is to validate the feasibility of integrating AutoPrognosis 2.0 with AWS services for practical deployment.
3. AutoPrognosis 2.0 explicitly supports classification, regression, and time-to-event analysis; among these, binary classification is the most appropriate starting point for a first end-to-end proof-of-concept implementation.

### 2.3 Current Working Definition
At this stage, the project will first aim to answer the following question:

**Can AutoPrognosis 2.0 produce a reliable binary CKD risk prediction model from structured clinical data, and can that model later be integrated into a reproducible AWS-based deployment pipeline?**

---

## 3. Modeling Scope

### 3.1 In-Scope
The first implementation phase includes:

- structured tabular dataset
- binary target variable
- supervised learning pipeline
- baseline model comparison
- AutoPrognosis 2.0 pipeline optimization
- local experimentation before cloud deployment
- later integration into backend inference API and AWS architecture

### 3.2 Out-of-Scope (Current Phase)
The following items are not included in the first modeling phase:

- direct hospital HIS/EMR integration
- unstructured text data
- image-based diagnosis
- longitudinal repeated-measures modeling
- survival/time-to-event modeling
- federated learning
- real-time streaming clinical data

### 3.3 Future Extension
Possible future extensions include:

- time-to-event CKD progression modeling
- integration of longitudinal laboratory trajectories
- external validation on institutional data
- model drift monitoring in production

---

## 4. Dataset Source Plan

### 4.1 Dataset Source Strategy
The current recommended strategy is:

**Use a publicly available structured CKD-related dataset for the first proof-of-concept phase.**

### 4.2 Reason for This Strategy
This choice is made because the project has not yet finalized access to institutional data, and the immediate research need is to establish a complete, reproducible pipeline covering:

- data loading
- preprocessing
- model training
- model evaluation
- local API integration
- later cloud deployment

Using a public structured dataset allows the study to begin without delay and supports the thesis goal of demonstrating a practical and workable AutoML deployment example.

### 4.3 Dataset Requirements
The selected dataset should satisfy the following requirements:

1. structured/tabular format
2. CKD-related diagnosis or risk label available
3. sufficient number of features for clinical prediction
4. manageable missingness
5. acceptable for academic thesis use
6. usable for binary classification in the first phase

### 4.4 Dataset Status
**Not finalized yet**

### 4.5 Dataset Placeholder
- Dataset name: TBD
- Source: TBD
- Access URL / source record: TBD
- License / academic usability: TBD
- Number of samples: TBD
- Number of candidate features: TBD

---

## 5. Cohort Definition

### 5.1 Initial Cohort Principle
The modeling cohort will consist of patient-level structured records suitable for CKD-related prediction.

### 5.2 Inclusion Criteria (Draft)
The final dataset should preferably include:

- patient-level structured clinical observations
- sufficient completeness in key variables
- an identifiable outcome variable related to CKD presence, diagnosis, or risk status
- one row per subject or one clearly defined observation unit per prediction instance

### 5.3 Exclusion Criteria (Draft)
Potential exclusion rules include:

- duplicate rows
- records missing the target label
- records with extremely high missingness across key predictors
- records containing impossible or invalid clinical values after range validation
- features unavailable at prediction time (to avoid data leakage)

### 5.4 Cohort Definition Status
**To be finalized after dataset selection**

---

## 6. Prediction Target / Label Definition

### 6.1 Initial Labeling Strategy
The first-phase task will use a **binary target variable**.

### 6.2 Working Label Interpretation
The binary label should represent one of the following, depending on the final dataset:

- CKD vs non-CKD
- high CKD risk vs low CKD risk
- positive diagnosis vs negative diagnosis

### 6.3 Label Selection Rule
The final label definition must satisfy all of the following:

1. clinically interpretable
2. available directly from dataset variables or derivable through transparent rules
3. usable at prediction time without leakage
4. consistent with a binary classification setting

### 6.4 Label Documentation Requirements
Once the dataset is selected, the following must be documented:

- label variable name
- exact rule used to generate the binary label
- clinical meaning of positive class
- class distribution
- possible class imbalance severity

### 6.5 Current Status
- Label variable: TBD
- Positive class definition: TBD
- Negative class definition: TBD
- Class balance: TBD

---

## 7. Feature Schema Design

### 7.1 Feature Design Principle
The feature set should represent variables that would reasonably be available before or at the time of risk prediction.

### 7.2 Initial Feature Categories
The feature schema will likely include the following categories:

#### A. Demographic Features
- age
- sex
- possibly height / weight / BMI

#### B. Laboratory Features
- kidney-related biochemical markers
- urine-related indicators
- metabolic markers
- hematology-related markers if available

#### C. Clinical Condition Features
- comorbidities
- relevant disease history
- blood pressure or similar measurements if available

#### D. Administrative / Derived Features
- only if they are available at inference time and do not introduce leakage

### 7.3 Feature Exclusion Rule
The following variables should be excluded:

- direct leakage variables
- post-outcome variables
- identifiers
- free-text fields in the first phase
- features impossible to reproduce in the future web/API workflow

### 7.4 Feature Type Definition
Each feature must be assigned one of the following types:

- numerical
- categorical
- binary
- ordinal

### 7.5 Feature Schema Table Template
The following table must be completed after dataset selection:

| Feature Name | Description | Type | Unit | Missing Rate | Keep/Drop | Notes |
|---|---|---|---|---:|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD |

### 7.6 Current Status
**Feature schema not finalized**

---

## 8. Missing Data Strategy

### 8.1 Importance
Missingness is expected to be a core issue in clinical data, and it should not be treated as an afterthought.  
AutoPrognosis is specifically designed to handle pipeline stages that include missing data imputation, feature preprocessing, prediction, and calibration, making missing-data handling a formal part of the modeling workflow rather than an informal preprocessing shortcut.

### 8.2 Initial Missingness Policy
The initial policy is:

1. perform descriptive missingness analysis first
2. remove clearly unusable variables with excessive missingness if clinically unjustified
3. retain clinically meaningful variables when possible
4. allow AutoPrognosis-compatible imputation strategy to be part of the modeling workflow
5. document all exclusions and thresholds clearly

### 8.3 Missingness Analysis Outputs
The following outputs should be generated once the dataset is available:

- missing rate per variable
- missing rate per record
- missingness heatmap or summary figure
- variable retention decision log

### 8.4 Current Status
**Pending dataset acquisition**

---

## 9. Data Preprocessing Plan

### 9.1 General Principles
Preprocessing must be:

- reproducible
- documented
- leakage-aware
- compatible with both baseline models and AutoPrognosis workflow

### 9.2 Planned Preprocessing Steps
The first-phase preprocessing workflow should include:

1. column standardization
2. type conversion
3. duplicate removal
4. range and validity checks
5. missingness profiling
6. categorical encoding strategy identification
7. train/validation/test split preparation
8. baseline-compatible preprocessing
9. AutoPrognosis-compatible preprocessing configuration

### 9.3 Special Rule
Manual preprocessing should not unnecessarily duplicate what AutoPrognosis is already intended to optimize internally.  
Therefore, preprocessing should focus on:

- data validity
- type correctness
- leakage control
- structural consistency

rather than overengineering feature transformations too early.

---

## 10. Data Splitting Plan

### 10.1 First-Phase Evaluation Strategy
The recommended first-phase strategy is:

**Train / validation / test split with cross-validation inside training when appropriate**

### 10.2 Preferred Setup
Recommended initial setup:

- Train set: 70%
- Validation set: 15%
- Test set: 15%

Alternative:

- 5-fold cross-validation on training data
- final held-out test set for final reporting

### 10.3 Stratification
If the label is imbalanced, stratified splitting should be used.

### 10.4 Reproducibility
A fixed random seed must be documented.

### 10.5 Current Status
- split strategy: draft only
- random seed: TBD

---

## 11. Baseline Modeling Plan

### 11.1 Purpose
Before running AutoPrognosis, the study should establish baseline performance using conventional models.

### 11.2 Recommended Baseline Models
The first baseline set should include:

1. Logistic Regression
2. Random Forest
3. XGBoost or LightGBM

### 11.3 Rationale
This baseline set provides:

- a simple interpretable benchmark
- a common tree-based benchmark
- a strong boosting-based benchmark

This makes the AutoPrognosis comparison more meaningful.

### 11.4 Baseline Status
**Not started**

---

## 12. AutoPrognosis 2.0 Plan

### 12.1 Role in This Study
AutoPrognosis 2.0 is the core AutoML framework of this thesis.

### 12.2 Why It Is Used
AutoPrognosis 2.0 is suitable because it can automate the key parts of a clinical ML pipeline, including:

- missing data imputation
- feature processing
- model selection and fitting
- interpretability / explanations
- production of clinical demonstrators

It also supports classification tasks and is designed to improve accessibility and reproducibility for clinical users.

### 12.3 First-Phase Usage Plan
The initial AutoPrognosis workflow in this thesis should:

1. use classification mode
2. optimize candidate pipelines on the selected CKD dataset
3. compare results against baseline models
4. export the best-performing model and metrics
5. generate a model artifact suitable for later backend inference integration

### 12.4 Initial Experiment Constraints
Because this is the first implementation phase, the initial AutoPrognosis experiment should be moderate in complexity:

- classification only
- limited search budget at first
- tabular data only
- one finalized feature schema
- one clear label definition

### 12.5 Planned Outputs
The AutoPrognosis stage should eventually produce:

- optimized model or ensemble
- evaluation metrics
- selected feature importance / explanations
- model artifact for inference
- reproducible experiment configuration

---

## 13. Evaluation Metrics

### 13.1 Primary Predictive Metrics
The following metrics are recommended for the first phase:

- AUROC
- AUPRC
- F1-score
- Recall / Sensitivity
- Specificity

### 13.2 Calibration Metrics
Because this is a clinical risk prediction problem, calibration should also be included:

- Brier Score
- Calibration Curve
- Expected Calibration Error (optional)

### 13.3 System-Level Metrics (Later Phase)
After local model development is complete and backend deployment begins, the following system metrics should be added:

- average inference latency
- p95 inference latency
- cold start latency
- error rate
- training runtime
- estimated cloud cost

### 13.4 Current Status
Predictive metrics planned, but not yet executed.

---

## 14. Alignment with Web UI and Backend

### 14.1 UI Alignment Principle
The final model input schema should be consistent with the web UI form fields.

### 14.2 Backend Alignment Principle
The backend inference API should eventually receive a JSON payload whose fields correspond directly to the finalized feature schema.

### 14.3 Immediate Requirement
After dataset selection, the next required task is:

**map finalized dataset features to UI input fields and future API request schema**

### 14.4 Current Status
Not yet aligned because feature schema is not finalized.

---

## 15. Data Governance and Reproducibility

### 15.1 General Principle
Even in the proof-of-concept phase, the project should maintain reproducible data handling practices.

### 15.2 Required Reproducibility Items
The following should be documented:

- dataset source
- dataset version or acquisition date
- preprocessing decisions
- feature inclusion/exclusion log
- label generation rule
- split rule
- random seed
- experiment config
- output metrics

### 15.3 Sensitive Data Policy
At the current stage, no real patient-identifiable data should be committed to the repository.

---

## 16. Risks and Open Questions

### 16.1 Current Risks
- dataset not finalized
- label definition not finalized
- feature schema not finalized
- class imbalance level unknown
- missingness pattern unknown
- UI/model input mismatch possible

### 16.2 Open Questions
1. Which dataset will be used in phase 1?
2. What exact binary label definition will be adopted?
3. Which features from the dataset are also suitable for web-based manual input?
4. How large should the first AutoPrognosis search budget be?
5. Which interpretability outputs will be reported in the thesis?

---

## 17. Immediate Next Actions

### Priority 1
Finalize one candidate public CKD-related structured dataset.

### Priority 2
Define the binary label rule clearly.

### Priority 3
Create the first feature dictionary.

### Priority 4
Perform dataset profiling:
- number of samples
- number of variables
- missingness summary
- class distribution

### Priority 5
Implement baseline models before AutoPrognosis.

### Priority 6
Run the first AutoPrognosis classification experiment.

---

## 18. Summary of This Version
This v1 data design specification defines the project’s first executable methodological direction:

- start with structured CKD-related tabular data
- formulate the first task as binary classification
- document cohort, label, features, and missingness explicitly
- compare baseline models with AutoPrognosis 2.0
- keep the design aligned with later API and AWS deployment needs

This document should be revised immediately after the final dataset is selected.
