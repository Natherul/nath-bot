#!/usr/bin/env python3
from datetime import datetime
from datetime import timedelta
from typing import Literal, Optional
import discord
from discord.utils import get
from discord import File
import json
import time
import ast
from discord.ext import tasks
from discord import app_commands
import domain_filter
import uuid
import logging
import sys
import sto_news

# Constants
QUESTION_ICON = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Question_mark_%28black%29.svg/1200px-Question_mark_%28black%29.svg.png"
ANNOUNCE_ICON = "http://tue.nu/misc/announce.png"
BANNED_ICON = "https://e7.pngegg.com/pngimages/1003/312/png-clipart-hammer-game-pension-review-internet-crouton-hammer-technic-discord-thumbnail.png"
KICKED_ICON = "https://p7.hiclipart.com/preview/825/776/55/karate-kick-martial-arts-taekwondo-clip-art-kicked-thumbnail.jpg"
ERROR_ICON = "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Error.svg/1200px-Error.svg.png"
ROR_ICON = "http://www.tue.nu/misc/ror.png"
TIME_STRING = "%Y-%m-%d %H:%M:%S"
CONFIGURATION = "guilds.txt"
DESTRO_STRING = ",Destruction\n"
ORDER_STRING = ",Order\n"
NOT_MOD_STRING = "You are not set as moderator and is not allowed to use this command."
LOG_PERM_ERROR = "Nath-bot is enabled on your server but does not have the permissions to send messages to the log channel though its set to log to a set channel."
HTTP_ERROR = "HTTP error"
NOW_SET_TO_ = " is now set to: "

logger = logging.getLogger('discord-bot')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

h1 = logging.StreamHandler(sys.stdout)
h1.setLevel(logging.DEBUG)
h1.addFilter(lambda record: record.levelno <= logging.INFO)
h1.setFormatter(formatter)

h2 = logging.StreamHandler()
h2.setLevel(logging.WARNING)
h2.setFormatter(formatter)
logger.addHandler(h1)
logger.addHandler(h2)

t = open('token.txt', 'r')
TOKEN = t.read() 
t.close()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guild_messages = True
intents.guilds = True
intents.messages = True
intents.dm_messages = True
intents.bans = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)
bot.currentZones = ""
bot.TUE = 173443661713899521
bot.forts = ['The Maw', 'Reikwald', 'Fell Landing', 'Shining Way', 'Butchers Pass', 'Stonewatch']
bot.cities = ['Inevitable City', 'Altdorf']
bot.started = False
bot.commandDescriptions = {'configure': 'Commands to configure the bot (these can only be issued by the owner of the discord and there are multiple subcommands here)',
                           'citystat' : 'Posts the statistics for cities',
                           'fortstat' : 'Posts the statistics for fortresses',
                           'add Fortping' : 'Adds you to the group that gets pinged on fortresses',
                           'add CityPing' : 'Adds you to the group that gets pinged on cities',
                           'remove FortPing' : 'Removes you from the group that gets pinged in fortresses',
                           'remove CityPing' : 'Removes you from the group that gets pinged when cities happen',
                           'add Event' : 'Adds an event to the bot using syntax: "epoch,name,description" (https://www.epochconverter.com/)',
                           'remove Event' : 'Removes an event with the specified ID',
                           'list Event' : 'Lists all events for the guild',
                           'add Channel' : 'Creates a temporary channel on the server. This channel will get deleted once no members are present in it and unless a name is specified the channel will get a UUID as a name.'}

bot.configDesc = {'announceChannel' : '(String/int)What channel to post campaign to (either Channel name or channelID specified)',
                  'logChannel' : '(String/int)What channel to pot logs about moderation or role changes (either channel name or channelID specified)',
                  'welcomeMessage' : '(String)What the bot should greet someone that joins the server with ("{display_name/name/id/mention} can be used to let the bot substitute it")',
                  'leaveMessage' : '(String)What the bot should say when someone leaves the server ("{display_name/name/id/mention} can be used to let the bot substitute it")',
                  'boardingChannel' : '(String/int)What channel to post welcome/leave messages to (either channel name or channelID specified)',
                  'moderator' : '(String/int)What role to allow moderator commands',
                  'fortPing' : '(String/int)What role to attatch to announcement of campaign when a fort happens (role name or roleID specified)',
                  'cityPing' : '(String/int)What role to attach to announcement of campagin when a city happens(role name or roleID specified)',
                  'removeAnnounce' : '(bool as int)If the bot should post in the log channel when someone gets kicked or banned from the server',
                  'announceServmsg': '(bool as int)If the bot should announce issues or other messages from soronline.us',
                  'eventChannel' : '(String/int)What channel to post event messages to (either channel name or channelID specified)',
                  'chatModeration' : '(bool as int)If the bot should moderate chat messages',
                  'allowTempChannels' : '(bool as int)If anyone is allowed to ask the bot to make temporary voice channels',
                  'stoNewsChannel' : '(String/int)What channel if any to post news from Star trek online. (either channel name or channelID specified)'}

