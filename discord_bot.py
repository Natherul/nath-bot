from datetime import datetime
import discord
import asyncio
from discord.utils import get
#from discord.ext import commands
import soronline
from discord import File
import json

TOKEN = ''
description = '''Naths Discord Bot'''
bot = discord.Client() 
bot.currentZones = ""
bot.forts = ['The Maw', 'Reikwald', 'Fell Landing', 'Shining Way', 'Butchers Pass', 'Stonewatch']
bot.cities = ['Inevitable City', 'Altdorf']
bot.started = False
bot.spammalus = 0
bot.prefix = "|"
bot.commandDescriptions = {'configure': 'Commands to configure the bot (these can only be issued by the owner of the discord and there are multiple subcommands here)', 'citystat' : 'Posts the statistics for cities', 'fortstat' : 'Posts the statistics for fortresses', 'Add Fortping' : 'Adds you to the group that gets pinged on fortresses', 'Add CityPing' : 'Adds you to the group that gets pinged on cities', 'Remove FortPing' : 'Removes you from the group that gets pinged in fortresses', 'Remove CityPing' : 'Removes you from the group that gets pinged when cities happen'}
bot.configureCommands = ['announceChannel', 'logChannel', 'welcomeMessage', 'boardingChannel', 'fortPing', 'cityPing']
bot.allconf = {'announceChannel' : '0', 'logChannel' : '0', 'welcomeMessage' : '0', 'boardingChannel' : '0', 'fortPing' : '0', 'cityPing' : '0', 'enabled' : '1'}
bot.confs = {}

