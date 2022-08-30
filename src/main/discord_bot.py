#!/usr/bin/env python3
from datetime import datetime
from datetime import timedelta
from typing import Literal, Optional
import discord
#import asyncio
from discord.utils import get
#import soronline
from discord import File
import json
import time
import ast
from discord.ext import tasks
from discord import app_commands


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
bot.commandDescriptions = {'configure': 'Commands to configure the bot (these can only be issued by the owner of the discord and there are multiple subcommands here)', 'citystat' : 'Posts the statistics for cities', 'fortstat' : 'Posts the statistics for fortresses', 'add Fortping' : 'Adds you to the group that gets pinged on fortresses', 'add CityPing' : 'Adds you to the group that gets pinged on cities', 'remove FortPing' : 'Removes you from the group that gets pinged in fortresses', 'remove CityPing' : 'Removes you from the group that gets pinged when cities happen', 'add Event' : 'Adds an event to the bot using syntax: "epoch,name,description" (https://www.epochconverter.com/)', 'remove Event' : 'Removes an event with the specified ID', 'list Event' : 'Lists all events for the guild'}
bot.configureCommands = ['announceChannel', 'logChannel', 'welcomeMessage', 'boardingChannel', 'fortPing', 'cityPing', 'removeAnnounce', 'announceServmsg', 'eventChannel']
bot.configDesc = {'announceChannel' : '(String/int)What channel to post campaign to (either Channel name or channelID specified)', 'logChannel' : '(String/int)What channel to pot logs about moderation or role changes (either channel name or channelID specified)', 'welcomeMessage' : '(String)What the bot should greet someone that joins the server with', 'boardingChannel': '(String/int)What channel to post welcome messages to (either channel name or channelID specified)', 'fortPing' : '(String/int)What role to attatch to announcement of campaign when a fort happens (role name or roleID specified)', 'cityPing' : '(String/int)What role to attach to announcement of campagin when a city happens(role name or roleID specified)', 'removeAnnounce' : '(bool as int)If the bot should post in the log channel when someone gets kicked or banned from the server', 'announceServmsg': '(bool as int)If the bot should announce issues or other messages from soronline.us', 'eventChannel' : '(String/int)What channel to post event messages to (either channel name or channelID specified)'}
bot.allconf = {'announceChannel' : '0', 'logChannel' : '0', 'welcomeMessage' : '0', 'boardingChannel' : '0', 'fortPing' : '0', 'cityPing' : '0', 'enabled' : '1', 'removeAnnounce': '0', 'announceServmsg' : '0', "eventChannel" : "0", "events" : {}}
bot.confs = {}
bot.lastCityTime = 0
bot.servmsg = ""
bot.lastannounce = ""
bot.lasterr = ""

# Constants
bot.QUESTION_ICON = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Question_mark_%28black%29.svg/1200px-Question_mark_%28black%29.svg.png"
bot.ANNOUNCE_ICON = "http://tue.nu/misc/announce.png"
bot.BANNED_ICON = "https://e7.pngegg.com/pngimages/1003/312/png-clipart-hammer-game-pension-review-internet-crouton-hammer-technic-discord-thumbnail.png"
bot.KICKED_ICON = "https://p7.hiclipart.com/preview/825/776/55/karate-kick-martial-arts-taekwondo-clip-art-kicked-thumbnail.jpg"
bot.ERROR_ICON = "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Error.svg/1200px-Error.svg.png"
bot.ROR_ICON = "http://www.tue.nu/misc/ror.png"
bot.TIME_STRING = "%Y-%m-%d %H:%M:%S"
bot.CONFIGURATION = "guilds.txt"
bot.DESTRO_STRING = ",Destruction\n"
bot.ORDER_STRING = ",Order\n"

# for if we want to edit announces
bot.lastAnnounceMessage = {}

@bot.event
async def on_ready():
    if bot.started == False:
        bot.started = True
        print('Logged in as')
        print(bot.user.name)
        print(bot.user.id)
        print('------')
        print(str(datetime.utcnow().strftime(bot.TIME_STRING)) + ' loading old scrape')
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
        # the configurations for the diff disc servers
        g = open(bot.CONFIGURATION, 'r')
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
            c = open(bot.CONFIGURATION, 'w')
            c.write(str(bot.confs))
            c.close()

        print(str(datetime.utcnow().strftime(bot.TIME_STRING)) + ' LOADED')
        event_check.start(bot)
        #zone_check.start(bot)
        await tree.sync()
        await tree.sync(guild=discord.Object(id=bot.TUE))


