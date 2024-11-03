import json

# A template to generate Dual Metric CloudWatch Alarms for Nat Gateways
NatGatewayDualMetricTemplate = """{
    "Type": "AWS::CloudWatch::Alarm",
    "Properties": {
        "AlarmName": "NAME",
        "AlarmDescription": "Alarm to trigger VPC Flow Logs on a Nat Gateway",
        "ActionsEnabled": false,
        "OKActions": [],
        "AlarmActions": [],
        "InsufficientDataActions": [],
        "Dimensions": [],
        "EvaluationPeriods": 3,
        "DatapointsToAlarm": 1,
        "Threshold": 1,
        "ComparisonOperator": "GreaterThanOrEqualToThreshold",
        "TreatMissingData": "missing",
        "Metrics": [
            {
                "Id": "e1",
                "Label": "Bytes From Source or Destination above threshold",
                "ReturnData": true,
                "Expression": "IF(m1 > {}, 1, 0) + IF(m2 > {},1, 0)"
            },
            {
                "Id": "m1",
                "ReturnData": false,
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/NATGateway",
                        "MetricName": "BytesInFromSource",
                        "Dimensions": [
                            {
                                "Name": "NatGatewayId",
                                "Value": "natgateway-id"
                            }
                        ]
                    },
                    "Period": 60,
                    "Stat": "Sum"
                }
            },
            {
                "Id": "m2",
                "ReturnData": false,
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/NATGateway",
                        "MetricName": "BytesInFromDestination",
                        "Dimensions": [
                            {
                                "Name": "NatGatewayId",
                                "Value": "natgateway-id"
                            }
                        ]
                    },
                    "Period": 60,
                    "Stat": "Sum"
                }
            }
        ]
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
      NatGatewayAlarm = BuildDualMetricAlarm(SamplingPeriod, EvaluationPeriods, DatapointsToAlarm, Threshold)
      ResourceName = f"NATGatewayAlarm{i + 1}"

      # Add the new resource to the resource array
      Resources[ResourceName] = NatGatewayAlarm

    # Return the modified template
    return {
        'requestId': event['requestId'],
        'status': "success",
        "fragment": fragment
    }

# Load and initialize an alarm with a two metrics
def BuildDualMetricAlarm(nat_id, SamplingPeriod, EvaluationPeriods, DatapointsToAlarm, Threshold):
      NatGatewayAlarm = json.loads(NatGatewaySingleMetricTemplate)
      NatGatewayAlarm['Properties']['AlarmName'] = f"NatGateway Alarm for: {nat_id}"
      NatGatewayAlarm['Properties']['Dimensions'][0]['Value'] = nat_id
      NatGatewayAlarm['Properties']['Period'] = int(SamplingPeriod)
      NatGatewayAlarm['Properties']['EvaluationPeriods'] = int(EvaluationPeriods)
      NatGatewayAlarm['Properties']['DatapointsToAlarm'] = int(DatapointsToAlarm)
      NatGatewayAlarm['Properties']['Threshold'] = int(Threshold)

      # Update the Value for Nat ID in the "m1" and "m2" elements
      NatGatewayAlarm['Properties']['Metrics'][1]['MetricStat']['Metric']['Dimensions'][0]['Value'] = nat_id
      NatGatewayAlarm['Properties']['Metrics'][2]['MetricStat']['Metric']['Dimensions'][0]['Value'] = nat_id

      # Update the Sampling Period for Nat ID in the "m1" and "m2" elements
      NatGatewayAlarm['Properties']['Metrics'][1]['MetricStat']['Period'] = int(SamplingPeriod)
      NatGatewayAlarm['Properties']['Metrics'][2]['MetricStat']['Period'] = int(SamplingPeriod)

      # Update the Threshold value in "Expression" for the "e1" element (the alarm's condition)
      NatGatewayAlarm['Properties']['Metrics'][0]['Expression'] = f"IF(m1 > {Threshold}, 1, 0) + IF(m2 > {Threshold}, 1, 0)"

      return NatGatewayAlarm  