import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
from python_mcstatus import statusJava
import asyncio
import os
import sys

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename= 'isupy_discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='isupy', intents=intents)

## arg passing
FREQUENCY_MAP = {
    "1": 60,       # 1 min
    "2": 300,      # 5 min
    "3": 600,      # 10 min
    "4": 3600,     # 1 hour
    "5": 21600     # 6 hours
}

## Configuration loading
def load_config(config_file="config.txt"):
    """Load configuration from a text file"""
    config = {}
    
    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found.")
        print("Please create a config.txt file with the required settings.")
        sys.exit(1)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value pairs
                if '=' not in line:
                    print(f"Warning: Invalid format on line {line_num}: {line}")
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Convert boolean strings
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                # Convert numeric strings
                elif value.isdigit():
                    value = int(value)
                
                config[key] = value
                
    except Exception as e:
        print(f"Error reading configuration file: {e}")
        sys.exit(1)
    
    # Validate required settings
    required_settings = ['ip_address', 'port', 'query', 'channel_id', 'show_player_names', 'frequency_level']
    missing = [setting for setting in required_settings if setting not in config]
    
    if missing:
        print(f"Error: Missing required settings in config file: {', '.join(missing)}")
        sys.exit(1)
    
    # Validate frequency level
    if config['frequency_level'] not in range(1, 6):
        print("Error: frequency_level must be between 1 and 5")
        sys.exit(1)
    
    # Validate port
    if not (0 <= config['port'] <= 65535):
        print("Error: port must be between 0 and 65535")
        sys.exit(1)
    
    return config

def show_help():
    print("IsupyBot - Minecraft Server Status Monitor")
    print("Usage: python main.py [config_file]")
    print("\nIf no config file is specified, 'config.txt' will be used.")
    print("\nConfiguration file format:")
    print("ip_address=your.server.ip")
    print("port=25565")
    print("query=true")
    print("channel_id=your_discord_channel_id")
    print("show_player_names=true")
    print("frequency_level=1")
    print("\nFrequency levels:")
    for level, seconds in FREQUENCY_MAP.items():
        print(f"{level}: {seconds // 60} minutes")
    sys.exit(0)

# Parse arguments
config_file = "config.txt"
if len(sys.argv) > 1:
    if sys.argv[1].lower() in ['--help', '-h', 'help']:
        show_help()
    else:
        config_file = sys.argv[1]

# Load configuration
config = load_config(config_file)
MC_IP = config['ip_address']
PORT = config['port']
QUERY = config['query']
CHANNEL_ID = config['channel_id']
SHOW_PLAYER_NAMES = config['show_player_names']
FREQUENCY_LEVEL = str(config['frequency_level'])

if FREQUENCY_LEVEL not in FREQUENCY_MAP:
    print("Error: Frequency level must be a number from 1 to 5.")
    sys.exit(1)

PING_INTERVAL = FREQUENCY_MAP[FREQUENCY_LEVEL]


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id} - On server: {len(bot.guilds)} servers')
    
    # Start the status monitoring task
    bot.loop.create_task(monitor_server_status())