bot.allconf = {'announceChannel' : '0',
               'logChannel' : '0',
               'welcomeMessage' : '0',
               'leaveMessage' : '0',
               'boardingChannel' : '0',
               'fortPing' : '0',
               'cityPing' : '0',
               'enabled' : '1',
               'removeAnnounce': '0',
               'announceServmsg' : '0',
               "eventChannel" : "0",
               "events" : {},
               'moderator' : '0',
               'chatModeration' : '0',
               'tempChannels' : [],
               'stoNewsChannel' : '0'}


bot.confs = {}
bot.lastCityTime = 0
bot.servmsg = ""
bot.lastannounce = ""
bot.lasterr = ""
bot.sto_news = []

# for if we want to edit announces
bot.lastAnnounceMessage = {}

bot.bad_domains = []
# Ugly hack workaround since apparently a bot that deletes a message does not create an audit trail...
bot.lastDeletedMessage = ""


@bot.event
async def on_ready():
    """Starting method for the bot. This is where the bot loads previous values"""
    if not bot.started:
        bot.started = True
        logger.info('Logged in as')
        logger.info(bot.user.name)
        logger.info(bot.user.id)
        logger.info('loading old scrape')
        # load last scrape
        f = open('result.txt', 'r')
        result_string = f.read()
        if result_string != "":
            bot.currentZones = ast.literal_eval(result_string)
        f.close()
        # used to make sure to not spam cityping and city stats
        l = open('lastcity.txt', 'r')
        bot.lastCityTime = l.read()
        l.close()
        # load previos news to know if there is new news
        f = open('sto_news.txt', 'r')
        bot.sto_news = json.loads(f.read())
        f.close()
        # the configurations for the diff disc servers
        g = open(CONFIGURATION, 'r')
        bot.confs = json.loads(g.read().replace("'", '"'))
        g.close()
        remake = False
        for guild in bot.confs:
            this_guild = bot.confs[str(guild)]
            for configuration in bot.allconf:
                if configuration not in this_guild:
                    this_guild[configuration] = bot.allconf[configuration]
                    bot.confs[str(guild)] = this_guild
                    remake = True

        if remake:
            c = open(CONFIGURATION, 'w')
            c.write(str(bot.confs))
            c.close()

        logger.info('Downloading new bad domain lists')
        domain_filter.download_files()
        logger.info('Processing downloaded files to make a full list of bad domains')
        bot.bad_domains = domain_filter.load_bad_domains()

        logger.info('LOADED')
        event_check.start(bot)
        channel_check.start(bot)
        sto_news_check.start(bot)
        await tree.sync()
        await tree.sync(guild=discord.Object(id=bot.TUE))


@bot.event
async def on_guild_join(guild):
    """When the bot joins a new server it will configure itself with the values it needs saved"""
    if guild.id not in bot.confs:
        this_guild = bot.allconf
        bot.confs[str(guild.id)] = this_guild
        save_conf()
    else:
        this_guild = bot.confs[str(guild.id)]
        this_guild['enabled'] = '1'
        bot.confs[str(guild.id)] = this_guild
        save_conf()
    await guild.owner.send('Thanks for inviting me to the server. To get started you need to set up what channels I should talk to when announcing. Do this by:\n"/configure" in any channel in the guild and I will respond with your options.\nYou can at any time also issue: "/help" to see what commands are avilable.')


@bot.event
async def on_guild_remove(guild):
    """When the bot gets removed from a server we set the config to not be enabled on that server"""
    this_guild = bot.confs[str(guild.id)]
    this_guild['enabled'] = '0'
    bot.confs[str(guild.id)] = this_guild
    save_conf()


@tree.command(name="help", description="The help command for the bot")
async def helpmessage(ctx):
    await ctx.response.send_message(embed=make_embed("Available Commands", "These are the commands that you can use", 0xfa00f2, QUESTION_ICON, bot.commandDescriptions))


