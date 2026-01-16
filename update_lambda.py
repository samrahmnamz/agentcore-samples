#!/usr/bin/env python3
"""
Update Lambda function environment variables with memory ID
"""
import os
import boto3
import sys

REGION = os.getenv("AWS_REGION", "us-east-1")
STACK_NAME = "userinfoagent-memory-infrastructure"

def update_lambda_memory_id(memory_id):
    """Update Lambda function environment variable with memory ID"""
    try:
        # Get Lambda function name from CloudFormation
        cf = boto3.client("cloudformation", region_name=REGION)
        lambda_client = boto3.client("lambda", region_name=REGION)
        
        # Get stack outputs
        response = cf.describe_stacks(StackName=STACK_NAME)
        outputs = response['Stacks'][0]['Outputs']
        
        # Find Lambda function ARN
        lambda_arn = None
        for output in outputs:
            if output['OutputKey'] == 'LambdaFunctionArn':
                lambda_arn = output['OutputValue']
                break
        
        if lambda_arn:
            function_name = lambda_arn.split(':')[-1]
            
            # Update environment variables
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Environment={
                    'Variables': {
                        'AGENTCORE_MEMORY_ID': memory_id,
                        'MY_BEDROCK_MODEL_ID': 'anthropic.claude-3-haiku-20240307-v1:0'
                    }
                }
            )
            print(f"Updated Lambda function {function_name} with memory ID: {memory_id}")
        else:
            print("Error: Could not find Lambda function ARN in stack outputs")
            return False
            
    except Exception as e:
        print(f"Error: Could not update Lambda function: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_lambda.py <memory_id>")
        sys.exit(1)
    
    memory_id = sys.argv[1]
    success = update_lambda_memory_id(memory_id)
    sys.exit(0 if success else 1)