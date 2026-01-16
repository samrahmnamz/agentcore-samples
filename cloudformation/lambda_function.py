import json
import boto3
import os
from typing import Dict, Any

def lambda_handler(event, context):
    """Process memory events from SQS"""
    
    # Initialize clients
    s3 = boto3.client('s3')
    bedrock_control = boto3.client('bedrock-agentcore-control')
    
    processed_count = 0
    
    for record in event['Records']:
        try:
            # Parse SNS message from SQS
            sns_message = json.loads(record['body'])
            message_body = json.loads(sns_message['Message'])
            
            # Get S3 object details
            bucket = message_body['bucket']
            key = message_body['key']
            
            # Download and process the memory event
            response = s3.get_object(Bucket=bucket, Key=key)
            event_data = json.loads(response['Body'].read())
            
            # Extract user info from the event
            user_info = extract_user_info_from_event(event_data)
            
            if user_info:
                # Store in bedrock-agentcore memory
                store_user_info(bedrock_control, event_data, user_info)
                processed_count += 1
                
        except Exception as e:
            print(f"Error processing record: {str(e)}")
            continue
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed_count': processed_count,
            'total_records': len(event['Records'])
        })
    }

def extract_user_info_from_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract user info from memory event"""
    try:
        # Look for user info in the event metadata or content
        if 'metadata' in event_data and 'user_info' in event_data['metadata']:
            return event_data['metadata']['user_info']
        return None
    except Exception:
        return None

def store_user_info(bedrock_control, event_data: Dict[str, Any], user_info: Dict[str, Any]):
    """Store user info in bedrock-agentcore memory"""
    try:
        memory_id = event_data.get('memoryId')
        actor_id = event_data.get('actorId', 'default')
        
        if not memory_id:
            return
            
        # Store user info facts
        for key, value in user_info.items():
            if value:
                bedrock_control.put_memory_record(
                    memoryId=memory_id,
                    namespace=f"/users/{actor_id}/info",
                    recordId=key,
                    content=str(value),
                    metadata={
                        'type': 'user_info',
                        'field': key,
                        'extracted_at': event_data.get('timestamp')
                    }
                )
                
    except Exception as e:
        print(f"Error storing user info: {str(e)}")