@bot.event
async def on_guild_join(guild):
    if guild.id not in bot.confs:
        this_guild = {"announceChannel" : "0", "logChannel" : "0", "welcomeMessage" : "0", "boardingChannel" : "0", "fortPing" : "0", "cityPing" : "0", 'enabled' : '1', 'removeAnnounce' : '0', 'announceServmsg' : '0', 'eventChannel' : '0', "events" : {}}
        bot.confs[str(guild.id)] = this_guild
        save_conf()
    else:
        this_guild = bot.confs[str(guild.id)]
        this_guild['enabled'] = '1'
        bot.confs[str(guild.id)] = this_guild
        save_conf()
    await guild.owner.send('Thanks for inviting me to the server. To get started you need to set up what channels I should talk to when announcing. Do this by:\n"' + bot.command_prefix + 'configure" in any channel in the guild and I will respond with your options.\nYou can at any time also issue: "' + bot.command_prefix + 'help" to see what commands are avilable.')


@bot.event
async def on_guild_remove(guild):
    this_guild = bot.confs[str(guild.id)]
    this_guild['enabled'] = '0'
    bot.confs[str(guild.id)] = this_guild
    save_conf()


@tree.command(name="help", description="The help command for the bot")
async def helpmessage(ctx):
    await ctx.response.send_message(embed=make_embed("Available Commands", "These are the commands that you can use", 0xfa00f2, bot.QUESTION_ICON, bot.commandDescriptions))


@tree.command(name="add", description="Command group to add pings or events")
@app_commands.describe(type="What to add", args="Event parameters")
async def add(ctx, type: Literal['FortPing', 'CityPing', 'Event'], args: Optional[str]):
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
            except:
                await bot.get_guild(int(ctx.guild.id)).owner.send(
                    "Something went wrong when attempting to add a role or when trying to post to the log channel")
    elif "CityPing" == type:
        if this_guild['cityPing'] != '0':
            try:
                role = get(ctx.guild.roles, id=int(this_guild['cityPing']))
                await ctx.guild.get_member(ctx.user.id).add_roles(role)
                await ctx.response.send_message("Role added")
                if this_guild['logChannel'] != '0':
                    await bot.get_channel(int(this_guild["logChannel"])).send(
                        "Added " + str(ctx.user.id) + " / " + str(ctx.user.display_name) + " to CityPings")
            except:
                await bot.get_guild(int(ctx.guild.id)).owner.send(
                    "Something went wrong when attempting to add a role or when trying to post to the log channel")
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
            except:
                await bot.get_guild(int(ctx.guild.id)).owner.send(
                    "Something went wrong when either removing a permission from a user or  when trying to post it in the log channel")
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
            except:
                await bot.get_guild(int(ctx.guild.id)).owner.send(
                    "Something went wrong when either removing a permission from a user or  when trying to post it in the log channel")
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
                        embed=make_embed("Announcement from Natherul", message, 0x00ff00, bot.ANNOUNCE_ICON,
                                         {}))
                except:
                    print("announcement channel wrong in: " + str(this_guild))
    else:
        await ctx.response.send_message("This command is locked to only be useable by Natherul")


