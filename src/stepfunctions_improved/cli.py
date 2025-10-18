#!/usr/bin/env python3
"""
Command-line interface for Improved Step Functions Framework
"""

import json
import sys
from pathlib import Path
from typing import Optional

try:
    import click
    from dynaconf import Dynaconf
except ImportError:
    print("CLI dependencies not installed. Run: pip install click")
    sys.exit(1)

from .config import setup_config
from .validation import StateMachineValidator
from .simulation import StateMachineSimulator


@click.group()
@click.version_option(version="1.0.0")
def main():
    """Improved Step Functions Framework CLI"""
    pass


@main.command()
@click.argument('definition_file', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def validate(definition_file: str, verbose: bool):
    """Validate a Step Functions state machine definition"""
    
    try:
        with open(definition_file, 'r') as f:
            definition = json.load(f)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON in {definition_file}: {e}", err=True)
        sys.exit(1)
    
    validator = StateMachineValidator(definition)
    is_valid = validator.validate()
    
    if is_valid:
        click.echo(f"✅ {definition_file} is valid")
    else:
        click.echo(f"❌ {definition_file} has validation errors:")
        for error in validator.get_errors():
            click.echo(f"  • {error}")
        sys.exit(1)
    
    warnings = validator.get_warnings()
    if warnings and verbose:
        click.echo("⚠️  Warnings:")
        for warning in warnings:
            click.echo(f"  • {warning}")


@main.command()
@click.argument('definition_file', type=click.Path(exists=True))
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--mocks', '-m', type=click.Path(exists=True), help='JSON file with mock responses')
@click.option('--output', '-o', type=click.Path(), help='Output file for results')
def simulate(definition_file: str, input_file: str, mocks: Optional[str], output: Optional[str]):
    """Simulate execution of a Step Functions state machine"""
    
    try:
        with open(definition_file, 'r') as f:
            definition = json.load(f)
        
        with open(input_file, 'r') as f:
            input_data = json.load(f)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON: {e}", err=True)
        sys.exit(1)
    
    simulator = StateMachineSimulator(definition)
    
    # Load mock responses if provided
    if mocks:
        try:
            with open(mocks, 'r') as f:
                mock_responses = json.load(f)
            for state_name, response in mock_responses.items():
                simulator.add_mock_response(state_name, response)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON in mocks file: {e}", err=True)
            sys.exit(1)
    
    # Run simulation
    result = simulator.simulate_execution(input_data)
    
    # Format output
    output_data = {
        "status": result.status.value,
        "output": result.output,
        "error": result.error,
        "execution_trace": result.execution_trace
    }
    
    if output:
        with open(output, 'w') as f:
            json.dump(output_data, f, indent=2)
        click.echo(f"Results written to {output}")
    else:
        click.echo(json.dumps(output_data, indent=2))


@main.command()
@click.option('--env', '-e', help='Environment to show config for')
def config(env: Optional[str]):
    """Show current configuration"""
    
    config_obj = setup_config()
    
    if env:
        config_obj.setenv(env)
    
    click.echo(f"Current environment: {config_obj.current_env}")
    click.echo(f"AWS region: {config_obj.get('aws_region', 'not set')}")
    
    # Show some key configuration values
    sections = ['lambda', 'sagemaker', 'step_functions']
    for section in sections:
        section_config = config_obj.get(section, {})
        if section_config:
            click.echo(f"\n{section.upper()} Configuration:")
            for key, value in section_config.items():
                if isinstance(value, dict):
                    click.echo(f"  {key}: {len(value)} items")
                else:
                    click.echo(f"  {key}: {value}")


@main.command()
@click.argument('pipeline_name')
@click.option('--env', '-e', default='development', help='Environment to generate for')
@click.option('--output', '-o', type=click.Path(), help='Output file for pipeline definition')
def generate(pipeline_name: str, env: str, output: Optional[str]):
    """Generate a pipeline definition from factory"""
    
    config_obj = setup_config()
    config_obj.setenv(env)
    
    try:
        from .workflow import PipelineFactory
        
        factory = PipelineFactory(config_obj)
        
        if pipeline_name == "ml-training":
            definition = factory.create_ml_training_pipeline()
        elif pipeline_name == "data-processing":
            definition = factory.create_data_processing_pipeline()
        elif pipeline_name == "notification":
            definition = factory.create_notification_pipeline()
        else:
            click.echo(f"Unknown pipeline type: {pipeline_name}", err=True)
            click.echo("Available types: ml-training, data-processing, notification")
            sys.exit(1)
        
        if output:
            with open(output, 'w') as f:
                json.dump(definition, f, indent=2)
            click.echo(f"Pipeline definition written to {output}")
        else:
            click.echo(json.dumps(definition, indent=2))
    
    except Exception as e:
        click.echo(f"Error generating pipeline: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('definition_file', type=click.Path(exists=True))
@click.option('--env', '-e', default='development', help='Environment to deploy to')
@click.option('--name', '-n', help='Override state machine name')
def deploy(definition_file: str, env: str, name: Optional[str]):
    """Deploy a state machine to AWS Step Functions"""
    
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
    except ImportError:
        click.echo("AWS dependencies not available. Run: pip install boto3", err=True)
        sys.exit(1)
    
    config_obj = setup_config()
    config_obj.setenv(env)
    
    try:
        with open(definition_file, 'r') as f:
            definition = json.load(f)
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON in {definition_file}: {e}", err=True)
        sys.exit(1)
    
    # Validate first
    validator = StateMachineValidator(definition)
    if not validator.validate():
        click.echo("❌ Definition is not valid. Fix errors first:", err=True)
        for error in validator.get_errors():
            click.echo(f"  • {error}", err=True)
        sys.exit(1)
    
    # Get configuration
    execution_role = config_obj.get('step_functions.execution_role')
    if not execution_role:
        click.echo("Error: step_functions.execution_role not configured", err=True)
        sys.exit(1)
    
    region = config_obj.get('aws_region', 'us-east-1')
    state_machine_name = name or f"{env}-{Path(definition_file).stem}"
    
    try:
        client = boto3.client('stepfunctions', region_name=region)
        
        # Try to create state machine
        response = client.create_state_machine(
            name=state_machine_name,
            definition=json.dumps(definition),
            roleArn=execution_role,
            tags=[
                {"key": "Environment", "value": env},
                {"key": "DeployedBy", "value": "stepfunctions-improved-cli"}
            ]
        )
        
        click.echo(f"✅ State machine created: {response['stateMachineArn']}")
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'StateMachineAlreadyExists':
            # Try to update existing state machine
            try:
                # Find existing state machine
                paginator = client.get_paginator('list_state_machines')
                for page in paginator.paginate():
                    for sm in page['stateMachines']:
                        if sm['name'] == state_machine_name:
                            client.update_state_machine(
                                stateMachineArn=sm['stateMachineArn'],
                                definition=json.dumps(definition),
                                roleArn=execution_role
                            )
                            click.echo(f"✅ State machine updated: {sm['stateMachineArn']}")
                            return
                
                click.echo(f"Error: Could not find existing state machine: {state_machine_name}", err=True)
                sys.exit(1)
            
            except ClientError as update_error:
                click.echo(f"Error updating state machine: {update_error}", err=True)
                sys.exit(1)
        else:
            click.echo(f"Error creating state machine: {e}", err=True)
            sys.exit(1)
    
    except NoCredentialsError:
        click.echo("Error: AWS credentials not configured", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()