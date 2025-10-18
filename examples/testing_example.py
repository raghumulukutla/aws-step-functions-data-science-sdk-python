#!/usr/bin/env python3
"""
Example: Testing Step Functions with Simulation and Validation
"""

import json
from stepfunctions_improved import (
    StepFunctionBuilder, ConfigurableStepFunctionBuilder, setup_config,
    StateMachineValidator, StateMachineSimulator,
    NumericGreaterThan, StringEquals, BooleanEquals
)


def create_test_pipeline():
    """Create a simple pipeline for testing"""
    builder = StepFunctionBuilder("TestPipeline")
    
    builder.start_with("StartTest")
    builder.add_pass("StartTest", result={"test_id": "12345", "status": "started"})
    
    builder.add_lambda_task("ProcessData", "test-function",
                          payload_path="$",
                          timeout_seconds=30)
    
    choice_builder = builder.add_choice("CheckResult")
    choice_builder.when(
        NumericGreaterThan("$.score", 0.8),
        "Success"
    ).otherwise("Retry")
    
    builder.add_pass("Retry", result={"action": "retry"})
    builder.end_with_success("Success")
    
    return builder.build()


def create_complex_test_pipeline():
    """Create a more complex pipeline for comprehensive testing"""
    builder = StepFunctionBuilder("ComplexTestPipeline")
    
    builder.start_with("Initialize")
    builder.add_pass("Initialize", 
                    result={"pipeline_id": "test-123", "timestamp": "2024-01-01T00:00:00Z"})
    
    # Parallel processing branches
    branch1 = StepFunctionBuilder("Branch1")
    branch1.start_with("ProcessA")
    branch1.add_lambda_task("ProcessA", "process-a-function")
    branch1.add_lambda_task("ValidateA", "validate-a-function")
    branch1.end_with_success()
    
    branch2 = StepFunctionBuilder("Branch2")
    branch2.start_with("ProcessB")
    branch2.add_lambda_task("ProcessB", "process-b-function")
    branch2.add_lambda_task("ValidateB", "validate-b-function")
    branch2.end_with_success()
    
    builder.add_parallel("ProcessParallel", [branch1, branch2])
    
    # Map state for batch processing
    iterator = StepFunctionBuilder("Iterator")
    iterator.start_with("ProcessItem")
    iterator.add_lambda_task("ProcessItem", "process-item-function")
    iterator.end_with_success()
    
    builder.add_map("ProcessItems", iterator, items_path="$.items", max_concurrency=5)
    
    # Complex choice logic
    choice_builder = builder.add_choice("FinalDecision")
    
    from stepfunctions_improved.choice_rules import AndRule, OrRule
    
    choice_builder.when(
        AndRule(
            NumericGreaterThan("$.overall_score", 0.9),
            BooleanEquals("$.all_validations_passed", True)
        ),
        "DeployToProduction"
    ).when(
        OrRule(
            NumericGreaterThan("$.overall_score", 0.7),
            StringEquals("$.environment", "staging")
        ),
        "DeployToStaging"
    ).otherwise("RejectDeployment")
    
    builder.add_pass("DeployToProduction", result={"deployment": "production"})
    builder.add_pass("DeployToStaging", result={"deployment": "staging"})
    builder.end_with_failure("RejectDeployment", 
                            error="DeploymentRejected",
                            cause="Quality criteria not met")
    
    return builder.build()


