# Copyright 2024 Improved Step Functions Framework

"""
High-level workflow management with configuration support
"""

import json
import boto3
from typing import Dict, Any, Optional, Callable
from dynaconf import Dynaconf

from .builder import ConfigurableStepFunctionBuilder
from .aws_services import ConfigurableAWSServices
from .validation import StateMachineValidator, ValidationError


class ConfigurableWorkflow:
    """Configuration-aware workflow management"""
    
    def __init__(self, name: str, definition_factory: Callable[[Dynaconf], dict]):
        self.name = name
        self.definition_factory = definition_factory
        self._cached_definitions: Dict[str, dict] = {}
    
    def create_for_environment(self, config: Dynaconf) -> dict:
        """Create workflow definition for specific environment"""
        env = config.current_env
        
        # Use cached definition if available
        if env in self._cached_definitions:
            return self._cached_definitions[env]
        
        # Create new definition
        definition = self.definition_factory(config)
        
        # Validate definition
        validator = StateMachineValidator(definition)
        if not validator.validate():
            errors = validator.get_errors()
            raise ValidationError(f"Invalid state machine definition: {'; '.join(errors)}")
        
        # Cache and return
        self._cached_definitions[env] = definition
        return definition
    
    def deploy_to_environment(self, config: Dynaconf, 
                            step_functions_client: Optional[Any] = None) -> str:
        """Deploy workflow to specific environment"""
        if step_functions_client is None:
            region = config.get("aws.region", "us-east-1")
            step_functions_client = boto3.client('stepfunctions', region_name=region)
        
        definition = self.create_for_environment(config)
        
        # Environment-specific state machine name
        env = config.current_env
        state_machine_name = f"{env}-{self.name}" if env != "default" else self.name
        
        # Get execution role from config
        execution_role = config.get("step_functions.execution_role")
        if not execution_role:
            raise ValueError("step_functions.execution_role not configured")
        
        # Get tags from config
        tags = []
        if env != "default":
            tags.append({"key": "Environment", "value": env})
        tags.append({"key": "Pipeline", "value": self.name})
        
        # Add custom tags from config
        custom_tags = config.get("step_functions.tags", {})
        for key, value in custom_tags.items():
            tags.append({"key": key, "value": value})
        
        try:
            response = step_functions_client.create_state_machine(
                name=state_machine_name,
                definition=json.dumps(definition, indent=2),
                roleArn=execution_role,
                tags=tags
            )
            return response["stateMachineArn"]
            
        except step_functions_client.exceptions.StateMachineAlreadyExists:
            # Update existing state machine
            state_machines = step_functions_client.list_state_machines()
            arn = next(
                (sm["stateMachineArn"] for sm in state_machines["stateMachines"] 
                 if sm["name"] == state_machine_name),
                None
            )
            
            if arn:
                step_functions_client.update_state_machine(
                    stateMachineArn=arn,
                    definition=json.dumps(definition, indent=2),
                    roleArn=execution_role
                )
                return arn
            else:
                raise ValueError(f"Could not find existing state machine: {state_machine_name}")
    
    def execute(self, config: Dynaconf, 
               input_data: Optional[dict] = None,
               execution_name: Optional[str] = None,
               step_functions_client: Optional[Any] = None) -> dict:
        """Execute the workflow"""
        if step_functions_client is None:
            region = config.get("aws.region", "us-east-1")
            step_functions_client = boto3.client('stepfunctions', region_name=region)
        
        # Get state machine ARN
        env = config.current_env
        state_machine_name = f"{env}-{self.name}" if env != "default" else self.name
        
        state_machines = step_functions_client.list_state_machines()
        arn = next(
            (sm["stateMachineArn"] for sm in state_machines["stateMachines"] 
             if sm["name"] == state_machine_name),
            None
        )
        
        if not arn:
            raise ValueError(f"State machine not found: {state_machine_name}. Deploy it first.")
        
        # Start execution
        params = {"stateMachineArn": arn}
        
        if execution_name:
            params["name"] = execution_name
        
        if input_data:
            params["input"] = json.dumps(input_data)
        
        return step_functions_client.start_execution(**params)


