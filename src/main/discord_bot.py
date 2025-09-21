#!/usr/bin/env python3
import discord
import json
import ast
from discord.ext import tasks, commands
import domain_filter
import logging
import sys

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

logger = logging.getLogger()
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

bot = commands.Bot(command_prefix='!', intents=intents)
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
                  'chatModeration' : '(bool as int)If the bot should moderate chat messages',
                  'allowTempChannels' : '(bool as int)If anyone is allowed to ask the bot to make temporary voice channels',
                  'ignoredLogChannels' : '(String/int)What channels if any to exclude from logging changes in (comma separated if multiple channels)'}

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
               'stoNewsChannel' : '0',
               'ignoredLogChannels' : []}


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
        logger.info('Loading old scrape')
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
        logger.info('Loading guild configuration')
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
            logger.debug('Configuration missed in guild config. Remaking')
            c = open(CONFIGURATION, 'w')
            c.write(str(bot.confs))
            c.close()

        logger.info('Downloading new bad domain lists')
        domain_filter.download_files()
        logger.info('Processing downloaded files to make a full list of bad domains')
        bot.bad_domains = domain_filter.load_bad_domains()

        logger.info("Loading warhammer events module")
        await bot.load_extension('warhammer_events')
        logger.info("Loading moderation module")
        await bot.load_extension('moderation')
        logger.info("Loading TUE specific module")
        await bot.load_extension('tue_specifics')
        logger.info('LOADED')
        channel_check.start(bot)

        logger.info("starting sync")
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} commands")
            # Always sync directly to TUE
            bot.tree.copy_global_to(guild=discord.Object(id=bot.TUE))
            special_sync = await bot.tree.sync(guild=discord.Object(id=bot.TUE))
            logger.info(f"Synced {len(special_sync)} commands to TUE")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
        need_save = False
        for guild in bot.guilds:
            if str(guild.id) not in bot.confs:
                this_guild = bot.allconf
                bot.confs[str(guild.id)] = this_guild
                need_save = True
        if need_save:
            save_conf()


@bot.event
async def on_guild_join(guild):
    """When the bot joins a new server it will configure itself with the values it needs saved
    :param guild: The guild it happened on"""
    if str(guild.id) not in bot.confs:
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
    """When the bot gets removed from a server we set the config to not be enabled on that server
    :param guild: The guild it happened on"""
    this_guild = bot.confs[str(guild.id)]
    this_guild['enabled'] = '0'
    bot.confs[str(guild.id)] = this_guild
    save_conf()


@bot.event
async def on_message(message):
    """This is the method to check content of someone's message
    :param message: The message that the bot intercepted"""
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
    """If someone joins a guild the bot (if configured to do so) will greet them
    :param member: The member that joined"""
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
     check if the leaving was because of a moderator action.
     :param member: The member that left or got kicked/banned"""
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
    """If a member get edited the bot will check if it was due to a moderator action and log that
    :param before: The member object before changes
    :param after: The member object after changes"""
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
    """If a message gets edited the bot can announce that someone has changed their message
    :param before: The message object before changes
    :param after: The message object after changes"""
    guild = bot.confs[str(before.guild.id)]
    if guild['logChannel'] == '0' or str(before.channel.id) in guild['ignoredLogChannels']:
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
    """If a message gets deleted the bot can find it and see if it was done by a moderator or its author
    :param message: The message that got deleted"""
    guild = bot.confs[str(message.guild.id)]
    if guild['logChannel'] == '0' or bot.lastDeletedMessage == message.content or str(message.channel.id) in guild['ignoredLogChannels']:
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
    """If a thread is created the bot should see it and log it if logging is on
    :param thread: The thread object that got created"""
    guild = bot.confs[str(thread.guild.id)]
    if guild['logChannel'] == '0' or str(thread.channel.id) in guild['ignoredLogChannels']:
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
    """If a thread is removed then the bot should log it if logging is on
    :param thread: The thread object that got deleted"""
    guild = bot.confs[str(thread.guild.id)]
    if guild['logChannel'] == '0' or str(thread.channel.id) in guild['ignoredLogChannels']:
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
    """If the thread gets updated the bot should log it if logging is on
    :param before: The thread object before changes
    :param after: The thread object after changes"""
    guild = bot.confs[str(before.guild.id)]
    if guild['logChannel'] == '0' or str(before.channel.id) in guild['ignoredLogChannels']:
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


@tasks.loop(seconds=60)
async def channel_check(self):
    """Help method to check for channels created by the bot that is not empty and should be deleted
    :param self: The bot object"""
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
    """Help method to see if the current user roles contain the set moderator role for the server
    :param user_roles: the toles of a user
    :param this_guild: The guild configuration
    :return: if the user is part of the configured mod group (boolean)
    :rtype: bool"""
    for role in user_roles:
        if role.name == this_guild['moderator']:
            return True
    if not is_mod:
        return False


def message_formatter_member(message, member, is_leaving):
    """Help function to substitute member specific message parts
    :param message: The message to format
    :param member: the member that the edit is about
    :param is_leaving: boolean if the message is a leave message or not
    :return: a formatted message where entries has been replaced as wanted
    :rtype: str"""
    return message.format(
        display_name=member.display_name,
        id=member.id, name=member.name,
        mention=member.mention if not is_leaving else member.name)


def make_embed(title, description, colour, thumbnail, fields):
    """Help method to make embed messages which are prettier
    :param title: the title of the embed
    :param description: The description of the event
    :param colour: The colout that the embed gets
    :param thumbnail: A thumbnail for the embed (optional)
    :param fields: A dict with other fields to be embedded (optional)
    :return: the embed object
    :rtype: discord.Embed"""
    embed_var = discord.Embed(title=title, description=description, color=colour)
    if thumbnail != "":
        embed_var.set_thumbnail(url=thumbnail)
    for entry in fields:
        embed_var.add_field(name=entry, value=fields[entry], inline=False)
    return embed_var


def save_conf():
    """Help method to update the saved configuration of a server"""
    g = open(CONFIGURATION, 'w')
    g.write(str(bot.confs))
    g.close()


def load_list(variable, file_path):
    """Helper method to load a list from file
    :param variable: The variable to load the list into
    :param file_path: The path to the list to load"""
    f = open(file_path, 'r')
    content = f.read()
    f.close()
    for element in content.replace('[', '').replace(']', '').replace('"', '').replace("'", '').strip().split(','):
        variable.append(str(element.strip()))


bot.run(TOKEN)
