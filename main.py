import discord
import os
import boto3
import uuid
from discord.ext import tasks
from datetime import datetime, timedelta

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
DYNAMO_TABLE = os.getenv("DYNAMO_TABLE")
WEBSITE_URL = os.getenv("WEBSITE_URL")
AUTH_TOKENS_TABLE = os.getenv("AUTH_TOKENS_TABLE")

# Initialize DynamoDB
dynamodb = boto3.resource(
    "dynamodb",
    region_name=AWS_DEFAULT_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

quotes_table = dynamodb.Table(DYNAMO_TABLE)
auth_table = dynamodb.Table(AUTH_TOKENS_TABLE)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Changed from discord.Client to discord.Bot for slash commands
bot = discord.Bot(intents=intents)

status = "Bot Version: 2.0.0"


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
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")
    change_status.start()


@tasks.loop(seconds=60)
async def change_status():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Game(status)
    )


@bot.event
async def on_message(message):
    # Keep existing message monitoring functionality
    if message.author.bot:
        return
    if message.channel.id == CHANNEL_ID:
        save_message_to_dynamodb(message)

    # Process commands if any
    await bot.process_application_commands(message)


@bot.slash_command(name="quotes", description="Get your personal access link to the After Dark quotes website")
async def quotes_command(ctx):
    """Generate and send a unique authentication link to access the quotes website"""

    try:
        # Generate unique token
        token = str(uuid.uuid4())

        # Get current time and calculate expiry (8 hours)
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=8)

        # Get user's display name (server nickname if set, otherwise username)
        display_name = ctx.author.display_name
        username = ctx.author.name

        # Store token in DynamoDB with user info
        auth_table.put_item(Item={
            'token': token,
            'discord_id': str(ctx.author.id),
            'username': username,
            'display_name': display_name,
            'created_at': now.isoformat(),
            'expires_at': expires_at.isoformat(),
            'used': False
        })

        # Create the authentication link
        link = f"{WEBSITE_URL}/auth/{token}"

        # Send ephemeral message (only visible to the user)
        embed = discord.Embed(
            title="🎭 After Dark Quotes Access",
            description=f"Click the link below to access the quotes rating website:",
            color=discord.Color.purple()
        )
        embed.add_field(name="Access Link", value=f"[Click Here]({link})", inline=False)
        embed.add_field(name="⏰ Valid For", value="8 hours", inline=True)
        embed.add_field(name="🔒 Security", value="Link is single-use only", inline=True)
        embed.set_footer(text="This message is only visible to you")

        await ctx.respond(embed=embed, ephemeral=True)

        print(f"Generated auth token for {ctx.author.name} (ID: {ctx.author.id})")

    except Exception as e:
        print(f"Error generating auth token: {e}")
        await ctx.respond(
            "❌ An error occurred while generating your access link. Please try again later.",
            ephemeral=True
        )


bot.run(TOKEN)
