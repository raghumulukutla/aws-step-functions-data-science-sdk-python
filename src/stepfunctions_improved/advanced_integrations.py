# Copyright 2024 Improved Step Functions Framework

"""
Advanced AWS service integrations for Step Functions
"""

from typing import Optional, Dict, Any, List, Union
from dynaconf import Dynaconf


class AdvancedAWSIntegrations:
    """Advanced AWS service integrations beyond basic services"""
    
    @staticmethod
    def codebuild_start_build(project_name: str,
                             source_version: Optional[str] = None,
                             artifacts_override: Optional[dict] = None,
                             environment_variables_override: Optional[List[dict]] = None,
                             source_type_override: Optional[str] = None,
                             source_location_override: Optional[str] = None,
                             wait_for_completion: bool = True) -> dict:
        """Start AWS CodeBuild project"""
        
        resource = "arn:aws:states:::codebuild:startBuild"
        if wait_for_completion:
            resource += ".sync"
        
        parameters = {"ProjectName": project_name}
        
        if source_version:
            parameters["SourceVersion"] = source_version
        
        if artifacts_override:
            parameters["ArtifactsOverride"] = artifacts_override
        
        if environment_variables_override:
            parameters["EnvironmentVariablesOverride"] = environment_variables_override
        
        if source_type_override:
            parameters["SourceTypeOverride"] = source_type_override
        
        if source_location_override:
            parameters["SourceLocationOverride"] = source_location_override
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": parameters
        }
    
    @staticmethod
    def athena_start_query_execution(query_string: str,
                                   result_configuration: dict,
                                   query_execution_context: Optional[dict] = None,
                                   work_group: Optional[str] = None,
                                   wait_for_completion: bool = True) -> dict:
        """Execute Athena query"""
        
        resource = "arn:aws:states:::athena:startQueryExecution"
        if wait_for_completion:
            resource += ".sync"
        
        parameters = {
            "QueryString": query_string,
            "ResultConfiguration": result_configuration
        }
        
        if query_execution_context:
            parameters["QueryExecutionContext"] = query_execution_context
        
        if work_group:
            parameters["WorkGroup"] = work_group
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": parameters
        }
    
    @staticmethod
    def databrew_start_job_run(job_name: str,
                              wait_for_completion: bool = True) -> dict:
        """Start AWS Glue DataBrew job"""
        
        resource = "arn:aws:states:::databrew:startJobRun"
        if wait_for_completion:
            resource += ".sync"
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": {
                "Name": job_name
            }
        }
    
    @staticmethod
    def mediaconvert_create_job(job_template: Optional[str] = None,
                               queue: Optional[str] = None,
                               user_metadata: Optional[dict] = None,
                               role: Optional[str] = None,
                               settings: Optional[dict] = None,
                               wait_for_completion: bool = True) -> dict:
        """Create MediaConvert job"""
        
        resource = "arn:aws:states:::mediaconvert:createJob"
        if wait_for_completion:
            resource += ".sync"
        
        parameters = {}
        
        if job_template:
            parameters["JobTemplate"] = job_template
        
        if queue:
            parameters["Queue"] = queue
        
        if user_metadata:
            parameters["UserMetadata"] = user_metadata
        
        if role:
            parameters["Role"] = role
        
        if settings:
            parameters["Settings"] = settings
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": parameters
        }
    
    @staticmethod
    def textract_start_document_analysis(document_location: dict,
                                        feature_types: List[str],
                                        output_config: Optional[dict] = None,
                                        kms_key_id: Optional[str] = None,
                                        notification_channel: Optional[dict] = None,
                                        wait_for_completion: bool = True) -> dict:
        """Start Textract document analysis"""
        
        resource = "arn:aws:states:::textract:startDocumentAnalysis"
        if wait_for_completion:
            resource += ".sync"
        
        parameters = {
            "DocumentLocation": document_location,
            "FeatureTypes": feature_types
        }
        
        if output_config:
            parameters["OutputConfig"] = output_config
        
        if kms_key_id:
            parameters["KMSKeyId"] = kms_key_id
        
        if notification_channel:
            parameters["NotificationChannel"] = notification_channel
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": parameters
        }
    
    @staticmethod
    def comprehend_start_dominant_language_detection_job(input_data_config: dict,
                                                        output_data_config: dict,
                                                        data_access_role_arn: str,
                                                        job_name: Optional[str] = None,
                                                        client_request_token: Optional[str] = None,
                                                        wait_for_completion: bool = True) -> dict:
        """Start Comprehend dominant language detection job"""
        
        resource = "arn:aws:states:::comprehend:startDominantLanguageDetectionJob"
        if wait_for_completion:
            resource += ".sync"
        
        parameters = {
            "InputDataConfig": input_data_config,
            "OutputDataConfig": output_data_config,
            "DataAccessRoleArn": data_access_role_arn
        }
        
        if job_name:
            parameters["JobName"] = job_name
        
        if client_request_token:
            parameters["ClientRequestToken"] = client_request_token
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": parameters
        }
    
    @staticmethod
    def bedrock_invoke_model(model_id: str,
                           body: dict,
                           content_type: str = "application/json",
                           accept: str = "application/json") -> dict:
        """Invoke Amazon Bedrock model"""
        
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::bedrock:invokeModel",
            "Parameters": {
                "ModelId": model_id,
                "Body": body,
                "ContentType": content_type,
                "Accept": accept
            }
        }
    
    @staticmethod
    def apigateway_invoke(api_endpoint: str,
                         method: str,
                         headers: Optional[dict] = None,
                         query_parameters: Optional[dict] = None,
                         path_parameters: Optional[dict] = None,
                         request_body: Optional[dict] = None,
                         stage: Optional[str] = None) -> dict:
        """Invoke API Gateway endpoint"""
        
        parameters = {
            "ApiEndpoint": api_endpoint,
            "Method": method
        }
        
        if headers:
            parameters["Headers"] = headers
        
        if query_parameters:
            parameters["QueryParameters"] = query_parameters
        
        if path_parameters:
            parameters["PathParameters"] = path_parameters
        
        if request_body:
            parameters["RequestBody"] = request_body
        
        if stage:
            parameters["Stage"] = stage
        
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::apigateway:invoke",
            "Parameters": parameters
        }
    
    @staticmethod
    def eventbridge_put_events(entries: List[dict]) -> dict:
        """Put events to EventBridge"""
        
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::events:putEvents",
            "Parameters": {
                "Entries": entries
            }
        }
    
    @staticmethod
    def s3_copy_object(source_bucket: str,
                      source_key: str,
                      destination_bucket: str,
                      destination_key: str,
                      metadata_directive: str = "COPY") -> dict:
        """Copy S3 object"""
        
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::aws-sdk:s3:copyObject",
            "Parameters": {
                "Bucket": destination_bucket,
                "CopySource": f"{source_bucket}/{source_key}",
                "Key": destination_key,
                "MetadataDirective": metadata_directive
            }
        }
    
    @staticmethod
    def s3_list_objects(bucket: str,
                       prefix: Optional[str] = None,
                       max_keys: Optional[int] = None) -> dict:
        """List S3 objects"""
        
        parameters = {"Bucket": bucket}
        
        if prefix:
            parameters["Prefix"] = prefix
        
        if max_keys:
            parameters["MaxKeys"] = max_keys
        
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::aws-sdk:s3:listObjectsV2",
            "Parameters": parameters
        }
    
    @staticmethod
    def secrets_manager_get_secret_value(secret_id: str,
                                       version_id: Optional[str] = None,
                                       version_stage: Optional[str] = None) -> dict:
        """Get secret from AWS Secrets Manager"""
        
        parameters = {"SecretId": secret_id}
        
        if version_id:
            parameters["VersionId"] = version_id
        
        if version_stage:
            parameters["VersionStage"] = version_stage
        
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::aws-sdk:secretsmanager:getSecretValue",
            "Parameters": parameters
        }
    
    @staticmethod
    def ssm_get_parameter(name: str,
                         with_decryption: bool = False) -> dict:
        """Get parameter from AWS Systems Manager Parameter Store"""
        
        return {
            "Type": "Task",
            "Resource": "arn:aws:states:::aws-sdk:ssm:getParameter",
            "Parameters": {
                "Name": name,
                "WithDecryption": with_decryption
            }
        }
    
    @staticmethod
    def cloudformation_create_stack(stack_name: str,
                                  template_body: Optional[str] = None,
                                  template_url: Optional[str] = None,
                                  parameters: Optional[List[dict]] = None,
                                  capabilities: Optional[List[str]] = None,
                                  tags: Optional[List[dict]] = None,
                                  wait_for_completion: bool = True) -> dict:
        """Create CloudFormation stack"""
        
        resource = "arn:aws:states:::cloudformation:createStack"
        if wait_for_completion:
            resource += ".sync"
        
        params = {"StackName": stack_name}
        
        if template_body:
            params["TemplateBody"] = template_body
        elif template_url:
            params["TemplateURL"] = template_url
        else:
            raise ValueError("Either template_body or template_url must be provided")
        
        if parameters:
            params["Parameters"] = parameters
        
        if capabilities:
            params["Capabilities"] = capabilities
        
        if tags:
            params["Tags"] = tags
        
        return {
            "Type": "Task",
            "Resource": resource,
            "Parameters": params
        }


