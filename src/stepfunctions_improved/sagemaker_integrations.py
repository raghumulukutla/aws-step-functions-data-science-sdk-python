# Copyright 2024 Improved Step Functions Framework

"""
Comprehensive SageMaker integrations for Step Functions
"""

from typing import Optional, Dict, Any, List, Union
from dynaconf import Dynaconf
from .aws_services import AWSServiceIntegrations


class SageMakerIntegrations:
    """Comprehensive SageMaker service integrations"""
    
    @staticmethod
    def training_job(job_name: str,
                    algorithm_specification: dict,
                    input_data_config: list,
                    output_data_config: dict,
                    resource_config: dict,
                    role_arn: str,
                    hyperparameters: Optional[dict] = None,
                    stopping_condition: Optional[dict] = None,
                    vpc_config: Optional[dict] = None,
                    tags: Optional[List[dict]] = None,
                    enable_network_isolation: bool = False,
                    enable_inter_container_traffic_encryption: bool = False,
                    enable_managed_spot_training: bool = False,
                    checkpoint_config: Optional[dict] = None,
                    debug_hook_config: Optional[dict] = None,
                    profiler_config: Optional[dict] = None,
                    experiment_config: Optional[dict] = None,
                    wait_for_completion: bool = True) -> dict:
        """Create comprehensive SageMaker training job"""
        
        resource = "arn:aws:states:::sagemaker:createTrainingJob"
        if wait_for_completion:
            resource += ".sync"
        
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
            parameters["StoppingCondition"] = {"MaxRuntimeInSeconds": 86400}
        
        if vpc_config:
            parameters["VpcConfig"] = vpc_config
        
        if tags:
            parameters["Tags"] = tags
        
        if enable_network_isolation:
            parameters["EnableNetworkIsolation"] = True
        
        if enable_inter_container_traffic_encryption:
            parameters["EnableInterContainerTrafficEncryption"] = True
        
        if enable_managed_spot_training:
            parameters["EnableManagedSpotTraining"] = True
        
        if checkpoint_config:
            parameters["CheckpointConfig"] = checkpoint_config
        
        if debug_hook_config:
            parameters["DebugHookConfig"] = debug_hook_config
        
        if profiler_config:
            parameters["ProfilerConfig"] = profiler_config
        
        if experiment_config:
            parameters["ExperimentConfig"] = experiment_config
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": parameters
        }
    
    @staticmethod
    def hyperparameter_tuning_job(tuning_job_name: str,
                                 hyperparameter_tuning_job_config: dict,
                                 training_job_definition: dict,
                                 role_arn: str,
                                 tags: Optional[List[dict]] = None,
                                 warm_start_config: Optional[dict] = None,
                                 wait_for_completion: bool = True) -> dict:
        """Create SageMaker hyperparameter tuning job"""
        
        resource = "arn:aws:states:::sagemaker:createHyperParameterTuningJob"
        if wait_for_completion:
            resource += ".sync"
        
        parameters = {
            "HyperParameterTuningJobName": tuning_job_name,
            "HyperParameterTuningJobConfig": hyperparameter_tuning_job_config,
            "TrainingJobDefinition": training_job_definition,
            "RoleArn": role_arn
        }
        
        if tags:
            parameters["Tags"] = tags
        
        if warm_start_config:
            parameters["WarmStartConfig"] = warm_start_config
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": parameters
        }
    
    @staticmethod
    def transform_job(transform_job_name: str,
                     model_name: str,
                     transform_input: dict,
                     transform_output: dict,
                     transform_resources: dict,
                     data_capture_config: Optional[dict] = None,
                     transform_job_definition: Optional[dict] = None,
                     tags: Optional[List[dict]] = None,
                     wait_for_completion: bool = True) -> dict:
        """Create SageMaker transform (batch inference) job"""
        
        resource = "arn:aws:states:::sagemaker:createTransformJob"
        if wait_for_completion:
            resource += ".sync"
        
        parameters = {
            "TransformJobName": transform_job_name,
            "ModelName": model_name,
            "TransformInput": transform_input,
            "TransformOutput": transform_output,
            "TransformResources": transform_resources
        }
        
        if data_capture_config:
            parameters["DataCaptureConfig"] = data_capture_config
        
        if transform_job_definition:
            parameters.update(transform_job_definition)
        
        if tags:
            parameters["Tags"] = tags
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": parameters
        }
    
    @staticmethod
    def create_model(model_name: str,
                    execution_role_arn: str,
                    primary_container: Optional[dict] = None,
                    containers: Optional[List[dict]] = None,
                    inference_execution_config: Optional[dict] = None,
                    vpc_config: Optional[dict] = None,
                    tags: Optional[List[dict]] = None,
                    enable_network_isolation: bool = False) -> dict:
        """Create SageMaker model"""
        
        parameters = {
            "ModelName": model_name,
            "ExecutionRoleArn": execution_role_arn
        }
        
        if primary_container:
            parameters["PrimaryContainer"] = primary_container
        elif containers:
            parameters["Containers"] = containers
        else:
            raise ValueError("Either primary_container or containers must be provided")
        
        if inference_execution_config:
            parameters["InferenceExecutionConfig"] = inference_execution_config
        
        if vpc_config:
            parameters["VpcConfig"] = vpc_config
        
        if tags:
            parameters["Tags"] = tags
        
        if enable_network_isolation:
            parameters["EnableNetworkIsolation"] = True
        
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::sagemaker:createModel",
            "Parameters": parameters
        }
    
    @staticmethod
    def create_endpoint_config(endpoint_config_name: str,
                              production_variants: List[dict],
                              data_capture_config: Optional[dict] = None,
                              kms_key_id: Optional[str] = None,
                              tags: Optional[List[dict]] = None,
                              async_inference_config: Optional[dict] = None,
                              explainer_config: Optional[dict] = None) -> dict:
        """Create SageMaker endpoint configuration"""
        
        parameters = {
            "EndpointConfigName": endpoint_config_name,
            "ProductionVariants": production_variants
        }
        
        if data_capture_config:
            parameters["DataCaptureConfig"] = data_capture_config
        
        if kms_key_id:
            parameters["KmsKeyId"] = kms_key_id
        
        if tags:
            parameters["Tags"] = tags
        
        if async_inference_config:
            parameters["AsyncInferenceConfig"] = async_inference_config
        
        if explainer_config:
            parameters["ExplainerConfig"] = explainer_config
        
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::sagemaker:createEndpointConfig",
            "Parameters": parameters
        }
    
    @staticmethod
    def create_endpoint(endpoint_name: str,
                       endpoint_config_name: str,
                       tags: Optional[List[dict]] = None,
                       wait_for_completion: bool = True) -> dict:
        """Create SageMaker endpoint"""
        
        resource = "arn:aws:states:::sagemaker:createEndpoint"
        if wait_for_completion:
            resource += ".sync"
        
        parameters = {
            "EndpointName": endpoint_name,
            "EndpointConfigName": endpoint_config_name
        }
        
        if tags:
            parameters["Tags"] = tags
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": parameters
        }
    
    @staticmethod
    def update_endpoint(endpoint_name: str,
                       endpoint_config_name: str,
                       retain_all_variant_properties: bool = False,
                       exclude_retained_variant_properties: Optional[List[str]] = None,
                       wait_for_completion: bool = True) -> dict:
        """Update SageMaker endpoint"""
        
        resource = "arn:aws:states:::sagemaker:updateEndpoint"
        if wait_for_completion:
            resource += ".sync"
        
        parameters = {
            "EndpointName": endpoint_name,
            "EndpointConfigName": endpoint_config_name
        }
        
        if retain_all_variant_properties:
            parameters["RetainAllVariantProperties"] = True
        
        if exclude_retained_variant_properties:
            parameters["ExcludeRetainedVariantProperties"] = exclude_retained_variant_properties
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": parameters
        }
    
    @staticmethod
    def delete_endpoint(endpoint_name: str) -> dict:
        """Delete SageMaker endpoint"""
        
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::sagemaker:deleteEndpoint",
            "Parameters": {
                "EndpointName": endpoint_name
            }
        }
    
    @staticmethod
    def processing_job(processing_job_name: str,
                      app_specification: dict,
                      role_arn: str,
                      processing_inputs: Optional[List[dict]] = None,
                      processing_output_config: Optional[dict] = None,
                      processing_resources: Optional[dict] = None,
                      stopping_condition: Optional[dict] = None,
                      environment: Optional[dict] = None,
                      network_config: Optional[dict] = None,
                      tags: Optional[List[dict]] = None,
                      experiment_config: Optional[dict] = None,
                      wait_for_completion: bool = True) -> dict:
        """Create SageMaker processing job"""
        
        resource = "arn:aws:states:::sagemaker:createProcessingJob"
        if wait_for_completion:
            resource += ".sync"
        
        parameters = {
            "ProcessingJobName": processing_job_name,
            "AppSpecification": app_specification,
            "RoleArn": role_arn
        }
        
        if processing_inputs:
            parameters["ProcessingInputs"] = processing_inputs
        
        if processing_output_config:
            parameters["ProcessingOutputConfig"] = processing_output_config
        
        if processing_resources:
            parameters["ProcessingResources"] = processing_resources
        else:
            parameters["ProcessingResources"] = {
                "ClusterConfig": {
                    "InstanceCount": 1,
                    "InstanceType": "ml.m5.large",
                    "VolumeSizeInGB": 30
                }
            }
        
        if stopping_condition:
            parameters["StoppingCondition"] = stopping_condition
        
        if environment:
            parameters["Environment"] = environment
        
        if network_config:
            parameters["NetworkConfig"] = network_config
        
        if tags:
            parameters["Tags"] = tags
        
        if experiment_config:
            parameters["ExperimentConfig"] = experiment_config
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": parameters
        }
    
    @staticmethod
    def auto_ml_job(auto_ml_job_name: str,
                   input_data_config: List[dict],
                   output_data_config: dict,
                   problem_type: str,
                   role_arn: str,
                   auto_ml_job_objective: Optional[dict] = None,
                   auto_ml_job_config: Optional[dict] = None,
                   generate_candidate_definitions_only: bool = False,
                   tags: Optional[List[dict]] = None,
                   model_deploy_config: Optional[dict] = None,
                   wait_for_completion: bool = True) -> dict:
        """Create SageMaker AutoML job"""
        
        resource = "arn:aws:states:::sagemaker:createAutoMLJob"
        if wait_for_completion:
            resource += ".sync"
        
        parameters = {
            "AutoMLJobName": auto_ml_job_name,
            "InputDataConfig": input_data_config,
            "OutputDataConfig": output_data_config,
            "ProblemType": problem_type,
            "RoleArn": role_arn
        }
        
        if auto_ml_job_objective:
            parameters["AutoMLJobObjective"] = auto_ml_job_objective
        
        if auto_ml_job_config:
            parameters["AutoMLJobConfig"] = auto_ml_job_config
        
        if generate_candidate_definitions_only:
            parameters["GenerateCandidateDefinitionsOnly"] = True
        
        if tags:
            parameters["Tags"] = tags
        
        if model_deploy_config:
            parameters["ModelDeployConfig"] = model_deploy_config
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": parameters
        }
    
    @staticmethod
    def labeling_job(labeling_job_name: str,
                    label_attribute_name: str,
                    input_config: dict,
                    output_config: dict,
                    role_arn: str,
                    human_task_config: dict,
                    label_category_config_s3_uri: Optional[str] = None,
                    stopping_conditions: Optional[dict] = None,
                    labeling_job_algorithms_config: Optional[dict] = None,
                    tags: Optional[List[dict]] = None,
                    wait_for_completion: bool = True) -> dict:
        """Create SageMaker labeling job"""
        
        resource = "arn:aws:states:::sagemaker:createLabelingJob"
        if wait_for_completion:
            resource += ".sync"
        
        parameters = {
            "LabelingJobName": labeling_job_name,
            "LabelAttributeName": label_attribute_name,
            "InputConfig": input_config,
            "OutputConfig": output_config,
            "RoleArn": role_arn,
            "HumanTaskConfig": human_task_config
        }
        
        if label_category_config_s3_uri:
            parameters["LabelCategoryConfigS3Uri"] = label_category_config_s3_uri
        
        if stopping_conditions:
            parameters["StoppingConditions"] = stopping_conditions
        
        if labeling_job_algorithms_config:
            parameters["LabelingJobAlgorithmsConfig"] = labeling_job_algorithms_config
        
        if tags:
            parameters["Tags"] = tags
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": parameters
        }