@tree.command(name="add", description="Command group to add pings or events")
@app_commands.describe(type="What to add", args="Event parameters")
async def add(ctx, type: Literal['FortPing', 'CityPing', 'Event', 'Channel'], args: Optional[str]):
    this_guild = bot.confs[str(ctx.guild.id)]
    if "FortPing" == type:
        if this_guild['fortPing'] != '0':
            try:
                role = get(ctx.guild.roles, id=int(this_guild['fortPing']))
                await ctx.guild.get_member(ctx.user.id).add_roles(role)
                await ctx.response.send_message("Role added")
                if this_guild['logChannel'] != '0':
                    await bot.get_channel(int(this_guild["logChannel"])).send(
                        "Added " + str(ctx.user.id) + " / " + str(ctx.user.display_name) + " to FortPings")
            except discord.Forbidden:
                await bot.get_guild(int(ctx.guild.id)).owner.send(
                    "Something went wrong when attempting to add a role or when trying to post to the log channel")
            except discord.HTTPException:
                logger.error(HTTP_ERROR)
    elif "CityPing" == type:
        if this_guild['cityPing'] != '0':
            try:
                role = get(ctx.guild.roles, id=int(this_guild['cityPing']))
                await ctx.guild.get_member(ctx.user.id).add_roles(role)
                await ctx.response.send_message("Role added")
                if this_guild['logChannel'] != '0':
                    await bot.get_channel(int(this_guild["logChannel"])).send(
                        "Added " + str(ctx.user.id) + " / " + str(ctx.user.display_name) + " to CityPings")
            except discord.Forbidden:
                await bot.get_guild(int(ctx.guild.id)).owner.send(
                    "Something went wrong when attempting to add a role or when trying to post to the log channel")
            except discord.HTTPException:
                logger.error(HTTP_ERROR)
    elif "Event" == type:
        if args is None:
            await ctx.response.send_message("When adding an even you need to add the parameters in a comma seperated way. Epoch,EventName,Description. Example: 1624723200,Testing,Testevent")
        elif this_guild['eventChannel'] == '0':
            await ctx.response.send_message("This guild has not set up a channel for events, creating events is disabled.")
        elif add_event(args, ctx.guild.id, ctx.user) != 0:
            await ctx.response.send_message(
                "Something went wrong when attempting to create an event, please ensure that you formatted the command correct")
        else:
            await ctx.response.send_message("Event added")
    elif "Channel" == type:
        # Make sure that the person is already connected to a channel else we cannot move him
        if ctx.guild.get_member(ctx.user.id).voice is not None:
            try:
                channel_name = str(uuid.uuid4().hex) if args is None else args
                channel = await ctx.guild.create_voice_channel(name=channel_name,
                    reason="Channel requested by user: {user}".format(user=ctx.user.display_name))
                current_temp_channels = this_guild['tempChannels']
                current_temp_channels.append(channel.id)
                this_guild['tempChannels'] = current_temp_channels
                bot.confs[str(ctx.guild.id)] = this_guild
                save_conf()
                await ctx.guild.get_member(ctx.user.id).move_to(channel)
                await ctx.response.send_message("Temporary channel created and user moved to channel.")
            except (discord.Forbidden, TypeError):
                await ctx.response.send_message("Something went wrong when attempting to either create the channel or move you to the channel.")
            except discord.HTTPException:
                logger.error(HTTP_ERROR)
        else:
            await ctx.response.send_message(
                "You need to be connected to a channel before issuing this command. The bot will move you to the channel when its created and remove the channel once its empty.")


@tree.command(name="remove", description="Command group to remove pings or events")
@app_commands.describe(type="What to remove", args="Event parameters")
async def remove(ctx, type: Literal['FortPing', 'CityPing', 'Event'], args: Optional[str]):
    this_guild = bot.confs[str(ctx.guild.id)]
    if "FortPing" == type:
        if this_guild['fortPing'] != '0':
            try:
                role = get(ctx.guild.roles, id=int(this_guild['fortPing']))
                await ctx.guild.get_member(ctx.user.id).remove_roles(role)
                await ctx.response.send_message("Role removed")
                if this_guild['logChannel'] != '0':
                    await bot.get_channel(int(this_guild["logChannel"])).send(
                        "Removed " + str(ctx.user.id) + " / " + str(
                            ctx.user.display_name) + " from FortPings")
            except discord.Forbidden:
                await bot.get_guild(int(ctx.guild.id)).owner.send(
                    "Something went wrong when either removing a permission from a user or  when trying to post it in the log channel")
            except discord.HTTPException:
                logger.error(HTTP_ERROR)
    elif "CityPing" == type:
        if this_guild['cityPing'] != '0':
            try:
                role = get(ctx.guild.roles, id=int(this_guild['cityPing']))
                await ctx.guild.get_member(ctx.user.id).remove_roles(role)
                await ctx.response.send_message("Role removed")
                if this_guild['logChannel'] != '0':
                    await bot.get_channel(int(this_guild["logChannel"])).send(
                        "Removed " + str(ctx.user.id) + " / " + str(
                        ctx.user.display_name) + " from CityPings")
            except discord.Forbidden:
                await bot.get_guild(int(ctx.guild.id)).owner.send(
                    "Something went wrong when either removing a permission from a user or  when trying to post it in the log channel")
            except discord.HTTPException:
                logger.error(HTTP_ERROR)
    elif "Event" == type:
        if args is None:
            await ctx.response.send_message("When removing an event you need to specify the id which can be found using list command")
        elif not remove_event(ctx.guild.id, args):
            await ctx.response.send_message("There is no such event to remove")
        else:
            await ctx.response.send_message("Event removed")
    else:
        await ctx.response.send_message("No such remove option")


@tree.command(name="list", description="Command group to list events")
@app_commands.describe(type="What to list")
async def list(ctx, type: Literal['Event']):
    this_guild = bot.confs[str(ctx.guild.id)]
    if type == "Event":
        events = this_guild['events']
        for event in events:
            await ctx.response.send_message(embed=make_embed("Event", event, 0x038cfc, "", events[event]))
        if len(events) == 0:
            await ctx.response.send_message("No events in the database for this server")
    else:
        await ctx.response.send_message("Sorry but currently the only thing that can be listed is events")