class ConfigurableAdvancedIntegrations:
    """Configuration-aware advanced AWS integrations"""
    
    def __init__(self, config: Dynaconf):
        self.config = config
    
    def codebuild_project(self, logical_project_name: str, **kwargs) -> dict:
        """Start CodeBuild project with config resolution"""
        
        actual_project_name = self.config.get(f"codebuild.projects.{logical_project_name}")
        if not actual_project_name:
            raise ValueError(f"CodeBuild project {logical_project_name} not configured")
        
        return AdvancedAWSIntegrations.codebuild_start_build(
            project_name=actual_project_name,
            **kwargs
        )
    
    def athena_query(self, query_string: str, logical_workgroup: Optional[str] = None, **kwargs) -> dict:
        """Execute Athena query with config defaults"""
        
        # Get result configuration from config
        result_configuration = kwargs.pop("result_configuration", None) or {
            "OutputLocation": self.config.get("athena.output_location", "s3://athena-results/")
        }
        
        workgroup = None
        if logical_workgroup:
            workgroup = self.config.get(f"athena.workgroups.{logical_workgroup}")
        
        return AdvancedAWSIntegrations.athena_start_query_execution(
            query_string=query_string,
            result_configuration=result_configuration,
            work_group=workgroup,
            **kwargs
        )
    
    def s3_operation(self, operation: str, logical_bucket_name: str, **kwargs) -> dict:
        """Perform S3 operation with config-resolved bucket name"""
        
        actual_bucket_name = self.config.get(f"s3.buckets.{logical_bucket_name}")
        if not actual_bucket_name:
            raise ValueError(f"S3 bucket {logical_bucket_name} not configured")
        
        if operation == "listObjects":
            return AdvancedAWSIntegrations.s3_list_objects(
                bucket=actual_bucket_name,
                **kwargs
            )
        elif operation == "copyObject":
            return AdvancedAWSIntegrations.s3_copy_object(
                destination_bucket=actual_bucket_name,
                **kwargs
            )
        else:
            raise ValueError(f"Unsupported S3 operation: {operation}")
    
    def secrets_manager_secret(self, logical_secret_name: str, **kwargs) -> dict:
        """Get secret with config resolution"""
        
        actual_secret_id = self.config.get(f"secrets.{logical_secret_name}")
        if not actual_secret_id:
            raise ValueError(f"Secret {logical_secret_name} not configured")
        
        return AdvancedAWSIntegrations.secrets_manager_get_secret_value(
            secret_id=actual_secret_id,
            **kwargs
        )
    
    def bedrock_model_invocation(self, logical_model_name: str, body: dict, **kwargs) -> dict:
        """Invoke Bedrock model with config resolution"""
        
        model_id = self.config.get(f"bedrock.models.{logical_model_name}")
        if not model_id:
            raise ValueError(f"Bedrock model {logical_model_name} not configured")
        
        return AdvancedAWSIntegrations.bedrock_invoke_model(
            model_id=model_id,
            body=body,
            **kwargs
        )


