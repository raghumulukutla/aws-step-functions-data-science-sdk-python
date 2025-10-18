#!/usr/bin/env python3
"""
Example: Data Processing Pipeline using Improved Step Functions Framework
"""

import json
from stepfunctions_improved import (
    ConfigurableWorkflow, PipelineFactory, setup_config,
    StepFunctionBuilder, ConfigurableStepFunctionBuilder,
    NumericGreaterThan, StringEquals, BooleanEquals
)


def create_etl_pipeline(config):
    """Create a comprehensive ETL pipeline"""
    builder = ConfigurableStepFunctionBuilder("ETLPipeline", config)
    
    # Start pipeline
    builder.start_with("InitializeETL")
    builder.add_pass("InitializeETL",
                    result={"pipeline_id": "${aws:executionId}", "status": "started"},
                    comment="Initialize ETL pipeline execution")
    
    # Data ingestion from multiple sources
    ingestion_branch1 = ConfigurableStepFunctionBuilder("IngestDatabase", config)
    ingestion_branch1.start_with("ExtractFromDB")
    ingestion_branch1.add_lambda_task("ExtractFromDB", "extract_database_data")
    ingestion_branch1.add_lambda_task("ValidateDBData", "validate_data")
    ingestion_branch1.end_with_success()
    
    ingestion_branch2 = ConfigurableStepFunctionBuilder("IngestAPI", config)
    ingestion_branch2.start_with("ExtractFromAPI")
    ingestion_branch2.add_lambda_task("ExtractFromAPI", "extract_api_data")
    ingestion_branch2.add_lambda_task("ValidateAPIData", "validate_data")
    ingestion_branch2.end_with_success()
    
    ingestion_branch3 = ConfigurableStepFunctionBuilder("IngestFiles", config)
    ingestion_branch3.start_with("ExtractFromS3")
    ingestion_branch3.add_lambda_task("ExtractFromS3", "extract_s3_data")
    ingestion_branch3.add_lambda_task("ValidateFileData", "validate_data")
    ingestion_branch3.end_with_success()
    
    builder.add_parallel("IngestData", [ingestion_branch1, ingestion_branch2, ingestion_branch3],
                        comment="Ingest data from multiple sources in parallel")
    
    # Data quality checks
    builder.add_lambda_task("DataQualityCheck", "check_data_quality",
                          comment="Perform comprehensive data quality checks")
    
    # Conditional processing based on data quality
    choice_builder = builder.add_choice("QualityGate",
                                      comment="Route based on data quality score")
    
    choice_builder.when(
        NumericGreaterThan("$.quality_score", 0.9),
        "ProcessHighQualityData"
    ).when(
        NumericGreaterThan("$.quality_score", 0.7),
        "ProcessMediumQualityData"
    ).otherwise("HandlePoorQualityData")
    
    # High quality data processing
    builder.add_lambda_task("ProcessHighQualityData", "process_high_quality",
                          comment="Fast processing for high quality data")
    
    # Medium quality data processing (with additional cleaning)
    builder.add_lambda_task("ProcessMediumQualityData", "process_medium_quality",
                          comment="Enhanced processing for medium quality data")
    builder.add_lambda_task("AdditionalCleaning", "clean_data",
                          comment="Additional data cleaning steps")
    
    # Poor quality data handling
    builder.add_lambda_task("HandlePoorQualityData", "handle_poor_quality",
                          comment="Special handling for poor quality data")
    builder.add_sns_task("NotifyDataIssues", "alerts",
                       message="Data quality issues detected - manual review required",
                       subject="Data Quality Alert")
    
    # Data transformation
    transform_branch1 = ConfigurableStepFunctionBuilder("TransformCustomers", config)
    transform_branch1.start_with("TransformCustomerData")
    transform_branch1.add_lambda_task("TransformCustomerData", "transform_customers")
    transform_branch1.end_with_success()
    
    transform_branch2 = ConfigurableStepFunctionBuilder("TransformOrders", config)
    transform_branch2.start_with("TransformOrderData")
    transform_branch2.add_lambda_task("TransformOrderData", "transform_orders")
    transform_branch2.end_with_success()
    
    builder.add_parallel("TransformData", [transform_branch1, transform_branch2],
                        comment="Transform different data entities in parallel")
    
    # Data aggregation
    builder.add_lambda_task("AggregateData", "aggregate_transformed_data",
                          comment="Aggregate transformed data for analytics")
    
    # Load to data warehouse
    builder.add_lambda_task("LoadToWarehouse", "load_data_warehouse",
                          comment="Load processed data to data warehouse")
    
    # Update metadata
    builder.add_dynamodb_task("UpdateMetadata", "putItem", "etl_metadata",
                            item={
                                "pipeline_id.$": "$.pipeline_id",
                                "execution_time.$": "$$.State.EnteredTime",
                                "records_processed.$": "$.records_count",
                                "quality_score.$": "$.quality_score"
                            },
                            comment="Update ETL execution metadata")
    
    # Send completion notification
    builder.add_sns_task("NotifyCompletion", "alerts",
                       message="ETL pipeline completed successfully",
                       subject="ETL Pipeline Completion")
    
    builder.end_with_success("Success")
    
    return builder.build()


