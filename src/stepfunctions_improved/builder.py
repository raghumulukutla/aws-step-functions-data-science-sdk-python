# Copyright 2024 Improved Step Functions Framework

"""
Fluent builder pattern for creating Step Functions state machines
"""

from typing import Dict, Optional, List, Any, Union
from dynaconf import Dynaconf

from .choice_rules import ChoiceRule
from .error_handling import RetryConfig, CatchConfig, ErrorHandling
from .aws_services import AWSServiceIntegrations, ConfigurableAWSServices
from .sagemaker_integrations import SageMakerIntegrations, ConfigurableSageMakerIntegrations
from .advanced_integrations import AdvancedAWSIntegrations, ConfigurableAdvancedIntegrations, MLOpsIntegrations


class ChoiceBuilder:
    """Builder for Choice state branches"""
    
    def __init__(self, parent: 'StepFunctionBuilder', choice_state_id: str):
        self.parent = parent
        self.choice_state_id = choice_state_id
    
    def when(self, condition: ChoiceRule, next_state: str) -> 'ChoiceBuilder':
        """Add a conditional branch"""
        choice_def = condition.to_dict()
        choice_def["Next"] = next_state
        self.parent.states[self.choice_state_id]["Choices"].append(choice_def)
        return self
    
    def otherwise(self, next_state: str) -> 'StepFunctionBuilder':
        """Set default branch when no conditions match"""
        self.parent.states[self.choice_state_id]["Default"] = next_state
        return self.parent


