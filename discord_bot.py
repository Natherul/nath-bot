from datetime import datetime
import discord
import asyncio
from discord.utils import get
#from discord.ext import commands
import soronline
from discord import File
import json
import time
import ast

TOKEN = ''
bot = discord.Client() 
bot.currentZones = ""
bot.forts = ['The Maw', 'Reikwald', 'Fell Landing', 'Shining Way', 'Butchers Pass', 'Stonewatch']
bot.cities = ['Inevitable City', 'Altdorf']
bot.started = False
bot.prefix = "|"
bot.commandDescriptions = {'configure': 'Commands to configure the bot (these can only be issued by the owner of the discord and there are multiple subcommands here)', 'citystat' : 'Posts the statistics for cities', 'fortstat' : 'Posts the statistics for fortresses', 'Add Fortping' : 'Adds you to the group that gets pinged on fortresses', 'Add CityPing' : 'Adds you to the group that gets pinged on cities', 'Remove FortPing' : 'Removes you from the group that gets pinged in fortresses', 'Remove CityPing' : 'Removes you from the group that gets pinged when cities happen'}
bot.configureCommands = ['announceChannel', 'logChannel', 'welcomeMessage', 'boardingChannel', 'fortPing', 'cityPing', 'removeAnnounce', 'announceServmsg']
bot.configDesc = {'announceChannel' : '(String/int)What channel to post campaign to (either Channel name or channelID specified)', 'logChannel' : '(String/int)What channel to pot logs about moderation or role changes (either channel name or channelID specified)', 'welcomeMessage' : '(String)What the bot should greet someone that joins the server with', 'boardingChannel': '(String/int)What channel to post welcome messages to (either channel name or channelID specified)', 'fortPing' : '(String/int)What role to attatch to announcement of campaign when a fort happens (role name or roleID specified)', 'cityPing' : '(String/int)What role to attach to announcement of campagin when a city happens(role name or roleID specified)', 'removeAnnounce' : '(bool as int)If the bot should post in the log channel when someone gets kicked or banned from the server', 'announceServmsg': '(bool as int)If the bot should announce issues or other messages from soronline.us'}
bot.allconf = {'announceChannel' : '0', 'logChannel' : '0', 'welcomeMessage' : '0', 'boardingChannel' : '0', 'fortPing' : '0', 'cityPing' : '0', 'enabled' : '1', 'removeAnnounce': '0', 'announceServmsg' : '0'}
bot.confs = {}
bot.lastCityTime = 0
bot.servmsg = ""
bot.lastannounce = ""
bot.lasterr = ""

