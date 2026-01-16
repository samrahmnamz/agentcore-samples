#!/usr/bin/env python3
"""
Simple Lambda update - copy from local environment
"""
import os
import sys
import boto3
import zipfile
import io
import shutil
import tempfile
import time

REGION = os.getenv("AWS_REGION", "us-east-1")
STACK_NAME = "userinfoagent-memory-infrastructure-02"

def update_lambda_code(memory_id=None):
    """Update Lambda function with code and dependencies"""
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
        
        # Create temporary directory for building package
        with tempfile.TemporaryDirectory() as temp_dir:
            print("Copying dependencies from local environment...")
            
            # Copy bedrock_agentcore from local env
            local_site_packages = "/home/ubuntu/tiaa-agentcore/.env3/lib/python3.10/site-packages"
            
            # Copy required packages
            for pkg in ["bedrock_agentcore", "boto3", "botocore", "pydantic", "typing_extensions", 
                       "annotated_types", "pydantic_core", "s3transfer", "jmespath", "python_dateutil",
                       "urllib3", "six", "certifi", "charset_normalizer", "idna", "requests", "starlette",
                       "anyio", "sniffio", "typing_inspection"]:
                src = os.path.join(local_site_packages, pkg)
                if os.path.exists(src):
                    if os.path.isdir(src):
                        shutil.copytree(src, os.path.join(temp_dir, pkg))
                    else:
                        shutil.copy2(src, temp_dir)
                        
                # Also check for .py files
                src_py = os.path.join(local_site_packages, pkg + ".py")
                if os.path.exists(src_py):
                    shutil.copy2(src_py, temp_dir)
                        
            # Also copy .dist-info directories
            for item in os.listdir(local_site_packages):
                if item.endswith('.dist-info') and any(pkg in item for pkg in 
                    ["bedrock_agentcore", "boto3", "botocore", "pydantic", "typing_extensions", "starlette"]):
                    src = os.path.join(local_site_packages, item)
                    shutil.copytree(src, os.path.join(temp_dir, item))
            
            # Read lambda function code
            with open('lambda_function.py', 'r') as f:
                code_content = f.read()
            
            # Write lambda code to temp directory
            with open(os.path.join(temp_dir, 'index.py'), 'w') as f:
                f.write(code_content)
            
            # Create zip file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, temp_dir)
                        zip_file.write(file_path, arc_name)
            
            zip_buffer.seek(0)
            
            print(f"Updating Lambda function {function_name}...")
            
            # Update Lambda function code
            lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_buffer.read()
            )
            
            # Wait for code update to complete before updating configuration
            if memory_id:
                print("Waiting for code update to complete...")
                time.sleep(10)
            
            # Update environment variables if memory_id provided
            if memory_id:
                print(f"Updating environment variables with memory ID: {memory_id}")
                lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Environment={
                        'Variables': {
                            'AGENTCORE_MEMORY_ID': memory_id,
                            'MY_BEDROCK_MODEL_ID': 'anthropic.claude-3-haiku-20240307-v1:0'
                        }
                    }
                )
            
            print(f"Updated Lambda function {function_name} with new code and dependencies")
            return True
        
    except Exception as e:
        print(f"Error: Could not update Lambda function: {str(e)}")
        return False

if __name__ == "__main__":
    memory_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not memory_id:
        print("Usage: python update_lambda_simple.py <MEMORY_ID>")
        sys.exit(1)
    
    print(f"Using memory ID: {memory_id}")
    success = update_lambda_code(memory_id)
    exit(0 if success else 1)