<h1>VPC FlowLogs Recorder for Network Spikes on NAT Gateways</h1>

This is a serverless solution to create VPC FlowLogs to record spiky traffic in NAT Gateways.  
It has an accompanying Medium Blog Post [here](https://medium.com/doit-international/serverless-vpc-flow-logs-recording-nat-gateway-traffic-spikes-a37658821302)

<h2>February 2025 Update</h2>

There is a new branch called "JSONata" in which the Step Function was converted to JSONata and Variables.  
The body (ASL) of the step function was also moved from the SAM YAML template to its own JSON file, which is referenced from the SAM YAML Template.  
It is a simpler, smaller, clearer code than before.  

<h2>The Problem</h2>

It can be challenging to deal with unexpected traffic spikes in AWS's Network Address Translation (NAT) Gateways Service. While VPC Flow Logs provide valuable insights into network traffic, constantly recording them can lead to unnecessary storage costs and a deluge of data that might not be relevant during normal operations.
What if you could selectively enable VPC Flow Logs only when a surge in traffic is detected?

<h2>The Solution</h2>

The solution ensures that VPC Flow Logs are recorded when a NAT Gatway's traffic surpasses a certain threshold. For instance, if the regular traffic pattern for a NAT Gateway is 10MB per minute, you could set an alarm to trigger when traffic exceeds 100MB per minute for a specific duration.
This solution won't be practical for short-lived traffic spikes because VPC Flow Logs will only be created after such a spike is detected. Though the spike doesn't need to be very long to be captured, it must be longer than 3 minutes to ensure it starts recording the traffic.  
The VPC Flow Logs will stop recording in one of two cases - whichever happens first:  
1. The Alram returns to OK
2. The Timeout set to wait for the Alarm expires

The Step Function's state, "WaitForAlaramOrTimeout," is waiting (as the name suggests) for either the Alarm to return to OK or for the Timeout to expire.  
When the Alarm returns to OK, it is caught by an EventBridge Rule that triggers a Lambda function that checks whether the Step Function's Wait Token still exists in its DynamoDB table. If it does, it sends a send_task_success to the waiting Step Function.  
The waiting state will then be resumed and transitioned to the next state responsible for deleting the Token from the DynamoDB table.  

If the Timeout expires first, the Step Function will transition to the same next state that deletes the Token from DynamoDB. When the Alarm returns to OK, the Lambda function will not find the Token and end without notifying the Step Function.  

If the Timeout expires and before it has a chance to remove the Token, the Alarm returns to OK so that the Lambda does find the Token; calling the Step Function with send_task_success will have no effect as the state has already stopped waiting and is transitioning to the next state.

This solution uses the following VPC Flow Log row format:  
```${action} ${flow-direction} ${traffic-path} ${srcaddr} ${srcport} ${dstaddr} ${dstport} ${protocol} ${bytes} ${type} ${pkt-srcaddr} ${pkt-src-aws-service} ${pkt-dstaddr} ${pkt-dst-aws-service}```

You can find information about these fields [here](https://docs.aws.amazon.com/vpc/latest/userguide/flow-log-records.html#flow-logs-fields).

To be able to view the data in a human-friendly format, you can use the following query inside of CloudWatch Logs Insight.  
It has been created automatically as part of the deployment and can be found in CloudWatch Logs Insight -> Saved Queries under the name "Serverless Auto VPC Flow Log Recorder."  
It is already associated with the CloudWatch Log Group where the VPC Recordings are stored, so just by choosing the query it will automatically use the right log group.

```
fields @timestamp, @message
| parse @message "* * * * * * * * * * * * * *" as action, flowDirection, trafficPathNum, srcAddr, srcPort, dstAddr, dstPort, proto, bytes, type, pkt_srcaddr, SrcService, pkt_dstaddr, DstService
| display @timestamp, action, flowDirection, 
        if(trafficPathNum == 1, "Through another resource in the same VPC",
        if(trafficPathNum == 2, "Through an internet gateway or a gateway VPC endpoint",
        if(trafficPathNum == 3, "Through a virtual private gateway",
        if(trafficPathNum == 4, "Through an intra-region VPC peering connection",
        if(trafficPathNum == 5, "Through an inter-region VPC peering connection",
        if(trafficPathNum == 6, "Through a local gateway",
        if(trafficPathNum == 7, "Through a gateway VPC endpoint (Nitro-based instances only)",
        if(trafficPathNum == 8, "Through an internet gateway (Nitro-based instances only)",
        "unknown")))))))) as trafficPath,
        srcAddr, srcPort, dstAddr, dstPort, 
        if(proto == 6, "TCP",
        if(proto == 17, "UDP",
        proto)) as protocol,
        bytes, type, pkt_srcaddr, SrcService, pkt_dstaddr, DstService
| sort @timestamp desc 
| limit 1000
```

If traffic is generated to or from an AWS Service, its name will appear under the 'SrcService' or 'DstService' fields.  
Seeing a service name there means no VPC Endpoint is set up for that service.  
Unless you have a specific reason not to define a VPC Endpoint, you should do so as it is more secure (all traffic is internal to the AWS Network) and cheaper than the NAT Gateway.  
<br><br/>
<h1>Installation</h1>

1. You must have SAM CLI installed:  
[SAM Installation Instructions](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)

2. Clone the repository  
   `git clone https://github.com/doitintl/vpc-flowlogs-recorder.git`

<h3>Deploy the Macros</h3>

3. CD into the assistive Macros  
   `cd cf-assistive-macros`

4. Build the deployment package  
   `sam build`

5. Deploy the Macros  
   `sam deploy --guided`
   - **Stack Name**: Enter a meaningful stack name such as vpc-flowlogs-recorder-assistive-macros
   - **AWS Region**: Enter the AWS Region you want to deploy the solution in
   - **LambdaGroupRetentionTimeDays**: How many days do you want to store the logs for the Macro Lambdas
   - Accept the defaults for the rest of the parameters

<h3>Deploy the main solution</h3>

Once the deployment is complete, continue to install the main solution.  

**NOTE!**  
During the deployment, SNS will send a subscription notification email to the address you entered, so make sure it doesn't end up in your spam folder.  
Check your spam if you don't see it in your inbox by the time the deployment completes.  
If you still can't find the subscription confirmation request, you can always go to the topic "NATGatewayFlowLogsRecorded" in SNS, where you can resend the request using "Request Confirmation" in the "Subscriptions" Tab.  

7. Return to the parent folder (the vpc-flowlogs-recorder)  
   `cd ..`

8. Build the deployment package  
   `sam build`

9. Deploy the solution  
   `sam deploy --guided`
   - **Stack Name**: Enter a meaningful stack name such as vpc-flowlogs-recorder
   - **AWS Region**: Enter the AWS Region you want to deploy the solution in
   - **VPCFlowLogRetentionTimeDays**: How many days do you want to store the logs for the VPCFlowLogs that will be recorded
   - **LambdaLogGroupRetentionTimeDays**: How many days do you want to store the logs for the two Lambdas used in the solution
   - **EmailAddress**: The email of the person that will be notified after each recording
   - **NatGatewayIDs**: A comma-separated NAT Gateway IDs for the NAT Gateways you want to activate the VPC FLowLogs on
   - **SamplingPeriod**: How many seconds do you want the CloudWatch Alarm to sample the metrics (you can use the default value)
   - **EvaluationPeriods**: How many periods of sampling should be evaluated (leave the default unless you have a good reason to change it)
   - **Threshold**: What is the threshold in bytes that the alarm should be set if the traffic through the NAT Gateway exceeds?
                    The current default is 100MB. You can change it as per your use case
   - **DatapointsToAlarm**: How many data points with a threshold exceeding value should be examined?
                            (Leave the default unless you have your own good reason to change it)
   - **RecordingTime**: How much time to continue recording (in **seconds**) if the Alarm is still set.
                        If the Alarm returns to "OK" before this time passes, the recording will stop
   - **NumOfRecordings**: The number of recordings to make (0 means no limit, so record whenever there is a new Alarm).
                          You can use this to limit the number of recordings if you don't want traffic to be recorded every time the alarm is set.
   - Accept the defaults for the rest of the parameters


<h1>Uninstalling</h1>
You can uninstall it in two ways:  

1. Via the AWS CloudFormation Console, locate and delete the two stacks starting with the names you gave during installation.

2. By going to the vpc-flowlogs-recorder directory (where you cloned the git repository into)  
    - First, run the following:  
      `sam delete --no-prompts`
    - Then cd into the cf-assistive-macros directory and run the same command there  
      `cd cf-assistive-macros`  
      `sam delete --no-prompts`

The CloudWatch Logs where the VPC FlowLogs were delivered will remain after the solution is uninstalled.
Its contents will be removed based on the value you entered in **VPCFlowLogRetentionTimeDays** during installation.


<h3>The Step Function's Diagram</h3>

![State Machine](stepfunctions_graph.svg)