@tree.command(name="announce", description="Announce things through all servers the bot is present on", guild=discord.Object(id=bot.TUE))
@app_commands.describe(message="What to announce")
async def announce(ctx, message: str):
    if ctx.user.id == 173443339025121280:
        for guild in bot.confs:
            this_guild = bot.confs[guild]
            if this_guild['enabled'] == '1' and this_guild['announceChannel'] != '0':
                try:
                    bot.lastAnnounceMessage[guild] = await bot.get_channel(int(this_guild['announceChannel'])).send(
                        embed=make_embed("Announcement from Natherul", message, 0x00ff00, ANNOUNCE_ICON,
                                         {}))
                except (discord.Forbidden, ValueError, TypeError):
                    logger.warning("announcement channel wrong in: " + str(this_guild) + " removing the announce channel from it")
                    this_guild['announceChannel'] = "0"
                    bot.confs[str(ctx.guild.id)] = this_guild
                    save_conf()
                except discord.HTTPException:
                    logger.error(HTTP_ERROR)
    else:
        await ctx.response.send_message("This command is locked to only be useable by Natherul")


@tree.command(name="configure", description="Command group to configure the bot on your server")
@app_commands.describe(option="What setting to change", args="The setting for the option")
@app_commands.default_permissions(administrator=True)
async def configure(ctx, option: Literal['announceChannel', 'logChannel', 'welcomeMessage', 'leaveMessage', 'boardingChannel', 'stoNewsChannel', 'fortPing', 'cityPing', 'moderator', 'chatModeration', 'allowTempChannels', 'removeAnnounce', 'announceServmsg', 'eventChannel', 'help'], args: Optional[str]):
    if ctx.user.id == ctx.guild.owner.id or ctx.user.id == 173443339025121280:
        if str(ctx.guild.id) not in bot.confs.keys():
            this_guild = bot.allconf
            bot.confs[str(ctx.guild.id)] = this_guild
            save_conf()
            await ctx.response.send_message("The guild was missing from the internal database and it has been added with no values, please configure the bot with all info it needs. (The command you entered was not saved)")
        elif option == "help" or args is None:
            await ctx.response.send_message(embed=make_embed("Available Configure Commands", "These are the configure commands available", 0xfa00f2, QUESTION_ICON, bot.configDesc))
        elif option in ("announceChannel", "logChannel", "boardingChannel", "eventChannel", "stoNewsChannel"):
            tmp_guild = ctx.guild
            tmp_channels = tmp_guild.text_channels
            for channel in tmp_channels:
                if args == str(channel.id) or args == channel.name:
                    this_guild = bot.confs[str(ctx.guild.id)]
                    this_guild[option] = args
                    bot.confs[str(ctx.guild.id)] = this_guild
                    await ctx.response.send_message(option + NOW_SET_TO_ + args)
                    save_conf()
                    return
            await ctx.response.send_message("No channel found with that name or ID")
        elif option in ("fortPing", "cityPing", "moderator"):
            tmp_guild = ctx.guild
            tmp_roles = tmp_guild.roles
            for role in tmp_roles:
                if args == str(role.id) or args == role.name:
                    this_guild = bot.confs[str(ctx.guild.id)]
                    this_guild[option] = args
                    bot.confs[str(ctx.guild.id)] = this_guild
                    await ctx.response.send_message(option + NOW_SET_TO_ + args)
                    save_conf()
                    return
            await ctx.response.send_message("No role with that name or ID was found")
        elif option in ("removeAnnounce", "announceServmsg", "chatModeration", "allowTempChannels"):
            if args != "1" and args != "0":
                await ctx.response.send_message("For this setting you can only specify it being on (1) or off (0)")
            else:
                this_guild = bot.confs[str(ctx.guild.id)]
                this_guild[option] = args
                bot.confs[str(ctx.guild.id)] = this_guild
                await ctx.response.send_message(option + NOW_SET_TO_ + args)
                save_conf()
        # Currently this is only welcomeMessage/leaveMessage, but it can be set directly.
        else:
            this_guild = bot.confs[str(ctx.guild.id)]
            this_guild[option] = args
            bot.confs[str(ctx.guild.id)] = this_guild
            await ctx.response.send_message(option + NOW_SET_TO_ + args)
            save_conf()
    else:
        await ctx.response.send_message("You are neither a server owner nor Natherul so configuring the server is not allowed.")


@tree.command(name="kick", description="Kick member from the server")
@app_commands.describe(member="The member to kick", reason="The reason for the kick")
@app_commands.default_permissions(kick_members=True)
async def kick_member(ctx, member : discord.Member, reason : str):
    try:
        if member.id == bot.user.id:
            await ctx.response.send_message("You cannot kick the bot")
            return
        this_guild = bot.confs[str(ctx.guild.id)]
        if not is_mod(ctx.user.roles, this_guild):
            await ctx.response.send_message(NOT_MOD_STRING)
            return
        if ctx.guild.owner.id == member.id:
            await ctx.response.send_message("You cannot kick a server owner")
            return
        elif this_guild['logChannel'] != '0':
            await bot.get_channel(int(this_guild['logChannel'])).send(
                embed=make_embed("User Kicked", member.display_name + " was kicked by " +
                                 ctx.user.display_name, 0xfa0000, KICKED_ICON, {'Reason' : reason}))
        await member.kick(reason=reason)
        await ctx.response.send_message("User kicked")
    except discord.Forbidden:
        await bot.get_guild(ctx.guild.id).owner.send("Nath-bot is enabled on your server but does not have the permissions to kick someone even though a moderation group has been set.")
    except discord.HTTPException:
        logger.error(HTTP_ERROR)
    
    
