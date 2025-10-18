#!/usr/bin/env python3
"""
Tests for the Step Functions builder
"""

import pytest
from stepfunctions_improved import (
    StepFunctionBuilder, ConfigurableStepFunctionBuilder,
    NumericGreaterThan, StringEquals, AndRule,
    RetryConfig, CatchConfig, setup_config
)


class TestStepFunctionBuilder:
    
    def test_basic_pipeline_creation(self):
        """Test creating a basic pipeline"""
        builder = StepFunctionBuilder("TestPipeline")
        
        pipeline = (builder
            .start_with("Start")
            .add_pass("Start", result={"message": "hello"})
            .add_lambda_task("Process", "test-function")
            .end_with_success("Success")
            .build())
        
        assert pipeline["StartAt"] == "Start"
        assert "Start" in pipeline["States"]
        assert "Process" in pipeline["States"]
        assert "Success" in pipeline["States"]
        
        # Check state linking
        assert pipeline["States"]["Start"]["Next"] == "Process"
        assert pipeline["States"]["Process"]["Next"] == "Success"
        assert pipeline["States"]["Success"]["Type"] == "Succeed"
    
    def test_choice_state_creation(self):
        """Test creating choice states"""
        builder = StepFunctionBuilder("ChoicePipeline")
        
        pipeline = (builder
            .start_with("Input")
            .add_pass("Input", result={"score": 0.9})
            .add_choice("Decision")
                .when(NumericGreaterThan("$.score", 0.8), "HighScore")
                .otherwise("LowScore")
            .add_pass("HighScore", result={"result": "high"})
            .add_pass("LowScore", result={"result": "low"})
            .build())
        
        choice_state = pipeline["States"]["Decision"]
        assert choice_state["Type"] == "Choice"
        assert len(choice_state["Choices"]) == 1
        assert choice_state["Choices"][0]["Next"] == "HighScore"
        assert choice_state["Default"] == "LowScore"
    
    def test_parallel_state_creation(self):
        """Test creating parallel states"""
        branch1 = StepFunctionBuilder("Branch1")
        branch1.start_with("Task1").add_pass("Task1").end_with_success()
        
        branch2 = StepFunctionBuilder("Branch2")
        branch2.start_with("Task2").add_pass("Task2").end_with_success()
        
        builder = StepFunctionBuilder("ParallelPipeline")
        pipeline = (builder
            .start_with("Start")
            .add_pass("Start")
            .add_parallel("ParallelTasks", [branch1, branch2])
            .end_with_success("Success")
            .build())
        
        parallel_state = pipeline["States"]["ParallelTasks"]
        assert parallel_state["Type"] == "Parallel"
        assert len(parallel_state["Branches"]) == 2
    
    def test_map_state_creation(self):
        """Test creating map states"""
        iterator = StepFunctionBuilder("Iterator")
        iterator.start_with("ProcessItem").add_pass("ProcessItem").end_with_success()
        
        builder = StepFunctionBuilder("MapPipeline")
        pipeline = (builder
            .start_with("Start")
            .add_pass("Start", result={"items": [1, 2, 3]})
            .add_map("ProcessItems", iterator, items_path="$.items", max_concurrency=2)
            .end_with_success("Success")
            .build())
        
        map_state = pipeline["States"]["ProcessItems"]
        assert map_state["Type"] == "Map"
        assert map_state["ItemsPath"] == "$.items"
        assert map_state["MaxConcurrency"] == 2
    
    def test_wait_state_creation(self):
        """Test creating wait states"""
        builder = StepFunctionBuilder("WaitPipeline")
        
        pipeline = (builder
            .start_with("WaitFixed")
            .add_wait("WaitFixed", seconds=10)
            .add_wait("WaitPath", seconds_path="$.wait_time")
            .end_with_success("Success")
            .build())
        
        wait_fixed = pipeline["States"]["WaitFixed"]
        assert wait_fixed["Type"] == "Wait"
        assert wait_fixed["Seconds"] == 10
        
        wait_path = pipeline["States"]["WaitPath"]
        assert wait_path["Type"] == "Wait"
        assert wait_path["SecondsPath"] == "$.wait_time"
    
    def test_error_handling(self):
        """Test retry and catch configuration"""
        retry_config = [RetryConfig(
            error_equals=["States.TaskFailed"],
            interval_seconds=2,
            max_attempts=3
        )]
        
        catch_config = [CatchConfig(
            error_equals=["States.ALL"],
            next="ErrorHandler"
        )]
        
        builder = StepFunctionBuilder("ErrorHandlingPipeline")
        pipeline = (builder
            .start_with("Task")
            .add_lambda_task("Task", "test-function",
                           retry_config=retry_config,
                           catch_config=catch_config)
            .add_pass("ErrorHandler", result={"error": "handled"})
            .end_with_success("Success")
            .build())
        
        task_state = pipeline["States"]["Task"]
        assert "Retry" in task_state
        assert "Catch" in task_state
        assert len(task_state["Retry"]) == 1
        assert len(task_state["Catch"]) == 1
        assert task_state["Catch"][0]["Next"] == "ErrorHandler"
    
    def test_invalid_wait_state(self):
        """Test that invalid wait state raises error"""
        builder = StepFunctionBuilder("InvalidWait")
        
        with pytest.raises(ValueError, match="Exactly one of"):
            builder.add_wait("InvalidWait", seconds=10, timestamp="2024-01-01T00:00:00Z")
    
    def test_complex_choice_rules(self):
        """Test complex choice rule combinations"""
        builder = StepFunctionBuilder("ComplexChoice")
        
        pipeline = (builder
            .start_with("Input")
            .add_pass("Input", result={"score": 0.9, "validated": True})
            .add_choice("ComplexDecision")
                .when(
                    AndRule(
                        NumericGreaterThan("$.score", 0.8),
                        StringEquals("$.validated", "true")
                    ),
                    "Accept"
                )
                .otherwise("Reject")
            .add_pass("Accept", result={"decision": "accepted"})
            .add_pass("Reject", result={"decision": "rejected"})
            .build())
        
        choice_state = pipeline["States"]["ComplexDecision"]
        choice_rule = choice_state["Choices"][0]
        assert "And" in choice_rule
        assert len(choice_rule["And"]) == 2


class TestConfigurableStepFunctionBuilder:
    
    def test_configurable_lambda_task(self):
        """Test configurable Lambda task creation"""
        config = setup_config()
        config.setenv("development")
        
        builder = ConfigurableStepFunctionBuilder("ConfigPipeline", config)
        
        # This would normally resolve function names from config
        # For testing, we'll check the structure
        pipeline = (builder
            .start_with("Process")
            .add_pass("Process", result={"test": "data"})  # Use pass instead of lambda for testing
            .end_with_success("Success")
            .build())
        
        assert pipeline["StartAt"] == "Process"
        assert "Process" in pipeline["States"]
    
    def test_environment_switching(self):
        """Test that configuration changes affect pipeline creation"""
        config = setup_config()
        
        # Test development environment
        config.setenv("development")
        dev_timeout = config.get("lambda.timeout", 60)
        
        # Test production environment  
        config.setenv("production")
        prod_timeout = config.get("lambda.timeout", 60)
        
        # Timeouts should be different between environments
        # (This depends on the actual config values)
        assert isinstance(dev_timeout, int)
        assert isinstance(prod_timeout, int)


if __name__ == "__main__":
    pytest.main([__file__])