class StepFunctionBuilder:
    """Fluent builder for Step Functions state machines"""
    
    def __init__(self, name: str):
        self.name = name
        self.states: Dict[str, dict] = {}
        self.start_at: Optional[str] = None
        self._current_state: Optional[str] = None
    
    def start_with(self, state_id: str) -> 'StepFunctionBuilder':
        """Set the starting state"""
        self.start_at = state_id
        self._current_state = state_id
        return self
    
    def add_pass(self, state_id: str, 
                result: Optional[Any] = None,
                comment: Optional[str] = None,
                input_path: Optional[str] = None,
                output_path: Optional[str] = None,
                result_path: Optional[str] = None) -> 'StepFunctionBuilder':
        """Add a Pass state"""
        state_def = {"Type": "Pass"}
        
        if result is not None:
            state_def["Result"] = result
        if comment:
            state_def["Comment"] = comment
        if input_path:
            state_def["InputPath"] = input_path
        if output_path:
            state_def["OutputPath"] = output_path
        if result_path:
            state_def["ResultPath"] = result_path
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_wait(self, state_id: str, 
                seconds: Optional[int] = None,
                timestamp: Optional[str] = None,
                seconds_path: Optional[str] = None,
                timestamp_path: Optional[str] = None,
                comment: Optional[str] = None) -> 'StepFunctionBuilder':
        """Add a Wait state"""
        state_def = {"Type": "Wait"}
        
        # Exactly one timing parameter must be provided
        timing_params = [seconds, timestamp, seconds_path, timestamp_path]
        if sum(x is not None for x in timing_params) != 1:
            raise ValueError("Exactly one of seconds, timestamp, seconds_path, or timestamp_path must be provided")
        
        if seconds is not None:
            state_def["Seconds"] = seconds
        elif timestamp is not None:
            state_def["Timestamp"] = timestamp
        elif seconds_path is not None:
            state_def["SecondsPath"] = seconds_path
        elif timestamp_path is not None:
            state_def["TimestampPath"] = timestamp_path
        
        if comment:
            state_def["Comment"] = comment
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_choice(self, state_id: str, 
                  comment: Optional[str] = None,
                  input_path: Optional[str] = None,
                  output_path: Optional[str] = None) -> ChoiceBuilder:
        """Add a Choice state"""
        state_def = {
            "Type": "Choice",
            "Choices": []
        }
        
        if comment:
            state_def["Comment"] = comment
        if input_path:
            state_def["InputPath"] = input_path
        if output_path:
            state_def["OutputPath"] = output_path
        
        self.states[state_id] = state_def
        self._link_if_needed(state_id)
        return ChoiceBuilder(self, state_id)
    
    def add_parallel(self, state_id: str, 
                    branches: List['StepFunctionBuilder'],
                    comment: Optional[str] = None,
                    retry_config: Optional[List[RetryConfig]] = None,
                    catch_config: Optional[List[CatchConfig]] = None) -> 'StepFunctionBuilder':
        """Add a Parallel state"""
        state_def = {
            "Type": "Parallel",
            "Branches": [branch.build() for branch in branches]
        }
        
        if comment:
            state_def["Comment"] = comment
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_map(self, state_id: str,
               iterator: 'StepFunctionBuilder',
               items_path: str = "$",
               max_concurrency: Optional[int] = None,
               comment: Optional[str] = None,
               retry_config: Optional[List[RetryConfig]] = None,
               catch_config: Optional[List[CatchConfig]] = None) -> 'StepFunctionBuilder':
        """Add a Map state"""
        state_def = {
            "Type": "Map",
            "ItemsPath": items_path,
            "Iterator": iterator.build()
        }
        
        if max_concurrency is not None:
            state_def["MaxConcurrency"] = max_concurrency
        if comment:
            state_def["Comment"] = comment
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_lambda_task(self, state_id: str, 
                       function_name: str,
                       payload_path: str = "$",
                       wait_for_callback: bool = False,
                       timeout_seconds: Optional[int] = None,
                       retry_config: Optional[List[RetryConfig]] = None,
                       catch_config: Optional[List[CatchConfig]] = None,
                       comment: Optional[str] = None) -> 'StepFunctionBuilder':
        """Add a Lambda task state"""
        state_def = AWSServiceIntegrations.lambda_invoke(
            function_name=function_name,
            payload_path=payload_path,
            wait_for_callback=wait_for_callback,
            timeout_seconds=timeout_seconds
        )
        
        if comment:
            state_def["Comment"] = comment
        
        # Add default retry if none provided
        if retry_config is None:
            retry_config = [ErrorHandling.LAMBDA_RETRY]
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_custom_task(self, state_id: str, 
                       task_definition: dict,
                       retry_config: Optional[List[RetryConfig]] = None,
                       catch_config: Optional[List[CatchConfig]] = None) -> 'StepFunctionBuilder':
        """Add a custom task state"""
        state_def = task_definition.copy()
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def end_with_success(self, state_id: str = "Success",
                        comment: Optional[str] = None) -> 'StepFunctionBuilder':
        """Add a Succeed terminal state"""
        state_def = {"Type": "Succeed"}
        if comment:
            state_def["Comment"] = comment
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def end_with_failure(self, state_id: str = "Failure",
                        error: str = "WorkflowFailed",
                        cause: str = "Workflow execution failed",
                        comment: Optional[str] = None) -> 'StepFunctionBuilder':
        """Add a Fail terminal state"""
        state_def = {
            "Type": "Fail",
            "Error": error,
            "Cause": cause
        }
        if comment:
            state_def["Comment"] = comment
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def _link_if_needed(self, state_id: str) -> 'StepFunctionBuilder':
        """Link previous state to current state if needed"""
        if self._current_state and self._current_state != state_id:
            current_state = self.states[self._current_state]
            # Only add Next field for states that support it
            if current_state.get("Type") not in ["Succeed", "Fail", "Choice"]:
                current_state["Next"] = state_id
        
        self._current_state = state_id
        return self
    
    def build(self) -> dict:
        """Build the complete state machine definition"""
        if not self.start_at:
            raise ValueError("State machine must have a starting state")
        
        # Set End: true for terminal states that don't have Next
        for state_id, state_def in self.states.items():
            if ("Next" not in state_def and 
                state_def.get("Type") not in ["Succeed", "Fail", "Choice"]):
                state_def["End"] = True
        
        return {
            "Comment": f"State machine: {self.name}",
            "StartAt": self.start_at,
            "States": self.states
        }


