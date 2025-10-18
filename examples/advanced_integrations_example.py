#!/usr/bin/env python3
"""
Advanced AWS Integrations Example - Comprehensive Enterprise Workflow
"""

import json
from stepfunctions_improved import (
    ConfigurableStepFunctionBuilder, ConfigurableWorkflow, setup_config,
    NumericGreaterThan, StringEquals, AndRule, OrRule, BooleanEquals
)


def create_comprehensive_data_pipeline(config):
    """Create a comprehensive data pipeline using advanced AWS services"""
    builder = ConfigurableStepFunctionBuilder("ComprehensiveDataPipeline", config)
    
    # Start with getting configuration from Secrets Manager
    builder.start_with("GetDatabaseCredentials")
    builder.add_secrets_manager_get_secret("GetDatabaseCredentials", "database_credentials",
                                         comment="Retrieve database credentials securely")
    
    # List source data files in S3
    builder.add_s3_operation("ListSourceFiles", "listObjects", "source_data",
                           prefix="raw-data/",
                           comment="List all source data files for processing")
    
    # Conditional processing based on file count
    choice_builder = builder.add_choice("CheckFileCount",
                                      comment="Determine processing strategy based on file count")
    
    choice_builder.when(
        NumericGreaterThan("$.file_count", 100),
        "ProcessLargeDataset"
    ).when(
        NumericGreaterThan("$.file_count", 10),
        "ProcessMediumDataset"
    ).otherwise("ProcessSmallDataset")
    
    # Large dataset processing with CodeBuild
    builder.add_codebuild_project("ProcessLargeDataset", "large_data_processor",
                                comment="Process large dataset using CodeBuild for scalability")
    
    # Medium dataset processing with Athena
    builder.add_athena_query("ProcessMediumDataset",
                           query_string="""
                           SELECT customer_id, 
                                  SUM(amount) as total_amount,
                                  COUNT(*) as transaction_count
                           FROM source_table 
                           WHERE date_partition >= '${execution_date}'
                           GROUP BY customer_id
                           """,
                           logical_workgroup="analytics_workgroup",
                           comment="Process medium dataset using Athena analytics")
    
    # Small dataset processing with Lambda
    builder.add_lambda_task("ProcessSmallDataset", "small_data_processor",
                          comment="Process small dataset using Lambda function")
    
    # AI/ML Analysis using Bedrock
    builder.add_bedrock_model_invocation("AnalyzeWithAI", "claude_model", {
        "prompt": "Analyze the following data patterns and provide insights: ${processed_data}",
        "max_tokens": 1000,
        "temperature": 0.1
    }, comment="Generate AI insights using Amazon Bedrock")
    
    # Document processing with Textract (if documents are detected)
    textract_choice = builder.add_choice("CheckForDocuments")
    textract_choice.when(
        BooleanEquals("$.has_documents", True),
        "ProcessDocuments"
    ).otherwise("SkipDocumentProcessing")
    
    builder.add_custom_task("ProcessDocuments", {
        "Type": "Task",
        "Resource": "arn:aws:states:::textract:startDocumentAnalysis.sync",
        "Parameters": {
            "DocumentLocation": {
                "S3Object": {
                    "Bucket.$": "$.document_bucket",
                    "Name.$": "$.document_key"
                }
            },
            "FeatureTypes": ["TABLES", "FORMS", "SIGNATURES"]
        }
    }, comment="Extract data from documents using Textract")
    
    builder.add_pass("SkipDocumentProcessing",
                   result={"document_processing": "skipped"},
                   comment="Skip document processing when no documents present")
    
    # Natural Language Processing with Comprehend
    builder.add_custom_task("AnalyzeText", {
        "Type": "Task",
        "Resource": "arn:aws:states:::comprehend:startDominantLanguageDetectionJob.sync",
        "Parameters": {
            "InputDataConfig": {
                "S3Uri.$": "$.text_data_location",
                "InputFormat": "ONE_DOC_PER_LINE"
            },
            "OutputDataConfig": {
                "S3Uri": config.get("s3.comprehend_output", "s3://comprehend-output/")
            },
            "DataAccessRoleArn": config.get("comprehend.role_arn")
        }
    }, comment="Analyze text data for language detection and sentiment")
    
    # Data Quality Assessment
    builder.add_lambda_task("AssessDataQuality", "data_quality_assessor",
                          comment="Assess overall data quality and completeness")
    
    # Conditional actions based on data quality
    quality_choice = builder.add_choice("DataQualityDecision")
    
    quality_choice.when(
        AndRule(
            NumericGreaterThan("$.quality_score", 0.8),
            BooleanEquals("$.completeness_check", True)
        ),
        "PublishToDataLake"
    ).when(
        NumericGreaterThan("$.quality_score", 0.6),
        "PublishToStagingArea"
    ).otherwise("HandleDataQualityIssues")
    
    # Publish high-quality data to data lake
    builder.add_s3_operation("PublishToDataLake", "copyObject", "data_lake",
                           source_bucket="${source_bucket}",
                           source_key="${processed_data_key}",
                           destination_key="curated/${execution_date}/${file_name}",
                           comment="Publish high-quality data to production data lake")
    
    # Publish medium-quality data to staging
    builder.add_s3_operation("PublishToStagingArea", "copyObject", "staging_data",
                           source_bucket="${source_bucket}",
                           source_key="${processed_data_key}",
                           destination_key="staging/${execution_date}/${file_name}",
                           comment="Publish medium-quality data to staging area for review")
    
    # Handle data quality issues
    builder.add_lambda_task("HandleDataQualityIssues", "data_quality_handler",
                          comment="Handle data quality issues and create remediation plan")
    
    # Send notifications via EventBridge
    builder.add_eventbridge_put_events("NotifyProcessingComplete", [
        {
            "Source": "data.pipeline",
            "DetailType": "Data Processing Complete",
            "Detail": {
                "executionId.$": "$$.Execution.Name",
                "status.$": "$.final_status",
                "qualityScore.$": "$.quality_score",
                "recordsProcessed.$": "$.records_processed"
            }
        }
    ], comment="Notify downstream systems of processing completion")
    
    # Update processing metadata in DynamoDB
    builder.add_dynamodb_task("UpdateProcessingMetadata", "putItem", "processing_metadata",
                            item={
                                "execution_id.$": "$$.Execution.Name",
                                "processing_date.$": "$$.State.EnteredTime",
                                "status.$": "$.final_status",
                                "quality_score.$": "$.quality_score",
                                "files_processed.$": "$.files_processed",
                                "ai_insights.$": "$.ai_analysis.insights"
                            },
                            comment="Store processing metadata for audit and monitoring")
    
    builder.end_with_success("Success", comment="Data pipeline completed successfully")
    
    return builder.build()


