from flask import Flask, request, jsonify
import configparser
import boto3
import json
import os

app = Flask(__name__)

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join("sample.ini")))
# print(config['default']['aws_access_key_id'])
# print(config['default']['aws_secret_access_key'])
# AWS Bedrock runtime client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-west-2',  # Change if needed
    aws_access_key_id=config['default']['aws_access_key_id'],
    aws_secret_access_key=config['default']['aws_secret_access_key']
    
    
)

# Prompt template builder
def build_prompt(data):
    return f"""
You are a cybersecurity and fraud analysis expert AI. 

Based on the following transaction metadata, analyze and return a single JSON object with a risk score between 0 (no risk) and 1 (very high risk).

Use your understanding of common fraud patterns (like high amounts, suspicious IPs, failed logins, unfamiliar devices or locations).

Respond in this format: {{"risk_score": float}}

Transaction metadata:
Amount: {data['amount']}
Location (State): {data['location']}
IP Address: {data['ip']}
Device Type: {data['device_type']}
Login Attempt: {data['login_attempt']}
"""

@app.route("/risk-score", methods=["GET","POST"])
def risk_score():
    try:
        # input_data = request.get_json()

        input_data = {
            "amount": 4800,
            "location": "Uttar Pradesh",
            "ip": "192.168.2.35",
            "device_type": "Android",
            "login_attempt": "Failure"
            }

        # Validate input fields
        required_fields = ['amount', 'location', 'ip', 'device_type', 'login_attempt']
        for field in required_fields:
            if field not in input_data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # Build prompt
        prompt = build_prompt(input_data)

        # Claude 3 Sonnet request
        response = bedrock.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "temperature": 0.2,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            })
        )

        # Parse response
        model_response = json.loads(response['body'].read().decode())
        assistant_msg = model_response['content'][0]['text'].strip()

        # Parse JSON result from Claude
        risk_result = json.loads(assistant_msg)
        return jsonify(risk_result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
