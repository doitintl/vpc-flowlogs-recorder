<h1> Create Temporary VPC Flow Logs for Nat Gateway when heavy traffic is detected</h1>

<h3>The Problem</h3>
Constantly recording VPC Flow Logs may generate a lot of data with its associated costs, and record information that during "normal times" may not interest you.
Though it is possible to query the logs over a specific time frame when needed, why store data that you don't need?

<h3>The Solution</h3>
The concept of this solution is to create VPC Flow Logs when spiky unexpected traffic is detected that is above a certain threshold.
Let's assume you normally have a regular traffic of 10MB per minute via your Nat Gateway.
Volume wise, this would come up to 10MB X 1440 (minutes per day) * 30.5 (days per month)  = 439GB
The NAT Gateway Data **Processing** Charge per GB in N.Virginia is $0.045.
So the monthly cost would be: 493 * 0.045 = $19.764
A very low cost.

In cases where you have code that suddenly and unexpectedly sends or receives a much higher traffic volume over a period of time that isn't measured in a minute or two, you would like to be able to understand the reason behind this traffic.
Specifically the source and destination.
This will allow you to investigate why it happened and if it is ok or not.

This repository contains code that is deployable via AWS SAM.
It has two different SAM Yaml file deploying two different CloudFormation Stacks.
The first contains CloudFormation Macros used by the second template.
It has a macro to auto generate the CloudWatch Alarm for each specified Nat Gateway
It has another macro to convert String to Int due to an issue with CloudFormation Parameters always being treated as Strings.

The second deployment creates the following resources:
- DynamoDB Table that handles the number of recording done per Nat Gateway as well as holds a Callback Token to be used when the Alarm returns to "OK"
- A Cloudwatch Alarm that monitors specific Nat Gateways that you specify as well as a Threshold for the amount of data.
- An EventBridge Rule that matches this Alarm and triggers a Step Function
- An EventBridge Rule that matches this Alarm when it returns to "Ok" and triggers a Lambda function
- A Step function that:
  - Ensures that the desired number of recordings hasn't been reached
  - Handles creation of VPC Flow Logs for each ENI belonging to the Nat Gateways
  - Waits for the Alarm to return to "Ok" or a certain time (that you define while deploying the SAM Template) passes
  - Deletes the Recording of the VPC Flow Logs (don't delete the recorded logs of course)
  - Sends an SNS Email notification to whomever you specified when deploying the solution
- A Lambda function that is triggered by the EventBridge Rule that matches the Alarm returning to "OK"
  - The Lambda retrieves the Step Function callback Token from Dynamo DB and calls the Step Function to resume its operation

<h3>The Step Function's Diagram</h3>
![stepfunctions_graph](https://github.com/user-attachments/assets/2b83cb7e-eb01-44ef-9382-65db7953329b)
