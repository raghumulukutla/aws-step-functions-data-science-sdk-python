# Copyright 2024 Improved Step Functions Framework

"""
Error handling configurations for Step Functions states
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    error_equals: List[str]
    interval_seconds: int = 1
    max_attempts: int = 3
    backoff_rate: float = 2.0
    
    def to_dict(self) -> dict:
        return {
            "ErrorEquals": self.error_equals,
            "IntervalSeconds": self.interval_seconds,
            "MaxAttempts": self.max_attempts,
            "BackoffRate": self.backoff_rate
        }


@dataclass 
class CatchConfig:
    """Configuration for catch behavior"""
    error_equals: List[str]
    next: str
    result_path: Optional[str] = None
    
    def to_dict(self) -> dict:
        result = {
            "ErrorEquals": self.error_equals,
            "Next": self.next
        }
        if self.result_path:
            result["ResultPath"] = self.result_path
        return result


class ErrorHandling:
    """Predefined error handling configurations for common AWS services"""
    
    # Common retry patterns
    LAMBDA_RETRY = RetryConfig(
        error_equals=[
            "Lambda.ServiceException", 
            "Lambda.AWSLambdaException", 
            "Lambda.SdkClientException",
            "Lambda.TooManyRequestsException"
        ],
        interval_seconds=2,
        max_attempts=3,
        backoff_rate=2.0
    )
    
    SAGEMAKER_RETRY = RetryConfig(
        error_equals=[
            "SageMaker.AmazonSageMakerException",
            "SageMaker.ResourceLimitExceededException"
        ],
        interval_seconds=5,
        max_attempts=2,
        backoff_rate=3.0
    )
    
    BATCH_RETRY = RetryConfig(
        error_equals=[
            "Batch.AWSBatchException"
        ],
        interval_seconds=10,
        max_attempts=2,
        backoff_rate=2.0
    )
    
    DYNAMODB_RETRY = RetryConfig(
        error_equals=[
            "DynamoDB.AmazonDynamoDBException",
            "DynamoDB.ProvisionedThroughputExceededException",
            "DynamoDB.ThrottlingException"
        ],
        interval_seconds=1,
        max_attempts=5,
        backoff_rate=2.0
    )
    
    SNS_RETRY = RetryConfig(
        error_equals=[
            "SNS.AmazonSNSException",
            "SNS.ThrottledException"
        ],
        interval_seconds=1,
        max_attempts=3,
        backoff_rate=2.0
    )
    
    # Generic retry for all task failures
    GENERIC_TASK_RETRY = RetryConfig(
        error_equals=["States.TaskFailed"],
        interval_seconds=2,
        max_attempts=3,
        backoff_rate=2.0
    )
    
    # Generic retry for timeouts
    TIMEOUT_RETRY = RetryConfig(
        error_equals=["States.Timeout"],
        interval_seconds=5,
        max_attempts=2,
        backoff_rate=3.0
    )
    
    @staticmethod
    def catch_all_to_failure(failure_state: str = "WorkflowFailed", 
                           result_path: str = "$.error") -> CatchConfig:
        """Catch all errors and route to failure state"""
        return CatchConfig(
            error_equals=["States.ALL"],
            next=failure_state,
            result_path=result_path
        )
    
    @staticmethod
    def catch_timeout_to_retry(retry_state: str = "RetryTask",
                              result_path: str = "$.timeout_error") -> CatchConfig:
        """Catch timeout errors and route to retry logic"""
        return CatchConfig(
            error_equals=["States.Timeout"],
            next=retry_state,
            result_path=result_path
        )
    
    @staticmethod
    def catch_task_failed_to_cleanup(cleanup_state: str = "Cleanup",
                                   result_path: str = "$.task_error") -> CatchConfig:
        """Catch task failures and route to cleanup"""
        return CatchConfig(
            error_equals=["States.TaskFailed"],
            next=cleanup_state,
            result_path=result_path
        )
    
    @staticmethod
    def get_service_retry(service_name: str) -> Optional[RetryConfig]:
        """Get predefined retry configuration for AWS service"""
        service_retries = {
            "lambda": ErrorHandling.LAMBDA_RETRY,
            "sagemaker": ErrorHandling.SAGEMAKER_RETRY,
            "batch": ErrorHandling.BATCH_RETRY,
            "dynamodb": ErrorHandling.DYNAMODB_RETRY,
            "sns": ErrorHandling.SNS_RETRY
        }
        return service_retries.get(service_name.lower())