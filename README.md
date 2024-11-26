# Minecraft Server State Manager Lambda Function
Start, Stop, and check the player count of a Minecraft Server running in Amazon EC2.

## Prerequisites
1. Ensure you have a working Minecraft Server running in an EC2 instance.
   - It is recommended to have a fixed IP address for this server.
3. Enable 'query.enabled' property and (optional) change 'query.port'
4. Create a Lambda layer for mcstatus
5. Create a Schedule in EventBridge
6. Update Environment Variables in Lambda to reflect your cloud environment

## Enhancements
1. Have the /start and /manage-status endpoints be invoked by a Discord bot