class ConfigurableSageMakerIntegrations:
    """Configuration-aware SageMaker integrations"""
    
    def __init__(self, config: Dynaconf):
        self.config = config
    
    def training_job(self, job_config: dict, **kwargs) -> dict:
        """Create training job with configuration defaults"""
        
        # Merge with configuration defaults
        resource_config = {
            "InstanceType": self.config.get("sagemaker.training.instance_type", "ml.m5.large"),
            "InstanceCount": self.config.get("sagemaker.training.instance_count", 1),
            "VolumeSizeInGB": self.config.get("sagemaker.training.volume_size", 30),
            **job_config.get("resource_config", {})
        }
        
        role_arn = job_config.get("role_arn") or self.config.get("sagemaker.role_arn")
        if not role_arn:
            raise ValueError("SageMaker role ARN not configured")
        
        # Default stopping condition
        stopping_condition = job_config.get("stopping_condition") or {
            "MaxRuntimeInSeconds": self.config.get("sagemaker.training.max_runtime", 86400)
        }
        
        # Default VPC config if specified
        vpc_config = job_config.get("vpc_config")
        if not vpc_config and self.config.get("sagemaker.vpc_config"):
            vpc_config = self.config.get("sagemaker.vpc_config")
        
        return SageMakerIntegrations.training_job(
            job_name=job_config["job_name"],
            algorithm_specification=job_config["algorithm_specification"],
            input_data_config=job_config["input_data_config"],
            output_data_config=job_config["output_data_config"],
            resource_config=resource_config,
            role_arn=role_arn,
            stopping_condition=stopping_condition,
            vpc_config=vpc_config,
            **kwargs
        )
    
    def processing_job(self, job_config: dict, **kwargs) -> dict:
        """Create processing job with configuration defaults"""
        
        # Default processing resources
        processing_resources = job_config.get("processing_resources") or {
            "ClusterConfig": {
                "InstanceCount": self.config.get("sagemaker.processing.instance_count", 1),
                "InstanceType": self.config.get("sagemaker.processing.instance_type", "ml.m5.large"),
                "VolumeSizeInGB": self.config.get("sagemaker.processing.volume_size", 30)
            }
        }
        
        role_arn = job_config.get("role_arn") or self.config.get("sagemaker.role_arn")
        if not role_arn:
            raise ValueError("SageMaker role ARN not configured")
        
        return SageMakerIntegrations.processing_job(
            processing_job_name=job_config["job_name"],
            app_specification=job_config["app_specification"],
            role_arn=role_arn,
            processing_resources=processing_resources,
            **kwargs
        )
    
    def endpoint_deployment(self, deployment_config: dict) -> List[dict]:
        """Create complete endpoint deployment pipeline"""
        
        model_name = deployment_config["model_name"]
        endpoint_config_name = deployment_config["endpoint_config_name"]
        endpoint_name = deployment_config["endpoint_name"]
        
        # Get default instance type from config
        instance_type = deployment_config.get("instance_type") or \
                       self.config.get("sagemaker.inference.instance_type", "ml.m5.large")
        
        initial_instance_count = deployment_config.get("initial_instance_count") or \
                               self.config.get("sagemaker.inference.initial_instance_count", 1)
        
        role_arn = deployment_config.get("role_arn") or self.config.get("sagemaker.role_arn")
        
        steps = []
        
        # Step 1: Create model
        if deployment_config.get("create_model", True):
            model_step = SageMakerIntegrations.create_model(
                model_name=model_name,
                execution_role_arn=role_arn,
                primary_container=deployment_config["primary_container"]
            )
            steps.append(("CreateModel", model_step))
        
        # Step 2: Create endpoint config
        production_variants = deployment_config.get("production_variants") or [{
            "VariantName": "primary",
            "ModelName": model_name,
            "InitialInstanceCount": initial_instance_count,
            "InstanceType": instance_type
        }]
        
        endpoint_config_step = SageMakerIntegrations.create_endpoint_config(
            endpoint_config_name=endpoint_config_name,
            production_variants=production_variants,
            data_capture_config=deployment_config.get("data_capture_config")
        )
        steps.append(("CreateEndpointConfig", endpoint_config_step))
        
        # Step 3: Create endpoint
        endpoint_step = SageMakerIntegrations.create_endpoint(
            endpoint_name=endpoint_name,
            endpoint_config_name=endpoint_config_name
        )
        steps.append(("CreateEndpoint", endpoint_step))
        
        return steps
    
    def ml_pipeline_with_hyperparameter_tuning(self, pipeline_config: dict) -> List[dict]:
        """Create complete ML pipeline with hyperparameter tuning"""
        
        steps = []
        
        # Step 1: Data preprocessing (if specified)
        if pipeline_config.get("preprocessing_job"):
            preprocessing_step = self.processing_job(pipeline_config["preprocessing_job"])
            steps.append(("PreprocessData", preprocessing_step))
        
        # Step 2: Hyperparameter tuning
        tuning_step = SageMakerIntegrations.hyperparameter_tuning_job(
            tuning_job_name=pipeline_config["tuning_job_name"],
            hyperparameter_tuning_job_config=pipeline_config["tuning_config"],
            training_job_definition=pipeline_config["training_job_definition"],
            role_arn=self.config.get("sagemaker.role_arn")
        )
        steps.append(("HyperparameterTuning", tuning_step))
        
        # Step 3: Model evaluation (processing job)
        if pipeline_config.get("evaluation_job"):
            evaluation_step = self.processing_job(pipeline_config["evaluation_job"])
            steps.append(("EvaluateModel", evaluation_step))
        
        # Step 4: Conditional deployment based on metrics
        if pipeline_config.get("deployment_config"):
            deployment_steps = self.endpoint_deployment(pipeline_config["deployment_config"])
            steps.extend(deployment_steps)
        
        return steps