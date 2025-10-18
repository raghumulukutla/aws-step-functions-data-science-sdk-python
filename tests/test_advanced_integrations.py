#!/usr/bin/env python3
"""
Tests for advanced AWS integrations
"""

import pytest
from stepfunctions_improved import (
    ConfigurableStepFunctionBuilder, setup_config,
    AdvancedAWSIntegrations, StateMachineValidator
)


class TestAdvancedAWSIntegrations:
    
    def test_codebuild_integration(self):
        """Test CodeBuild integration"""
        task_def = AdvancedAWSIntegrations.codebuild_start_build(
            project_name="test-project",
            source_version="main",
            wait_for_completion=True
        )
        
        assert task_def["Type"] == "Task"
        assert task_def["Resource"] == "arn:aws:states:::codebuild:startBuild.sync"
        assert task_def["Parameters"]["ProjectName"] == "test-project"
        assert task_def["Parameters"]["SourceVersion"] == "main"
    
    def test_athena_integration(self):
        """Test Athena integration"""
        task_def = AdvancedAWSIntegrations.athena_start_query_execution(
            query_string="SELECT * FROM table",
            result_configuration={"OutputLocation": "s3://results/"},
            wait_for_completion=True
        )
        
        assert task_def["Type"] == "Task"
        assert task_def["Resource"] == "arn:aws:states:::athena:startQueryExecution.sync"
        assert task_def["Parameters"]["QueryString"] == "SELECT * FROM table"
        assert task_def["Parameters"]["ResultConfiguration"]["OutputLocation"] == "s3://results/"
    
    def test_bedrock_integration(self):
        """Test Bedrock integration"""
        task_def = AdvancedAWSIntegrations.bedrock_invoke_model(
            model_id="anthropic.claude-v2",
            body={"prompt": "Hello", "max_tokens": 100}
        )
        
        assert task_def["Type"] == "Task"
        assert task_def["Resource"] == "arn:aws:states:::bedrock:invokeModel"
        assert task_def["Parameters"]["ModelId"] == "anthropic.claude-v2"
        assert task_def["Parameters"]["Body"]["prompt"] == "Hello"
    
    def test_s3_operations(self):
        """Test S3 operations"""
        list_task = AdvancedAWSIntegrations.s3_list_objects(
            bucket="test-bucket",
            prefix="data/",
            max_keys=100
        )
        
        assert list_task["Type"] == "Task"
        assert list_task["Resource"] == "arn:aws:states:::aws-sdk:s3:listObjectsV2"
        assert list_task["Parameters"]["Bucket"] == "test-bucket"
        assert list_task["Parameters"]["Prefix"] == "data/"
        assert list_task["Parameters"]["MaxKeys"] == 100
        
        copy_task = AdvancedAWSIntegrations.s3_copy_object(
            source_bucket="source-bucket",
            source_key="source/file.txt",
            destination_bucket="dest-bucket",
            destination_key="dest/file.txt"
        )
        
        assert copy_task["Type"] == "Task"
        assert copy_task["Resource"] == "arn:aws:states:::aws-sdk:s3:copyObject"
        assert copy_task["Parameters"]["Bucket"] == "dest-bucket"
        assert copy_task["Parameters"]["CopySource"] == "source-bucket/source/file.txt"
    
    def test_secrets_manager_integration(self):
        """Test Secrets Manager integration"""
        task_def = AdvancedAWSIntegrations.secrets_manager_get_secret_value(
            secret_id="prod/database/password",
            version_stage="AWSCURRENT"
        )
        
        assert task_def["Type"] == "Task"
        assert task_def["Resource"] == "arn:aws:states:::aws-sdk:secretsmanager:getSecretValue"
        assert task_def["Parameters"]["SecretId"] == "prod/database/password"
        assert task_def["Parameters"]["VersionStage"] == "AWSCURRENT"
    
    def test_eventbridge_integration(self):
        """Test EventBridge integration"""
        events = [
            {
                "Source": "myapp",
                "DetailType": "User Action",
                "Detail": {"action": "login", "user": "john"}
            }
        ]
        
        task_def = AdvancedAWSIntegrations.eventbridge_put_events(entries=events)
        
        assert task_def["Type"] == "Task"
        assert task_def["Resource"] == "arn:aws:states:::events:putEvents"
        assert task_def["Parameters"]["Entries"] == events
    
    def test_textract_integration(self):
        """Test Textract integration"""
        task_def = AdvancedAWSIntegrations.textract_start_document_analysis(
            document_location={
                "S3Object": {
                    "Bucket": "documents",
                    "Name": "document.pdf"
                }
            },
            feature_types=["TABLES", "FORMS"],
            wait_for_completion=True
        )
        
        assert task_def["Type"] == "Task"
        assert task_def["Resource"] == "arn:aws:states:::textract:startDocumentAnalysis.sync"
        assert task_def["Parameters"]["FeatureTypes"] == ["TABLES", "FORMS"]


