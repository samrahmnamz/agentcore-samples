#!/usr/bin/env python3
"""
Update Lambda function code from lambda_function.py
"""
import os
import boto3
import zipfile
import io

REGION = os.getenv("AWS_REGION", "us-east-1")
STACK_NAME = "userinfoagent-memory-infrastructure-02"

def update_lambda_code():
    """Update Lambda function with code from lambda_function.py"""
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
        
        if not lambda_arn:
            print("Error: Could not find Lambda function ARN in stack outputs")
            return False
        
        function_name = lambda_arn.split(':')[-1]
        
        # Read lambda function code
        with open('lambda_function.py', 'r') as f:
            code_content = f.read()
        
        # Create zip file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('index.py', code_content)
        
        zip_buffer.seek(0)
        
        # Update Lambda function code
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_buffer.read()
        )
        
        print(f"Updated Lambda function {function_name} with new code")
        return True
        
    except FileNotFoundError:
        print("Error: lambda_function.py not found")
        return False
    except Exception as e:
        print(f"Error: Could not update Lambda function: {str(e)}")
        return False

if __name__ == "__main__":
    success = update_lambda_code()
    exit(0 if success else 1)