import json

# This function converts the value passed in 'Value' to an Integer
# This is because Parameters in CloudFormation, are converted to Strings even if defined as Number
# Sum properties (e.g. HeartbeatSeconds in a Step Function Task) can't handle strings
def lambda_handler(event, context):
    # Print for debug
    print(event)

    # Return the modified template
    return {
        'requestId': event['requestId'],
        'status': "success",
        # Convert to Integer
        "fragment": int(event['params']['Value'])
    }