@tree.command(name="ban", description="Ban member from the server")
@app_commands.describe(member="The member to ban", reason="The reason for the ban")
@app_commands.default_permissions(ban_members=True)
async def ban_member(ctx, member : discord.Member, reason : str):
    try:
        if member.id == bot.user.id:
            await ctx.response.send_message("You cannot ban the bot")
            return
        this_guild = bot.confs[str(ctx.guild.id)]
        if not is_mod(ctx.user.roles, this_guild):
            await ctx.response.send_message(NOT_MOD_STRING)
            return
        if ctx.guild.owner.id == member.id:
            await ctx.response.send_message("You cannot ban a server owner")
            return
        elif this_guild['logChannel'] != '0':
            await bot.get_channel(int(this_guild['logChannel'])).send(
                embed=make_embed("User Banned", member.display_name + " was banned by " +
                                 ctx.user.display_name, 0xfa0000, BANNED_ICON, {'Reason' : reason}))
        await member.ban(reason=reason)
        await ctx.response.send_message("User banned")
    except discord.Forbidden:
        await bot.get_guild(ctx.guild.id).owner.send("Nath-bot is enabled on your server but does not have the permissions to ban someone even though a moderation group has been set.")
    except discord.HTTPException:
        logger.error(HTTP_ERROR)


@tree.command(name="purge", description="Purges a set number of messages from the current channel")
@app_commands.describe(number="The number of messages to delete", reason="The reason for the purge")
@app_commands.default_permissions(manage_messages=True)
async def purge(ctx, number : int, reason : str):
    this_guild = bot.confs[str(ctx.guild.id)]
    if not is_mod(ctx.user.roles, this_guild):
        await ctx.response.send_message(NOT_MOD_STRING)
        return
    messages = [message async for message in ctx.channel.history(limit=number)]
    await ctx.response.send_message(str(number) + " messages will be purged")
    try:
        await ctx.channel.delete_messages(messages, reason=reason)
        if this_guild['logChannel'] != '0':
            message = "{moderator} pruned {channel} of {number} of messages".format(
                moderator=ctx.user.display_name, number=number, channel=ctx.channel.name)
            await bot.get_channel(int(this_guild['logChannel'])).send(
                embed=make_embed("Channel Pruned", message, 0xfa0000, "", {'Reason': reason}))
    except discord.Forbidden:
        await bot.get_guild(ctx.guild.id).owner.send("Nath-bot is enabled on your server but does not have the permissions to purge messages though moderation group has been set.")
    except discord.HTTPException:
        logger.error(HTTP_ERROR)


@tree.command(name="citystat", description="Command to return the stats for cities in RoR")
async def citystat(ctx):
    await ctx.response.send_message("Current gathered stats for cities", file=File('citystat.csv'))


@tree.command(name="fortstat", description="Command to return the stats for forts in RoR")
async def fortstat(ctx):
    await ctx.response.send_message("Current gathered stats for forts", file=File('fortstat.csv'))


@tree.command(name="debug", description="Debug command to print information that Nath will want to troubleshoot issues")
@app_commands.default_permissions(administrator=True)
async def debug(ctx):
    this_guild = bot.confs[str(ctx.guild.id)]
    await ctx.response.send_message(embed=make_embed("These are the current settings for this server", "", 0xd8de0c,
                                                QUESTION_ICON,
                                                this_guild))


@tree.command(name="editannounce", description="Edit previous announcement", guild=discord.Object(id=bot.TUE))
@app_commands.describe(message="What to edit the message to")
async def edit_announce(ctx, message: str):
    if ctx.user.id == 173443339025121280:
        for old_message in bot.lastAnnounceMessage:
            bot.lastAnnounceMessage[old_message].edit(
                embed=make_embed("Announcement from Natherul", message, 0x00ff00, ANNOUNCE_ICON, {}))
        await ctx.response.send_message("Announcement updated")
    else:
        await ctx.response.send_message("This command is locked to only be usable by Natherul")


@bot.event
async def on_message(message):
    """This is the method to check content of someone's message"""
    # do not listen to bots own messages
    if message.author.id == bot.user.id:
        return
    # do not allow PMs to the bot
    elif "Direct Message" in str(message.channel):
        await message.author.send("im sorry but I do not respond to DMs.\nhttps://www.youtube.com/watch?v=agUaHwxcXHY")
    # Message moderation
    else:
        guild = bot.confs[str(message.guild.id)]
        if guild['chatModeration'] == '1':
            if set(bot.bad_domains).intersection(set(message.content.split())):
                # The message contained a bad domain and should be blocked
                bot.lastDeletedMessage = message.content
                await message.delete()
                if guild['logChannel'] == '0':
                    return
                else:
                    try:
                        await bot.get_channel(int(guild['logChannel'])).send(
                            embed=make_embed("Message automatically removed by bot", bot.lastDeletedMessage, 0xfa0000, ERROR_ICON, {"Reason": "Contained bad link"}))
                    except discord.Forbidden:
                        await bot.get_guild(message.guild.id).owner.send(LOG_PERM_ERROR)
                    except discord.HTTPException:
                        logger.error(HTTP_ERROR)


