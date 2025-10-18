# Copyright 2024 Improved Step Functions Framework

"""
Simulation utilities for testing Step Functions state machines
"""

import json
from typing import Dict, Any, Optional, List
from enum import Enum


class ExecutionStatus(Enum):
    """Execution status enumeration"""
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    ABORTED = "ABORTED"


class SimulationResult:
    """Result of a state machine simulation"""
    
    def __init__(self, status: ExecutionStatus, output: Any = None, error: Optional[str] = None):
        self.status = status
        self.output = output
        self.error = error
        self.execution_trace: List[Dict[str, Any]] = []
    
    def add_trace_event(self, state_name: str, state_type: str, input_data: Any, output_data: Any = None):
        """Add an event to the execution trace"""
        self.execution_trace.append({
            "state_name": state_name,
            "state_type": state_type,
            "input": input_data,
            "output": output_data,
            "timestamp": len(self.execution_trace)
        })
    
    def to_dict(self) -> dict:
        """Convert result to dictionary"""
        return {
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "execution_trace": self.execution_trace
        }


class StateMachineSimulator:
    """Simulator for Step Functions state machines (for testing purposes)"""
    
    def __init__(self, definition: dict):
        self.definition = definition
        self.mock_responses: Dict[str, Any] = {}
        self.max_iterations = 1000  # Prevent infinite loops
    
    def add_mock_response(self, state_name: str, response: Any):
        """Add mock response for a specific state"""
        self.mock_responses[state_name] = response
    
    def simulate_execution(self, input_data: dict) -> SimulationResult:
        """
        Simulate execution of the state machine
        
        Args:
            input_data: Input data for the execution
            
        Returns:
            SimulationResult: Result of the simulation
        """
        try:
            result = SimulationResult(ExecutionStatus.RUNNING)
            current_state = self.definition["StartAt"]
            context = input_data.copy()
            iterations = 0
            
            while current_state and iterations < self.max_iterations:
                iterations += 1
                
                state_def = self.definition["States"][current_state]
                state_type = state_def["Type"]
                
                # Process the current state
                next_state, context = self._process_state(current_state, state_def, context, result)
                
                # Check for terminal states
                if state_type in ["Succeed", "Fail"]:
                    if state_type == "Succeed":
                        result.status = ExecutionStatus.SUCCEEDED
                        result.output = context
                    else:
                        result.status = ExecutionStatus.FAILED
                        result.error = state_def.get("Error", "Unknown error")
                    break
                
                current_state = next_state
            
            if iterations >= self.max_iterations:
                result.status = ExecutionStatus.FAILED
                result.error = "Maximum iterations exceeded - possible infinite loop"
            
            return result
            
        except Exception as e:
            result = SimulationResult(ExecutionStatus.FAILED, error=str(e))
            return result
    
    def _process_state(self, state_name: str, state_def: dict, context: Any, result: SimulationResult) -> tuple:
        """
        Process a single state
        
        Returns:
            tuple: (next_state_name, updated_context)
        """
        state_type = state_def["Type"]
        input_data = self._apply_input_path(context, state_def.get("InputPath"))
        
        # Apply Parameters if present
        if "Parameters" in state_def:
            input_data = self._apply_parameters(input_data, state_def["Parameters"])
        
        output_data = input_data  # Default: pass through
        
        if state_type == "Pass":
            if "Result" in state_def:
                output_data = state_def["Result"]
        
        elif state_type == "Wait":
            # In simulation, we just pass through
            output_data = input_data
        
        elif state_type == "Task":
            # Use mock response if available, otherwise pass through
            if state_name in self.mock_responses:
                output_data = self.mock_responses[state_name]
            else:
                # Default task simulation - just pass input as output
                output_data = input_data
        
        elif state_type == "Choice":
            # Evaluate choice rules
            next_state = self._evaluate_choice_rules(state_def, input_data)
            result.add_trace_event(state_name, state_type, input_data, output_data)
            return next_state, context
        
        elif state_type == "Parallel":
            # Simulate parallel execution (simplified)
            branches = state_def.get("Branches", [])
            branch_results = []
            for branch in branches:
                # Simulate each branch (simplified - just return input)
                branch_results.append(input_data)
            output_data = branch_results
        
        elif state_type == "Map":
            # Simulate map execution (simplified)
            items_path = state_def.get("ItemsPath", "$")
            items = self._apply_json_path(input_data, items_path)
            if isinstance(items, list):
                # Simulate iterator for each item (simplified)
                output_data = [item for item in items]
            else:
                output_data = []
        
        # Apply ResultPath
        if "ResultPath" in state_def:
            context = self._apply_result_path(context, output_data, state_def["ResultPath"])
        else:
            context = output_data
        
        # Apply OutputPath
        if "OutputPath" in state_def:
            context = self._apply_output_path(context, state_def["OutputPath"])
        
        result.add_trace_event(state_name, state_type, input_data, output_data)
        
        # Determine next state
        next_state = None
        if "Next" in state_def:
            next_state = state_def["Next"]
        elif state_def.get("End"):
            next_state = None
        
        return next_state, context
    
    def _evaluate_choice_rules(self, choice_def: dict, input_data: Any) -> Optional[str]:
        """Evaluate choice rules and return next state"""
        choices = choice_def.get("Choices", [])
        
        for choice in choices:
            if self._evaluate_single_choice_rule(choice, input_data):
                return choice.get("Next")
        
        # No rules matched, use default
        return choice_def.get("Default")
    
    def _evaluate_single_choice_rule(self, rule: dict, input_data: Any) -> bool:
        """Evaluate a single choice rule"""
        # Simplified rule evaluation
        variable = rule.get("Variable", "$")
        value = self._apply_json_path(input_data, variable)
        
        # Numeric comparisons
        if "NumericEquals" in rule:
            return value == rule["NumericEquals"]
        elif "NumericGreaterThan" in rule:
            return value > rule["NumericGreaterThan"]
        elif "NumericLessThan" in rule:
            return value < rule["NumericLessThan"]
        elif "NumericGreaterThanEquals" in rule:
            return value >= rule["NumericGreaterThanEquals"]
        elif "NumericLessThanEquals" in rule:
            return value <= rule["NumericLessThanEquals"]
        
        # String comparisons
        elif "StringEquals" in rule:
            return str(value) == rule["StringEquals"]
        elif "StringMatches" in rule:
            import re
            return bool(re.match(rule["StringMatches"], str(value)))
        
        # Boolean comparison
        elif "BooleanEquals" in rule:
            return bool(value) == rule["BooleanEquals"]
        
        # Logical operators
        elif "And" in rule:
            return all(self._evaluate_single_choice_rule(sub_rule, input_data) for sub_rule in rule["And"])
        elif "Or" in rule:
            return any(self._evaluate_single_choice_rule(sub_rule, input_data) for sub_rule in rule["Or"])
        elif "Not" in rule:
            return not self._evaluate_single_choice_rule(rule["Not"], input_data)
        
        # Default: rule doesn't match
        return False
    
    def _apply_input_path(self, data: Any, input_path: Optional[str]) -> Any:
        """Apply InputPath to data"""
        if input_path is None:
            return data
        return self._apply_json_path(data, input_path)
    
    def _apply_output_path(self, data: Any, output_path: Optional[str]) -> Any:
        """Apply OutputPath to data"""
        if output_path is None:
            return data
        return self._apply_json_path(data, output_path)
    
    def _apply_result_path(self, original_data: Any, result_data: Any, result_path: Optional[str]) -> Any:
        """Apply ResultPath to combine original data with result"""
        if result_path is None or result_path == "$":
            return result_data
        
        if result_path == "null":
            return original_data
        
        # Simplified: just set the result at the specified path
        if isinstance(original_data, dict) and result_path.startswith("$."):
            key = result_path[2:]  # Remove "$."
            result = original_data.copy()
            result[key] = result_data
            return result
        
        return result_data
    
    def _apply_parameters(self, input_data: Any, parameters: dict) -> Any:
        """Apply Parameters transformation"""
        # Simplified parameter application
        result = {}
        for key, value in parameters.items():
            if isinstance(value, str) and value.endswith(".$"):
                # JSONPath reference
                path = value[:-2]  # Remove ".$"
                result[key] = self._apply_json_path(input_data, path)
            else:
                result[key] = value
        return result
    
    def _apply_json_path(self, data: Any, path: str) -> Any:
        """Apply JSONPath to data (simplified implementation)"""
        if path == "$":
            return data
        
        if path == "null":
            return None
        
        if path.startswith("$."):
            # Simplified JSONPath - just handle basic field access
            field = path[2:]
            if isinstance(data, dict):
                return data.get(field, None)
        
        return data