import discord
import json
import asyncio
import boto3
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
DYNAMO_TABLE = os.getenv("DYNAMO_TABLE")
WEBSITE_URL = os.getenv("WEBSITE_URL")
AUTH_TOKENS_TABLE = os.getenv("AUTH_TOKENS_TABLE")


dynamodb = boto3.resource("dynamodb", region_name=AWS_DEFAULT_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

quotes_table = dynamodb.Table(DYNAMO_TABLE)
auth_table = dynamodb.Table(AUTH_TOKENS_TABLE)

intents = discord.Intents.default()
intents.members = True  # Enable member tracking
intents.message_content = True

bot = discord.Client(intents=intents)


def save_message_to_dynamodb(message):
        message_data = {
                "message_id": str(message.id),
                "user": message.author.name,
                "content": message.content,
                "timestamp": str(message.created_at),
        }
        try:
                quotes_table.put_item(Item=message_data)
                print(f"Saved message: {message.id} from {message.author.name}")
        except Exception as e:
                print(f"Error saving to DynamoDB: {e}")


@bot.event
async def on_message(message):
        if message.author.bot:
                return
        if message.channel.id == CHANNEL_ID:
                save_message_to_dynamodb(message)

bot.run(TOKEN)
