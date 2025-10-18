#!/usr/bin/env python3
"""
Comprehensive SageMaker Integration Examples
"""

import json
from stepfunctions_improved import (
    ConfigurableStepFunctionBuilder, ConfigurableWorkflow, setup_config,
    SageMakerIntegrations, NumericGreaterThan, AndRule, StringEquals
)


def create_complete_ml_pipeline(config):
    """Create a comprehensive ML pipeline with all SageMaker services"""
    builder = ConfigurableStepFunctionBuilder("ComprehensiveMLPipeline", config)
    
    # Start with data preprocessing using SageMaker Processing
    builder.start_with("PreprocessData")
    builder.add_sagemaker_processing_job("PreprocessData", {
        "job_name": "preprocess-job-${aws:executionId}",
        "app_specification": {
            "ImageUri": "382416733822.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3",
            "ContainerEntrypoint": ["python3", "/opt/ml/code/preprocess.py"]
        },
        "processing_inputs": [{
            "InputName": "raw-data",
            "S3Input": {
                "S3Uri.$": "$.input_data_path",
                "LocalPath": "/opt/ml/processing/input",
                "S3DataType": "S3Prefix",
                "S3InputMode": "File"
            }
        }],
        "processing_output_config": {
            "Outputs": [{
                "OutputName": "processed-data",
                "S3Output": {
                    "S3Uri": config.get("s3.processed_data_bucket", "s3://processed-data/"),
                    "LocalPath": "/opt/ml/processing/output",
                    "S3UploadMode": "EndOfJob"
                }
            }]
        },
        "environment": {
            "DATASET_TYPE": "tabular"
        }
    }, comment="Preprocess raw data using SageMaker Processing")
    
    # Hyperparameter tuning job
    builder.add_sagemaker_hyperparameter_tuning("TuneHyperparameters", {
        "tuning_job_name": "hpo-job-${aws:executionId}",
        "tuning_config": {
            "Strategy": "Bayesian",
            "HyperParameterTuningJobObjective": {
                "Type": "Maximize",
                "MetricName": "validation:auc"
            },
            "ResourceLimits": {
                "MaxNumberOfTrainingJobs": config.get("sagemaker.tuning.max_jobs", 20),
                "MaxParallelTrainingJobs": config.get("sagemaker.tuning.max_parallel_jobs", 2)
            },
            "ParameterRanges": {
                "ContinuousParameterRanges": [
                    {
                        "Name": "eta",
                        "MinValue": "0.1",
                        "MaxValue": "0.5"
                    },
                    {
                        "Name": "alpha",
                        "MinValue": "0",
                        "MaxValue": "2"
                    }
                ],
                "IntegerParameterRanges": [
                    {
                        "Name": "max_depth",
                        "MinValue": "3",
                        "MaxValue": "12"
                    }
                ]
            }
        },
        "training_job_definition": {
            "AlgorithmSpecification": {
                "TrainingImage": "382416733822.dkr.ecr.us-east-1.amazonaws.com/xgboost:latest",
                "TrainingInputMode": "File"
            },
            "InputDataConfig": [{
                "ChannelName": "training",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri.$": "$.preprocessing_output.processed_data_path",
                        "S3DataDistributionType": "FullyReplicated"
                    }
                }
            }],
            "OutputDataConfig": {
                "S3OutputPath": config.get("s3.model_artifacts_bucket", "s3://model-artifacts/")
            },
            "ResourceConfig": {
                "InstanceType": config.get("sagemaker.training.instance_type", "ml.m5.large"),
                "InstanceCount": 1,
                "VolumeSizeInGB": config.get("sagemaker.training.volume_size", 30)
            },
            "StoppingCondition": {
                "MaxRuntimeInSeconds": config.get("sagemaker.training.max_runtime", 3600)
            },
            "StaticHyperParameters": {
                "objective": "binary:logistic",
                "num_round": "100"
            }
        }
    }, comment="Optimize hyperparameters using Bayesian optimization")
    
    # Model evaluation using Processing
    builder.add_sagemaker_processing_job("EvaluateModel", {
        "job_name": "evaluate-job-${aws:executionId}",
        "app_specification": {
            "ImageUri": "382416733822.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3",
            "ContainerEntrypoint": ["python3", "/opt/ml/code/evaluate.py"]
        },
        "processing_inputs": [
            {
                "InputName": "model",
                "S3Input": {
                    "S3Uri.$": "$.tuning_output.BestTrainingJob.ModelArtifacts.S3ModelArtifacts",
                    "LocalPath": "/opt/ml/processing/model",
                    "S3DataType": "S3Prefix",
                    "S3InputMode": "File"
                }
            },
            {
                "InputName": "test-data",
                "S3Input": {
                    "S3Uri.$": "$.test_data_path",
                    "LocalPath": "/opt/ml/processing/test",
                    "S3DataType": "S3Prefix",
                    "S3InputMode": "File"
                }
            }
        ],
        "processing_output_config": {
            "Outputs": [{
                "OutputName": "evaluation",
                "S3Output": {
                    "S3Uri": config.get("s3.evaluation_bucket", "s3://model-evaluation/"),
                    "LocalPath": "/opt/ml/processing/evaluation",
                    "S3UploadMode": "EndOfJob"
                }
            }]
        }
    }, comment="Evaluate model performance on test dataset")
    
    # Conditional deployment based on model performance
    choice_builder = builder.add_choice("DeploymentDecision",
                                      comment="Decide deployment strategy based on model performance")
    
    # High performance - deploy to production
    choice_builder.when(
        AndRule(
            NumericGreaterThan("$.evaluation.auc", 0.9),
            NumericGreaterThan("$.evaluation.accuracy", 0.85)
        ),
        "DeployToProduction"
    )
    
    # Medium performance - deploy to staging
    choice_builder.when(
        AndRule(
            NumericGreaterThan("$.evaluation.auc", 0.8),
            NumericGreaterThan("$.evaluation.accuracy", 0.75)
        ),
        "DeployToStaging"
    )
    
    # Low performance - retrain or notify
    choice_builder.otherwise("HandleLowPerformance")
    
    # Production deployment with real-time endpoint
    production_deployment_config = {
        "model_name": "production-model-${aws:executionId}",
        "endpoint_config_name": "production-config-${aws:executionId}",
        "endpoint_name": config.get("sagemaker.production_endpoint_name", "production-ml-endpoint"),
        "primary_container": {
            "Image": "382416733822.dkr.ecr.us-east-1.amazonaws.com/xgboost:latest",
            "ModelDataUrl.$": "$.tuning_output.BestTrainingJob.ModelArtifacts.S3ModelArtifacts"
        },
        "instance_type": config.get("sagemaker.inference.instance_type", "ml.m5.large"),
        "initial_instance_count": config.get("sagemaker.inference.initial_instance_count", 2),
        "data_capture_config": {
            "EnableCapture": config.get("sagemaker.inference.enable_data_capture", True),
            "InitialSamplingPercentage": 100,
            "DestinationS3Uri": config.get("s3.data_capture_bucket", "s3://data-capture/"),
            "CaptureOptions": [
                {"CaptureMode": "Input"},
                {"CaptureMode": "Output"}
            ]
        } if config.get("sagemaker.inference.enable_data_capture", False) else None
    }
    
    builder.add_sagemaker_endpoint_deployment("DeployToProduction", production_deployment_config,
                                            comment="Deploy high-performance model to production")
    
    # Staging deployment with smaller instance
    staging_deployment_config = {
        "model_name": "staging-model-${aws:executionId}",
        "endpoint_config_name": "staging-config-${aws:executionId}",
        "endpoint_name": config.get("sagemaker.staging_endpoint_name", "staging-ml-endpoint"),
        "primary_container": {
            "Image": "382416733822.dkr.ecr.us-east-1.amazonaws.com/xgboost:latest",
            "ModelDataUrl.$": "$.tuning_output.BestTrainingJob.ModelArtifacts.S3ModelArtifacts"
        },
        "instance_type": "ml.t3.medium",
        "initial_instance_count": 1
    }
    
    builder.add_sagemaker_endpoint_deployment("DeployToStaging", staging_deployment_config,
                                            comment="Deploy medium-performance model to staging")
    
    # Handle low performance - could retrain or notify
    builder.add_sns_task("HandleLowPerformance", "alerts",
                       message="Model performance below threshold - manual review required",
                       subject="ML Model Performance Alert")
    
    builder.end_with_success("Success", comment="ML pipeline completed successfully")
    
    return builder.build()


