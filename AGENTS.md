# Nath-bot Agents

This document describes the various agents and components that make up the Nath-bot Discord bot for Warhammer Online.

## Core Bot Structure

### `src/main/discord_bot.py`
The main bot entry point that initializes the Discord client, sets up intents, and loads cogs. Contains:
- Bot initialization with command prefix and intents
- Event handlers for guild join/leave, member updates, message events
- Configuration loading and saving
- Logging setup
- Token reading from file
- Domain filtering integration
- Warhammer events module loading
- Moderation module loading
- TUE specific module loading

### `src/main/moderation.py`
Moderation commands and utilities for server management:
- `/help` - Display available commands
- `/add` - Add pings or events (FortPing, CityPing, Event, Channel)
- `/remove` - Remove pings or events (FortPing, CityPing, Event)
- `/announce` - Announce messages across servers (admin only)
- `/configure` - Configure bot settings for the server
- `/kick` - Kick members from server
- `/ban` - Ban members from server
- `/purge` - Purge messages from channel
- `/citystat` - Return city statistics
- `/fortstat` - Return fort statistics
- `/debug` - Debug command for bot information (admin only)
- `/editannounce` - Edit previous announcements (admin only)

### `src/main/warhammer_events.py`
Warhammer Online event management system:
- `/create_ror_event` - Create a new Warhammer Online event
- `/accept_ror_signup` - Accept a sign-up for an event
- `/reject_ror_signup` - Reject a sign-up for an event
- `/cancel_ror_event` - Cancel an event
- Interactive event creation with career selection buttons
- Event alert system for upcoming events
- Event cleanup for passed events
- Career-based event organization (Order/Destruction factions)

### `src/main/tue_specifics.py`
TUE (The Unofficial Empire) specific features:
- Guild member checking using RoR API
- Role management for guild members
- Officer and member tracking
- Automatic role assignment based on RoR guild membership

### `src/main/domain_filter.py`
Domain filtering system:
- Malicious domain detection
- URL filtering
- Blacklist management
- Download and processing of domain lists from multiple sources
- Support for both malicious and suspicious domains

## Configuration Files

### `guilds.json`
Server configuration data including:
- Announcement channels
- Moderator roles
- Welcome/leave messages
- Event settings
- Logging channels
- Chat moderation settings

### `token.txt`
Discord bot token file (not included in repo)

## Icon Resources

### `src/main/icons/`
Directory containing faction and career icons used in event displays:
- am.png, bg.png, bo.png, bw.png, choppa.png, chosen.png, dok.png, eng.png, ib.png, kotbs.png, magus.png, mara.png, rp.png, sh.png, shaman.png, slayer.png, sm.png, sorc.png, sw.png, we.png, wh.png, wl.png, wp.png, zeal.png

## External Dependencies

### GitHub Templates
- `.github/ISSUE_TEMPLATE/bug-report.md` - Bug report template
- `.github/dependabot.yml` - Dependency update configuration
- `.github/pull_request_template.md` - Pull request template

### Documentation
- `CONTRIBUTING.md` - Contribution guidelines
- `LICENSE` - Project license
- `README.md` - Project overview
- `configure.jpg` - Configuration guide image
- `typical.jpg` - Typical usage image
- `examples/systemd-example.service` - Systemd service example
- `pom.xml` - Maven project configuration (possibly for build system)

## Features

### Moderation
- Channel logging for various events
- Message filtering and deletion
- Role management for members
- Kick and ban functionality with logging
- Purge messages functionality

### Warhammer Online Integration
- Event creation and management
- Career-based signup system
- Automatic event alerts
- Integration with RoR API for guild membership

### Domain Filtering
- Automatic download of malicious domain lists
- Real-time filtering of messages containing bad domains
- Support for multiple domain filtering sources

### Server Configuration
- Per-server configuration management
- Flexible channel and role settings
- Welcome/leave message customization
- Logging configuration
