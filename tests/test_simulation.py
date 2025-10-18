#!/usr/bin/env python3
"""
Tests for state machine simulation
"""

import pytest
from stepfunctions_improved import (
    StateMachineSimulator, ExecutionStatus, StepFunctionBuilder,
    NumericGreaterThan, StringEquals, BooleanEquals
)


class TestStateMachineSimulator:
    
    def test_simple_pass_simulation(self):
        """Test simulation of simple Pass state"""
        pipeline = {
            "StartAt": "Start",
            "States": {
                "Start": {
                    "Type": "Pass",
                    "Result": {"message": "hello"},
                    "End": True
                }
            }
        }
        
        simulator = StateMachineSimulator(pipeline)
        result = simulator.simulate_execution({"input": "test"})
        
        assert result.status == ExecutionStatus.SUCCEEDED
        assert result.output == {"message": "hello"}
        assert len(result.execution_trace) == 1
        assert result.execution_trace[0]["state_name"] == "Start"
    
    def test_task_state_simulation(self):
        """Test simulation of Task state with mock response"""
        pipeline = {
            "StartAt": "TaskState",
            "States": {
                "TaskState": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "End": True
                }
            }
        }
        
        simulator = StateMachineSimulator(pipeline)
        simulator.add_mock_response("TaskState", {"result": "mocked"})
        
        result = simulator.simulate_execution({"input": "test"})
        
        assert result.status == ExecutionStatus.SUCCEEDED
        assert result.output == {"result": "mocked"}
    
    def test_choice_state_simulation(self):
        """Test simulation of Choice state"""
        pipeline = {
            "StartAt": "ChoiceState",
            "States": {
                "ChoiceState": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.score",
                            "NumericGreaterThan": 0.8,
                            "Next": "HighScore"
                        }
                    ],
                    "Default": "LowScore"
                },
                "HighScore": {
                    "Type": "Pass",
                    "Result": {"result": "high"},
                    "End": True
                },
                "LowScore": {
                    "Type": "Pass",
                    "Result": {"result": "low"},
                    "End": True
                }
            }
        }
        
        simulator = StateMachineSimulator(pipeline)
        
        # Test high score path
        result = simulator.simulate_execution({"score": 0.9})
        assert result.status == ExecutionStatus.SUCCEEDED
        assert result.output == {"result": "high"}
        
        # Test low score path
        result = simulator.simulate_execution({"score": 0.5})
        assert result.status == ExecutionStatus.SUCCEEDED
        assert result.output == {"result": "low"}
    
    def test_parallel_state_simulation(self):
        """Test simulation of Parallel state"""
        pipeline = {
            "StartAt": "ParallelState",
            "States": {
                "ParallelState": {
                    "Type": "Parallel",
                    "Branches": [
                        {
                            "StartAt": "Branch1",
                            "States": {
                                "Branch1": {
                                    "Type": "Pass",
                                    "Result": {"branch": 1},
                                    "End": True
                                }
                            }
                        },
                        {
                            "StartAt": "Branch2", 
                            "States": {
                                "Branch2": {
                                    "Type": "Pass",
                                    "Result": {"branch": 2},
                                    "End": True
                                }
                            }
                        }
                    ],
                    "End": True
                }
            }
        }
        
        simulator = StateMachineSimulator(pipeline)
        result = simulator.simulate_execution({"input": "test"})
        
        assert result.status == ExecutionStatus.SUCCEEDED
        # Parallel state should return array of results
        assert isinstance(result.output, list)
    
    def test_map_state_simulation(self):
        """Test simulation of Map state"""
        pipeline = {
            "StartAt": "MapState",
            "States": {
                "MapState": {
                    "Type": "Map",
                    "ItemsPath": "$.items",
                    "Iterator": {
                        "StartAt": "ProcessItem",
                        "States": {
                            "ProcessItem": {
                                "Type": "Pass",
                                "End": True
                            }
                        }
                    },
                    "End": True
                }
            }
        }
        
        simulator = StateMachineSimulator(pipeline)
        result = simulator.simulate_execution({"items": ["a", "b", "c"]})
        
        assert result.status == ExecutionStatus.SUCCEEDED
        assert isinstance(result.output, list)
        assert len(result.output) == 3
    
    def test_wait_state_simulation(self):
        """Test simulation of Wait state"""
        pipeline = {
            "StartAt": "WaitState",
            "States": {
                "WaitState": {
                    "Type": "Wait",
                    "Seconds": 5,
                    "Next": "Continue"
                },
                "Continue": {
                    "Type": "Pass",
                    "Result": {"waited": True},
                    "End": True
                }
            }
        }
        
        simulator = StateMachineSimulator(pipeline)
        result = simulator.simulate_execution({"input": "test"})
        
        assert result.status == ExecutionStatus.SUCCEEDED
        assert result.output == {"waited": True}
    
    def test_succeed_state_simulation(self):
        """Test simulation of Succeed state"""
        pipeline = {
            "StartAt": "SucceedState",
            "States": {
                "SucceedState": {
                    "Type": "Succeed"
                }
            }
        }
        
        simulator = StateMachineSimulator(pipeline)
        result = simulator.simulate_execution({"input": "test"})
        
        assert result.status == ExecutionStatus.SUCCEEDED
    
    def test_fail_state_simulation(self):
        """Test simulation of Fail state"""
        pipeline = {
            "StartAt": "FailState",
            "States": {
                "FailState": {
                    "Type": "Fail",
                    "Error": "TestError",
                    "Cause": "Test failure"
                }
            }
        }
        
        simulator = StateMachineSimulator(pipeline)
        result = simulator.simulate_execution({"input": "test"})
        
        assert result.status == ExecutionStatus.FAILED
        assert result.error == "TestError"
    
    def test_complex_choice_rules(self):
        """Test simulation with complex choice rules"""
        pipeline = {
            "StartAt": "ComplexChoice",
            "States": {
                "ComplexChoice": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "And": [
                                {
                                    "Variable": "$.score",
                                    "NumericGreaterThan": 0.8
                                },
                                {
                                    "Variable": "$.validated",
                                    "BooleanEquals": True
                                }
                            ],
                            "Next": "Accept"
                        },
                        {
                            "Or": [
                                {
                                    "Variable": "$.score",
                                    "NumericGreaterThan": 0.5
                                },
                                {
                                    "Variable": "$.environment",
                                    "StringEquals": "staging"
                                }
                            ],
                            "Next": "Review"
                        }
                    ],
                    "Default": "Reject"
                },
                "Accept": {
                    "Type": "Pass",
                    "Result": {"decision": "accepted"},
                    "End": True
                },
                "Review": {
                    "Type": "Pass",
                    "Result": {"decision": "review"},
                    "End": True
                },
                "Reject": {
                    "Type": "Pass",
                    "Result": {"decision": "rejected"},
                    "End": True
                }
            }
        }
        
        simulator = StateMachineSimulator(pipeline)
        
        # Test AND condition (accept)
        result = simulator.simulate_execution({
            "score": 0.9,
            "validated": True,
            "environment": "production"
        })
        assert result.output["decision"] == "accepted"
        
        # Test OR condition (review)
        result = simulator.simulate_execution({
            "score": 0.3,
            "validated": False,
            "environment": "staging"
        })
        assert result.output["decision"] == "review"
        
        # Test default (reject)
        result = simulator.simulate_execution({
            "score": 0.3,
            "validated": False,
            "environment": "production"
        })
        assert result.output["decision"] == "rejected"
    
    def test_input_output_path_processing(self):
        """Test InputPath and OutputPath processing"""
        pipeline = {
            "StartAt": "ProcessPath",
            "States": {
                "ProcessPath": {
                    "Type": "Pass",
                    "InputPath": "$.data",
                    "Result": {"processed": True},
                    "ResultPath": "$.result",
                    "OutputPath": "$.result",
                    "End": True
                }
            }
        }
        
        simulator = StateMachineSimulator(pipeline)
        result = simulator.simulate_execution({
            "data": {"value": 123},
            "metadata": {"id": "test"}
        })
        
        assert result.status == ExecutionStatus.SUCCEEDED
        # Output should be just the result due to OutputPath
        assert result.output == {"processed": True}
    
    def test_parameters_processing(self):
        """Test Parameters field processing"""
        pipeline = {
            "StartAt": "TaskWithParams",
            "States": {
                "TaskWithParams": {
                    "Type": "Task",
                    "Resource": "arn:aws:states:::lambda:invoke",
                    "Parameters": {
                        "FunctionName": "test-function",
                        "Payload.$": "$"
                    },
                    "End": True
                }
            }
        }
        
        simulator = StateMachineSimulator(pipeline)
        simulator.add_mock_response("TaskWithParams", {"result": "success"})
        
        result = simulator.simulate_execution({"input": "test"})
        
        assert result.status == ExecutionStatus.SUCCEEDED
        assert result.output == {"result": "success"}
    
    def test_execution_trace(self):
        """Test execution trace generation"""
        builder = StepFunctionBuilder("TracePipeline")
        pipeline = (builder
            .start_with("Start")
            .add_pass("Start", result={"step": 1})
            .add_pass("Middle", result={"step": 2})
            .add_pass("End", result={"step": 3})
            .build())
        
        simulator = StateMachineSimulator(pipeline)
        result = simulator.simulate_execution({"input": "test"})
        
        assert result.status == ExecutionStatus.SUCCEEDED
        assert len(result.execution_trace) == 3
        
        # Check trace order
        trace_states = [event["state_name"] for event in result.execution_trace]
        assert trace_states == ["Start", "Middle", "End"]
    
    def test_infinite_loop_prevention(self):
        """Test that infinite loops are prevented"""
        # Create a pipeline that could loop infinitely
        pipeline = {
            "StartAt": "LoopState",
            "States": {
                "LoopState": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.counter",
                            "NumericLessThan": 10,
                            "Next": "LoopState"  # Points to itself
                        }
                    ],
                    "Default": "End"
                },
                "End": {
                    "Type": "Succeed"
                }
            }
        }
        
        simulator = StateMachineSimulator(pipeline)
        result = simulator.simulate_execution({"counter": 0})
        
        # Should fail due to max iterations
        assert result.status == ExecutionStatus.FAILED
        assert "Maximum iterations exceeded" in result.error


if __name__ == "__main__":
    pytest.main([__file__])