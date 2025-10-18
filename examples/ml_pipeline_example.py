#!/usr/bin/env python3
"""
Example: ML Training Pipeline using Improved Step Functions Framework
"""

import json
import boto3
from stepfunctions_improved import (
    ConfigurableWorkflow, PipelineFactory, setup_config,
    NumericGreaterThan, AndRule, StringEquals
)


def create_ml_pipeline(config):
    """Create ML training pipeline using the factory"""
    factory = PipelineFactory(config)
    return factory.create_ml_training_pipeline("MLTrainingPipeline")


def create_custom_ml_pipeline(config):
    """Create a custom ML pipeline with specific business logic"""
    from stepfunctions_improved.builder import ConfigurableStepFunctionBuilder
    from stepfunctions_improved.error_handling import RetryConfig, CatchConfig, ErrorHandling
    
    builder = ConfigurableStepFunctionBuilder("CustomMLPipeline", config)
    
    # Start with data validation
    builder.start_with("ValidateInput")
    builder.add_pass("ValidateInput", 
                    result={"validation_status": "started"},
                    comment="Initialize pipeline with input validation")
    
    # Data preprocessing with custom retry logic
    custom_retry = [RetryConfig(
        error_equals=["States.TaskFailed"],
        interval_seconds=5,
        max_attempts=2,
        backoff_rate=2.0
    )]
    
    builder.add_lambda_task("PreprocessData", "preprocess_data",
                          retry_config=custom_retry,
                          comment="Preprocess training data")
    
    # Feature engineering
    builder.add_lambda_task("FeatureEngineering", "feature_engineering",
                          comment="Extract and transform features")
    
    # Model training with SageMaker
    training_config = {
        "job_name": f"custom-training-${{aws:executionId}}",
        "algorithm_specification": {
            "TrainingImage": "382416733822.dkr.ecr.us-east-1.amazonaws.com/xgboost:latest",
            "TrainingInputMode": "File"
        },
        "input_data_config": [{
            "ChannelName": "training",
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri.$": "$.preprocessing_output.training_data_path",
                    "S3DataDistributionType": "FullyReplicated"
                }
            }
        }],
        "output_data_config": {
            "S3OutputPath": config.get("s3.model_artifacts_bucket", "s3://ml-models/")
        }
    }
    
    builder.add_sagemaker_training("TrainModel", training_config,
                                 comment="Train XGBoost model using SageMaker")
    
    # Model evaluation with multiple metrics
    builder.add_lambda_task("EvaluateModel", "evaluate_model",
                          comment="Evaluate model performance metrics")
    
    # Complex decision logic for deployment
    choice_builder = builder.add_choice("DeploymentDecision",
                                      comment="Make deployment decision based on multiple criteria")
    
    # High quality model - deploy to production
    choice_builder.when(
        AndRule(
            NumericGreaterThan("$.evaluation.accuracy", 0.95),
            NumericGreaterThan("$.evaluation.precision", 0.90),
            NumericGreaterThan("$.evaluation.recall", 0.90)
        ),
        "DeployToProduction"
    )
    
    # Good quality model - deploy to staging
    choice_builder.when(
        AndRule(
            NumericGreaterThan("$.evaluation.accuracy", 0.85),
            NumericGreaterThan("$.evaluation.precision", 0.80)
        ),
        "DeployToStaging"
    )
    
    # Poor quality model - retrain with different parameters
    choice_builder.otherwise("RetrainModel")
    
    # Production deployment
    builder.add_lambda_task("DeployToProduction", "deploy_production",
                          comment="Deploy model to production environment")
    
    # Staging deployment  
    builder.add_lambda_task("DeployToStaging", "deploy_staging",
                          comment="Deploy model to staging environment")
    
    # Retrain with different hyperparameters
    builder.add_lambda_task("RetrainModel", "retrain_model",
                          comment="Retrain model with adjusted hyperparameters")
    
    # Store model metadata
    builder.add_dynamodb_task("StoreModelMetadata", "putItem", "model_metadata",
                            item={
                                "model_id.$": "$.model_id",
                                "accuracy.$": "$.evaluation.accuracy",
                                "deployment_status.$": "$.deployment_status",
                                "timestamp.$": "$$.State.EnteredTime"
                            },
                            comment="Store model metadata in DynamoDB")
    
    # Send completion notification
    builder.add_sns_task("NotifyCompletion", "alerts",
                       message="ML pipeline completed successfully",
                       subject="ML Pipeline Notification",
                       comment="Notify team of pipeline completion")
    
    builder.end_with_success("Success", comment="Pipeline completed successfully")
    
    return builder.build()


def main():
    """Main example execution"""
    
    # Setup configuration
    config = setup_config()
    
    # Create workflows
    ml_workflow = ConfigurableWorkflow("MLPipeline", create_ml_pipeline)
    custom_ml_workflow = ConfigurableWorkflow("CustomMLPipeline", create_custom_ml_pipeline)
    
    # Switch to development environment
    config.setenv("development")
    
    print("=== Development Environment ===")
    print(f"Current environment: {config.current_env}")
    print(f"AWS region: {config.aws_region}")
    print(f"Lambda timeout: {config.lambda.timeout}")
    print(f"SageMaker instance: {config.sagemaker.instance_type}")
    
    # Generate development pipeline definition
    dev_definition = ml_workflow.create_for_environment(config)
    print("\n=== Development ML Pipeline Definition ===")
    print(json.dumps(dev_definition, indent=2))
    
    # Switch to production environment
    config.setenv("production")
    
    print(f"\n=== Production Environment ===")
    print(f"Current environment: {config.current_env}")
    print(f"AWS region: {config.aws_region}")
    print(f"Lambda timeout: {config.lambda.timeout}")
    print(f"SageMaker instance: {config.sagemaker.instance_type}")
    
    # Generate production pipeline definition
    prod_definition = ml_workflow.create_for_environment(config)
    print("\n=== Production ML Pipeline Definition ===")
    print(json.dumps(prod_definition, indent=2))
    
    # Create custom pipeline for development
    config.setenv("development")
    custom_definition = custom_ml_workflow.create_for_environment(config)
    print("\n=== Custom ML Pipeline Definition (Development) ===")
    print(json.dumps(custom_definition, indent=2))
    
    # Example: Deploy to AWS (commented out to avoid actual deployment)
    """
    try:
        # Deploy to development
        config.setenv("development")
        dev_arn = ml_workflow.deploy_to_environment(config)
        print(f"Deployed to development: {dev_arn}")
        
        # Execute pipeline
        execution_result = ml_workflow.execute(
            config,
            input_data={
                "data_source": "s3://ml-training-data/dataset.csv",
                "model_type": "xgboost",
                "hyperparameters": {
                    "max_depth": 6,
                    "eta": 0.3,
                    "objective": "binary:logistic"
                }
            },
            execution_name="test-execution-001"
        )
        print(f"Execution started: {execution_result['executionArn']}")
        
    except Exception as e:
        print(f"Deployment/execution error: {e}")
    """


if __name__ == "__main__":
    main()