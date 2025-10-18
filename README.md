# Improved AWS Step Functions Framework

A modern, type-safe, and configuration-driven framework for building AWS Step Functions workflows with enhanced developer experience.

## Features

### 🎯 **Type Safety & Modern Python**
- Strong typing with dataclasses and type hints
- Runtime validation with clear error messages
- IDE support with autocomplete and type checking

### ⚙️ **Configuration Management with Dynaconf**
- Environment-specific configurations (dev/staging/prod)
- Secure secret management
- Resource name resolution per environment
- Feature flags and environment-specific behavior

### 🏗️ **Fluent Builder Pattern**
- Intuitive, chainable API for building state machines
- Built-in AWS service integrations
- Automatic error handling and retry configuration

### ✅ **Validation & Testing**
- Comprehensive state machine validation
- Built-in simulation for testing workflows
- Mock support for unit testing

### 🔧 **Enhanced Error Handling**
- Predefined retry patterns for AWS services
- Type-safe error configuration
- Automatic catch block generation

## Quick Start

### Installation

```bash
pip install stepfunctions-improved
```

### Basic Usage

```python
from stepfunctions_improved import (
    StepFunctionBuilder, ConfigurableWorkflow, 
    setup_config, NumericGreaterThan
)

# Setup configuration
config = setup_config()

# Create a simple workflow
def create_ml_pipeline(config):
    builder = StepFunctionBuilder("MLPipeline")
    
    return (builder
        .start_with("PreprocessData")
        .add_lambda_task("PreprocessData", "preprocess-function")
        .add_lambda_task("TrainModel", "training-function")
        .add_choice("EvaluateResults")
            .when(NumericGreaterThan("$.accuracy", 0.9), "DeployModel")
            .otherwise("NotifyFailure")
        .add_lambda_task("DeployModel", "deploy-function")
        .end_with_success("Success")
        .build())

# Create and deploy workflow
workflow = ConfigurableWorkflow("MLPipeline", create_ml_pipeline)

# Deploy to different environments
config.setenv("development")
dev_arn = workflow.deploy_to_environment(config)

config.setenv("production") 
prod_arn = workflow.deploy_to_environment(config)
```

### Configuration-Driven Workflows

Create `config/settings.toml`:

```toml
[development]
aws_region = "us-west-2"
auto_deploy = true

[development.functions]
preprocess_data = "dev-preprocess-function"
train_model = "dev-train-function"
deploy_model = "dev-deploy-function"

[development.lambda]
timeout = 30
memory_size = 256

[production]
aws_region = "us-east-1"
auto_deploy = false

[production.functions]
preprocess_data = "prod-preprocess-function"
train_model = "prod-train-function"
deploy_model = "prod-deploy-function"

[production.lambda]
timeout = 120
memory_size = 1024
```

Use configuration in your workflows:

```python
from stepfunctions_improved import ConfigurableStepFunctionBuilder

def create_configurable_pipeline(config):
    builder = ConfigurableStepFunctionBuilder("Pipeline", config)
    
    return (builder
        .start_with("Process")
        .add_lambda_task("Process", "preprocess_data")  # Resolves to env-specific function
        .add_sagemaker_training("Train", {
            "job_name": "training-job-${aws:executionId}",
            # Uses config defaults for instance type, volume size, etc.
        })
        .end_with_success()
        .build())
```

## Advanced Features

### AWS Service Integrations

```python
from stepfunctions_improved import AWSServiceIntegrations

# Pre-built service integrations
lambda_task = AWSServiceIntegrations.lambda_invoke("my-function")
training_job = AWSServiceIntegrations.sagemaker_training_job(...)
batch_job = AWSServiceIntegrations.batch_submit_job(...)
```

### Complex Choice Rules

```python
from stepfunctions_improved import NumericGreaterThan, AndRule, OrRule

choice_builder.when(
    AndRule(
        NumericGreaterThan("$.accuracy", 0.9),
        NumericGreaterThan("$.precision", 0.85)
    ),
    "DeployToProduction"
).when(
    OrRule(
        NumericGreaterThan("$.accuracy", 0.7),
        StringEquals("$.environment", "staging")
    ),
    "DeployToStaging"
).otherwise("RejectDeployment")
```

