#!/usr/bin/env python3
"""
Check what's stored in the memory
"""
import os
import sys
import boto3
from datetime import datetime

REGION = os.getenv("AWS_REGION", "us-east-1")

def check_memory_records(memory_id, actor_id="user"):
    """Check what records are stored in memory"""
    try:
        client = boto3.client("bedrock-agentcore", region_name=REGION)
        
        print(f"Checking memory: {memory_id}")
        
        # Try different namespace approaches
        namespaces_to_try = [
            f"/users/{actor_id}/info" if actor_id else None,
            "/users",
            "/"
        ]
        
        total_records = 0
        for namespace in namespaces_to_try:
            if namespace is None:
                continue
                
            try:
                print(f"Searching namespace: {namespace}")
                response = client.list_memory_records(
                    memoryId=memory_id,
                    namespace=namespace
                )
                
                records = response.get('memoryRecords', [])
                print(f"Found {len(records)} records in {namespace}")
                
                for i, record in enumerate(records, 1):
                    print(f"\nRecord {total_records + i}:")
                    print(f"  ID: {record.get('id', 'N/A')}")
                    print(f"  Content: {record.get('content', {})}")
                    print(f"  Namespaces: {record.get('namespaces', [])}")
                    print(f"  Timestamp: {record.get('timestamp', 'N/A')}")
                    
                total_records += len(records)
                
            except Exception as e:
                print(f"Error searching {namespace}: {str(e)}")
                continue
                
        return total_records
        
    except Exception as e:
        print(f"Error checking memory records: {str(e)}")
        return 0

if __name__ == "__main__":
    memory_id = sys.argv[1] if len(sys.argv) > 1 else "UserInfoSelfManagedMemory-Vi7ki5GF4T"
    actor_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    count = check_memory_records(memory_id, actor_id)
    print(f"\nTotal records: {count}")