def create_batch_inference_pipeline(config):
    """Create a batch inference pipeline using SageMaker Transform"""
    builder = ConfigurableStepFunctionBuilder("BatchInferencePipeline", config)
    
    builder.start_with("PrepareBatchData")
    builder.add_lambda_task("PrepareBatchData", "prepare_batch_data",
                          comment="Prepare batch data for inference")
    
    # Batch transform job
    builder.add_sagemaker_transform_job("BatchInference", {
        "job_name": "batch-inference-${aws:executionId}",
        "model_name": config.get("sagemaker.batch_model_name", "production-model"),
        "transform_input": {
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri.$": "$.batch_input_path"
                }
            },
            "ContentType": "text/csv",
            "SplitType": "Line"
        },
        "transform_output": {
            "S3OutputPath": config.get("s3.batch_output_bucket", "s3://batch-inference-output/"),
            "AssembleWith": "Line"
        },
        "transform_resources": {
            "InstanceType": config.get("sagemaker.transform.instance_type", "ml.m5.large"),
            "InstanceCount": config.get("sagemaker.transform.instance_count", 1)
        }
    }, comment="Run batch inference on prepared data")
    
    # Post-process results
    builder.add_lambda_task("PostProcessResults", "post_process_batch_results",
                          comment="Post-process batch inference results")
    
    builder.end_with_success("Success")
    
    return builder.build()


