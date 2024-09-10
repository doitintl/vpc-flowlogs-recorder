Uses AWS SAM to create a serverless solution for automatically creating FPC Flow Logs for Nat Gateways.

A prerequisit is to create an Alarm for Nat Gateway, usually for BytesInFromDestination that will be set to ALARM if the volume of the data is greater than a certain threshold.

In this case an Event Rule would catch it and trigger a Step Function state machine.
The State Machine will first check if a DynamoDB table contains an entry with the Nat Gateway ID.
If it does, then the State Machine will exit.

If no such entry is found:
* Create a new item in the DynamoDB Table with the key equals to the Nat Gateway ID
* Call a Lambda function to create a VPC Flow log on all the ENIs belonging to the Nat Gateway
* Wait 15 minutes
* Delete the previously creatsed VPC Flow logs



This removes the need to leave the VPC Flow log running all the time, and instead it will be created only when there is a traffic spike.


The CloudWatch Alarm that can be set to fire when the Nat Gateway passes over a desired threshold can be defined like so:
```yaml
Type: AWS::CloudWatch::Alarm
Properties:
    AlarmName: NATGateway-spike
    ActionsEnabled: true
    OKActions: []
    AlarmActions: []
    InsufficientDataActions: []
    MetricName: BytesInFromDestination
    Namespace: AWS/NATGateway
    Statistic: Sum
    Dimensions:
        - Name: NatGatewayId
          Value: nat-0fb9d5ee549ddb49b
    Period: 60
    EvaluationPeriods: 3
    DatapointsToAlarm: 1
    Threshold: 1000000
    ComparisonOperator: GreaterThanThreshold
    TreatMissingData: missing
```