@bot.event
async def on_member_join(member):
    """If someone joins a guild the bot (if configured to do so) will greet them"""
    guild = bot.confs[str(member.guild.id)]
    if guild['boardingChannel'] != '0' and guild['welcomeMessage'] != '0':
        message = message_formatter_member(guild['welcomeMessage'], member, False)
        try:
            await bot.get_channel(int(guild["boardingChannel"])).send(message)
        except discord.Forbidden:
            await bot.get_guild(member.guild.id).owner.send(
                "Nath-bot is enabled on your server but does not have the permissions to send messages to the boarding channel though a boarding channel is set.")
        except discord.HTTPException:
            logger.error(HTTP_ERROR)


@bot.event
async def on_member_remove(member):
    """If a member leaves the server the bot will (if configured to do so) say that they left as well as
     check if the leaving was because of a moderator action."""
    guild = bot.confs[str(member.guild.id)]
    if guild['removeAnnounce'] != '0' and guild['logChannel'] != '0':
        this_guild = bot.get_guild(member.guild.id) 
        async for entry in this_guild.audit_logs(limit=1):
            # this is only the most recent event due to limit set above
            if entry.user.id == bot.user.id:
                # Bot kicks and bans are already handled in its commands so no need to send it twice.
                return
            try:
                if entry.action == discord.AuditLogAction.ban and entry.target.name == member.name:
                    msg = entry.user.name + " banned " + entry.target.name
                    await bot.get_channel(int(guild['logChannel'])).send(
                        embed=make_embed("User Banned", msg, 0xfa0000, BANNED_ICON, {"Reason" : entry.reason}))
                    return
                elif entry.action == discord.AuditLogAction.kick and entry.target.name == member.name:
                    msg = entry.user.name + " kicked " + entry.target.name
                    await bot.get_channel(int(guild['logChannel'])).send(
                        embed=make_embed("User Kicked", msg, 0xfa0000, KICKED_ICON, {"Reason" : entry.reason}))
                    return
            except discord.Forbidden:
                await bot.get_guild(member.guild.id).owner.send(LOG_PERM_ERROR)
            except discord.HTTPException:
                logger.error(HTTP_ERROR)
    if guild['leaveMessage'] != '0' and guild['boardingChannel'] != '0':
        message = message_formatter_member(guild['leaveMessage'], member, True)
        try:
            await bot.get_channel(int(guild["boardingChannel"])).send(message)
        except discord.Forbidden:
            await bot.get_guild(member.guild.id).owner.send(
                "Nath-bot is enabled on your server but does not have the permissions to send messages to the boarding channel though a boarding channel is set.")
        except discord.HTTPException:
            logger.error(HTTP_ERROR)


@bot.event
async def on_member_update(before, after):
    """If a member get edited the bot will check if it was due to a moderator action and log that"""
    guild = bot.confs[str(before.guild.id)]
    if guild['logChannel'] == '0':
        return
    # A role has been added or removed
    this_guild = bot.get_guild(before.guild.id)
    try:
        async for entry in this_guild.audit_logs(limit=1):
            if entry.user.id == bot.user.id:
                # We always handle logging when the bot does something so this is to not log it twice
                return
            elif before.roles != after.roles:
                if entry.action == discord.AuditLogAction.member_role_update and entry.target.name == after.name:
                    action = " added " if len(after.roles) > len(before.roles) else " removed "
                    role = ""
                    verb = ""
                    for old_role in before.roles:
                        if old_role not in after.roles:
                            role = old_role
                            verb = "from"
                    if role == "":
                        for new_role in after.roles:
                            if new_role not in before.roles:
                                role = new_role
                                verb = "to"
                    message = "{moderator} {action} {role} {verb} {target}".format(
                        action=action, moderator=entry.user.display_name, target=entry.target.display_name, role=role, verb=verb)
                    await bot.get_channel(int(guild['logChannel'])).send(
                        embed=make_embed("Role update", message, 0xfa0000, "", {}))
                    return
            elif before.display_name != after.display_name:
                if entry.action == discord.AuditLogAction.member_update and entry.target.name == after.name:
                    message = "{moderator} changed the name of {target} (account name) to {newname}".format(
                        moderator=entry.user.display_name, target=entry.target.name, newname=after.display_name)
                    await bot.get_channel(int(guild['logChannel'])).send(
                        embed=make_embed("Name updated", message, 0xfa0000, "", {}))
                    return
            elif entry.action == discord.AuditLogAction.unban and entry.target.name == after.name:
                message = "{moderator} unbanned {target} (account name)".format(
                    moderator=entry.user.display_name, target=entry.target.name)
                await bot.get_channel(int(guild['logChannel'])).send(
                    embed=make_embed("Member unbanned", message, 0xfa0000, "", {}))
                return
    except discord.Forbidden:
        await this_guild.owner.send("Nath-bot is enabled on your server but the bot does not have the permissions to look at the audit log or does not have the permissions to post in the log channel and a log channel is set.")
    except discord.HTTPException:
        logger.error(HTTP_ERROR)


