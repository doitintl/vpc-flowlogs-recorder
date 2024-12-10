import os
import boto3

# Initialize the EC2 client
region = os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION')
client = boto3.client('ec2', region_name=region)

def lambda_handler(event, context):
    print("Triggered by event!")
    
    log_group_name = os.environ['LOG_GROUP_NAME']
    
    # Get NAT Gateway ID
#    nat_gateway_id = event['alarmData']['configuration']['metrics'][0]['metricStat']['metric']['dimensions']['NatGatewayId']
    nat_gateway_id = event['ngwid']
    
    eni = get_eni_from_natgateway(nat_gateway_id)

    flow_log_ids = []
    log_format = '${action} ${flow-direction} ${traffic-path} ${srcaddr} ${srcport} ${dstaddr} ${dstport} ${protocol} ${bytes} ${type} ${pkt-srcaddr} ${pkt-src-aws-service} ${pkt-dstaddr} ${pkt-dst-aws-service}'
    
    # Create the VPC Flow Logs for the NAT Gateway's ENI
    try:
        response = client.create_flow_logs(
            ResourceIds=[eni],
            ResourceType='NetworkInterface',
            TrafficType='ALL',
            LogGroupName=log_group_name,
            DeliverLogsPermissionArn= os.environ['VPC_FLOW_LOG_ROLE'],
            LogFormat=log_format
        )
        flow_log_ids.append(response['FlowLogIds'][0])
    except Exception as e:
        print("Failed to create VPC Flow log with", str(e))
    
    return {
        'statusCode': 200,
        'body': { 'FlowLogIds' : flow_log_ids, 'ENI' : eni }
    } 


def get_eni_from_natgateway(nat_gateway_id):
    params = {
        'NatGatewayIds': [nat_gateway_id]
    }
    
    eni = None

    try:
        response = client.describe_nat_gateways(**params)
        if len(response['NatGateways']) > 0:  # Found the NAT Gateway's ENI(s)
            eni = response['NatGateways'][0]['NatGatewayAddresses'][0]['NetworkInterfaceId']
            print("Found ENI associated with NAT Gateway", eni)
        else:
            print("No NAT Gateway found with the specified ID.")
    except Exception as e:
        print("Failed to describe NAT Gateways with", str(e))
    
    return eni