def create_automl_pipeline(config):
    """Create an AutoML pipeline for automated model development"""
    builder = ConfigurableStepFunctionBuilder("AutoMLPipeline", config)
    
    builder.start_with("PrepareAutoMLData")
    builder.add_lambda_task("PrepareAutoMLData", "prepare_automl_data",
                          comment="Prepare data for AutoML job")
    
    # AutoML job
    builder.add_sagemaker_automl_job("AutoMLJob", {
        "job_name": "automl-job-${aws:executionId}",
        "input_data_config": [{
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri.$": "$.automl_input_path"
                }
            },
            "TargetAttributeName": "target"
        }],
        "output_data_config": {
            "S3OutputPath": config.get("s3.automl_output_bucket", "s3://automl-output/")
        },
        "problem_type": "BinaryClassification",
        "job_objective": {
            "MetricName": "AUC"
        },
        "job_config": {
            "CompletionCriteria": {
                "MaxCandidates": config.get("sagemaker.automl.max_candidates", 250),
                "MaxRuntimePerTrainingJobInSeconds": 3600,
                "MaxAutoMLJobRuntimeInSeconds": 86400
            }
        }
    }, comment="Run AutoML to automatically find best model")
    
    # Evaluate AutoML results
    builder.add_lambda_task("EvaluateAutoMLResults", "evaluate_automl_results",
                          comment="Evaluate AutoML job results")
    
    # Conditional deployment of best AutoML model
    choice_builder = builder.add_choice("AutoMLDeploymentDecision")
    
    choice_builder.when(
        NumericGreaterThan("$.automl_best_candidate.FinalAutoMLJobObjectiveMetric.Value", 0.85),
        "DeployAutoMLModel"
    ).otherwise("NotifyAutoMLResults")
    
    # Deploy best AutoML model
    automl_deployment_config = {
        "model_name": "automl-model-${aws:executionId}",
        "endpoint_config_name": "automl-config-${aws:executionId}",
        "endpoint_name": config.get("sagemaker.automl_endpoint_name", "automl-endpoint"),
        "primary_container": {
            "Image.$": "$.automl_best_candidate.InferenceContainers[0].Image",
            "ModelDataUrl.$": "$.automl_best_candidate.InferenceContainers[0].ModelDataUrl"
        },
        "instance_type": config.get("sagemaker.inference.instance_type", "ml.m5.large"),
        "initial_instance_count": 1
    }
    
    builder.add_sagemaker_endpoint_deployment("DeployAutoMLModel", automl_deployment_config)
    
    builder.add_sns_task("NotifyAutoMLResults", "alerts",
                       message="AutoML job completed - review results",
                       subject="AutoML Job Completion")
    
    builder.end_with_success("Success")
    
    return builder.build()


