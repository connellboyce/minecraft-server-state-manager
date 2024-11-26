import boto3
import os
from mcstatus import JavaServer

# Initialize AWS clients
ec2 = boto3.client('ec2')
scheduler = boto3.client('scheduler')

# Load environment variables
INSTANCE_ID = os.getenv("INSTANCE_ID")  # EC2 instance ID
RULE_NAME = os.getenv("RULE_NAME")  # EventBridge rule name
SERVER_IP = os.getenv("SERVER_IP")  # Minecraft server public IP or DNS
QUERY_PORT = int(os.getenv("QUERY_PORT", 25565))  # Default to 25565 if not set

flex_window = { "Mode": "OFF" }

def lambda_handler(event, context):
    path = event.get("rawPath", "")

    schedule_template = {
        "RoleArn": os.getenv("SCHEDULE_ROLE"),
        "Arn": context.invoked_function_arn,
        "Input": "{\"rawPath\": \"/manage-state\"}"}

    if path == "/start":
        return start_server(schedule_template)

    elif path == "/manage-state":
        return manage_server_state(schedule_template)

    else:
        return {
            "statusCode": 400,
            "body": "Invalid path. Use '/start' or '/manage-state'."
        }

def start_server(schedule_template):
    response = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
    state = response['Reservations'][0]['Instances'][0]['State']['Name']

    # Check if the server is able to be started
    if state == "stopping":
        return {
            "statusCode": 200,
            "body": "Server is in the process of shutting down. Try again in a few moments."
        }
    
    # Start the EC2 instance
    ec2.start_instances(InstanceIds=[INSTANCE_ID])
    
    # Enable EventBridge rule
    scheduler.update_schedule(Name=RULE_NAME, State='ENABLED', FlexibleTimeWindow=flex_window, ScheduleExpression="rate(1 hour)", Target=schedule_template)

    return {
        "statusCode": 200,
        "body": "Server started and state management enabled."
    }

def manage_server_state(schedule_template):
    try:
        # Check if the server is online
        server = JavaServer(SERVER_IP, QUERY_PORT)
        status = server.status()
        player_count = status.players.online
    except Exception:
        # Describe the instance
        response = ec2.describe_instances(InstanceIds=[INSTANCE_ID])

        # Get the state of the instance
        state = response['Reservations'][0]['Instances'][0]['State']['Name']

	# If the instance is running and this exception is being handled, it means Minecraft is not accessible. 
        if state != "running":
            scheduler.update_schedule(Name=RULE_NAME, State='DISABLED', FlexibleTimeWindow=flex_window, ScheduleExpression="rate(1 hour)", Target=schedule_template)

            return {
                "statusCode": 200,
                "body": "Server is not running."
            }
        return {
                "statusCode": 200,
                "body": "Server is not reachable at this time."
            }
    if player_count == 0:
        # Stop EC2 instance if no players are online
        ec2.stop_instances(InstanceIds=[INSTANCE_ID])

        # Disable EventBridge rule
        scheduler.update_schedule(Name=RULE_NAME, State='DISABLED', FlexibleTimeWindow=flex_window, ScheduleExpression="rate(1 hour)", Target=schedule_template)

        return {
            "statusCode": 200,
            "body": "Server is being stopped and state management disabled (no players online)."
        }

    return {
        "statusCode": 200,
        "body": f"Server is running with {player_count} player(s) online."
    }
