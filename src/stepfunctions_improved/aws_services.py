# Copyright 2024 Improved Step Functions Framework

"""
AWS service integration templates for Step Functions
"""

from typing import Optional, Dict, Any, List
from dynaconf import Dynaconf


class AWSServiceIntegrations:
    """Static methods for creating AWS service integration task definitions"""
    
    @staticmethod
    def lambda_invoke(function_name: str, 
                     payload_path: str = "$", 
                     wait_for_callback: bool = False,
                     timeout_seconds: Optional[int] = None) -> dict:
        """Create Lambda invoke task definition"""
        resource = "arn:aws:states:::lambda:invoke"
        if wait_for_callback:
            resource += ".waitForTaskToken"
        
        task_def = {
            "Type": "Task",
            "Resource": resource,
            "Parameters": {
                "FunctionName": function_name,
                "Payload.$": payload_path
            }
        }
        
        if timeout_seconds:
            task_def["TimeoutSeconds"] = timeout_seconds
        
        return task_def
    
    @staticmethod
    def sagemaker_training_job(job_name: str, 
                              algorithm_specification: dict,
                              input_data_config: list,
                              output_data_config: dict,
                              resource_config: dict,
                              role_arn: str,
                              hyperparameters: Optional[dict] = None,
                              stopping_condition: Optional[dict] = None) -> dict:
        """Create SageMaker training job task definition"""
        parameters = {
            "TrainingJobName": job_name,
            "AlgorithmSpecification": algorithm_specification,
            "InputDataConfig": input_data_config,
            "OutputDataConfig": output_data_config,
            "ResourceConfig": resource_config,
            "RoleArn": role_arn
        }
        
        if hyperparameters:
            parameters["HyperParameters"] = hyperparameters
        
        if stopping_condition:
            parameters["StoppingCondition"] = stopping_condition
        else:
            parameters["StoppingCondition"] = {"MaxRuntimeInSeconds": 86400}  # 24 hours default
        
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::sagemaker:createTrainingJob.sync",
            "Parameters": parameters
        }
    
    @staticmethod
    def sagemaker_transform_job(job_name: str,
                               model_name: str,
                               transform_input: dict,
                               transform_output: dict,
                               transform_resources: dict) -> dict:
        """Create SageMaker transform job task definition"""
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::sagemaker:createTransformJob.sync",
            "Parameters": {
                "TransformJobName": job_name,
                "ModelName": model_name,
                "TransformInput": transform_input,
                "TransformOutput": transform_output,
                "TransformResources": transform_resources
            }
        }
    
    @staticmethod
    def batch_submit_job(job_name: str, 
                        job_queue: str, 
                        job_definition: str,
                        parameters: Optional[dict] = None,
                        wait_for_completion: bool = True) -> dict:
        """Create Batch submit job task definition"""
        resource = "arn:aws:states:::batch:submitJob"
        if wait_for_completion:
            resource += ".sync"
        
        params = {
            "JobName": job_name,
            "JobQueue": job_queue,
            "JobDefinition": job_definition
        }
        
        if parameters:
            params["Parameters"] = parameters
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": params
        }
    
    @staticmethod
    def dynamodb_put_item(table_name: str, item: dict) -> dict:
        """Create DynamoDB put item task definition"""
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::dynamodb:putItem",
            "Parameters": {
                "TableName": table_name,
                "Item": item
            }
        }
    
    @staticmethod
    def dynamodb_get_item(table_name: str, key: dict) -> dict:
        """Create DynamoDB get item task definition"""
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::dynamodb:getItem",
            "Parameters": {
                "TableName": table_name,
                "Key": key
            }
        }
    
    @staticmethod
    def dynamodb_update_item(table_name: str, 
                           key: dict, 
                           update_expression: str,
                           expression_attribute_values: Optional[dict] = None) -> dict:
        """Create DynamoDB update item task definition"""
        params = {
            "TableName": table_name,
            "Key": key,
            "UpdateExpression": update_expression
        }
        
        if expression_attribute_values:
            params["ExpressionAttributeValues"] = expression_attribute_values
        
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::dynamodb:updateItem",
            "Parameters": params
        }
    
    @staticmethod
    def sns_publish(topic_arn: str, 
                   message: str, 
                   subject: Optional[str] = None,
                   message_attributes: Optional[dict] = None) -> dict:
        """Create SNS publish task definition"""
        params = {
            "TopicArn": topic_arn,
            "Message": message
        }
        
        if subject:
            params["Subject"] = subject
        
        if message_attributes:
            params["MessageAttributes"] = message_attributes
        
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::sns:publish",
            "Parameters": params
        }
    
    @staticmethod
    def sqs_send_message(queue_url: str, 
                        message_body: str,
                        delay_seconds: Optional[int] = None,
                        message_attributes: Optional[dict] = None) -> dict:
        """Create SQS send message task definition"""
        params = {
            "QueueUrl": queue_url,
            "MessageBody": message_body
        }
        
        if delay_seconds is not None:
            params["DelaySeconds"] = delay_seconds
        
        if message_attributes:
            params["MessageAttributes"] = message_attributes
        
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::sqs:sendMessage",
            "Parameters": params
        }
    
    @staticmethod
    def glue_start_job_run(job_name: str, 
                          arguments: Optional[dict] = None,
                          wait_for_completion: bool = True) -> dict:
        """Create Glue start job run task definition"""
        resource = "arn:aws:states:::glue:startJobRun"
        if wait_for_completion:
            resource += ".sync"
        
        params = {"JobName": job_name}
        if arguments:
            params["Arguments"] = arguments
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": params
        }
    
    @staticmethod
    def ecs_run_task(cluster: str,
                    task_definition: str,
                    network_configuration: Optional[dict] = None,
                    wait_for_completion: bool = True) -> dict:
        """Create ECS run task definition"""
        resource = "arn:aws:states:::ecs:runTask"
        if wait_for_completion:
            resource += ".sync"
        
        params = {
            "Cluster": cluster,
            "TaskDefinition": task_definition,
            "LaunchType": "FARGATE"
        }
        
        if network_configuration:
            params["NetworkConfiguration"] = network_configuration
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": params
        }


