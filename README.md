# Nath-bot

A Discord bot for Warhammer Online: Age of Reckoning (WoAOR) that monitors game events and provides server management features.

## Features

- **Game Event Tracking**: Monitors Warhammer Online events and provides signup functionality
- **Server Management**: Moderation commands for managing your Discord server
- **Event Management**: Create, manage, and track game events with signups
- **Domain Filtering**: Blocks malicious domains and links
- **Customizable Configuration**: Easy setup with `/configure` command

## Bot Invite

To add the bot to your server, click this link:
[Invite Nath-bot](https://discord.com/oauth2/authorize?client_id=758718771275497559&scope=bot&permissions=268471296)

After inviting, configure the bot by running `/configure` in any channel the bot can see.

## Self-Hosting

### Requirements
- Python 3.8+
- Discord.py library
- Python dependencies (requests, etc.)

### Setup
1. Clone the repository
2. Install Python dependencies
3. Create a `token.txt` file with your bot token
4. Run `python3 src/main/discord_bot.py`

### Configuration
The bot uses `guilds.json` for configuration. Run `/configure` to set up your server preferences.