def create_model_monitoring_pipeline(config):
    """Create a pipeline for model monitoring and retraining"""
    builder = ConfigurableStepFunctionBuilder("ModelMonitoringPipeline", config)
    
    builder.start_with("CheckModelDrift")
    builder.add_lambda_task("CheckModelDrift", "check_model_drift",
                          comment="Check for model drift using captured data")
    
    # Conditional retraining based on drift detection
    choice_builder = builder.add_choice("DriftDecision")
    
    choice_builder.when(
        AndRule(
            NumericGreaterThan("$.drift_score", 0.1),
            StringEquals("$.drift_detected", "true")
        ),
        "TriggerRetraining"
    ).otherwise("ContinueMonitoring")
    
    # Trigger retraining with updated data
    builder.add_sagemaker_training_job("TriggerRetraining", {
        "job_name": "retrain-job-${aws:executionId}",
        "algorithm_specification": {
            "TrainingImage": "382416733822.dkr.ecr.us-east-1.amazonaws.com/xgboost:latest",
            "TrainingInputMode": "File"
        },
        "input_data_config": [{
            "ChannelName": "training",
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri.$": "$.updated_training_data_path",
                    "S3DataDistributionType": "FullyReplicated"
                }
            }
        }],
        "output_data_config": {
            "S3OutputPath": config.get("s3.retrained_models_bucket", "s3://retrained-models/")
        },
        "hyperparameters": {
            "objective": "binary:logistic",
            "num_round": "100",
            "max_depth": "6",
            "eta": "0.3"
        }
    }, comment="Retrain model with updated data")
    
    # A/B test new model
    builder.add_lambda_task("SetupABTest", "setup_ab_test",
                          comment="Setup A/B test for new model")
    
    builder.add_pass("ContinueMonitoring",
                   result={"action": "continue_monitoring"},
                   comment="Continue monitoring without retraining")
    
    builder.end_with_success("Success")
    
    return builder.build()


def main():
    """Main example execution"""
    
    # Setup configuration
    config = setup_config()
    
    # Create workflows
    comprehensive_workflow = ConfigurableWorkflow("ComprehensiveML", create_complete_ml_pipeline)
    batch_workflow = ConfigurableWorkflow("BatchInference", create_batch_inference_pipeline)
    automl_workflow = ConfigurableWorkflow("AutoML", create_automl_pipeline)
    monitoring_workflow = ConfigurableWorkflow("ModelMonitoring", create_model_monitoring_pipeline)
    
    # Switch to development environment
    config.setenv("development")
    
    print("=== Comprehensive ML Pipeline (Development) ===")
    comprehensive_definition = comprehensive_workflow.create_for_environment(config)
    print(json.dumps(comprehensive_definition, indent=2))
    
    print("\n=== Batch Inference Pipeline ===")
    batch_definition = batch_workflow.create_for_environment(config)
    print(json.dumps(batch_definition, indent=2))
    
    print("\n=== AutoML Pipeline ===")
    automl_definition = automl_workflow.create_for_environment(config)
    print(json.dumps(automl_definition, indent=2))
    
    print("\n=== Model Monitoring Pipeline ===")
    monitoring_definition = monitoring_workflow.create_for_environment(config)
    print(json.dumps(monitoring_definition, indent=2))
    
    # Show configuration differences
    print(f"\n=== SageMaker Configuration (Development) ===")
    print(f"Training instance: {config.sagemaker.training.instance_type}")
    print(f"Processing instance: {config.sagemaker.processing.instance_type}")
    print(f"Inference instance: {config.sagemaker.inference.instance_type}")
    print(f"Max tuning jobs: {config.sagemaker.tuning.max_jobs}")
    print(f"AutoML max candidates: {config.sagemaker.automl.max_candidates}")
    
    # Switch to production environment
    config.setenv("production")
    print(f"\n=== SageMaker Configuration (Production) ===")
    print(f"Training instance: {config.sagemaker.training.instance_type}")
    print(f"Processing instance: {config.sagemaker.processing.instance_type}")
    print(f"Inference instance: {config.sagemaker.inference.instance_type}")
    print(f"Max tuning jobs: {config.sagemaker.tuning.max_jobs}")
    print(f"AutoML max candidates: {config.sagemaker.automl.max_candidates}")


if __name__ == "__main__":
    main()