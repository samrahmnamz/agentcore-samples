#!/usr/bin/env python3
"""
Check what's stored in the memory
"""
import os
import sys
import boto3

REGION = os.getenv("AWS_REGION", "us-east-1")

def check_memory_records(memory_id):
    """Check what records are stored in memory"""
    client = boto3.client("bedrock-agentcore", region_name=REGION)
    
    print(f"Checking memory: {memory_id}")
    print("\nReading memory records...")
    
    response = client.list_memory_records(memoryId=memory_id, namespace="/")
    
    records = response.get("memoryRecordSummaries", [])
    print(f"Found {len(records)} total records:")
    
    for record in records:
        content = record.get("content", {})
        timestamp = record.get("timestamp", "")
        print(f"  - {content.get('text', 'N/A')} (created: {timestamp[:19] if timestamp else 'N/A'})")
    
    return len(records)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_memory.py <memory-id>")
        sys.exit(1)
    
    memory_id = sys.argv[1]
    count = check_memory_records(memory_id)
    print(f"\nTotal records: {count}")