def create_mlops_pipeline(config):
    """Create an MLOps pipeline with model registry and monitoring"""
    builder = ConfigurableStepFunctionBuilder("MLOpsPipeline", config)
    
    builder.start_with("ValidateModelInput")
    builder.add_lambda_task("ValidateModelInput", "validate_model_input",
                          comment="Validate model training inputs and parameters")
    
    # Feature engineering with SageMaker Processing
    builder.add_sagemaker_processing_job("FeatureEngineering", {
        "job_name": "feature-engineering-${aws:executionId}",
        "app_specification": {
            "ImageUri": config.get("sagemaker.feature_engineering_image"),
            "ContainerEntrypoint": ["python3", "/opt/ml/code/feature_engineering.py"]
        },
        "processing_inputs": [{
            "InputName": "raw-features",
            "S3Input": {
                "S3Uri.$": "$.raw_features_path",
                "LocalPath": "/opt/ml/processing/input",
                "S3DataType": "S3Prefix"
            }
        }],
        "processing_output_config": {
            "Outputs": [{
                "OutputName": "engineered-features",
                "S3Output": {
                    "S3Uri": config.get("s3.engineered_features", "s3://engineered-features/"),
                    "LocalPath": "/opt/ml/processing/output"
                }
            }]
        }
    }, comment="Engineer features for model training")
    
    # Model training with hyperparameter optimization
    builder.add_sagemaker_hyperparameter_tuning("OptimizeModel", {
        "tuning_job_name": "hpo-${aws:executionId}",
        "tuning_config": {
            "Strategy": "Bayesian",
            "HyperParameterTuningJobObjective": {
                "Type": "Maximize",
                "MetricName": "validation:f1"
            },
            "ResourceLimits": {
                "MaxNumberOfTrainingJobs": config.get("sagemaker.tuning.max_jobs", 10),
                "MaxParallelTrainingJobs": config.get("sagemaker.tuning.max_parallel_jobs", 2)
            },
            "ParameterRanges": {
                "ContinuousParameterRanges": [
                    {"Name": "learning_rate", "MinValue": "0.001", "MaxValue": "0.1"},
                    {"Name": "dropout_rate", "MinValue": "0.1", "MaxValue": "0.5"}
                ],
                "IntegerParameterRanges": [
                    {"Name": "batch_size", "MinValue": "32", "MaxValue": "256"},
                    {"Name": "epochs", "MinValue": "10", "MaxValue": "100"}
                ]
            }
        },
        "training_job_definition": {
            "AlgorithmSpecification": {
                "TrainingImage": config.get("sagemaker.training_image"),
                "TrainingInputMode": "File"
            },
            "InputDataConfig": [{
                "ChannelName": "training",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri.$": "$.engineered_features_path"
                    }
                }
            }],
            "OutputDataConfig": {
                "S3OutputPath": config.get("s3.model_artifacts", "s3://model-artifacts/")
            }
        }
    }, comment="Optimize model hyperparameters using Bayesian optimization")
    
    # Model evaluation and validation
    builder.add_sagemaker_processing_job("EvaluateModel", {
        "job_name": "model-evaluation-${aws:executionId}",
        "app_specification": {
            "ImageUri": config.get("sagemaker.evaluation_image"),
            "ContainerEntrypoint": ["python3", "/opt/ml/code/evaluate_model.py"]
        },
        "processing_inputs": [
            {
                "InputName": "model",
                "S3Input": {
                    "S3Uri.$": "$.best_training_job.ModelArtifacts.S3ModelArtifacts",
                    "LocalPath": "/opt/ml/processing/model"
                }
            },
            {
                "InputName": "test-data",
                "S3Input": {
                    "S3Uri.$": "$.test_data_path",
                    "LocalPath": "/opt/ml/processing/test"
                }
            }
        ],
        "processing_output_config": {
            "Outputs": [{
                "OutputName": "evaluation-report",
                "S3Output": {
                    "S3Uri": config.get("s3.evaluation_reports", "s3://evaluation-reports/"),
                    "LocalPath": "/opt/ml/processing/evaluation"
                }
            }]
        }
    }, comment="Evaluate model performance on test dataset")
    
    # Model registry registration
    builder.add_custom_task("RegisterModel", {
        "Type": "Task",
        "Resource": "arn:aws:states:::sagemaker:createModelPackage",
        "Parameters": {
            "ModelPackageGroupName": config.get("sagemaker.model_package_group"),
            "ModelApprovalStatus": "PendingManualApproval",
            "InferenceSpecification": {
                "Containers": [{
                    "Image": config.get("sagemaker.inference_image"),
                    "ModelDataUrl.$": "$.best_training_job.ModelArtifacts.S3ModelArtifacts"
                }],
                "SupportedContentTypes": ["application/json"],
                "SupportedResponseMIMETypes": ["application/json"]
            },
            "ModelMetrics": {
                "ModelQuality": {
                    "Statistics": {
                        "ContentType": "application/json",
                        "S3Uri.$": "$.evaluation_output.model_statistics_path"
                    }
                }
            }
        }
    }, comment="Register model in SageMaker Model Registry")
    
    # Conditional deployment based on model performance
    deployment_choice = builder.add_choice("DeploymentApproval")
    
    deployment_choice.when(
        AndRule(
            NumericGreaterThan("$.evaluation.f1_score", 0.85),
            NumericGreaterThan("$.evaluation.precision", 0.8),
            NumericGreaterThan("$.evaluation.recall", 0.8)
        ),
        "AutoApproveDeployment"
    ).otherwise("RequestManualApproval")
    
    # Auto-approve high-performing models
    builder.add_custom_task("AutoApproveDeployment", {
        "Type": "Task",
        "Resource": "arn:aws:states:::sagemaker:updateModelPackage",
        "Parameters": {
            "ModelPackageArn.$": "$.model_package_arn",
            "ModelApprovalStatus": "Approved"
        }
    }, comment="Auto-approve high-performing models for deployment")
    
    # Request manual approval for borderline models
    builder.add_sns_task("RequestManualApproval", "model_approval_alerts",
                       message="Model requires manual approval for deployment",
                       subject="MLOps: Model Approval Required")
    
    # Deploy approved model to staging
    staging_deployment_config = {
        "model_name": "staging-model-${aws:executionId}",
        "endpoint_config_name": "staging-config-${aws:executionId}",
        "endpoint_name": config.get("sagemaker.staging_endpoint"),
        "primary_container": {
            "ModelPackageName.$": "$.model_package_arn"
        },
        "instance_type": config.get("sagemaker.staging.instance_type", "ml.t3.medium"),
        "initial_instance_count": 1
    }
    
    builder.add_sagemaker_endpoint_deployment("DeployToStaging", staging_deployment_config,
                                            comment="Deploy approved model to staging environment")
    
    # Set up model monitoring
    builder.add_custom_task("SetupModelMonitoring", {
        "Type": "Task",
        "Resource": "arn:aws:states:::sagemaker:createMonitoringSchedule",
        "Parameters": {
            "MonitoringScheduleName": "model-monitoring-${aws:executionId}",
            "MonitoringScheduleConfig": {
                "ScheduleConfig": {
                    "ScheduleExpression": "cron(0 */6 * * ? *)"  # Every 6 hours
                },
                "MonitoringJobDefinition": {
                    "MonitoringInputs": [{
                        "EndpointInput": {
                            "EndpointName.$": "$.staging_endpoint_name",
                            "LocalPath": "/opt/ml/processing/input/endpoint"
                        }
                    }],
                    "MonitoringOutputConfig": {
                        "MonitoringOutputs": [{
                            "S3Output": {
                                "S3Uri": config.get("s3.monitoring_output", "s3://model-monitoring/"),
                                "LocalPath": "/opt/ml/processing/output"
                            }
                        }]
                    },
                    "MonitoringResources": {
                        "ClusterConfig": {
                            "InstanceCount": 1,
                            "InstanceType": "ml.m5.large",
                            "VolumeSizeInGB": 20
                        }
                    },
                    "MonitoringAppSpecification": {
                        "ImageUri": "159807026194.dkr.ecr.us-east-1.amazonaws.com/sagemaker-model-monitor-analyzer"
                    }
                }
            }
        }
    }, comment="Set up continuous model monitoring for data drift detection")
    
    # Notify MLOps team of deployment completion
    builder.add_eventbridge_put_events("NotifyMLOpsTeam", [
        {
            "Source": "mlops.pipeline",
            "DetailType": "Model Deployment Complete",
            "Detail": {
                "modelPackageArn.$": "$.model_package_arn",
                "endpointName.$": "$.staging_endpoint_name",
                "modelMetrics.$": "$.evaluation",
                "deploymentStatus": "staging_deployed"
            }
        }
    ], comment="Notify MLOps team of successful model deployment")
    
    builder.end_with_success("Success", comment="MLOps pipeline completed successfully")
    
    return builder.build()


