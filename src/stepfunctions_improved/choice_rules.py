# Copyright 2024 Improved Step Functions Framework

"""
Type-safe choice rules for Step Functions Choice states
"""

from abc import ABC, abstractmethod
from typing import Union, List


class ChoiceRule(ABC):
    """Abstract base class for all choice rules"""
    
    @abstractmethod
    def to_dict(self) -> dict:
        """Convert rule to Step Functions JSON format"""
        pass


class NumericRule(ChoiceRule):
    """Rule for numeric comparisons"""
    
    def __init__(self, variable: str, operator: str, value: Union[int, float]):
        self.variable = variable
        self.operator = operator
        self.value = value
        
        # Validate operator
        valid_operators = [
            "NumericEquals", "NumericGreaterThan", "NumericGreaterThanEquals",
            "NumericLessThan", "NumericLessThanEquals"
        ]
        if operator not in valid_operators:
            raise ValueError(f"Invalid numeric operator: {operator}")
    
    def to_dict(self) -> dict:
        return {
            "Variable": self.variable,
            self.operator: self.value
        }


class StringRule(ChoiceRule):
    """Rule for string comparisons"""
    
    def __init__(self, variable: str, operator: str, value: str):
        self.variable = variable
        self.operator = operator
        self.value = value
        
        # Validate operator
        valid_operators = [
            "StringEquals", "StringGreaterThan", "StringGreaterThanEquals",
            "StringLessThan", "StringLessThanEquals", "StringMatches"
        ]
        if operator not in valid_operators:
            raise ValueError(f"Invalid string operator: {operator}")
    
    def to_dict(self) -> dict:
        return {
            "Variable": self.variable,
            self.operator: self.value
        }


class BooleanRule(ChoiceRule):
    """Rule for boolean comparisons"""
    
    def __init__(self, variable: str, value: bool):
        self.variable = variable
        self.value = value
    
    def to_dict(self) -> dict:
        return {
            "Variable": self.variable,
            "BooleanEquals": self.value
        }


class TimestampRule(ChoiceRule):
    """Rule for timestamp comparisons"""
    
    def __init__(self, variable: str, operator: str, value: str):
        self.variable = variable
        self.operator = operator
        self.value = value
        
        # Validate operator
        valid_operators = [
            "TimestampEquals", "TimestampGreaterThan", "TimestampGreaterThanEquals",
            "TimestampLessThan", "TimestampLessThanEquals"
        ]
        if operator not in valid_operators:
            raise ValueError(f"Invalid timestamp operator: {operator}")
    
    def to_dict(self) -> dict:
        return {
            "Variable": self.variable,
            self.operator: self.value
        }


class AndRule(ChoiceRule):
    """Compound rule for AND logic"""
    
    def __init__(self, *rules: ChoiceRule):
        if len(rules) < 2:
            raise ValueError("AND rule requires at least 2 sub-rules")
        self.rules = rules
    
    def to_dict(self) -> dict:
        return {
            "And": [rule.to_dict() for rule in self.rules]
        }


class OrRule(ChoiceRule):
    """Compound rule for OR logic"""
    
    def __init__(self, *rules: ChoiceRule):
        if len(rules) < 2:
            raise ValueError("OR rule requires at least 2 sub-rules")
        self.rules = rules
    
    def to_dict(self) -> dict:
        return {
            "Or": [rule.to_dict() for rule in self.rules]
        }


class NotRule(ChoiceRule):
    """Compound rule for NOT logic"""
    
    def __init__(self, rule: ChoiceRule):
        self.rule = rule
    
    def to_dict(self) -> dict:
        return {
            "Not": self.rule.to_dict()
        }


# Convenience functions for better readability
def NumericEquals(variable: str, value: Union[int, float]) -> NumericRule:
    return NumericRule(variable, "NumericEquals", value)


def NumericGreaterThan(variable: str, value: Union[int, float]) -> NumericRule:
    return NumericRule(variable, "NumericGreaterThan", value)


def NumericGreaterThanEquals(variable: str, value: Union[int, float]) -> NumericRule:
    return NumericRule(variable, "NumericGreaterThanEquals", value)


def NumericLessThan(variable: str, value: Union[int, float]) -> NumericRule:
    return NumericRule(variable, "NumericLessThan", value)


def NumericLessThanEquals(variable: str, value: Union[int, float]) -> NumericRule:
    return NumericRule(variable, "NumericLessThanEquals", value)


def StringEquals(variable: str, value: str) -> StringRule:
    return StringRule(variable, "StringEquals", value)


def StringMatches(variable: str, pattern: str) -> StringRule:
    return StringRule(variable, "StringMatches", pattern)


def BooleanEquals(variable: str, value: bool) -> BooleanRule:
    return BooleanRule(variable, value)


def TimestampEquals(variable: str, value: str) -> TimestampRule:
    return TimestampRule(variable, "TimestampEquals", value)


def TimestampGreaterThan(variable: str, value: str) -> TimestampRule:
    return TimestampRule(variable, "TimestampGreaterThan", value)


def TimestampLessThan(variable: str, value: str) -> TimestampRule:
    return TimestampRule(variable, "TimestampLessThan", value)