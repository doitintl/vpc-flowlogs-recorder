import json
import boto3
import os
from botocore.exceptions import ClientError

dynamodb = boto3.client('dynamodb')
stepFunction = boto3.client('stepfunctions')

# This function is triggered via EventBridge when the NatGateway alarm changes state to "OK".
# It checks if the token is still define in DynamoDB for this Nat Gateway ID, and if it is
# it will send a Task Success to the State Machine via the token
def lambda_handler(event, context):
    tableName = os.getenv('TABLE_NAME');
    ngwid = event['detail']['configuration']['metrics'][1]['metricStat']['metric']['dimensions']['NatGatewayId']
    
    tokenID = getToken(tableName, ngwid)
    
    if (tokenID != None):
        # Call Step Function with success and tokenID
        print("Send Task Success to StepFunction")
        stepFunction.send_task_success(
            taskToken=tokenID,
            output=json.dumps({"status": "success"})
        )
    else:
        print("token was alreadyt removed")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Alarm Off')
    }


# Gets the step function token associated with a specific Nat Gateway ID
def getToken(tableName, ngwid):
    tokenID = None
    
    key = {'ngwid': {'S': ngwid}}
    
    try:
        response = dynamodb.get_item(TableName=tableName, Key=key)
        if 'Item' in response:
            if 'tokenID' in response['Item']:
                tokenID = response['Item']['tokenID']['S']
    except ClientError as err:
        print("Failed to get item from dyanmoDB with error: ", err.response["Error"]["Message"])

    return tokenID