def create_streaming_pipeline(config):
    """Create a real-time streaming data pipeline"""
    builder = ConfigurableStepFunctionBuilder("StreamingPipeline", config)
    
    builder.start_with("ProcessStreamBatch")
    builder.add_lambda_task("ProcessStreamBatch", "process_stream_batch",
                          comment="Process batch of streaming data")
    
    # Real-time analytics
    builder.add_lambda_task("RealTimeAnalytics", "calculate_metrics",
                          comment="Calculate real-time metrics")
    
    # Anomaly detection
    builder.add_lambda_task("AnomalyDetection", "detect_anomalies",
                          comment="Detect anomalies in streaming data")
    
    # Alert on anomalies
    choice_builder = builder.add_choice("CheckAnomalies",
                                      comment="Check if anomalies were detected")
    
    choice_builder.when(
        BooleanEquals("$.anomalies_detected", True),
        "SendAnomalyAlert"
    ).otherwise("StoreResults")
    
    builder.add_sns_task("SendAnomalyAlert", "alerts",
                       message="Anomalies detected in streaming data",
                       subject="Real-time Anomaly Alert")
    
    # Store results in real-time database
    builder.add_dynamodb_task("StoreResults", "putItem", "streaming_metrics",
                            item={
                                "timestamp.$": "$$.State.EnteredTime",
                                "metrics.$": "$.calculated_metrics",
                                "anomaly_score.$": "$.anomaly_score"
                            })
    
    builder.end_with_success("Success")
    
    return builder.build()


def create_batch_processing_pipeline(config):
    """Create a large-scale batch processing pipeline using AWS Batch"""
    builder = ConfigurableStepFunctionBuilder("BatchProcessingPipeline", config)
    
    builder.start_with("PrepareJob")
    builder.add_lambda_task("PrepareJob", "prepare_batch_job",
                          comment="Prepare batch job parameters")
    
    # Submit batch job for large-scale processing
    from stepfunctions_improved.aws_services import AWSServiceIntegrations
    
    batch_job = AWSServiceIntegrations.batch_submit_job(
        job_name="large-scale-processing-${aws:executionId}",
        job_queue=config.get("batch.job_queues.processing", "default-queue"),
        job_definition=config.get("batch.job_definitions.processing", "default-job-def"),
        parameters={"inputPath.$": "$.input_path", "outputPath.$": "$.output_path"},
        wait_for_completion=True
    )
    
    builder.add_custom_task("SubmitBatchJob", batch_job,
                          comment="Submit large-scale batch processing job")
    
    # Post-process results
    builder.add_lambda_task("PostProcessResults", "post_process_batch_results",
                          comment="Post-process batch job results")
    
    # Validate output
    builder.add_lambda_task("ValidateOutput", "validate_batch_output",
                          comment="Validate batch processing output")
    
    # Conditional cleanup based on validation
    choice_builder = builder.add_choice("ValidationCheck",
                                      comment="Check validation results")
    
    choice_builder.when(
        BooleanEquals("$.validation_passed", True),
        "CleanupSuccess"
    ).otherwise("CleanupFailure")
    
    builder.add_lambda_task("CleanupSuccess", "cleanup_successful_job",
                          comment="Cleanup after successful processing")
    
    builder.add_lambda_task("CleanupFailure", "cleanup_failed_job",
                          comment="Cleanup after failed processing")
    builder.add_sns_task("NotifyFailure", "alerts",
                       message="Batch processing failed validation",
                       subject="Batch Processing Failure")
    
    builder.end_with_success("Success")
    
    return builder.build()


def main():
    """Main example execution"""
    
    # Setup configuration
    config = setup_config()
    
    # Create workflows
    etl_workflow = ConfigurableWorkflow("ETLPipeline", create_etl_pipeline)
    streaming_workflow = ConfigurableWorkflow("StreamingPipeline", create_streaming_pipeline)
    batch_workflow = ConfigurableWorkflow("BatchPipeline", create_batch_processing_pipeline)
    
    # Use factory for standard data processing pipeline
    factory = PipelineFactory(config)
    standard_pipeline = factory.create_data_processing_pipeline("StandardDataPipeline")
    
    # Switch to development environment
    config.setenv("development")
    
    print("=== ETL Pipeline (Development) ===")
    etl_definition = etl_workflow.create_for_environment(config)
    print(json.dumps(etl_definition, indent=2))
    
    print("\n=== Streaming Pipeline (Development) ===")
    streaming_definition = streaming_workflow.create_for_environment(config)
    print(json.dumps(streaming_definition, indent=2))
    
    print("\n=== Standard Data Processing Pipeline ===")
    print(json.dumps(standard_pipeline, indent=2))
    
    # Switch to production environment
    config.setenv("production")
    
    print("\n=== Batch Processing Pipeline (Production) ===")
    batch_definition = batch_workflow.create_for_environment(config)
    print(json.dumps(batch_definition, indent=2))
    
    # Example configuration differences
    print(f"\n=== Configuration Comparison ===")
    config.setenv("development")
    print(f"Development Lambda timeout: {config.lambda.timeout}")
    print(f"Development parallel processing: {config.pipelines.data_processing.enable_parallel_processing}")
    
    config.setenv("production")
    print(f"Production Lambda timeout: {config.lambda.timeout}")
    print(f"Production parallel processing: {config.pipelines.data_processing.enable_parallel_processing}")


if __name__ == "__main__":
    main()