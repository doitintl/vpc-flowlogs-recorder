import os
import boto3

# Initialize the EC2 client
region = os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION')
client = boto3.client('ec2', region_name=region)

def lambda_handler(event, context):
    FlowLogIds = event['FlowLogIds']
    
    client.delete_flow_logs(
        FlowLogIds=FlowLogIds
    )
    
    return {
        'statusCode': 200,
        'body': f'VPC Flow Logs {FlowLogIds} have been deleted'
    }
