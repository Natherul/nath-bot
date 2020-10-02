from datetime import datetime
import discord
import asyncio
from discord.utils import get
import soronline

TOKEN = '' #TOKEN GOES HERE
description = '''Naths Discord Bot'''
bot = discord.Client()  #commands.Bot(command_prefix='|', description=description)
bot.currentZones = ""
bot.forts = ['The Maw', 'Reikwald', 'Fell Landing', 'Shining Way', 'Butchers Pass', 'Stonewatch']
bot.cities = ['Inevitable City', 'Altdorf']
bot.started = False
bot.announceChannel = #ANNOUNCE CHANNEL ID GOES HERE
bot.logChannel = #LOG CHANNEL ID GOES HERE
bot.guild = #GUILD ID GOSE HERE

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
        await my_background_task(bot)


@bot.event
async def on_message(message):
    if "discord link" in message.content:
        await message.channel.send("The link to this discord is: ")
    elif "Direct Message" in str(message.channel) and message.author != bot.user:
        guild = bot.get_guild(bot.guild)
        if "Remove FortPing" in message.content:
            role = get(guild.roles, name="FortPing")
            await guild.get_member(message.author.id).remove_roles(role)
            await message.author.send(content = "Removed you from the fort pings")
            await bot.get_channel(bot.logChannel).send("Removed " + str(message.author.id) + " / " + str(message.author.display_name) + " from FortPings")
        elif "Add FortPing" in message.content:
            role = get(guild.roles, name="FortPing")
            await guild.get_member(message.author.id).add_roles(role)
            await message.author.send(content = "Added you for fort pings")
            await bot.get_channel(bot.logChannel).send("Added " + str(message.author.id) + " / " + str(message.author.display_name) + " to FortPings")
        elif "Remove CityPing" in message.content:
            role = get(guild.roles, name="CityPing")
            await guild.get_member(message.author.id).remove_roles(role)
            await message.author.send(content = "Removed you from the city pings")
            await bot.get_channel(bot.logChannel).send("Removed " + str(message.author.id) + " / " + str(message.author.display_name) + " from CityPings")
        elif "Add CityPing" in message.content:
            role = get(guild.roles, name="CityPing")
            await guild.get_member(message.author.id).add_roles(role)
            await message.author.send(content = "Added you for city pings")
            await bot.get_channel(bot.logChannel).send("Added " + str(message.author.id) + " / " + str(message.author.display_name) + " to CityPings")
        else:
            await message.author.send(content = "The only commands I recognize is currently: \n Remove FortPing \n Remove CityPing \n Add FortPing \n Add CityPing")


async def my_background_task(self):
    await self.wait_until_ready()
    channel = self.get_channel(bot.announceChannel) 
    while not self.is_closed():
        print(str(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")) + " scraping")
        openzones = soronline.scrape()
        if openzones == "No data updates, Most likely a game update." and bot.currentZones != openzones:
            bot.currentZones = openzones
            await channel.send("SoROnline is not serving data. Will post again once its reporting again.")
        elif bot.currentZones == "" and openzones != "":
            bot.currentZones = openzones
        elif openzones != "" and bot.currentZones != openzones:
            print(str(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")) + " sent " + str(openzones) + " to channel")
            await channel.send("Current zones are:\n" + openzones)
            for fort in bot.forts:
                if fort in openzones and fort not in bot.currentZones:
                    guild = bot.get_guild(bot.guild)
                    role = get(guild.roles, name="FortPing")
                    await channel.send(role.mention)
            for city in bot.cities:
                if city in openzones and city not in bot.currentZones:
                    guild = bot.get_guild(bot.guild)
                    role = get(guild.roles, name="CityPing")
                    await channel.send(role.mention)
            bot.currentZones = openzones
        await asyncio.sleep(60) 

bot.run(TOKEN)