class ConfigurableAWSServices:
    """Configuration-aware AWS service integrations using Dynaconf"""
    
    def __init__(self, config: Dynaconf):
        self.config = config
    
    def lambda_invoke(self, logical_function_name: str, **kwargs) -> dict:
        """Create Lambda invoke with config-resolved function name"""
        actual_function_name = self.config.get(f"functions.{logical_function_name}")
        if not actual_function_name:
            raise ValueError(f"Function {logical_function_name} not configured for environment {self.config.current_env}")
        
        timeout = kwargs.pop("timeout_seconds", None) or self.config.get("lambda.timeout", 60)
        
        return AWSServiceIntegrations.lambda_invoke(
            function_name=actual_function_name,
            timeout_seconds=timeout,
            **kwargs
        )
    
    def sagemaker_training_job(self, job_config: dict, **kwargs) -> dict:
        """Create SageMaker training job with config defaults"""
        # Merge with configuration defaults
        resource_config = {
            "InstanceType": self.config.get("sagemaker.instance_type", "ml.m5.large"),
            "InstanceCount": self.config.get("sagemaker.instance_count", 1),
            "VolumeSizeInGB": self.config.get("sagemaker.volume_size", 30),
            **job_config.get("resource_config", {})
        }
        
        role_arn = job_config.get("role_arn") or self.config.get("sagemaker.role_arn")
        if not role_arn:
            raise ValueError("SageMaker role ARN not configured")
        
        return AWSServiceIntegrations.sagemaker_training_job(
            job_name=job_config["job_name"],
            algorithm_specification=job_config["algorithm_specification"],
            input_data_config=job_config["input_data_config"],
            output_data_config=job_config["output_data_config"],
            resource_config=resource_config,
            role_arn=role_arn,
            **kwargs
        )
    
    def dynamodb_operation(self, operation: str, logical_table_name: str, **kwargs) -> dict:
        """Create DynamoDB operation with config-resolved table name"""
        actual_table_name = self.config.get(f"dynamodb.tables.{logical_table_name}")
        if not actual_table_name:
            raise ValueError(f"Table {logical_table_name} not configured for environment {self.config.current_env}")
        
        if operation == "putItem":
            return AWSServiceIntegrations.dynamodb_put_item(actual_table_name, **kwargs)
        elif operation == "getItem":
            return AWSServiceIntegrations.dynamodb_get_item(actual_table_name, **kwargs)
        elif operation == "updateItem":
            return AWSServiceIntegrations.dynamodb_update_item(actual_table_name, **kwargs)
        else:
            raise ValueError(f"Unsupported DynamoDB operation: {operation}")
    
    def sns_publish(self, logical_topic_name: str, message: str, **kwargs) -> dict:
        """Create SNS publish with config-resolved topic ARN"""
        topic_arn = self.config.get(f"sns.topics.{logical_topic_name}")
        if not topic_arn:
            raise ValueError(f"SNS topic {logical_topic_name} not configured for environment {self.config.current_env}")
        
        return AWSServiceIntegrations.sns_publish(topic_arn, message, **kwargs)
    
    def sqs_send_message(self, logical_queue_name: str, message_body: str, **kwargs) -> dict:
        """Create SQS send message with config-resolved queue URL"""
        queue_url = self.config.get(f"sqs.queues.{logical_queue_name}")
        if not queue_url:
            raise ValueError(f"SQS queue {logical_queue_name} not configured for environment {self.config.current_env}")
        
        return AWSServiceIntegrations.sqs_send_message(queue_url, message_body, **kwargs)
    
    def batch_submit_job(self, logical_job_name: str, **kwargs) -> dict:
        """Create Batch job with config-resolved job definition and queue"""
        job_queue = self.config.get(f"batch.job_queues.{logical_job_name}")
        job_definition = self.config.get(f"batch.job_definitions.{logical_job_name}")
        
        if not job_queue or not job_definition:
            raise ValueError(f"Batch job {logical_job_name} not fully configured for environment {self.config.current_env}")
        
        return AWSServiceIntegrations.batch_submit_job(
            job_name=kwargs.pop("job_name", f"{logical_job_name}-${{aws:executionId}}"),
            job_queue=job_queue,
            job_definition=job_definition,
            **kwargs
        )