@tree.command(name="configure", description="Command group to configure the bot on your server")
@app_commands.describe(option="What setting to change", args="The setting for the option")
async def configure(ctx, option: Literal['announceChannel', 'logChannel', 'welcomeMessage', 'boardingChannel', 'fortPing', 'cityPing', 'removeAnnounce', 'announceServmsg', 'eventChannel', 'help'], args: Optional[str]):
    if ctx.user.id == ctx.guild.owner.id or ctx.user.id == 173443339025121280:
        if str(ctx.guild.id) not in bot.confs.keys():
            this_guild = {"announceChannel" : "0", "logChannel" : "0", "welcomeMessage" : "0", "boardingChannel" : "0", "fortPing" : "0", "cityPing" : "0", 'enabled' : '1', 'removeAnnounce' : '0', 'announceServmsg' : '0', 'eventChannel' : '0', 'events' : []}
            bot.confs[str(ctx.guild.id)] = this_guild
            save_conf()
            await ctx.response.send_message("The guild was missing from the internal database and it has been added with no values, please configure the bot with all info it needs. (The command you entered was not saved)")
            return
        if option == "help" or args is None:
            await ctx.response.send_message(embed=make_embed("Avilable Configure Commands", "These are the configure commands avilable", 0xfa00f2, bot.QUESTION_ICON, bot.configDesc))
            return
        if option == "announceChannel" or option == "logChannel" or option == "boardingChannel" or option == "eventChannel":
            tmp_guild = ctx.guild
            tmp_channels = tmp_guild.text_channels
            for channel in tmp_channels:
                if args == str(channel.id) or args == channel.name:
                    this_guild = bot.confs[str(ctx.guild.id)]
                    this_guild[option] = args
                    bot.confs[str(ctx.guild.id)] = this_guild
                    await ctx.response.send_message(option + " is now set to: " + args)
                    save_conf()
                    return
            await ctx.response.send_message("No channel found with that name or ID")
            return
        elif option == "fortPing" or option == "cityPing":
            tmp_guild = ctx.guild
            tmp_roles = tmp_guild.roles
            for role in tmp_roles:
                if args == str(role.id) or args == role.name:
                    this_guild = bot.confs[str(ctx.guild.id)]
                    this_guild[option] = args
                    bot.confs[str(ctx.guild.id)] = this_guild
                    await ctx.response.send_message(option + " is now set to: " + args)
                    save_conf()
                    return
            await ctx.response.send_message("No role with that name or ID was found")
            return
        elif option == "removeAnnounce" or option == "announceServmsg":
            if args != "1" and args != "0":
                await ctx.response.send_message("For this setting you can only specify it being on (1) or off (0)")
                return
            else:
                this_guild = bot.confs[str(ctx.guild.id)]
                this_guild[option] = args
                bot.confs[str(ctx.guild.id)] = this_guild
                await ctx.response.send_message(option + " is now set to: " + args)
                save_conf()
                return


@tree.command(name="citystat", description="Command to return the stats for cities in RoR")
async def citystat(ctx):
    await ctx.response.send_message("Current gathered stats for cities", file=File('citystat.csv'))


@tree.command(name="fortstat", description="Command to return the stats for forts in RoR")
async def fortstat(ctx):
    await ctx.response.send_message("Current gathered stats for forts", file=File('fortstat.csv'))


@tree.command(name="debug", description="Debug command to print information that Nath will want to troubleshoot issues")
async def debug(ctx):
    this_guild = bot.confs[str(ctx.guild.id)]
    await ctx.response.send_message(embed=make_embed("These are the current settings for this server", "", 0xd8de0c,
                                                bot.QUESTION_ICON,
                                                this_guild))


@tree.command(name="editannounce", description="Edit previous announcement", guild=discord.Object(id=bot.TUE))
@app_commands.describe(message="What to edit the message to")
async def edit_announce(ctx, message: str):
    if ctx.user.id == 173443339025121280:
        for old_message in bot.lastAnnounceMessage:
            bot.lastAnnounceMessage[old_message].edit(
                embed=make_embed("Announcement from Natherul", message, 0x00ff00, bot.ANNOUNCE_ICON, {}))
        await ctx.response.send_message("Announcement updated")
    else:
        await ctx.response.send_message("This command is locked to only be useable by Natherul")


@bot.event
async def on_message(message):
    # do not listen to bots own messages
    if message.author.id == bot.user.id:
        return
    # do not allow PMs to the bot
    elif "Direct Message" in str(message.channel):
        await message.author.send("im sorry but I do not respond to DMs.\nhttps://www.youtube.com/watch?v=agUaHwxcXHY")
        return


@bot.event
async def on_member_join(member):
    guild = bot.confs[str(member.guild.id)]
    if guild['boardingChannel'] != '0' and guild['welcomeMessage'] != '0':
        try:
            await bot.get_channel(int(guild["boardingChannel"])).send(guild['welcomeMessage'])
        except:
            await bot.get_guild(int(member.guild.id)).owner.send("I tried to send a welcome message in the boarding channel but failed. Please reconfigure what channel to send welcomes to.")