@bot.event
async def on_message_edit(before, after):
    """If a message gets edited the bot can announce that someone has changed their message"""
    guild = bot.confs[str(before.guild.id)]
    if guild['logChannel'] == '0':
        return

    try:
        if before.content != after.content:
            await bot.get_channel(int(guild['logChannel'])).send(
                embed=make_embed("Message updated", before.author.display_name +
                                 "s message has been changed", 0xfa0000, "",
                                 {'Before' : before.content, 'After' : after.content}))
        elif before.pinned != after.pinned:
            moderator = ""
            this_guild = bot.get_guild(before.guild.id)
            async for entry in this_guild.audit_logs(limit=1):
                if entry.action == discord.AuditLogAction.message_pin or entry.action == discord.AuditLogAction.message_unpin:
                    moderator = entry.user.display_name
            message = before.author.display_name + "s message has " + "been pinned" if after.pinned else\
                "has had its pinned status removed" + " by " + moderator
            await bot.get_channel(int(guild['logChannel'])).send(
                embed=make_embed("Pin edit", message, 0xfa0000, "", {'Message': before.content}))
    except discord.Forbidden:
        await bot.get_guild(before.guild.id).owner.send(LOG_PERM_ERROR)
    except discord.HTTPException:
        logger.error(HTTP_ERROR)


@bot.event
async def on_message_delete(message):
    """If a message gets deleted the bot can find it and see if it was done by a moderator or its author"""
    guild = bot.confs[str(message.guild.id)]
    if guild['logChannel'] == '0' or bot.lastDeletedMessage == message.content:
        return
    try:
        this_guild = bot.get_guild(message.guild.id)
        async for entry in this_guild.audit_logs(limit=1):
            who_did = ""
            if entry.action == discord.AuditLogAction.message_delete:
                who_did = entry.user.display_name
            else:
                who_did = message.author.display_name
            await bot.get_channel(int(guild['logChannel'])).send(
                embed=make_embed("Message deletion", message.content, 0xfa0000, "", {'Who deleted message': who_did}))
    except discord.Forbidden:
        await bot.get_guild(message.guild.id).owner.send(LOG_PERM_ERROR)
    except discord.HTTPException:
        logger.error(HTTP_ERROR)


@bot.event
async def on_thread_create(thread):
    """If a thread is created the bot should see it and log it if logging is on"""
    guild = bot.confs[str(thread.guild.id)]
    if guild['logChannel'] == '0':
        return
    try:
        this_guild = bot.get_guild(thread.guild.id)
        async for entry in this_guild.audit_logs(limit=1):
            who_did = ""
            if entry.action == discord.AuditLogAction.thread_create:
                who_did = entry.user.display_name
            else:
                who_did = thread.owner.display_name
            await bot.get_channel(int(guild['logChannel'])).send(
                embed=make_embed("Thread creation", thread.starter_message, 0xfa0000, "", {'Who created thread': who_did}))
    except discord.Forbidden:
        await bot.get_guild(thread.guild.id).owner.send(LOG_PERM_ERROR)
    except discord.HTTPException:
        logger.error(HTTP_ERROR)


@bot.event
async def on_thread_delete(thread):
    """If a thread is removed then the bot should log it if logging is on"""
    guild = bot.confs[str(thread.guild.id)]
    if guild['logChannel'] == '0':
        return
    try:
        this_guild = bot.get_guild(thread.guild.id)
        async for entry in this_guild.audit_logs(limit=1):
            who_did = ""
            if entry.action == discord.AuditLogAction.thread_delete:
                who_did = entry.user.display_name
            else:
                who_did = thread.owner.display_name
            await bot.get_channel(int(guild['logChannel'])).send(
                embed=make_embed("Thread deletion", thread.starter_message, 0xfa0000, "", {'Who deleted thread': who_did}))
    except discord.Forbidden:
        await bot.get_guild(thread.guild.id).owner.send(LOG_PERM_ERROR)
    except discord.HTTPException:
        logger.error(HTTP_ERROR)


@bot.event
async def on_thread_update(before, after):
    """If the thread gets updated the bot should log it if logging is on"""
    guild = bot.confs[str(before.guild.id)]
    if guild['logChannel'] == '0':
        return
    try:
        if before.starter_message != after.starter_message:
            await bot.get_channel(int(guild['logChannel'])).send(
                embed=make_embed("Thread updated", before.owner.display_name +
                                 "s message has been changed", 0xfa0000, "",
                                 {'Before' : before.starter_message, 'After' : after.starter_message}))
        elif before.locked != after.locked:
            moderator = ""
            this_guild = bot.get_guild(before.guild.id)
            async for entry in this_guild.audit_logs(limit=1):
                if entry.action == discord.AuditLogAction.thread_update:
                    moderator = entry.user.display_name
            message = before.owner.display_name + "s thread has " + "been locked" if after.locked else\
                "has been unlocked" + " by " + moderator
            await bot.get_channel(int(guild['logChannel'])).send(
                embed=make_embed("Thread edit", message, 0xfa0000, "", {'Thread': before.starter_message}))
    except discord.Forbidden:
        await bot.get_guild(before.guild.id).owner.send(LOG_PERM_ERROR)
    except discord.HTTPException:
        logger.error(HTTP_ERROR)