def create_document_processing_pipeline(config):
    """Create a document processing pipeline with AI services"""
    builder = ConfigurableStepFunctionBuilder("DocumentProcessingPipeline", config)
    
    builder.start_with("ValidateDocuments")
    builder.add_lambda_task("ValidateDocuments", "validate_document_input",
                          comment="Validate document inputs and formats")
    
    # Extract text from documents using Textract
    builder.add_custom_task("ExtractText", {
        "Type": "Task",
        "Resource": "arn:aws:states:::textract:startDocumentAnalysis.sync",
        "Parameters": {
            "DocumentLocation": {
                "S3Object": {
                    "Bucket.$": "$.document_bucket",
                    "Name.$": "$.document_key"
                }
            },
            "FeatureTypes": ["TABLES", "FORMS", "SIGNATURES", "LAYOUT"]
        }
    }, comment="Extract text, tables, and forms from documents using Textract")
    
    # Analyze extracted text with Comprehend
    builder.add_custom_task("AnalyzeText", {
        "Type": "Task",
        "Resource": "arn:aws:states:::comprehend:startEntitiesDetectionJob.sync",
        "Parameters": {
            "InputDataConfig": {
                "S3Uri.$": "$.textract_output_location",
                "InputFormat": "ONE_DOC_PER_LINE"
            },
            "OutputDataConfig": {
                "S3Uri": config.get("s3.comprehend_output", "s3://comprehend-analysis/")
            },
            "DataAccessRoleArn": config.get("comprehend.role_arn"),
            "LanguageCode": "en"
        }
    }, comment="Detect entities and key phrases in extracted text")
    
    # Generate insights using Bedrock
    builder.add_bedrock_model_invocation("GenerateInsights", "claude_model", {
        "prompt": """
        Analyze the following document content and provide structured insights:
        
        Document Type: ${document_type}
        Extracted Text: ${extracted_text}
        Detected Entities: ${entities}
        
        Please provide:
        1. Document summary
        2. Key information extracted
        3. Potential compliance issues
        4. Recommended actions
        """,
        "max_tokens": 2000,
        "temperature": 0.1
    }, comment="Generate AI-powered insights from document analysis")
    
    # Classify document based on content
    builder.add_lambda_task("ClassifyDocument", "document_classifier",
                          comment="Classify document type and determine processing workflow")
    
    # Route based on document classification
    classification_choice = builder.add_choice("DocumentRouting")
    
    classification_choice.when(
        StringEquals("$.document_classification", "contract"),
        "ProcessContract"
    ).when(
        StringEquals("$.document_classification", "invoice"),
        "ProcessInvoice"
    ).when(
        StringEquals("$.document_classification", "legal"),
        "ProcessLegalDocument"
    ).otherwise("ProcessGenericDocument")
    
    # Contract processing workflow
    builder.add_lambda_task("ProcessContract", "contract_processor",
                          comment="Process contract-specific information and compliance checks")
    
    # Invoice processing workflow
    builder.add_lambda_task("ProcessInvoice", "invoice_processor",
                          comment="Process invoice data and financial information")
    
    # Legal document processing workflow
    builder.add_lambda_task("ProcessLegalDocument", "legal_document_processor",
                          comment="Process legal document with compliance analysis")
    
    # Generic document processing
    builder.add_lambda_task("ProcessGenericDocument", "generic_document_processor",
                          comment="Process generic document with standard analysis")
    
    # Store processed results
    builder.add_dynamodb_task("StoreResults", "putItem", "document_processing_results",
                            item={
                                "document_id.$": "$.document_id",
                                "processing_timestamp.$": "$$.State.EnteredTime",
                                "document_type.$": "$.document_classification",
                                "extracted_entities.$": "$.comprehend_analysis.entities",
                                "ai_insights.$": "$.bedrock_analysis.insights",
                                "processing_status": "completed"
                            },
                            comment="Store document processing results for retrieval")
    
    # Send completion notification
    builder.add_sns_task("NotifyCompletion", "document_processing_alerts",
                       message="Document processing completed successfully",
                       subject="Document Processing Complete")
    
    builder.end_with_success("Success")
    
    return builder.build()