def test_validation():
    """Test state machine validation"""
    print("=== Testing State Machine Validation ===")
    
    # Test valid pipeline
    valid_pipeline = create_test_pipeline()
    validator = StateMachineValidator(valid_pipeline)
    
    is_valid = validator.validate()
    print(f"Valid pipeline validation result: {is_valid}")
    
    if not is_valid:
        print("Validation errors:")
        for error in validator.get_errors():
            print(f"  - {error}")
    
    warnings = validator.get_warnings()
    if warnings:
        print("Validation warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    # Test invalid pipeline
    print("\n--- Testing Invalid Pipeline ---")
    invalid_pipeline = {
        "StartAt": "NonExistentState",
        "States": {
            "ValidState": {
                "Type": "Pass",
                "Next": "AnotherNonExistentState"
            },
            "InvalidTask": {
                "Type": "Task"
                # Missing required Resource field
            },
            "InvalidChoice": {
                "Type": "Choice"
                # Missing required Choices field
            }
        }
    }
    
    invalid_validator = StateMachineValidator(invalid_pipeline)
    is_valid = invalid_validator.validate()
    print(f"Invalid pipeline validation result: {is_valid}")
    
    if not is_valid:
        print("Validation errors:")
        for error in invalid_validator.get_errors():
            print(f"  - {error}")


def test_simulation():
    """Test state machine simulation"""
    print("\n=== Testing State Machine Simulation ===")
    
    # Create and simulate simple pipeline
    pipeline = create_test_pipeline()
    simulator = StateMachineSimulator(pipeline)
    
    # Add mock responses
    simulator.add_mock_response("ProcessData", {"score": 0.9, "result": "success"})
    
    # Test successful execution
    print("--- Test Case 1: Successful Execution ---")
    input_data = {"data": "test input"}
    result = simulator.simulate_execution(input_data)
    
    print(f"Execution status: {result.status.value}")
    print(f"Final output: {result.output}")
    print("Execution trace:")
    for event in result.execution_trace:
        print(f"  {event['state_name']} ({event['state_type']}): {event['input']} -> {event['output']}")
    
    # Test execution with retry path
    print("\n--- Test Case 2: Retry Path ---")
    simulator.add_mock_response("ProcessData", {"score": 0.5, "result": "needs_retry"})
    
    result = simulator.simulate_execution(input_data)
    print(f"Execution status: {result.status.value}")
    print(f"Final output: {result.output}")
    print("Execution trace:")
    for event in result.execution_trace:
        print(f"  {event['state_name']} ({event['state_type']}): {event['input']} -> {event['output']}")


def test_complex_simulation():
    """Test simulation of complex pipeline"""
    print("\n=== Testing Complex Pipeline Simulation ===")
    
    pipeline = create_complex_test_pipeline()
    simulator = StateMachineSimulator(pipeline)
    
    # Add mock responses for all Lambda functions
    simulator.add_mock_response("ProcessA", {"result_a": "processed", "score_a": 0.95})
    simulator.add_mock_response("ValidateA", {"validation_a": True})
    simulator.add_mock_response("ProcessB", {"result_b": "processed", "score_b": 0.85})
    simulator.add_mock_response("ValidateB", {"validation_b": True})
    simulator.add_mock_response("ProcessItem", {"processed": True})
    
    # Test with high quality results
    print("--- Test Case: High Quality Results ---")
    input_data = {
        "items": ["item1", "item2", "item3"],
        "overall_score": 0.95,
        "all_validations_passed": True,
        "environment": "production"
    }
    
    result = simulator.simulate_execution(input_data)
    print(f"Execution status: {result.status.value}")
    print(f"Final output: {result.output}")
    
    # Test with medium quality results
    print("\n--- Test Case: Medium Quality Results ---")
    input_data = {
        "items": ["item1", "item2"],
        "overall_score": 0.75,
        "all_validations_passed": False,
        "environment": "staging"
    }
    
    result = simulator.simulate_execution(input_data)
    print(f"Execution status: {result.status.value}")
    print(f"Final output: {result.output}")
    
    # Test with poor quality results
    print("\n--- Test Case: Poor Quality Results ---")
    input_data = {
        "items": ["item1"],
        "overall_score": 0.5,
        "all_validations_passed": False,
        "environment": "development"
    }
    
    result = simulator.simulate_execution(input_data)
    print(f"Execution status: {result.status.value}")
    print(f"Error: {result.error}")


def test_configuration_driven_pipeline():
    """Test configuration-driven pipeline creation and testing"""
    print("\n=== Testing Configuration-Driven Pipeline ===")
    
    config = setup_config()
    
    # Test in development environment
    config.setenv("development")
    print(f"Testing in {config.current_env} environment")
    
    builder = ConfigurableStepFunctionBuilder("ConfigTestPipeline", config)
    
    builder.start_with("Start")
    builder.add_pass("Start", result={"env": config.current_env})
    
    builder.add_lambda_task("ProcessData", "preprocess_data")
    
    # Environment-specific logic
    if config.get("auto_deploy", False):
        builder.add_lambda_task("AutoDeploy", "deploy_model")
    else:
        builder.add_sns_task("NotifyForApproval", "alerts",
                           message="Manual approval required")
    
    builder.end_with_success("Success")
    
    pipeline = builder.build()
    
    # Validate the pipeline
    validator = StateMachineValidator(pipeline)
    is_valid = validator.validate()
    print(f"Configuration-driven pipeline is valid: {is_valid}")
    
    if not is_valid:
        for error in validator.get_errors():
            print(f"  Error: {error}")
    
    # Simulate the pipeline
    simulator = StateMachineSimulator(pipeline)
    simulator.add_mock_response("ProcessData", {"processed": True})
    simulator.add_mock_response("AutoDeploy", {"deployed": True})
    
    result = simulator.simulate_execution({"input": "test"})
    print(f"Simulation result: {result.status.value}")
    print(f"Output: {result.output}")


def main():
    """Run all tests"""
    test_validation()
    test_simulation()
    test_complex_simulation()
    test_configuration_driven_pipeline()
    
    print("\n=== All Tests Completed ===")


if __name__ == "__main__":
    main()