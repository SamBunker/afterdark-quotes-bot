import discord
import json
import asyncio
import boto3
import os
import uuid
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
DYNAMO_TABLE = os.getenv("DYNAMO_TABLE")
WEBSITE_URL = os.getenv("WEBSITE_URL")
AUTH_TOKENS_TABLE = os.getenv("AUTH_TOKENS_TABLE")

## Defining the Tables ##
dynamodb = boto3.resource("dynamodb", region_name=AWS_DEFAULT_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
limbo_table = dynamodb.Table(DYNAMO_TABLE)
auth_table = dynamodb.Table(AUTH_TOKENS_TABLE)
## ## ##

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
                limbo_table.put_item(Item=message_data)
                print(f"Saved message: {message.id} from {message.author.name}")
        except Exception as e:
                print(f"Error saving to DynamoDB: {e}")

def create_auth_token(discord_id):
    """Create authentication token for user"""
    import datetime

    token = str(uuid.uuid4())
    now = datetime.datetime.utcnow()
    expires_at = now + datetime.timedelta(hours=1)

    token_data = {
        "token": token,
        "discord_id": int(discord_id),
        "created_at": now.isoformat() + "Z",
        "expires_at": expires_at.isoformat() + "Z",
        "used": False
    }

    try:
        auth_table.put_item(Item=token_data)
        return token
    except Exception as e:
        print(f"Error creating auth token: {e}")
        return None

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in!')

    # Sync slash commands with Discord
    try:
        print("Syncing slash commands...")
        synced = await bot.tree.sync()
        print(f"✅ Successfully synced {len(synced)} slash command(s)")
        for command in synced:
            print(f"  - /{command.name}: {command.description}")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
        print("Make sure the bot has the 'applications.commands' scope enabled")

@bot.event
async def on_message(message):
        if message.author.bot:
                return
        if message.channel.id == CHANNEL_ID:
                save_message_to_dynamodb(message)

@bot.tree.command(name="get-rating-link", description="Get a personal link to rate quotes")
async def get_rating_link(interaction: discord.Interaction):
    """Slash command to generate authentication link"""
    try:
        # Create authentication token
        token = create_auth_token(interaction.user.id)

        if not token:
            await interaction.response.send_message(
                "❌ Sorry, there was an error generating your link. Please try again later.",
                ephemeral=True
            )
            return

        # Generate the authentication URL
        auth_url = f"{WEBSITE_URL}/auth/{token}"

        # Create embed for the response
        embed = discord.Embed(
            title="🎪 Your Personal Rating Link",
            description="Click the link below to start rating quotes!",
            color=0x00ff00
        )
        embed.add_field(
            name="⏰ Link Expires",
            value="In 1 hour",
            inline=True
        )
        embed.add_field(
            name="🔐 Security",
            value="One-time use only",
            inline=True
        )
        embed.add_field(
            name="🔗 Your Link",
            value=f"[Click here to rate quotes!]({auth_url})",
            inline=False
        )
        embed.set_footer(text="This link is private and only visible to you.")

        await interaction.response.send_message(embed=embed, ephemeral=True)
        print(f"Generated auth link for {interaction.user.name} (ID: {interaction.user.id})")

    except Exception as e:
        print(f"Error in get_rating_link command: {e}")
        await interaction.response.send_message(
            "❌ An error occurred while generating your link. Please try again later.",
            ephemeral=True
        )



bot.run(TOKEN)