async def monitor_server_status():
    """Monitor Minecraft server status and send updates to Discord"""
    await bot.wait_until_ready()
    
    # Get channel from config
    channel = bot.get_channel(CHANNEL_ID)
    
    if not channel:
        print(f"Warning: Channel with ID {CHANNEL_ID} not found or not accessible")
        return
    
    previous_status = None
    status_message = None  # Keep track of the message to edit
    
    # Check for existing bot messages in the channel
    print("Checking for existing bot messages...")
    try:
        async for message in channel.history(limit=50):
            if message.author == bot.user and message.embeds:
                # Found an existing bot message with embeds
                embed = message.embeds[0]
                # Check if it looks like a status message
                if "Server Status" in embed.title:
                    status_message = message
                    print(f"Found existing status message (ID: {message.id}), will reuse it")
                    break
    except Exception as e:
        print(f"Error checking for existing messages: {e}")
    
    while not bot.is_closed():
        try:
            print(f"Checking server status for {MC_IP}:{PORT}")
            # Query the Minecraft server using config values
            response = statusJava(MC_IP, PORT, QUERY)
            print(f"Server online: {response.online if response else False}, Players: {response.players.online if response and hasattr(response, 'players') else 'N/A'}")
            
            if response and hasattr(response, 'players'):
                current_status = {
                    'online': True,
                    'host': MC_IP,
                    'port': PORT,
                    'players_online': response.players.online,
                    'players_max': response.players.max,
                    'version': response.version.name_clean,
                    'players_list': [player.name_clean for player in response.players.list] if response.players.list else [],
                    'icon': getattr(response, 'icon', None)
                    ##'latency': response.latency
                }
                
                # Create the embed for online status
                embed = discord.Embed(
                    title="🟢 Online",
                    color=0x00ff00,
                    description=f"**IP: {MC_IP}**\n**Port: {PORT}**"
                )
                
                embed.add_field(name="Players", value=f"{current_status['players_online']}/{current_status['players_max']}", inline=True)
                embed.add_field(name="Version", value=current_status['version'], inline=True)
                
                # Add server icon if available and valid
                if current_status.get('icon'):
                    try:
                        # Check if it's a valid HTTP/HTTPS URL
                        if current_status['icon'].startswith(('http://', 'https://')):
                            embed.set_thumbnail(url=current_status['icon'])
                        else:
                            print(f"Invalid icon URL format: {current_status['icon'][:100]}...")  # Log first 100 chars
                    except Exception as icon_error:
                        print(f"Failed to set thumbnail: {icon_error}")
                
                # Add players list if there are any online and if enabled in config
                if SHOW_PLAYER_NAMES and current_status['players_list']:
                    players_text = "\n".join(current_status['players_list'])
                    # Discord field values have a 1024 character limit
                    if len(players_text) > 1020:
                        players_text = players_text[:1020] + "..."
                    embed.add_field(name="Online Players", value=f"```\n{players_text}\n```", inline=False)
                elif SHOW_PLAYER_NAMES:
                    embed.add_field(name="Online Players", value="No players online", inline=False)
                
                embed.timestamp = discord.utils.utcnow()
                
                try:
                    if status_message is None:
                        # First time or message was deleted - send new message
                        status_message = await channel.send(embed=embed)
                        # Pin the message if it's not already pinned
                        try:
                            await status_message.pin()
                            print("Status message pinned")
                        except discord.HTTPException as pin_error:
                            print(f"Failed to pin message: {pin_error}")
                    else:
                        # Update existing message
                        await status_message.edit(embed=embed)
                except discord.HTTPException as discord_error:
                    print(f"Failed to send/edit Discord message: {discord_error}")
                    # Try sending a simpler message without the problematic elements
                    simple_embed = discord.Embed(
                        title="🟢 Online", 
                        color=0x00ff00,
                        description=f"**{MC_IP}:{PORT}** - {current_status['players_online']}/{current_status['players_max']} players"
                    )
                    if status_message is None:
                        status_message = await channel.send(embed=simple_embed)
                        # Pin the message if it's not already pinned
                        try:
                            await status_message.pin()
                            print("Fallback status message pinned")
                        except discord.HTTPException as pin_error:
                            print(f"Failed to pin fallback message: {pin_error}")
                    else:
                        await status_message.edit(embed=simple_embed)
                except discord.NotFound:
                    # Message was deleted, send a new one
                    print("Status message was deleted, sending new one")
                    status_message = await channel.send(embed=embed)
                    # Pin the new message
                    try:
                        await status_message.pin()
                        print("New status message pinned")
                    except discord.HTTPException as pin_error:
                        print(f"Failed to pin new message: {pin_error}")
                
                previous_status = current_status
                    
        except Exception as e:
            print(f"Error checking server status: {e}")
            print(f"Error type: {type(e)}")
            # Server is offline or unreachable
            current_status = {'online': False}
            
            if previous_status is None or previous_status.get('online', False):
                # Create offline embed
                embed = discord.Embed(
                    title="🔴 Offline",
                    color=0xff0000,
                    description=f"**IP: {MC_IP}**\n**Port: {PORT}**\n\n**{MC_IP}:{PORT}** is not responding"
                )
                embed.add_field(name="Error", value=str(e), inline=False)
                embed.timestamp = discord.utils.utcnow()
                
                try:
                    if status_message is None:
                        status_message = await channel.send(embed=embed)
                        # Pin the message if it's not already pinned
                        try:
                            await status_message.pin()
                            print("Offline status message pinned")
                        except discord.HTTPException as pin_error:
                            print(f"Failed to pin offline message: {pin_error}")
                    else:
                        await status_message.edit(embed=embed)
                except discord.NotFound:
                    # Message was deleted, send a new one
                    print("Status message was deleted, sending new one")
                    status_message = await channel.send(embed=embed)
                    # Pin the new message
                    try:
                        await status_message.pin()
                        print("New offline status message pinned")
                    except discord.HTTPException as pin_error:
                        print(f"Failed to pin new offline message: {pin_error}")
                
            previous_status = current_status
        
        # Wait for the specified interval before checking again
        await asyncio.sleep(PING_INTERVAL)

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