@bot.event
async def on_ready():
    if bot.started == False:
        bot.started = True
        print('Logged in as')
        print(bot.user.name)
        print(bot.user.id)
        print('------')
        print(str(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")) + ' loading old scrape')
        f = open('result.txt', 'r')
        bot.currentZones = f.read()
        f.close()
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
        thisGuild = {"announceChannel" : "0", "logChannel" : "0", "welcomeMessage" : "0", "boardingChannel" : "0", "fortPing" : "0", "cityPing" : "0", 'enabled' : '1'}
        bot.confs[str(guild.id)] = thisGuild
        g = open('guilds.txt', 'w')
        g.write(str(bot.confs))
        g.close()

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
    if message.content == bot.prefix or message.content == bot.prefix + "help":
        text = "These are the commands that can be issued:\n"
        for command in bot.commandDescriptions:
            text = text + bot.prefix + command + "   " + bot.commandDescriptions[command] + "\n"
        await message.channel.send(text)
    if message.content.startswith(bot.prefix + "configure") and message.author.id == message.guild.owner.id:
        if str(message.guild.id) not in bot.confs.keys():
            thisGuild = {"announceChannel" : "0", "logChannel" : "0", "welcomeMessage" : "0", "boardingChannel" : "0", "fortPing" : "0", "cityPing" : "0", 'enabled' : '1'}
            bot.confs[str(message.guild.id)] = thisGuild
            g = open('guilds.txt', 'w')
            g.write(str(bot.confs))
            g.close()
            await message.channel.send("The guild was missing from the internal database and it has been added with no values, please configure the bot with all info it needs. (The command you entered was not saved)")
            return
        found = False
        for command in bot.configureCommands:
            if command in message.content:
                found = True
                param = message.content.replace(bot.prefix + "configure " + command + " ", '')
                if command == 'announceChannel' or command == 'logChannel' or command == 'boardingChannel' or command == 'fortPing' or command == 'cityPing':
                    if param.isdecimal() == False:
                        await message.channel.send("The command you entered needs to be in ID form (number only)")
                        return
                thisGuild = bot.confs[str(message.guild.id)]
                thisGuild[command] = param
                bot.confs[str(message.guild.id)] = thisGuild
                await message.channel.send(command + " is now set to: " + param)
        if found == False:
            text = "Sorry I only accept the following configure commands: \n"
            for command in bot.configureCommands:
                text = text + command + "\n"
            await message.channel.send(text)
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
        text = "Announcement from Natherul: \n" + message.content.replace(bot.prefix + "announce ", '')
        for guild in bot.confs:
            thisGuild = bot.confs[guild]
            if thisGuild['enabled'] == '1' and thisGuild['announceChannel'] != '0':
                await bot.get_channel(int(thisGuild['announceChannel'])).send(text)

    elif bot.prefix + "Add " in message.content:
        thisGuild = bot.confs[str(message.guild.id)]
        if "FortPing" in message.content:
            if thisGuild['fortPing'] != '0':
                role = get(message.guild.roles, id=int(thisGuild['fortPing']))
                await message.guild.get_member(message.author.id).add_roles(role)
                if thisGuild['logChannel'] != '0':
                    await bot.get_channel(int(thisGuild["logChannel"])).send("Added " + str(message.author.id) + " / " + str(message.author.display_name) + " to FortPings")
        elif "CityPing" in message.content:
            if thisGuild['cityPing'] != '0':
                role = get(message.guild.roles, id=int(thisGuild['cityPing']))
                await message.guild.get_member(message.author.id).add_roles(role)
                if thisGuild['logChannel'] != '0':
                    await bot.get_channel(int(thisGuild["logChannel"])).send("Added " + str(message.author.id) + " / " + str(message.author.display_name) + " to CityPings")
    elif bot.prefix + "Remove " in message.content:
        thisGuild = bot.confs[str(message.guild.id)]
        if "FortPing" in message.content:
            if thisGuild['fortPing'] != '0':
                role = get(message.guild.roles, id=int(thisGuild['fortPing']))
                await message.guild.get_member(message.author.id).remove_roles(role)
                if thisGuild['logChannel'] != '0':
                    await bot.get_channel(int(thisGuild["logChannel"])).send("Removed " + str(message.author.id) + " / " + str(message.author.display_name) + " from FortPings")
        elif "CityPing" in message.content:
            if thisGuild['cityPing'] != '0':
                role = get(message.guild.roles, id=int(thisGuild['cityPing']))
                await message.guild.get_member(message.author.id).remove_roles(role)
                if thisGuild['logChannel'] != '0':
                    await bot.get_channel(int(thisGuild["logChannel"])).send("Removed " + str(message.author.id) + " / " + str(message.author.display_name) + " from CityPings")
        
        
async def on_member_join(member):
    guild = bot.confs[member.guild.id]
    if guild['boardingChannel'] != '0' and guild['welcomeMessage'] != '0':
        await bot.get_channel(int(guild["boardingChannel"])).send(guild['welcomeMessage'])

async def my_background_task(self):
    await self.wait_until_ready()
    while not self.is_closed():
        now = str(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        #print(now + " scraping")
        try:
            openzones = soronline.scrape()
        except:
            print(now + " something went wrong")
            await asyncio.sleep(60) 
            return
        if openzones == "No data updates, Most likely a game update." and bot.currentZones != openzones:
            await asyncio.sleep(60) 
            return
        #    if bot.spammalus == 5:
        #        #bot.currentZones = openzones
        #        for guild in bot.confs:
        #            thisGuild = bot.confs[guild]
        #            if thisGuild["announceChannel"] != '0':
        #                await bot.get_channel(int(thisGuild["announceChannel"])).send("SoROnline is not serving data. Will post again once its reporting again.")
        #    else:
        #        bot.spammalus += 1
        elif bot.currentZones == "" and openzones != "":
            bot.currentZones = openzones
        elif openzones != "" and bot.currentZones != openzones:
            print(now + " sent " + str(openzones) + " to channels")
            bot.spammalus = 0
            for guild in bot.confs:
                thisGuild = bot.confs[guild]
                if thisGuild['enabled'] == '0':
                    continue
                if thisGuild['announceChannel'] != '0':
                    await bot.get_channel(int(thisGuild["announceChannel"])).send("Current zones are:\n" + openzones)
                    for fort in bot.forts:
                        if fort in openzones and fort not in bot.currentZones:
                            if thisGuild['fortPing'] != '0':
                                guild2 = bot.get_guild(int(guild))
                                role = get(guild2.roles, id=int(thisGuild['fortPing']))
                                await bot.get_channel(int(thisGuild["announceChannel"])).send(role.mention)
                    for city in bot.cities:
                        if city in openzones and city not in bot.currentZones:
                            if thisGuild['cityPing'] != '0':
                                guild2 = bot.get_guild(int(guild))
                                role = get(guild2.roles, id=int(thisGuild['cityPing']))
                                await bot.get_channel(int(thisGuild["announceChannel"])).send(role.mention)
            #check if a fort happened and is now over
            for fort in bot.forts:
                if fort in bot.currentZones and fort not in openzones:
                #dumb logic
                    fortstat = open('fortstat.csv', 'a')
                    #order forts
                    if fort == "Reikwald" or fort == "Shining Way" or fort == "Stonewatch":
                        if "Dragonwake" in openzones or "Praag" in openzones or "Thunder Mountain" in openzones:
                            fortstat.write(now + "," + fort + ",Order\n")
                        else:
                            fortstat.write(now + "," + fort + ",Destruction\n")
                    #destro forts
                    else:
                        if "Dragonwake" in openzones or "Praag" in openzones or "Thunder Mountain" in openzones:
                            fortstat.write(now + "," + fort + ",Destruction\n")
                        else:
                            fortstat.write(now + "," + fort + ",Order\n")

                    fortstat.close()
            for city in bot.cities:
                if city in openzones and city not in bot.currentZones:
                    citystat = open('citystat.csv', 'a')
                    citystat.write(now + "," + city + "\n")
                    citystat.close()
            bot.currentZones = openzones
        await asyncio.sleep(60) 


bot.run(TOKEN)