@tasks.loop(minutes=10)
async def sto_news_check(self):
    """Method to check for new news items from star trek online"""
    new_news_ids = []
    for news_entry in sto_news.get_sto_news():
        new_news_ids.append(news_entry['id'])
        if news_entry['id'] not in self.sto_news:
            for guild in self.confs:
                this_guild = self.confs[guild]
                if this_guild['stoNewsChannel'] != '0':
                    try:
                        await self.get_channel(int(this_guild['stoNewsChannel'])).send(
                            embed=make_embed(news_entry['title'], news_entry['summary'], 0x1356e8, news_entry['images']['img_microsite_thumbnail']['url'], {}))
                    except discord.Forbidden:
                        await bot.get_guild(int(guild)).owner.send(
                            "Nath-bot is enabled on your server but does not have the permissions to send messages to the sto news channel channel though a channel is set for it.")
                    except discord.HTTPException:
                        logger.error(HTTP_ERROR)
    self.sto_news = new_news_ids
    f = open('sto_news.txt', 'w')
    f.write(str(new_news_ids))
    f.close()


@tasks.loop(seconds=60)
async def event_check(self):
    """Help method to see if we need to announce that an event is happening soon"""
    for guild in self.confs:
        this_guild = self.confs[guild]
        if this_guild['eventChannel'] != '0':
            events = this_guild['events']
            events_to_remove = []
            for event in events:
                event_time = datetime.strptime(events[event]['UTC Time'], self.TIME_STRING)
                reminder_time = event_time - timedelta(minutes=30)
                if datetime.utcnow() > reminder_time:
                    try:
                        await self.get_channel(int(this_guild['eventChannel'])).send(
                            embed=make_embed("Event is in less than 30 minutes!", event, 0x038cfc, "", events[event]))
                    except discord.Forbidden:
                        await bot.get_guild(int(guild)).owner.send(
                            "Nath-bot is enabled on your server but does not have the permissions to send messages to the event channel though an event channel is set.")
                    except discord.HTTPException:
                        logger.error(HTTP_ERROR)
                    events_to_remove.append(event)
            for event in events_to_remove:
                remove_event(guild, event)

@tasks.loop(seconds=60)
async def channel_check(self):
    """Help method to check for channels created by the bot that is not empty and should be deleted"""
    for guild in self.confs:
        this_guild = self.confs[guild]
        to_remove = []
        current_channels = this_guild['tempChannels']
        for temp_channel in current_channels:
            if len(self.get_channel(int(temp_channel)).members) == 0:
                try:
                    await self.get_channel(int(temp_channel)).delete(
                        reason="The temporary channel was empty and has been deleted as a result")
                    to_remove.append(temp_channel)
                except discord.Forbidden:
                    await bot.get_guild(int(guild)).owner.send(
                        "Nath-bot is enabled on your server but does not have the permissions delete channels even though it has created at least one temporary channel.")
                except discord.HTTPException:
                    logger.error(HTTP_ERROR)
        
        for old_channel in to_remove:
            current_channels.remove(old_channel)
        this_guild['tempChannels'] = current_channels
        save_conf()


def is_mod(user_roles, this_guild):
    """Help method to see if the current user roles contain the set moderator role for the server"""
    for role in user_roles:
        if role.name == this_guild['moderator']:
            return True
    if not is_mod:
        return False


def message_formatter_member(message, member, is_leaving):
    """Help function to substitute member specific message parts"""
    return message.format(
        display_name=member.display_name,
        id=member.id, name=member.name,
        mention=member.mention if not is_leaving else member.name)


def make_embed(title, description, colour, thumbnail, fields):
    """Help method to make embed messages which are prettier"""
    embed_var = discord.Embed(title=title, description=description, color=colour)
    if thumbnail != "":
        embed_var.set_thumbnail(url=thumbnail)
    for entry in fields:
        embed_var.add_field(name=entry, value=fields[entry], inline=False)
    return embed_var


def add_event(message, guildid, user):
    """Help method to add an event into the servers list of coming events"""
    now = str(time.time()).split('.')[0]
    this_guild = bot.confs[str(guildid)]
    events = this_guild['events']
    try:
        event_data = message.split(",")
        if datetime.fromtimestamp(int(event_data[0])) < datetime.utcnow():
            return 1
        this_event = {'Host' : user.display_name, 'Name' : event_data[1], 'Description' : event_data[2],
                      'UTC Time' : time.strftime(TIME_STRING, time.gmtime(int(event_data[0])))}
        events[now] = this_event
        this_guild['events'] = events
        bot.confs[str(guildid)] = this_guild
        save_conf()
        return 0
    except (OSError, OverflowError):
        return 1


def remove_event(guildid, id):
    """Help method to remove an event from a servers list of coming events"""
    this_guild = bot.confs[str(guildid)]
    events = this_guild['events']
    found = False
    if id in events:
        events.pop(id)
        found = True
    bot.confs[str(guildid)] = this_guild
    save_conf()
    return found


def save_conf():
    """Help method to update the saved configuration of a server"""
    g = open(CONFIGURATION, 'w')
    g.write(str(bot.confs))
    g.close()


bot.run(TOKEN, log_handler=h1)