class MLOpsIntegrations:
    """Specialized integrations for MLOps workflows"""
    
    @staticmethod
    def create_model_registry_pipeline(model_package_group_name: str,
                                     approval_status: str = "PendingManualApproval") -> List[dict]:
        """Create model registry workflow steps"""
        
        steps = []
        
        # Create model package
        create_model_package = {
            "Type": "Task",
            "Resource": "arn:aws:states:::sagemaker:createModelPackage",
            "Parameters": {
                "ModelPackageGroupName": model_package_group_name,
                "ModelApprovalStatus": approval_status,
                "InferenceSpecification": {
                    "Containers": [{
                        "Image.$": "$.model_image",
                        "ModelDataUrl.$": "$.model_artifacts_url"
                    }],
                    "SupportedContentTypes": ["text/csv"],
                    "SupportedResponseMIMETypes": ["text/csv"]
                }
            }
        }
        steps.append(("CreateModelPackage", create_model_package))
        
        return steps
    
    @staticmethod
    def create_feature_store_pipeline(feature_group_name: str,
                                    record_identifier_feature_name: str,
                                    event_time_feature_name: str,
                                    feature_definitions: List[dict]) -> List[dict]:
        """Create feature store workflow steps"""
        
        steps = []
        
        # Create feature group
        create_feature_group = {
            "Type": "Task",
            "Resource": "arn:aws:states:::sagemaker:createFeatureGroup",
            "Parameters": {
                "FeatureGroupName": feature_group_name,
                "RecordIdentifierFeatureName": record_identifier_feature_name,
                "EventTimeFeatureName": event_time_feature_name,
                "FeatureDefinitions": feature_definitions,
                "OnlineStoreConfig": {
                    "EnableOnlineStore": True
                },
                "OfflineStoreConfig": {
                    "S3StorageConfig": {
                        "S3Uri.$": "$.feature_store_s3_uri"
                    }
                }
            }
        }
        steps.append(("CreateFeatureGroup", create_feature_group))
        
        # Ingest features
        ingest_features = {
            "Type": "Task",
            "Resource": "arn:aws:states:::sagemaker:putRecord",
            "Parameters": {
                "FeatureGroupName": feature_group_name,
                "Record.$": "$.feature_record"
            }
        }
        steps.append(("IngestFeatures", ingest_features))
        
        return steps
    
    @staticmethod
    def create_data_quality_pipeline(baseline_job_name: str,
                                   monitoring_schedule_name: str) -> List[dict]:
        """Create data quality monitoring pipeline"""
        
        steps = []
        
        # Create baseline job
        create_baseline = {
            "Type": "Task",
            "Resource": "arn:aws:states:::sagemaker:createDataQualityJobDefinition",
            "Parameters": {
                "JobDefinitionName": baseline_job_name,
                "DataQualityAppSpecification": {
                    "ImageUri": "159807026194.dkr.ecr.us-east-1.amazonaws.com/sagemaker-model-monitor-analyzer"
                },
                "DataQualityJobInput": {
                    "EndpointInput": {
                        "EndpointName.$": "$.endpoint_name",
                        "LocalPath": "/opt/ml/processing/input/endpoint"
                    }
                },
                "DataQualityJobOutputConfig": {
                    "MonitoringOutputs": [{
                        "S3Output": {
                            "S3Uri.$": "$.monitoring_output_s3_uri",
                            "LocalPath": "/opt/ml/processing/output"
                        }
                    }]
                }
            }
        }
        steps.append(("CreateDataQualityBaseline", create_baseline))
        
        # Create monitoring schedule
        create_schedule = {
            "Type": "Task",
            "Resource": "arn:aws:states:::sagemaker:createMonitoringSchedule",
            "Parameters": {
                "MonitoringScheduleName": monitoring_schedule_name,
                "MonitoringScheduleConfig": {
                    "ScheduleConfig": {
                        "ScheduleExpression": "cron(0 * * * ? *)"  # Hourly
                    },
                    "MonitoringJobDefinitionName": baseline_job_name
                }
            }
        }
        steps.append(("CreateMonitoringSchedule", create_schedule))
        
        return steps