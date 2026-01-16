#!/bin/bash

STACK_NAME="userinfoagent-memory-infrastructure-02"
REGION="us-east-1"

echo "Deploying CloudFormation stack: $STACK_NAME"

# Use placeholder if MEMORY_ID not set
MEMORY_ID_PARAM=${MEMORY_ID:-"placeholder"}

# Check if MEMORY_EXEC_ROLE_ARN is set
if [ -z "$MEMORY_EXEC_ROLE_ARN" ]; then
    echo "Error: MEMORY_EXEC_ROLE_ARN environment variable is required"
    echo "Create the role manually first, then set: export MEMORY_EXEC_ROLE_ARN=arn:aws:iam::account:role/role-name"
    exit 1
fi

aws cloudformation deploy \
  --template-file template.yaml \
  --stack-name $STACK_NAME \
  --region $REGION \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides MemoryId=$MEMORY_ID_PARAM MemoryExecutionRoleArn=$MEMORY_EXEC_ROLE_ARN

if [ $? -eq 0 ]; then
    echo "Stack deployed successfully!"
    
    # Get outputs
    echo "Getting stack outputs..."
    BUCKET=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`MemoryEventsBucket`].OutputValue' --output text)
    TOPIC_ARN=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`MemoryEventsTopicArn`].OutputValue' --output text)
    LAMBDA_ARN=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionArn`].OutputValue' --output text)
    
    echo ""
    echo "Infrastructure deployed:"
    echo "S3 Bucket: $BUCKET"
    echo "SNS Topic: $TOPIC_ARN"
    echo "Lambda Function: $LAMBDA_ARN"
    echo ""
    echo "Set these environment variables:"
    echo "export MEMORY_EVENTS_BUCKET=$BUCKET"
    echo "export MEMORY_EVENTS_TOPIC_ARN=$TOPIC_ARN"
    echo ""
    echo "Then run: python create_memory.py"
else
    echo "Stack deployment failed!"
    exit 1
fi