class PipelineFactory:
    """Factory for creating common pipeline patterns"""
    
    def __init__(self, config: Dynaconf):
        self.config = config
        self.aws_services = ConfigurableAWSServices(config)
    
    def create_ml_training_pipeline(self, pipeline_name: str = "MLTrainingPipeline") -> dict:
        """Create a machine learning training pipeline"""
        builder = ConfigurableStepFunctionBuilder(pipeline_name, self.config)
        
        # Get pipeline configuration
        pipeline_config = self.config.get("pipelines.ml_training", {})
        
        # Start pipeline
        builder.start_with("StartPipeline")
        builder.add_pass("StartPipeline", 
                        result={"message": "Starting ML Training Pipeline"},
                        comment="Initialize pipeline execution")
        
        # Optional data validation step
        if pipeline_config.get("enable_data_validation", True):
            builder.add_lambda_task("ValidateData", "validate_data",
                                  comment="Validate input data quality and format")
        
        # Data preprocessing
        builder.add_lambda_task("PreprocessData", "preprocess_data",
                              comment="Clean and prepare data for training")
        
        # Training method selection based on config
        training_method = pipeline_config.get("training_method", "sagemaker")
        
        if training_method == "sagemaker":
            # SageMaker training job
            training_config = {
                "job_name": f"training-job-${{aws:executionId}}",
                "algorithm_specification": pipeline_config.get("algorithm_spec", {
                    "TrainingImage": "382416733822.dkr.ecr.us-east-1.amazonaws.com/xgboost:latest",
                    "TrainingInputMode": "File"
                }),
                "input_data_config": pipeline_config.get("input_config", [{
                    "ChannelName": "training",
                    "DataSource": {
                        "S3DataSource": {
                            "S3DataType": "S3Prefix",
                            "S3Uri.$": "$.preprocessing_output.training_data_path",
                            "S3DataDistributionType": "FullyReplicated"
                        }
                    }
                }]),
                "output_data_config": pipeline_config.get("output_config", {
                    "S3OutputPath": self.config.get("s3.model_artifacts_bucket", "s3://ml-model-artifacts/")
                })
            }
            
            builder.add_sagemaker_training("TrainModel", training_config,
                                         comment="Train ML model using SageMaker")
        
        elif training_method == "lambda":
            # Lambda-based training for smaller models
            builder.add_lambda_task("TrainModel", "train_model",
                                  comment="Train ML model using Lambda function")
        
        else:
            raise ValueError(f"Unsupported training method: {training_method}")
        
        # Model evaluation
        builder.add_lambda_task("EvaluateModel", "evaluate_model",
                              comment="Evaluate trained model performance")
        
        # Conditional deployment based on accuracy
        accuracy_threshold = pipeline_config.get("accuracy_threshold", 0.8)
        auto_deploy = self.config.get("auto_deploy", False)
        
        choice_builder = builder.add_choice("CheckModelQuality",
                                          comment="Decide deployment based on model quality")
        
        if auto_deploy:
            from .choice_rules import NumericGreaterThan
            choice_builder.when(
                NumericGreaterThan("$.evaluation.accuracy", accuracy_threshold),
                "DeployModel"
            ).otherwise("NotifyLowAccuracy")
            
            builder.add_lambda_task("DeployModel", "deploy_model",
                                  comment="Deploy model to production")
        else:
            from .choice_rules import NumericGreaterThan
            choice_builder.when(
                NumericGreaterThan("$.evaluation.accuracy", accuracy_threshold),
                "NotifyForApproval"
            ).otherwise("NotifyLowAccuracy")
            
            builder.add_sns_task("NotifyForApproval", "alerts",
                               message="Model ready for manual deployment approval",
                               subject="ML Model Ready for Deployment",
                               comment="Notify team for manual deployment")
        
        # Low accuracy notification
        builder.add_sns_task("NotifyLowAccuracy", "alerts",
                           message="Model accuracy below threshold - requires investigation",
                           subject="ML Model Quality Alert",
                           comment="Alert team about low model performance")
        
        # Success state
        builder.end_with_success("Success", comment="Pipeline completed successfully")
        
        return builder.build()
    
    def create_data_processing_pipeline(self, pipeline_name: str = "DataProcessingPipeline") -> dict:
        """Create a data processing pipeline"""
        builder = ConfigurableStepFunctionBuilder(pipeline_name, self.config)
        
        pipeline_config = self.config.get("pipelines.data_processing", {})
        
        builder.start_with("StartProcessing")
        builder.add_pass("StartProcessing", 
                        result={"message": "Starting Data Processing Pipeline"})
        
        # Parallel data processing branches
        if pipeline_config.get("enable_parallel_processing", True):
            # Create parallel branches for different data types
            branch1 = ConfigurableStepFunctionBuilder("ProcessStructuredData", self.config)
            branch1.start_with("ProcessCSV")
            branch1.add_lambda_task("ProcessCSV", "process_csv_data")
            branch1.end_with_success()
            
            branch2 = ConfigurableStepFunctionBuilder("ProcessUnstructuredData", self.config)
            branch2.start_with("ProcessJSON")
            branch2.add_lambda_task("ProcessJSON", "process_json_data")
            branch2.end_with_success()
            
            builder.add_parallel("ProcessDataParallel", [branch1, branch2],
                                comment="Process different data formats in parallel")
        else:
            # Sequential processing
            builder.add_lambda_task("ProcessStructuredData", "process_csv_data")
            builder.add_lambda_task("ProcessUnstructuredData", "process_json_data")
        
        # Aggregate results
        builder.add_lambda_task("AggregateResults", "aggregate_data",
                              comment="Combine processed data from all sources")
        
        # Store results
        builder.add_dynamodb_task("StoreResults", "putItem", "processed_data",
                                 item={"id.$": "$.execution_id", "data.$": "$.aggregated_data"},
                                 comment="Store processed data in DynamoDB")
        
        builder.end_with_success("Success")
        
        return builder.build()
    
    def create_notification_pipeline(self, pipeline_name: str = "NotificationPipeline") -> dict:
        """Create a notification pipeline"""
        builder = ConfigurableStepFunctionBuilder(pipeline_name, self.config)
        
        builder.start_with("ProcessNotification")
        builder.add_lambda_task("ProcessNotification", "process_notification",
                              comment="Process and format notification content")
        
        # Multi-channel notification
        from .choice_rules import StringEquals, AndRule
        
        choice_builder = builder.add_choice("SelectNotificationChannel",
                                          comment="Choose notification channels based on urgency")
        
        choice_builder.when(
            StringEquals("$.urgency", "high"),
            "SendUrgentNotifications"
        ).when(
            StringEquals("$.urgency", "medium"),
            "SendEmailNotification"
        ).otherwise("SendSlackNotification")
        
        # Urgent notifications (email + SMS + Slack)
        urgent_branch = ConfigurableStepFunctionBuilder("UrgentNotifications", self.config)
        urgent_branch.start_with("SendEmail")
        urgent_branch.add_sns_task("SendEmail", "email_notifications", 
                                  message="$.notification.content",
                                  subject="$.notification.subject")
        urgent_branch.add_sns_task("SendSMS", "sms_notifications",
                                  message="$.notification.short_content")
        urgent_branch.add_lambda_task("SendSlack", "send_slack_notification")
        urgent_branch.end_with_success()
        
        builder.add_parallel("SendUrgentNotifications", [urgent_branch],
                           comment="Send urgent notifications via multiple channels")
        
        # Regular email notification
        builder.add_sns_task("SendEmailNotification", "email_notifications",
                           message="$.notification.content",
                           subject="$.notification.subject",
                           comment="Send email notification")
        
        # Slack notification
        builder.add_lambda_task("SendSlackNotification", "send_slack_notification",
                              comment="Send Slack notification")
        
        builder.end_with_success("Success")
        
        return builder.build()