class TestConfigurableAdvancedIntegrations:
    
    def test_configurable_builder_advanced_methods(self):
        """Test advanced methods in configurable builder"""
        config = setup_config()
        config.setenv("development")
        
        builder = ConfigurableStepFunctionBuilder("AdvancedPipeline", config)
        
        # Test building a pipeline with advanced integrations
        pipeline = (builder
            .start_with("GetSecrets")
            .add_secrets_manager_get_secret("GetSecrets", "database_credentials")
            .add_s3_operation("ListFiles", "listObjects", "source_data", prefix="input/")
            .add_bedrock_model_invocation("AnalyzeData", "claude_model", {
                "prompt": "Analyze this data",
                "max_tokens": 500
            })
            .add_eventbridge_put_events("NotifyCompletion", [
                {
                    "Source": "data.pipeline",
                    "DetailType": "Processing Complete",
                    "Detail": {"status": "success"}
                }
            ])
            .end_with_success("Success")
            .build())
        
        # Validate the pipeline
        validator = StateMachineValidator(pipeline)
        is_valid = validator.validate()
        
        if not is_valid:
            print("Validation errors:")
            for error in validator.get_errors():
                print(f"  - {error}")
        
        assert is_valid == True
        assert "GetSecrets" in pipeline["States"]
        assert "ListFiles" in pipeline["States"]
        assert "AnalyzeData" in pipeline["States"]
        assert "NotifyCompletion" in pipeline["States"]
    
    def test_comprehensive_pipeline_validation(self):
        """Test validation of comprehensive pipeline with all integrations"""
        config = setup_config()
        config.setenv("development")
        
        builder = ConfigurableStepFunctionBuilder("ComprehensivePipeline", config)
        
        pipeline = (builder
            .start_with("Initialize")
            .add_pass("Initialize", result={"pipeline": "started"})
            .add_lambda_task("ProcessData", "process_data")
            .add_sagemaker_training_job("TrainModel", {
                "job_name": "training-job",
                "algorithm_specification": {
                    "TrainingImage": "382416733822.dkr.ecr.us-east-1.amazonaws.com/xgboost:latest",
                    "TrainingInputMode": "File"
                },
                "input_data_config": [{
                    "ChannelName": "training",
                    "DataSource": {
                        "S3DataSource": {
                            "S3DataType": "S3Prefix",
                            "S3Uri": "s3://training-data/"
                        }
                    }
                }],
                "output_data_config": {
                    "S3OutputPath": "s3://model-output/"
                }
            })
            .add_dynamodb_task("StoreResults", "putItem", "results_table",
                             item={"id": "test", "result": "success"})
            .add_sns_task("NotifySuccess", "alerts",
                        message="Pipeline completed",
                        subject="Pipeline Success")
            .end_with_success("Success")
            .build())
        
        # Validate the comprehensive pipeline
        validator = StateMachineValidator(pipeline)
        is_valid = validator.validate()
        
        assert is_valid == True
        assert len(pipeline["States"]) >= 6  # All the states we added
        
        # Check that all states are properly linked
        assert pipeline["States"]["Initialize"]["Next"] == "ProcessData"
        assert pipeline["States"]["ProcessData"]["Next"] == "TrainModel"


if __name__ == "__main__":
    pytest.main([__file__])