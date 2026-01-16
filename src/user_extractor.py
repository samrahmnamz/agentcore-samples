from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import boto3


class UserInfo(BaseModel):
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    ssn: Optional[str] = None


class UserInfoMemoryExtractor:
    def __init__(self):
        self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.user_info = UserInfo()
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract user info using Bedrock LLM"""
        if not text.strip():
            return {"user_info": self.user_info.model_dump()}
            
        prompt = f"""Extract user information from this text. Return only a JSON object with firstname, lastname, and ssn fields.
If information is not found, use null for that field.

Text: {text}

JSON:"""
        
        try:
            response = self.bedrock_client.invoke_model(
                modelId="anthropic.claude-3-haiku-20240307-v1:0",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 200,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            content = result['content'][0]['text']
            
            user_data = json.loads(content)
            extracted_info = UserInfo(**user_data)
            
            # Update stored info
            if extracted_info.firstname:
                self.user_info.firstname = extracted_info.firstname
            if extracted_info.lastname:
                self.user_info.lastname = extracted_info.lastname
            if extracted_info.ssn:
                self.user_info.ssn = extracted_info.ssn
            
            return {"user_info": self.user_info.model_dump()}
        except Exception as e:
            return {"user_info": self.user_info.model_dump(), "error": str(e)}