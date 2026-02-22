import boto3
import json

class BedrockEngine:
    def __init__(self, region="us-east-1"):
        self.client = boto3.client("bedrock-runtime", region_name=region)
        # We use Claude 3 Haiku for speed/cost, or Sonnet for reasoning
        self.model_id = "anthropic.claude-3-haiku-20240307-v1:0" 

    def generate(self, prompt: str):
        """
        Sends a prompt to AWS Bedrock and returns the text response.
        """
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=body
            )
            response_body = json.loads(response.get("body").read())
            return response_body["content"][0]["text"]
        except Exception as e:
            print(f"AWS Error: {e}")
            return "Error calling Bedrock"