@bot.event
async def on_member_remove(member):
    guild = bot.confs[str(member.guild.id)]
    if guild['removeAnnounce'] != '0' and guild['logChannel'] != '0':
        this_guild = bot.get_guild(member.guild.id) 
        async for entry in this_guild.audit_logs(limit=1):
            # this is only the most recent event due to limit set abouve
            if entry.action == discord.AuditLogAction.ban and entry.target.name == member.name:
                msg = entry.user.name + " banned " + entry.target.name
                await bot.get_channel(int(guild['logChannel'])).send(embed=make_embed("User Banned", "A user was banned", 0xfa0000, bot.BANNED_ICON, {msg : entry.reason}))
            if entry.action == discord.AuditLogAction.kick and entry.target.name == member.name:
                msg = entry.user.name + " kicked " + entry.target.name
                await bot.get_channel(int(guild['logChannel'])).send(embed=make_embed("User Kicked", "A user was kicked", 0xfa0000, bot.KICKED_ICON, {msg : entry.reason}))


@tasks.loop(seconds=60)
async def event_check(self):
    for guild in bot.confs:
        this_guild = bot.confs[guild]
        if this_guild['eventChannel'] != '0':
            events = this_guild['events']
            events_to_remove = []
            for event in events:
                event_time = datetime.strptime(events[event]['UTC Time'], bot.TIME_STRING)
                reminder_time = event_time - timedelta(minutes=30)
                if datetime.utcnow() > reminder_time:
                    await bot.get_channel(int(this_guild['eventChannel'])).send(embed=make_embed("Event is in less than 30 minutes!", event, 0x038cfc, "", events[event]))
                    events_to_remove.append(event)
            for event in events_to_remove:
                remove_event(guild, event)