### Error Handling

```python
from stepfunctions_improved import RetryConfig, CatchConfig, ErrorHandling

# Use predefined retry patterns
builder.add_lambda_task("ProcessData", "function-name",
    retry_config=[ErrorHandling.LAMBDA_RETRY],
    catch_config=[ErrorHandling.catch_all_to_failure("HandleError")])

# Custom retry configuration
custom_retry = RetryConfig(
    error_equals=["States.TaskFailed"],
    interval_seconds=5,
    max_attempts=3,
    backoff_rate=2.0
)
```

### Validation and Testing

```python
from stepfunctions_improved import StateMachineValidator, StateMachineSimulator

# Validate state machine
validator = StateMachineValidator(pipeline_definition)
if not validator.validate():
    print("Errors:", validator.get_errors())

# Simulate execution
simulator = StateMachineSimulator(pipeline_definition)
simulator.add_mock_response("ProcessData", {"result": "success"})
result = simulator.simulate_execution({"input": "test"})
print(f"Status: {result.status}, Output: {result.output}")
```

## Pipeline Factories

Use built-in factories for common patterns:

```python
from stepfunctions_improved import PipelineFactory

factory = PipelineFactory(config)

# Create ML training pipeline
ml_pipeline = factory.create_ml_training_pipeline()

# Create data processing pipeline
data_pipeline = factory.create_data_processing_pipeline()

# Create notification pipeline
notification_pipeline = factory.create_notification_pipeline()
```

## Environment Management

```python
# Switch environments dynamically
config.setenv("development")
dev_definition = workflow.create_for_environment(config)

config.setenv("production")
prod_definition = workflow.create_for_environment(config)

# Deploy to specific environment
arn = workflow.deploy_to_environment(config)

# Execute workflow
execution = workflow.execute(config, input_data={"key": "value"})
```

## Examples

See the `examples/` directory for comprehensive examples:

- `ml_pipeline_example.py` - Machine learning training pipeline
- `data_pipeline_example.py` - ETL and data processing pipelines  
- `testing_example.py` - Validation and simulation examples

## Configuration

The framework uses Dynaconf for configuration management. Configuration files are automatically loaded from:

- `settings.toml` - Main configuration
- `.secrets.toml` - Sensitive configuration (not committed to git)
- `config/settings.toml` - Alternative location
- Environment variables with `STEPFUNCTIONS_` prefix

### Configuration Structure

```toml
[default]
aws_region = "us-east-1"

[default.step_functions]
execution_role = "arn:aws:iam::123456789012:role/StepFunctionsRole"

[default.lambda]
timeout = 60
retry_attempts = 3

[environment_name]
# Environment-specific overrides

[environment_name.functions]
function_logical_name = "actual-function-name"

[environment_name.dynamodb.tables]
table_logical_name = "actual-table-name"

[environment_name.sns.topics]
topic_logical_name = "arn:aws:sns:region:account:topic-name"
```

## Comparison with Amazon's SDK

| Feature | Amazon SDK | Improved Framework |
|---------|------------|-------------------|
| Type Safety | ❌ Runtime errors | ✅ Compile-time checking |
| Configuration | ❌ Hardcoded values | ✅ Environment-aware config |
| Error Handling | ⚠️ Manual setup | ✅ Built-in patterns |
| Testing | ❌ Limited support | ✅ Simulation & validation |
| Builder Pattern | ❌ Verbose construction | ✅ Fluent API |
| AWS Integrations | ⚠️ Manual ARN construction | ✅ Pre-built integrations |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite: `pytest`
6. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Requirements

- Python 3.8+
- AWS credentials configured
- boto3
- dynaconf

## Roadmap

- [ ] Visual workflow designer
- [ ] CloudFormation template generation
- [ ] Integration with AWS CDK
- [ ] Performance monitoring and metrics
- [ ] Workflow versioning and rollback
- [ ] Advanced debugging tools