def main():
    """Main example execution"""
    
    # Setup configuration
    config = setup_config()
    
    # Create workflows
    data_pipeline_workflow = ConfigurableWorkflow("ComprehensiveDataPipeline", create_comprehensive_data_pipeline)
    mlops_workflow = ConfigurableWorkflow("MLOpsPipeline", create_mlops_pipeline)
    document_workflow = ConfigurableWorkflow("DocumentProcessing", create_document_processing_pipeline)
    
    # Switch to development environment
    config.setenv("development")
    
    print("=== Comprehensive Data Pipeline (Development) ===")
    data_pipeline_definition = data_pipeline_workflow.create_for_environment(config)
    print(json.dumps(data_pipeline_definition, indent=2))
    
    print("\n=== MLOps Pipeline ===")
    mlops_definition = mlops_workflow.create_for_environment(config)
    print(json.dumps(mlops_definition, indent=2))
    
    print("\n=== Document Processing Pipeline ===")
    document_definition = document_workflow.create_for_environment(config)
    print(json.dumps(document_definition, indent=2))
    
    # Show advanced service configurations
    print(f"\n=== Advanced Service Configuration ===")
    print(f"CodeBuild retry attempts: {config.get('codebuild.retry_attempts', 2)}")
    print(f"Athena output location: {config.get('athena.output_location', 's3://athena-results/')}")
    print(f"Bedrock retry attempts: {config.get('bedrock.retry_attempts', 3)}")
    print(f"S3 retry attempts: {config.get('s3.retry_attempts', 3)}")


if __name__ == "__main__":
    main()