import json

# A template to generate CloudWatch Alarms for Nat Gateways
NatGatewayTemplate = """{
    "Type": "AWS::CloudWatch::Alarm",
    "Properties": {
      "AlarmName": "NAME",
      "ActionsEnabled": "false",
      "MetricName": "BytesInFromDestination",
      "Namespace": "AWS/NATGateway",
      "Statistic": "Sum",
      "Dimensions": [
        {
          "Name": "NatGatewayId",
          "Value": "natgateway-id"
        }
      ],
      "Period": 60,
      "EvaluationPeriods": 3,
      "DatapointsToAlarm": 1,
      "Threshold": 100000,
      "ComparisonOperator": "GreaterThanThreshold",
      "TreatMissingData": "missing"
    }
}"""

def lambda_handler(event, context):
    # Print for debug
    print(event)
    
    fragment = event['fragment']
    Resources = fragment['Resources']
    params = event['templateParameterValues']

    # Extract the parameters
    NatGatewayIDs = params['NatGatewayIDs']
    SamplingPeriod = params['SamplingPeriod']
    EvaluationPeriods = params['EvaluationPeriods']
    Threshold = params['Threshold']
    DatapointsToAlarm = params['DatapointsToAlarm']
    
    # Split the comma-separated list into an array
    nat_gateway_ids_list = NatGatewayIDs.split(',')
    
    # Iterate over the array
    # - Use the template to generate a new resource
    # - Update the values with the parameters
    # - Add new resource to array
    for i, nat_id in enumerate(nat_gateway_ids_list):
      ResourceName = f"NATGatewayAlarm{i + 1}"
      NatGatewayAlarm = json.loads(NatGatewayTemplate)
      NatGatewayAlarm['Properties']['AlarmName'] = f"NatGateway Alarm for: {nat_id}"
      NatGatewayAlarm['Properties']['Dimensions'][0]['Value'] = nat_id
      NatGatewayAlarm['Properties']['Period'] = int(SamplingPeriod)
      NatGatewayAlarm['Properties']['EvaluationPeriods'] = int(EvaluationPeriods)
      NatGatewayAlarm['Properties']['DatapointsToAlarm'] = int(DatapointsToAlarm)
      NatGatewayAlarm['Properties']['Threshold'] = int(Threshold)
      # Add the new resource to the resource array
      Resources[ResourceName] = NatGatewayAlarm

    # Return the modified template
    return {
        'requestId': event['requestId'],
        'status': "success",
        "fragment": fragment
    }