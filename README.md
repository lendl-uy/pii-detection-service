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
        * __init__.py
        * /services
            * __init__.py
            * /backend_service
                * preprocessor.py
                * response_handler.py
                * validation_preprocessor.py
            * /ml_service
                * predictor.py
                * model_retrainer.py
                * model_storage_manager.py
        * /infra
            * __init__.py
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
