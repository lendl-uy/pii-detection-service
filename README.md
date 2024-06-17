# PII Detection Service

This repository is the codebase for the implementation of a PII detection service for the subject AI 231 2nd Semester 2023-2024.

# Contributors
Key contributors to this repository are the following:
1. Jan Lendl Uy
2. Christian Balanquit
3. James Benedict Janda
4. Al John Lexter Lozano

# Project Architecture

## Project Components
* PII Identifier
* PII Annotator
* PII Retrainer

## Structure

### A. Proposed Directory Structure
* /project_root
  * /app
    * \__init\__.py
    * /services
      * \__init\__.py
      * /backend_service
        * preprocessor.py
        * response_handler.py
        * validation_preprocessor.py
      * /ml_service
        * predictor.py
        * model_retrainer.py
        * model_storage_manager.py
    * /infra
      * \__init\__.py
      * database_manager.py
      * document_table.py
      * object_store_manager.py
      * backup_store_manager.py
    * /static
      * ...
    * /templates
      * ...
  * /tests
    * ...
  * config.py
  * run.py


## B. Branching Strategy
* eda
* model_training
* apps
  * apps/frontend
  * apps/backend
  * apps/ml_service
* infra
* cicd

## CICD Workflows
* Infra Setup: make sure infra setup is still intact
* Backend Services
* ML Services

Action Items:
- modify boto3 s3 client creation by utilizing AWS ACCESS KEY & SECRET KEY

## CICD Components
* Pylint
* Deploy to Backend ECS
* Deploy to ML ECS
* 

## D. Deployment
### Push to ECR
```
docker build -t pii-detection-service-ml . -f deploy/ml-Dockerfile

docker build -t pii-detection-service-backend . -f deploy/backend-Dockerfile

docker build -t pii-detection-service-nginx ./deploy -f deploy/nginx-Dockerfile
```