class ConfigurableStepFunctionBuilder(StepFunctionBuilder):
    """Configuration-aware Step Functions builder using Dynaconf"""
    
    def __init__(self, name: str, config: Dynaconf):
        super().__init__(name)
        self.config = config
        self.aws_services = ConfigurableAWSServices(config)
        self.sagemaker = ConfigurableSageMakerIntegrations(config)
        self.advanced = ConfigurableAdvancedIntegrations(config)
    
    def add_lambda_task(self, state_id: str,
                       logical_function_name: str,
                       payload_path: str = "$",
                       wait_for_callback: bool = False,
                       custom_config: Optional[dict] = None,
                       retry_config: Optional[List[RetryConfig]] = None,
                       catch_config: Optional[List[CatchConfig]] = None,
                       comment: Optional[str] = None) -> 'ConfigurableStepFunctionBuilder':
        """Add Lambda task with configuration resolution"""
        
        # Get timeout from config or custom override
        timeout = None
        if custom_config and "timeout_seconds" in custom_config:
            timeout = custom_config["timeout_seconds"]
        else:
            timeout = self.config.get("lambda.timeout", 60)
        
        state_def = self.aws_services.lambda_invoke(
            logical_function_name=logical_function_name,
            payload_path=payload_path,
            wait_for_callback=wait_for_callback,
            timeout_seconds=timeout
        )
        
        if comment:
            state_def["Comment"] = comment
        
        # Get retry config from configuration or use default
        if retry_config is None:
            retry_attempts = self.config.get("lambda.retry_attempts", 3)
            if retry_attempts > 0:
                retry_config = [RetryConfig(
                    error_equals=self.config.get("lambda.retry_errors", ErrorHandling.LAMBDA_RETRY.error_equals),
                    interval_seconds=self.config.get("lambda.retry_interval", 2),
                    max_attempts=retry_attempts,
                    backoff_rate=self.config.get("lambda.backoff_rate", 2.0)
                )]
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_sagemaker_training(self, state_id: str,
                              job_config: dict,
                              retry_config: Optional[List[RetryConfig]] = None,
                              catch_config: Optional[List[CatchConfig]] = None,
                              comment: Optional[str] = None) -> 'ConfigurableStepFunctionBuilder':
        """Add SageMaker training job with configuration defaults"""
        
        state_def = self.aws_services.sagemaker_training_job(job_config)
        
        if comment:
            state_def["Comment"] = comment
        
        # Get retry config from configuration or use default
        if retry_config is None:
            retry_attempts = self.config.get("sagemaker.retry_attempts", 2)
            if retry_attempts > 0:
                retry_config = [RetryConfig(
                    error_equals=self.config.get("sagemaker.retry_errors", ErrorHandling.SAGEMAKER_RETRY.error_equals),
                    interval_seconds=self.config.get("sagemaker.retry_interval", 5),
                    max_attempts=retry_attempts,
                    backoff_rate=self.config.get("sagemaker.backoff_rate", 3.0)
                )]
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_dynamodb_task(self, state_id: str,
                         operation: str,
                         logical_table_name: str,
                         retry_config: Optional[List[RetryConfig]] = None,
                         catch_config: Optional[List[CatchConfig]] = None,
                         comment: Optional[str] = None,
                         **kwargs) -> 'ConfigurableStepFunctionBuilder':
        """Add DynamoDB task with configuration resolution"""
        
        state_def = self.aws_services.dynamodb_operation(
            operation=operation,
            logical_table_name=logical_table_name,
            **kwargs
        )
        
        if comment:
            state_def["Comment"] = comment
        
        # Get retry config from configuration or use default
        if retry_config is None:
            retry_attempts = self.config.get("dynamodb.retry_attempts", 5)
            if retry_attempts > 0:
                retry_config = [ErrorHandling.DYNAMODB_RETRY]
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_sns_task(self, state_id: str,
                    logical_topic_name: str,
                    message: str,
                    subject: Optional[str] = None,
                    retry_config: Optional[List[RetryConfig]] = None,
                    catch_config: Optional[List[CatchConfig]] = None,
                    comment: Optional[str] = None) -> 'ConfigurableStepFunctionBuilder':
        """Add SNS publish task with configuration resolution"""
        
        state_def = self.aws_services.sns_publish(
            logical_topic_name=logical_topic_name,
            message=message,
            subject=subject
        )
        
        if comment:
            state_def["Comment"] = comment
        
        # Get retry config from configuration or use default
        if retry_config is None:
            retry_attempts = self.config.get("sns.retry_attempts", 3)
            if retry_attempts > 0:
                retry_config = [ErrorHandling.SNS_RETRY]
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    # Additional SageMaker Methods
    def add_sagemaker_processing_job(self, state_id: str,
                                   job_config: dict,
                                   retry_config: Optional[List[RetryConfig]] = None,
                                   catch_config: Optional[List[CatchConfig]] = None,
                                   comment: Optional[str] = None) -> 'ConfigurableStepFunctionBuilder':
        """Add SageMaker processing job with configuration defaults"""
        
        state_def = self.sagemaker.processing_job(job_config)
        
        if comment:
            state_def["Comment"] = comment
        
        if retry_config is None:
            retry_attempts = self.config.get("sagemaker.processing.retry_attempts", 2)
            if retry_attempts > 0:
                retry_config = [ErrorHandling.SAGEMAKER_RETRY]
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_sagemaker_hyperparameter_tuning(self, state_id: str,
                                          tuning_config: dict,
                                          retry_config: Optional[List[RetryConfig]] = None,
                                          catch_config: Optional[List[CatchConfig]] = None,
                                          comment: Optional[str] = None) -> 'ConfigurableStepFunctionBuilder':
        """Add SageMaker hyperparameter tuning job"""
        
        role_arn = tuning_config.get("role_arn") or self.config.get("sagemaker.role_arn")
        if not role_arn:
            raise ValueError("SageMaker role ARN not configured")
        
        state_def = SageMakerIntegrations.hyperparameter_tuning_job(
            tuning_job_name=tuning_config["tuning_job_name"],
            hyperparameter_tuning_job_config=tuning_config["tuning_config"],
            training_job_definition=tuning_config["training_job_definition"],
            role_arn=role_arn
        )
        
        if comment:
            state_def["Comment"] = comment
        
        if retry_config is None:
            retry_config = [ErrorHandling.SAGEMAKER_RETRY]
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_sagemaker_transform_job(self, state_id: str,
                                  transform_config: dict,
                                  retry_config: Optional[List[RetryConfig]] = None,
                                  catch_config: Optional[List[CatchConfig]] = None,
                                  comment: Optional[str] = None) -> 'ConfigurableStepFunctionBuilder':
        """Add SageMaker transform (batch inference) job"""
        
        state_def = SageMakerIntegrations.transform_job(
            transform_job_name=transform_config["job_name"],
            model_name=transform_config["model_name"],
            transform_input=transform_config["transform_input"],
            transform_output=transform_config["transform_output"],
            transform_resources=transform_config.get("transform_resources", {
                "InstanceType": self.config.get("sagemaker.transform.instance_type", "ml.m5.large"),
                "InstanceCount": self.config.get("sagemaker.transform.instance_count", 1)
            })
        )
        
        if comment:
            state_def["Comment"] = comment
        
        if retry_config is None:
            retry_config = [ErrorHandling.SAGEMAKER_RETRY]
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    # Advanced AWS Service Methods
    def add_codebuild_project(self, state_id: str,
                            logical_project_name: str,
                            source_version: Optional[str] = None,
                            retry_config: Optional[List[RetryConfig]] = None,
                            catch_config: Optional[List[CatchConfig]] = None,
                            comment: Optional[str] = None) -> 'ConfigurableStepFunctionBuilder':
        """Add CodeBuild project execution"""
        
        state_def = self.advanced.codebuild_project(
            logical_project_name=logical_project_name,
            source_version=source_version
        )
        
        if comment:
            state_def["Comment"] = comment
        
        if retry_config is None:
            retry_attempts = self.config.get("codebuild.retry_attempts", 2)
            if retry_attempts > 0:
                retry_config = [RetryConfig(
                    error_equals=["CodeBuild.AWSCodeBuildException"],
                    interval_seconds=5,
                    max_attempts=retry_attempts,
                    backoff_rate=2.0
                )]
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_athena_query(self, state_id: str,
                        query_string: str,
                        logical_workgroup: Optional[str] = None,
                        retry_config: Optional[List[RetryConfig]] = None,
                        catch_config: Optional[List[CatchConfig]] = None,
                        comment: Optional[str] = None) -> 'ConfigurableStepFunctionBuilder':
        """Add Athena query execution"""
        
        state_def = self.advanced.athena_query(
            query_string=query_string,
            logical_workgroup=logical_workgroup
        )
        
        if comment:
            state_def["Comment"] = comment
        
        if retry_config is None:
            retry_attempts = self.config.get("athena.retry_attempts", 3)
            if retry_attempts > 0:
                retry_config = [RetryConfig(
                    error_equals=["Athena.InvalidRequestException", "Athena.InternalServerException"],
                    interval_seconds=2,
                    max_attempts=retry_attempts,
                    backoff_rate=2.0
                )]
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_bedrock_model_invocation(self, state_id: str,
                                   logical_model_name: str,
                                   model_input: dict,
                                   retry_config: Optional[List[RetryConfig]] = None,
                                   catch_config: Optional[List[CatchConfig]] = None,
                                   comment: Optional[str] = None) -> 'ConfigurableStepFunctionBuilder':
        """Add Bedrock model invocation"""
        
        state_def = self.advanced.bedrock_model_invocation(
            logical_model_name=logical_model_name,
            body=model_input
        )
        
        if comment:
            state_def["Comment"] = comment
        
        if retry_config is None:
            retry_attempts = self.config.get("bedrock.retry_attempts", 3)
            if retry_attempts > 0:
                retry_config = [RetryConfig(
                    error_equals=["Bedrock.ThrottlingException", "Bedrock.ModelTimeoutException"],
                    interval_seconds=1,
                    max_attempts=retry_attempts,
                    backoff_rate=2.0
                )]
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_s3_operation(self, state_id: str,
                        operation: str,
                        logical_bucket_name: str,
                        retry_config: Optional[List[RetryConfig]] = None,
                        catch_config: Optional[List[CatchConfig]] = None,
                        comment: Optional[str] = None,
                        **kwargs) -> 'ConfigurableStepFunctionBuilder':
        """Add S3 operation (listObjects, copyObject, etc.)"""
        
        state_def = self.advanced.s3_operation(
            operation=operation,
            logical_bucket_name=logical_bucket_name,
            **kwargs
        )
        
        if comment:
            state_def["Comment"] = comment
        
        if retry_config is None:
            retry_attempts = self.config.get("s3.retry_attempts", 3)
            if retry_attempts > 0:
                retry_config = [RetryConfig(
                    error_equals=["S3.AmazonS3Exception"],
                    interval_seconds=1,
                    max_attempts=retry_attempts,
                    backoff_rate=2.0
                )]
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_secrets_manager_get_secret(self, state_id: str,
                                     logical_secret_name: str,
                                     retry_config: Optional[List[RetryConfig]] = None,
                                     catch_config: Optional[List[CatchConfig]] = None,
                                     comment: Optional[str] = None) -> 'ConfigurableStepFunctionBuilder':
        """Add Secrets Manager get secret operation"""
        
        state_def = self.advanced.secrets_manager_secret(
            logical_secret_name=logical_secret_name
        )
        
        if comment:
            state_def["Comment"] = comment
        
        if retry_config is None:
            retry_config = [RetryConfig(
                error_equals=["SecretsManager.ResourceNotFoundException", "SecretsManager.InvalidRequestException"],
                interval_seconds=1,
                max_attempts=3,
                backoff_rate=2.0
            )]
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
    
    def add_eventbridge_put_events(self, state_id: str,
                                 events: List[dict],
                                 retry_config: Optional[List[RetryConfig]] = None,
                                 catch_config: Optional[List[CatchConfig]] = None,
                                 comment: Optional[str] = None) -> 'ConfigurableStepFunctionBuilder':
        """Add EventBridge put events operation"""
        
        state_def = AdvancedAWSIntegrations.eventbridge_put_events(entries=events)
        
        if comment:
            state_def["Comment"] = comment
        
        if retry_config is None:
            retry_config = [RetryConfig(
                error_equals=["Events.InternalException"],
                interval_seconds=1,
                max_attempts=3,
                backoff_rate=2.0
            )]
        
        if retry_config:
            state_def["Retry"] = [retry.to_dict() for retry in retry_config]
        
        if catch_config:
            state_def["Catch"] = [catch.to_dict() for catch in catch_config]
        
        self.states[state_id] = state_def
        return self._link_if_needed(state_id)