#@tasks.loop(seconds=120)
#async def zone_check(self):
#    await self.wait_until_ready()
#    now = str(datetime.utcnow().strftime(bot.TIME_STRING))
#    skip_city_log = True
#    try:
#        openzones = soronline.scrape()
#    except:
#        print(now + " something went wrong, soronline might be down")
#        return
#    if "Server" in openzones:
#        if bot.servmsg != openzones or bot.lasterr < bot.lastannounce:
#            bot.servmsg = openzones
#            bot.lasterr = now
#            for guild in bot.confs:
#                this_guild = bot.confs[guild]
#                try:
#                    if this_guild['announceServmsg'] == '1' and this_guild['announceChannel'] != '0':
#                        await bot.get_channel(int(this_guild["announceChannel"])).send(embed=make_embed("Error", "soronline.us is reporting the following error", 0xff0000, bot.ERROR_ICON, openzones))
#                except:
#                        await bot.get_guild(int(guild)).owner.send("I tried to announce the current zones but failed. Please reconfigure what channel to send announcements to.")
#                        continue
#        await asyncio.sleep(60)
#
#    else:
#        if len(bot.currentZones) == 0 and len(openzones) > 0:
#            bot.currentZones = openzones
#        elif len(openzones) > 0 and bot.currentZones != openzones:
#            print(now + " sent " + str(openzones) + " to channels")
#            for guild in bot.confs:
#                this_guild = bot.confs[guild]
#                if this_guild['enabled'] == '0':
#                    continue
#                if this_guild['announceChannel'] != '0':
#                    try:
#                        if "Server" in openzones and this_guild['announceServmsg'] == '1':
#                            await bot.get_channel(int(this_guild["announceChannel"])).send(embed=make_embed("Error", "soronline.us is reporting the following error", 0xff0000, bot.ERROR_ICON, openzones))
#                        else:
#                            await bot.get_channel(int(this_guild["announceChannel"])).send(embed=make_embed("Current Zones", "These are the current zones reported by soronline.us", 0xe08a00, bot.ROR_ICON, openzones))
#                    except:
#                        await bot.get_guild(int(guild)).owner.send("I tried to announce the current zones but failed. Please reconfigure what channel to send announcements to.")
#                        print("skipped " + guild)
#                        continue
#                    for fort in bot.forts:
#                        if fort in openzones.values() and fort not in bot.currentZones.values() and this_guild[
#                            'fortPing'] != '0':
#                            guild2 = bot.get_guild(int(guild))
#                            try:
#                                role = get(guild2.roles, id=int(this_guild['fortPing']))
#                                await bot.get_channel(int(this_guild["announceChannel"])).send(role.mention)
#                            except:
#                                await bot.get_guild(int(guild)).owner.send("I tried to ping for fortresses but failed. Please reconfigure what group to ping")
#                    for city in bot.cities:
#                        if city in openzones.values() and city not in bot.currentZones.values() and time.time() > float(
#                                bot.lastCityTime):
#                            bot.lastCityTime = time.time() + 10800 #3 hours
#                            last_time = open('lastcity.txt', 'w')
#                            last_time.write(str(bot.lastCityTime))
#                            last_time.close()
#                            skip_city_log = False
#                            if this_guild['cityPing'] != '0':
#                                guild2 = bot.get_guild(int(guild))
#                                try:
#                                    role = get(guild2.roles, id=int(this_guild['cityPing']))
#                                    await bot.get_channel(int(this_guild["announceChannel"])).send(role.mention)
#                                except:
#                                    await bot.get_guild(int(guild)).owner.send("I tried to ping for city but failed. Please reconfigure what group to ping")
#            # check if a fort happened and is now over
#            for fort in bot.forts:
#                if fort in bot.currentZones.values() and fort not in openzones.values():
#                # dumb logic
#                    fortstat = open('fortstat.csv', 'a')
#                    #really really dumb
#                    if fort == "Reikwald":
#                        if "Praag" in openzones.values():
#                            fortstat.write(now + "," + fort + bot.ORDER_STRING)
#                        else:
#                            fortstat.write(now + "," + fort + bot.DESTRO_STRING)
#                    elif fort == "Shining Way":
#                        if "Dragonwake" in openzones.values():
#                            fortstat.write(now + "," + fort + bot.ORDER_STRING)
#                        else:
#                            fortstat.write(now + "," + fort + bot.DESTRO_STRING)
#                    elif fort == "Stonewatch":
#                        if "Thunder Mountain" in openzones.values():
#                            fortstat.write(now + "," + fort + bot.ORDER_STRING)
#                        else:
#                            fortstat.write(now + "," + fort + bot.DESTRO_STRING)
#                    elif fort == "The Maw":
#                        if "Praag" in openzones.values():
#                            fortstat.write(now + "," + fort + bot.DESTRO_STRING)
#                        else:
#                            fortstat.write(now + "," + fort + bot.ORDER_STRING)
#                    elif fort == "Fell Landing":
#                        if "Dragonwake" in openzones.values():
#                            fortstat.write(now + "," + fort + bot.DESTRO_STRING)
#                        else:
#                            fortstat.write(now + "," + fort + bot.ORDER_STRING)
#                    elif fort == "Butchers Pass":
#                        if "Thunder Mountain" in openzones.values():
#                            fortstat.write(now + "," + fort + bot.DESTRO_STRING)
#                        else:
#                            fortstat.write(now + "," + fort + bot.ORDER_STRING)
#
#                    fortstat.close()
#            for city in bot.cities:
#                if city in openzones.values() and city not in bot.currentZones.values() and skip_city_log == False:
#                    citystat = open('citystat.csv', 'a')
#                    citystat.write(now + "," + city + "\n")
#                    citystat.close()
#            bot.currentZones = openzones
#            bot.lastannounce = now


def make_embed(title, description, colour, thumbnail, fields):
    embed_var = discord.Embed(title=title, description=description, color=colour)
    if thumbnail != "":
        embed_var.set_thumbnail(url=thumbnail)
    for entry in fields:
        embed_var.add_field(name=entry, value=fields[entry], inline=False)
    return embed_var


def add_event(message, guildid, user):
    now = str(time.time()).split('.')[0]
    this_guild = bot.confs[str(guildid)]
    events = this_guild['events']
    try:
        event_data = message.split(",")
        if datetime.fromtimestamp(int(event_data[0])) < datetime.utcnow():
            return 1
        this_event = {'Host' : user.display_name, 'Name' : event_data[1], 'Description' : event_data[2], 'UTC Time' : time.strftime(bot.TIME_STRING, time.gmtime(int(event_data[0])))}
        events[now] = this_event
        this_guild['events'] = events
        bot.confs[str(guildid)] = this_guild
        save_conf()
        return 0
    except:
        return 1


def remove_event(guildid, id):
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
    g = open(bot.CONFIGURATION, 'w')
    g.write(str(bot.confs))
    g.close()


bot.run(TOKEN)