@bot.event
async def on_ready():
    if bot.started == False:
        bot.started = True
        print('Logged in as')
        print(bot.user.name)
        print(bot.user.id)
        print('------')
        print(str(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")) + ' loading old scrape')
        #load last scrape
        f = open('result.txt', 'r')
        resultString = f.read()
        if resultString != "":
            bot.currentZones = ast.literal_eval(resultString)
        f.close()
        #used to make sure to not spam cityping and city stats
        l = open('lastcity.txt', 'r')
        bot.lastCityTime = l.read()
        l.close()
        #the configurations for the diff disc servers
        g = open('guilds.txt', 'r')
        bot.confs = json.loads(g.read().replace("'", '"'))
        g.close()
        remake = False
        for guild in bot.confs:
            thisGuild = bot.confs[str(guild)]
            for configuration in bot.allconf:
                if configuration not in thisGuild:
                    thisGuild[configuration] = bot.allconf[configuration]
                    bot.confs[str(guild)] = thisGuild
                    remake = True

        if remake == True:
            c = open('guilds.txt', 'w')
            c.write(str(bot.confs))
            c.close()

        await my_background_task(bot)

@bot.event
async def on_guild_join(guild):
    if guild.id not in bot.confs:
        thisGuild = {"announceChannel" : "0", "logChannel" : "0", "welcomeMessage" : "0", "boardingChannel" : "0", "fortPing" : "0", "cityPing" : "0", 'enabled' : '1', 'removeAnnounce' : '0', 'announceServmsg' : '0'}
        bot.confs[str(guild.id)] = thisGuild
        g = open('guilds.txt', 'w')
        g.write(str(bot.confs))
        g.close()
    else:
        thisGuild = bot.confs[str(guild.id)]
        thisGuild['enabled'] = '1'
        bot.confs[str(guild.id)] = thisGuild
        g = open('guilds.txt', 'w')
        g.write(str(bot.confs))
        g.close()
    await guild.owner.send('Thanks for inviting me to the server. To get started you need to set up what channels I should talk to when announcing. Do this by:\n"' + bot.prefix + 'configure" in any channel in the guild and I will respond with your options.\nYou can at any time also issue: "' + bot.prefix + 'help" to see what commands are avilable.')

@bot.event
async def on_guild_remove(guild):
    thisGuild = bot.confs[str(guild.id)]
    thisGuild['enabled'] = '0'
    bot.confs[str(guild.id)] = thisGuild
    g = open('guilds.txt', 'w')
    g.write(str(bot.confs))
    g.close()

@bot.event
async def on_message(message):
    #do not listen to bots own messages
    if message.author.id == bot.user.id:
        return
    #do not allow PMs to the bot
    if "Direct Message" in str(message.channel):
        await message.author.send("im sorry but I do not respond to DMs.\nhttps://www.youtube.com/watch?v=agUaHwxcXHY")
        return
    if message.content == bot.prefix or message.content == bot.prefix + "help":
        await message.channel.send(embed=makeEmbed("Available Commands", "These are the commands that you can use", 0xfa00f2, "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Question_mark_%28black%29.svg/1200px-Question_mark_%28black%29.svg.png", bot.commandDescriptions))
    if message.content.startswith(bot.prefix + "configure") and message.author.id == message.guild.owner.id:
        if str(message.guild.id) not in bot.confs.keys():
            thisGuild = {"announceChannel" : "0", "logChannel" : "0", "welcomeMessage" : "0", "boardingChannel" : "0", "fortPing" : "0", "cityPing" : "0", 'enabled' : '1', 'removeAnnounce' : '0', 'announceServmsg' : '0'}
            bot.confs[str(message.guild.id)] = thisGuild
            g = open('guilds.txt', 'w')
            g.write(str(bot.confs))
            g.close()
            await message.channel.send("The guild was missing from the internal database and it has been added with no values, please configure the bot with all info it needs. (The command you entered was not saved)")
            return
        if message.content == bot.prefix + "configure" or message.content == bot.prefix + "configure help":
            await message.channel.send(embed=makeEmbed("Avilable Configure Commands", "These are the configure commands avilable", 0xfa00f2, "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Question_mark_%28black%29.svg/1200px-Question_mark_%28black%29.svg.png", bot.configDesc))
            return
        found = False
        for command in bot.configureCommands:
            if command in message.content:
                found = True
                param = message.content.replace(bot.prefix + "configure " + command + " ", '')
                if command == 'announceChannel' or command == 'logChannel' or command == 'boardingChannel' or command == 'fortPing' or command == 'cityPing':
                    tmpGuild = message.guild
                    tmpChannels = tmpGuild.text_channels
                    tmpRoles = tmpGuild.roles
                    Found = False
                    if command == 'announceChannel' or command == 'logChannel' or command == 'boardingChannel':
                        for channel in tmpChannels:
                            if param == str(channel.id) or param == channel.name:
                                param = str(channel.id)
                                Found = True
                    else:
                        for role in tmpRoles:
                            if param == str(role.id) or param == role.name:
                                param = str(role.id)
                                Found = True

                    if Found == False:
                        await message.channel.send("The parameter you specified was not found, please try again. I accept both names and IDs.")
                        return
                thisGuild = bot.confs[str(message.guild.id)]
                thisGuild[command] = param
                bot.confs[str(message.guild.id)] = thisGuild
                await message.channel.send(command + " is now set to: " + param)
        if found == False:
            await message.channel.send(embed=makeEmbed("Available Commands", "These are the commands that you can use", 0xfa00f2, "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Question_mark_%28black%29.svg/1200px-Question_mark_%28black%29.svg.png", bot.commandDescriptions))
        else:
            g = open('guilds.txt', 'w')
            g.write(str(bot.confs))
            g.close()
    elif bot.prefix + "fortstat" in message.content:
        await message.channel.send("Current gathered stats for forts", file=File('fortstat.csv'))
    elif bot.prefix + "citystat" in message.content:
        await message.channel.send("Current gathered stats for cities", file=File('citystat.csv'))
    
    elif message.author.id == 173443339025121280 and bot.prefix + "announce" in message.content:
        #nath announce
        text = message.content.replace(bot.prefix + "announce ", '')
        for guild in bot.confs:
            thisGuild = bot.confs[guild]
            if thisGuild['enabled'] == '1' and thisGuild['announceChannel'] != '0':
                try:
                    await bot.get_channel(int(thisGuild['announceChannel'])).send(embed=makeEmbed("Announcement from Natherul", text, 0x00ff00, "http://tue.nu/misc/announce.png", {}))
                except:
                    print("announcement channel wrong in: " + thisGuild)

    elif bot.prefix + "Add " in message.content:
        thisGuild = bot.confs[str(message.guild.id)]
        if "FortPing" in message.content:
            if thisGuild['fortPing'] != '0':
                if thisGuild['logChannel'] != '0':
                    try:
                        role = get(message.guild.roles, id=int(thisGuild['fortPing']))
                        await message.guild.get_member(message.author.id).add_roles(role)
                        await bot.get_channel(int(thisGuild["logChannel"])).send("Added " + str(message.author.id) + " / " + str(message.author.display_name) + " to FortPings")
                    except:
                        await bot.get_guild(int(message.guild.id)).owner.send("I tried to send a message in the log channel but failed. Please reconfigure what channel to send logs to.")
        elif "CityPing" in message.content:
            if thisGuild['cityPing'] != '0':
                if thisGuild['logChannel'] != '0':
                    try:
                        role = get(message.guild.roles, id=int(thisGuild['cityPing']))
                        await message.guild.get_member(message.author.id).add_roles(role)
                        await bot.get_channel(int(thisGuild["logChannel"])).send("Added " + str(message.author.id) + " / " + str(message.author.display_name) + " to CityPings")
                    except:
                        await bot.get_guild(int(message.guild.id)).owner.send("I tried to send a message in the log channel but failed. Please reconfigure what channel to send logs to.")
    elif bot.prefix + "Remove " in message.content:
        thisGuild = bot.confs[str(message.guild.id)]
        if "FortPing" in message.content:
            if thisGuild['fortPing'] != '0':
                if thisGuild['logChannel'] != '0':
                    try:
                        role = get(message.guild.roles, id=int(thisGuild['fortPing']))
                        await message.guild.get_member(message.author.id).remove_roles(role)
                        await bot.get_channel(int(thisGuild["logChannel"])).send("Removed " + str(message.author.id) + " / " + str(message.author.display_name) + " from FortPings")
                    except:
                        await bot.get_guild(int(message.guild.id)).owner.send("I tried to send a message in the log channel but failed. Please reconfigure what channel to send logs to.")
        elif "CityPing" in message.content:
            if thisGuild['cityPing'] != '0':
                if thisGuild['logChannel'] != '0':
                    try:
                        role = get(message.guild.roles, id=int(thisGuild['cityPing']))
                        await message.guild.get_member(message.author.id).remove_roles(role)
                        await bot.get_channel(int(thisGuild["logChannel"])).send("Removed " + str(message.author.id) + " / " + str(message.author.display_name) + " from CityPings")
                    except:
                        await bot.get_guild(int(message.guild.id)).owner.send("I tried to send a message in the log channel but failed. Please reconfigure what channel to send logs to.")
        

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
        thisGuild = bot.get_guild(member.guild.id) 
        async for entry in thisGuild.audit_logs(limit=1):
            #this is only the most recent event due to limit set abouve
            if entry.action == discord.AuditLogAction.ban and entry.target.name == member.name:
                msg = entry.user.name + " banned " + entry.target.name
                await bot.get_channel(int(guild['logChannel'])).send(embed=makeEmbed("User Banned", "A user was banned", 0xfa0000, "https://e7.pngegg.com/pngimages/1003/312/png-clipart-hammer-game-pension-review-internet-crouton-hammer-technic-discord-thumbnail.png", {msg : entry.reason}))
            if entry.action == discord.AuditLogAction.kick and entry.target.name == member.name:
                msg = entry.user.name + " kicked " + entry.target.name
                await bot.get_channel(int(guild['logChannel'])).send(embed=makeEmbed("User Kicked", "A user was kicked", 0xfa0000, "https://p7.hiclipart.com/preview/825/776/55/karate-kick-martial-arts-taekwondo-clip-art-kicked-thumbnail.jpg", {msg : entry.reason}))


async def my_background_task(self):
    await self.wait_until_ready()
    while not self.is_closed():
        now = str(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        skipCityLog = True
        try:
            openzones = soronline.scrape()
        except:
            print(now + " something went wrong")
            await asyncio.sleep(60) 
            continue
        if "Server" in openzones:
            if bot.servmsg != openzones or int(bot.lasterr) < int(bot.lastannounce):
                bot.servmsg = openzones
                bot.lasterr = now
                for guild in bot.confs:
                    thisGuild = bot.confs[guild]
                    try:
                        if thisGuild['announceServmsg'] == '1' and thisGuild['announceChannel'] != '0':
                            await bot.get_channel(int(thisGuild["announceChannel"])).send(embed=makeEmbed("Error", "soronline.us is reporting the following error", 0xff0000, "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Error.svg/1200px-Error.svg.png", openzones))
                    except:
                            await bot.get_guild(int(guild)).owner.send("I tried to announce the current zones but failed. Please reconfigure what channel to send announcements to.")
                            continue
            await asyncio.sleep(60)

        else:
            if len(bot.currentZones) == 0 and len(openzones) > 0:
                bot.currentZones = openzones
            elif len(openzones) > 0 and bot.currentZones != openzones:
                print(now + " sent " + str(openzones) + " to channels")
                for guild in bot.confs:
                    thisGuild = bot.confs[guild]
                    if thisGuild['enabled'] == '0':
                        continue
                    if thisGuild['announceChannel'] != '0':
                        try:
                            if "Server" in openzones and thisGuild['announceServmsg'] == '1':
                                await bot.get_channel(int(thisGuild["announceChannel"])).send(embed=makeEmbed("Error", "soronline.us is reporting the following error", 0xff0000, "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Error.svg/1200px-Error.svg.png", openzones))
                            else:
                                await bot.get_channel(int(thisGuild["announceChannel"])).send(embed=makeEmbed("Current Zones", "These are the current zones reported by soronline.us", 0xe08a00, "http://www.tue.nu/misc/ror.png", openzones))
                        except:
                            await bot.get_guild(int(guild)).owner.send("I tried to announce the current zones but failed. Please reconfigure what channel to send announcements to.")
                            continue
                        for fort in bot.forts:
                            if fort in openzones.values() and fort not in bot.currentZones.values():
                                if thisGuild['fortPing'] != '0':
                                    guild2 = bot.get_guild(int(guild))
                                    try:
                                        role = get(guild2.roles, id=int(thisGuild['fortPing']))
                                        await bot.get_channel(int(thisGuild["announceChannel"])).send(role.mention)
                                    except:
                                        await bot.get_guild(int(guild)).owner.send("I tried to ping for fortresses but failed. Please reconfigure what group to ping")
                        for city in bot.cities:
                            if city in openzones.values() and city not in bot.currentZones.values():
                                if time.time() > int(bot.lastCityTime):
                                    bot.lastCityTime = time.time() + 10800 #3 hours
                                    lastTime = open('lastcity.txt', 'w')
                                    lastTime.write(bot.lastCityTime)
                                    lastTime.close()
                                    skipCityLog = False
                                    if thisGuild['cityPing'] != '0':
                                        guild2 = bot.get_guild(int(guild))
                                        try:
                                            role = get(guild2.roles, id=int(thisGuild['cityPing']))
                                            await bot.get_channel(int(thisGuild["announceChannel"])).send(role.mention)
                                        except:
                                            await bot.get_guild(int(guild)).owner.send("I tried to ping for city but failed. Please reconfigure what group to ping")
                #check if a fort happened and is now over
                for fort in bot.forts:
                    if fort in bot.currentZones.values() and fort not in openzones.values():
                    #dumb logic
                        fortstat = open('fortstat.csv', 'a')
                        #really really dumb
                        if fort == "Reikwald":
                            if "Praag" in openzones.values():
                                fortstat.write(now + "," + fort + ",Order\n")
                            else:
                                fortstat.write(now + "," + fort + ",Destruction\n")
                        elif fort == "Shining Way":
                            if "Dragonwake" in openzones.values():
                                fortstat.write(now + "," + fort + ",Order\n")
                            else:
                                fortstat.write(now + "," + fort + ",Destruction\n")
                        elif fort == "Stonewatch":
                            if "Thunder Mountain" in openzones.values():
                                fortstat.write(now + "," + fort + ",Order\n")
                            else:
                                fortstat.write(now + "," + fort + ",Destruction\n")
                        elif fort == "The Maw":
                            if "Praag" in openzones.values():
                                fortstat.write(now + "," + fort + ",Destruction\n")
                            else:
                                fortstat.write(now + "," + fort + ",Order\n")
                        elif fort == "Fell Landing":
                            if "Dragonwake" in openzones.values():
                                fortstat.write(now + "," + fort + ",Destruction\n")
                            else:
                                fortstat.write(now + "," + fort + ",Order\n")
                        elif fort == "Butchers Pass":
                            if "Thunder Mountain" in openzones.values():
                                fortstat.write(now + "," + fort + ",Destruction\n")
                            else:
                                fortstat.write(now + "," + fort + ",Order\n")

                        fortstat.close()
                for city in bot.cities:
                    if city in openzones.values() and city not in bot.currentZones.values() and skipCityLog == False:
                        citystat = open('citystat.csv', 'a')
                        citystat.write(now + "," + city + "\n")
                        citystat.close()
                bot.currentZones = openzones
                bot.lastannounce = now
            await asyncio.sleep(60) 

def makeEmbed(title, description, colour, thumbnail, fields):
    embedVar = discord.Embed(title=title, description=description, color=colour)
    embedVar.set_thumbnail(url=thumbnail)
    for entry in fields:
        embedVar.add_field(name=entry, value=fields[entry], inline=False)
    return embedVar

bot.run(TOKEN)
