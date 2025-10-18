# Copyright 2024 Improved Step Functions Framework

"""
Validation utilities for Step Functions state machines
"""

import json
from typing import List, Set, Dict, Any
import re


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class StateMachineValidator:
    """Validator for Step Functions state machine definitions"""
    
    def __init__(self, definition: dict):
        self.definition = definition
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self) -> bool:
        """
        Validate the state machine definition
        
        Returns:
            bool: True if valid, False if errors found
        """
        self.errors.clear()
        self.warnings.clear()
        
        self._validate_structure()
        self._validate_state_references()
        self._validate_state_definitions()
        self._validate_choice_rules()
        self._validate_resource_arns()
        self._validate_paths()
        self._validate_timeouts()
        
        return len(self.errors) == 0
    
    def get_errors(self) -> List[str]:
        """Get validation errors"""
        return self.errors.copy()
    
    def get_warnings(self) -> List[str]:
        """Get validation warnings"""
        return self.warnings.copy()
    
    def _validate_structure(self):
        """Validate basic structure requirements"""
        required_fields = ["StartAt", "States"]
        for field in required_fields:
            if field not in self.definition:
                self.errors.append(f"Missing required field: {field}")
        
        if "States" in self.definition and not isinstance(self.definition["States"], dict):
            self.errors.append("States field must be a dictionary")
        
        if "States" in self.definition and len(self.definition["States"]) == 0:
            self.errors.append("States dictionary cannot be empty")
    
    def _validate_state_references(self):
        """Validate all state references are valid"""
        states = self.definition.get("States", {})
        start_at = self.definition.get("StartAt")
        
        # Validate StartAt reference
        if start_at and start_at not in states:
            self.errors.append(f"StartAt references non-existent state: {start_at}")
        
        # Check all Next references
        for state_name, state_def in states.items():
            next_state = state_def.get("Next")
            if next_state and next_state not in states:
                self.errors.append(f"State '{state_name}' references non-existent Next state: {next_state}")
            
            # Check Choice state references
            if state_def.get("Type") == "Choice":
                choices = state_def.get("Choices", [])
                for i, choice in enumerate(choices):
                    choice_next = choice.get("Next")
                    if choice_next and choice_next not in states:
                        self.errors.append(f"Choice state '{state_name}' choice {i} references non-existent state: {choice_next}")
                
                default = state_def.get("Default")
                if default and default not in states:
                    self.errors.append(f"Choice state '{state_name}' Default references non-existent state: {default}")
            
            # Check Catch references
            catches = state_def.get("Catch", [])
            for i, catch in enumerate(catches):
                catch_next = catch.get("Next")
                if catch_next and catch_next not in states:
                    self.errors.append(f"State '{state_name}' catch {i} references non-existent state: {catch_next}")
    
    def _validate_state_definitions(self):
        """Validate individual state definitions"""
        states = self.definition.get("States", {})
        
        for state_name, state_def in states.items():
            # Validate state name
            if not self._is_valid_state_name(state_name):
                self.errors.append(f"Invalid state name: '{state_name}'. State names must be 1-128 characters and contain only letters, numbers, and specific symbols")
            
            # Validate Type field
            state_type = state_def.get("Type")
            if not state_type:
                self.errors.append(f"State '{state_name}' missing required Type field")
                continue
            
            valid_types = ["Pass", "Task", "Choice", "Wait", "Succeed", "Fail", "Parallel", "Map"]
            if state_type not in valid_types:
                self.errors.append(f"State '{state_name}' has invalid Type: {state_type}")
            
            # Type-specific validation
            self._validate_state_type_specific(state_name, state_def, state_type)
    
    def _validate_state_type_specific(self, state_name: str, state_def: dict, state_type: str):
        """Validate type-specific state requirements"""
        if state_type == "Task":
            if "Resource" not in state_def:
                self.errors.append(f"Task state '{state_name}' missing required Resource field")
        
        elif state_type == "Wait":
            wait_fields = ["Seconds", "Timestamp", "SecondsPath", "TimestampPath"]
            present_fields = [field for field in wait_fields if field in state_def]
            if len(present_fields) != 1:
                self.errors.append(f"Wait state '{state_name}' must have exactly one of: {', '.join(wait_fields)}")
        
        elif state_type == "Choice":
            if "Choices" not in state_def:
                self.errors.append(f"Choice state '{state_name}' missing required Choices field")
            elif not isinstance(state_def["Choices"], list) or len(state_def["Choices"]) == 0:
                self.errors.append(f"Choice state '{state_name}' must have non-empty Choices array")
            
            # Choice states cannot have Next or End
            if "Next" in state_def:
                self.errors.append(f"Choice state '{state_name}' cannot have Next field")
            if "End" in state_def:
                self.errors.append(f"Choice state '{state_name}' cannot have End field")
        
        elif state_type == "Fail":
            # Fail states should have Error and Cause
            if "Error" not in state_def:
                self.warnings.append(f"Fail state '{state_name}' should have Error field")
            if "Cause" not in state_def:
                self.warnings.append(f"Fail state '{state_name}' should have Cause field")
        
        elif state_type == "Parallel":
            if "Branches" not in state_def:
                self.errors.append(f"Parallel state '{state_name}' missing required Branches field")
            elif not isinstance(state_def["Branches"], list) or len(state_def["Branches"]) == 0:
                self.errors.append(f"Parallel state '{state_name}' must have non-empty Branches array")
        
        elif state_type == "Map":
            if "Iterator" not in state_def:
                self.errors.append(f"Map state '{state_name}' missing required Iterator field")
    
    def _validate_choice_rules(self):
        """Validate Choice state rules"""
        states = self.definition.get("States", {})
        
        for state_name, state_def in states.items():
            if state_def.get("Type") == "Choice":
                choices = state_def.get("Choices", [])
                for i, choice in enumerate(choices):
                    self._validate_single_choice_rule(state_name, i, choice)
    
    def _validate_single_choice_rule(self, state_name: str, choice_index: int, choice: dict):
        """Validate a single choice rule"""
        if "Variable" not in choice:
            self.errors.append(f"Choice state '{state_name}' choice {choice_index} missing Variable field")
            return
        
        variable = choice["Variable"]
        if not variable.startswith("$"):
            self.errors.append(f"Choice state '{state_name}' choice {choice_index} Variable must start with '$'")
        
        # Check for comparison operators
        comparison_operators = [
            "StringEquals", "StringGreaterThan", "StringGreaterThanEquals", "StringLessThan", "StringLessThanEquals", "StringMatches",
            "NumericEquals", "NumericGreaterThan", "NumericGreaterThanEquals", "NumericLessThan", "NumericLessThanEquals",
            "BooleanEquals", "TimestampEquals", "TimestampGreaterThan", "TimestampGreaterThanEquals", "TimestampLessThan", "TimestampLessThanEquals",
            "IsNull", "IsPresent", "IsNumeric", "IsString", "IsBoolean", "IsTimestamp"
        ]
        
        logical_operators = ["And", "Or", "Not"]
        
        has_comparison = any(op in choice for op in comparison_operators)
        has_logical = any(op in choice for op in logical_operators)
        
        if not has_comparison and not has_logical:
            self.errors.append(f"Choice state '{state_name}' choice {choice_index} must have a comparison or logical operator")
    
    def _validate_resource_arns(self):
        """Validate AWS resource ARN formats"""
        states = self.definition.get("States", {})
        
        for state_name, state_def in states.items():
            if state_def.get("Type") == "Task":
                resource = state_def.get("Resource", "")
                if resource and not self._is_valid_resource_arn(resource):
                    self.errors.append(f"Task state '{state_name}' has invalid Resource ARN format: {resource}")
    
    def _validate_paths(self):
        """Validate JSONPath expressions"""
        states = self.definition.get("States", {})
        
        path_fields = ["InputPath", "OutputPath", "ResultPath", "ItemsPath", "SecondsPath", "TimestampPath"]
        
        for state_name, state_def in states.items():
            for field in path_fields:
                if field in state_def:
                    path = state_def[field]
                    if path is not None and not self._is_valid_json_path(path):
                        self.errors.append(f"State '{state_name}' has invalid {field}: {path}")
    
    def _validate_timeouts(self):
        """Validate timeout values"""
        states = self.definition.get("States", {})
        
        for state_name, state_def in states.items():
            # TimeoutSeconds validation
            timeout = state_def.get("TimeoutSeconds")
            if timeout is not None:
                if not isinstance(timeout, int) or timeout <= 0:
                    self.errors.append(f"State '{state_name}' TimeoutSeconds must be a positive integer")
            
            # HeartbeatSeconds validation
            heartbeat = state_def.get("HeartbeatSeconds")
            if heartbeat is not None:
                if not isinstance(heartbeat, int) or heartbeat <= 0:
                    self.errors.append(f"State '{state_name}' HeartbeatSeconds must be a positive integer")
                
                # Heartbeat must be less than timeout
                if timeout is not None and heartbeat >= timeout:
                    self.errors.append(f"State '{state_name}' HeartbeatSeconds must be less than TimeoutSeconds")
    
    def _is_valid_state_name(self, name: str) -> bool:
        """Check if state name is valid"""
        if not name or len(name) > 128:
            return False
        
        # State names can contain letters, numbers, and specific symbols
        # but cannot contain control characters or certain special characters
        invalid_chars = set('<>{}[]?*"#%\\^|~`$&,;:/')
        return not any(char in invalid_chars for char in name)
    
    def _is_valid_resource_arn(self, resource: str) -> bool:
        """Check if resource ARN format is valid"""
        if not resource:
            return False
        
        # Basic ARN format: arn:partition:service:region:account:resource
        # Step Functions service integrations: arn:aws:states:::service:action
        arn_pattern = r'^arn:aws:states:::[\w\-]+:[\w\-]+(\.\w+)?$'
        return bool(re.match(arn_pattern, resource))
    
    def _is_valid_json_path(self, path: str) -> bool:
        """Check if JSONPath expression is valid"""
        if path is None:
            return True
        
        if not isinstance(path, str):
            return False
        
        # Basic JSONPath validation - must start with $ or be null
        return path == "$" or path.startswith("$.") or path == "null"