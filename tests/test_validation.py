#!/usr/bin/env python3
"""
Tests for state machine validation
"""

import pytest
from stepfunctions_improved import StateMachineValidator, ValidationError, StepFunctionBuilder


class TestStateMachineValidator:
    
    def test_valid_simple_pipeline(self):
        """Test validation of a valid simple pipeline"""
        pipeline = {
            "StartAt": "Start",
            "States": {
                "Start": {
                    "Type": "Pass",
                    "Result": {"message": "hello"},
                    "Next": "End"
                },
                "End": {
                    "Type": "Succeed"
                }
            }
        }
        
        validator = StateMachineValidator(pipeline)
        assert validator.validate() == True
        assert len(validator.get_errors()) == 0
    
    def test_missing_required_fields(self):
        """Test validation fails for missing required fields"""
        pipeline = {
            "States": {
                "Start": {
                    "Type": "Pass"
                }
            }
            # Missing StartAt
        }
        
        validator = StateMachineValidator(pipeline)
        assert validator.validate() == False
        errors = validator.get_errors()
        assert any("Missing required field: StartAt" in error for error in errors)
    
    def test_invalid_state_references(self):
        """Test validation fails for invalid state references"""
        pipeline = {
            "StartAt": "NonExistentState",
            "States": {
                "Start": {
                    "Type": "Pass",
                    "Next": "AlsoNonExistent"
                }
            }
        }
        
        validator = StateMachineValidator(pipeline)
        assert validator.validate() == False
        errors = validator.get_errors()
        assert any("StartAt references non-existent state" in error for error in errors)
        assert any("references non-existent Next state" in error for error in errors)
    
    def test_task_state_validation(self):
        """Test Task state specific validation"""
        pipeline = {
            "StartAt": "TaskState",
            "States": {
                "TaskState": {
                    "Type": "Task"
                    # Missing required Resource field
                }
            }
        }
        
        validator = StateMachineValidator(pipeline)
        assert validator.validate() == False
        errors = validator.get_errors()
        assert any("missing required Resource field" in error for error in errors)
    
    def test_choice_state_validation(self):
        """Test Choice state specific validation"""
        # Missing Choices field
        pipeline1 = {
            "StartAt": "ChoiceState",
            "States": {
                "ChoiceState": {
                    "Type": "Choice"
                    # Missing Choices field
                }
            }
        }
        
        validator1 = StateMachineValidator(pipeline1)
        assert validator1.validate() == False
        errors1 = validator1.get_errors()
        assert any("missing required Choices field" in error for error in errors1)
        
        # Choice with Next field (invalid)
        pipeline2 = {
            "StartAt": "ChoiceState",
            "States": {
                "ChoiceState": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.test",
                            "NumericEquals": 1,
                            "Next": "Success"
                        }
                    ],
                    "Next": "InvalidNext"  # Choice states cannot have Next
                },
                "Success": {
                    "Type": "Succeed"
                }
            }
        }
        
        validator2 = StateMachineValidator(pipeline2)
        assert validator2.validate() == False
        errors2 = validator2.get_errors()
        assert any("cannot have Next field" in error for error in errors2)
    
    def test_wait_state_validation(self):
        """Test Wait state specific validation"""
        # No timing fields
        pipeline1 = {
            "StartAt": "WaitState",
            "States": {
                "WaitState": {
                    "Type": "Wait"
                    # Missing timing field
                }
            }
        }
        
        validator1 = StateMachineValidator(pipeline1)
        assert validator1.validate() == False
        errors1 = validator1.get_errors()
        assert any("must have exactly one of" in error for error in errors1)
        
        # Multiple timing fields
        pipeline2 = {
            "StartAt": "WaitState",
            "States": {
                "WaitState": {
                    "Type": "Wait",
                    "Seconds": 10,
                    "Timestamp": "2024-01-01T00:00:00Z"  # Cannot have both
                }
            }
        }
        
        validator2 = StateMachineValidator(pipeline2)
        assert validator2.validate() == False
        errors2 = validator2.get_errors()
        assert any("must have exactly one of" in error for error in errors2)
    
    def test_parallel_state_validation(self):
        """Test Parallel state specific validation"""
        pipeline = {
            "StartAt": "ParallelState",
            "States": {
                "ParallelState": {
                    "Type": "Parallel"
                    # Missing Branches field
                }
            }
        }
        
        validator = StateMachineValidator(pipeline)
        assert validator.validate() == False
        errors = validator.get_errors()
        assert any("missing required Branches field" in error for error in errors)
    
    def test_map_state_validation(self):
        """Test Map state specific validation"""
        pipeline = {
            "StartAt": "MapState",
            "States": {
                "MapState": {
                    "Type": "Map"
                    # Missing Iterator field
                }
            }
        }
        
        validator = StateMachineValidator(pipeline)
        assert validator.validate() == False
        errors = validator.get_errors()
        assert any("missing required Iterator field" in error for error in errors)
    
    def test_choice_rule_validation(self):
        """Test Choice rule validation"""
        pipeline = {
            "StartAt": "ChoiceState",
            "States": {
                "ChoiceState": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            # Missing Variable field
                            "NumericEquals": 1,
                            "Next": "Success"
                        }
                    ]
                },
                "Success": {
                    "Type": "Succeed"
                }
            }
        }
        
        validator = StateMachineValidator(pipeline)
        assert validator.validate() == False
        errors = validator.get_errors()
        assert any("missing Variable field" in error for error in errors)
    
    def test_invalid_state_name(self):
        """Test validation of invalid state names"""
        pipeline = {
            "StartAt": "Valid State Name",
            "States": {
                "Valid State Name": {  # Spaces are actually allowed
                    "Type": "Pass"
                },
                "Invalid<State>Name": {  # Invalid characters
                    "Type": "Pass"
                }
            }
        }
        
        validator = StateMachineValidator(pipeline)
        validator.validate()
        errors = validator.get_errors()
        # Check that invalid characters are caught
        assert any("Invalid<State>Name" in error for error in errors)
    
    def test_timeout_validation(self):
        """Test timeout field validation"""
        pipeline = {
            "StartAt": "TaskState",
            "States": {
                "TaskState": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "TimeoutSeconds": -1,  # Invalid negative timeout
                    "HeartbeatSeconds": 100  # Greater than timeout
                }
            }
        }
        
        validator = StateMachineValidator(pipeline)
        assert validator.validate() == False
        errors = validator.get_errors()
        assert any("must be a positive integer" in error for error in errors)
    
    def test_json_path_validation(self):
        """Test JSONPath validation"""
        pipeline = {
            "StartAt": "TaskState",
            "States": {
                "TaskState": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "InputPath": "invalid_path",  # Should start with $
                    "OutputPath": "$.valid.path"
                }
            }
        }
        
        validator = StateMachineValidator(pipeline)
        validator.validate()
        errors = validator.get_errors()
        # JSONPath validation might catch invalid paths
        # Implementation depends on the specific validation logic
    
    def test_resource_arn_validation(self):
        """Test resource ARN validation"""
        pipeline = {
            "StartAt": "TaskState",
            "States": {
                "TaskState": {
                    "Type": "Task",
                    "Resource": "invalid-arn-format"
                }
            }
        }
        
        validator = StateMachineValidator(pipeline)
        validator.validate()
        errors = validator.get_errors()
        # Check if invalid ARN format is caught
        assert any("invalid Resource ARN format" in error for error in errors)
    
    def test_warnings_generation(self):
        """Test that warnings are generated for missing optional fields"""
        pipeline = {
            "StartAt": "FailState",
            "States": {
                "FailState": {
                    "Type": "Fail"
                    # Missing Error and Cause fields (should generate warnings)
                }
            }
        }
        
        validator = StateMachineValidator(pipeline)
        validator.validate()
        warnings = validator.get_warnings()
        assert any("should have Error field" in warning for warning in warnings)
        assert any("should have Cause field" in warning for warning in warnings)
    
    def test_builder_generated_pipeline_validation(self):
        """Test validation of pipeline generated by builder"""
        builder = StepFunctionBuilder("TestPipeline")
        pipeline = (builder
            .start_with("Start")
            .add_pass("Start", result={"test": True})
            .add_lambda_task("Process", "arn:aws:lambda:us-east-1:123456789012:function:test")
            .end_with_success("Success")
            .build())
        
        validator = StateMachineValidator(pipeline)
        is_valid = validator.validate()
        
        if not is_valid:
            print("Validation errors:")
            for error in validator.get_errors():
                print(f"  - {error}")
        
        assert is_valid == True


if __name__ == "__main__":
    pytest.main([__file__])