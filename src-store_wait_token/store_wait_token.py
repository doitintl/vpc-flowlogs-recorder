import os
import boto3

# Initialize the EC2 client
region = os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION')
# Initialize the dynamoDB Client
dynamoDBClient = boto3.client('dynamodb', region_name=region)

def lambda_handler(event, context):
    print (event)

    nat_gateway_id = event['ngwid']
    token = event['token']
    tableName = event['TableName']


    try:
        response = dynamoDBClient.update_item(
            TableName=tableName,
            Key={
                'ngwid': {'S': nat_gateway_id}
            },
            UpdateExpression='SET #t = :val1',
            ExpressionAttributeNames={
                '#t': 'tokenID'
            },
            ExpressionAttributeValues={
                ':val1': {'S': token}
            }
        )
        print("Successfully updated DynamoDB item with token.")
    except Exception as e:
        print("Failed to update DynamoDB item with", str(e))

    return {
        'statusCode': 200,
        'body': ""
    } 