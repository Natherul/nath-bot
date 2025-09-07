import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import get
from typing import Literal, Optional
import logging
import uuid

CONFIGURATION = "guilds.txt"


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

def save_conf(self):
    """Help method to update the saved configuration of a server"""
    g = open(CONFIGURATION, 'w')
    g.write(str(self.config))
    g.close()

def is_mod(roles, guild_conf):
    # This is a placeholder for your is_mod function.
    # It checks if any of the user's roles match the configured moderator role.
    mod_role_id = guild_conf.get('moderator')
    if not mod_role_id or mod_role_id == '0':
        return False
    
    mod_role_id = int(mod_role_id)
    for role in roles:
        if role.id == mod_role_id:
            return True
    return False

# Constants (placeholders)
QUESTION_ICON = ""
ANNOUNCE_ICON = ""
KICKED_ICON = ""
BANNED_ICON = ""
HTTP_ERROR = "HTTPException occurred."
NOT_MOD_STRING = "You do not have the moderator role to use this command."
NOW_SET_TO_ = " is now set to "
logging = logging.getLogger(__name__)

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot, conf: dict):
        self.bot = bot
        self.config = conf

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog {self.qualified_name} is ready.')


    @app_commands.command(name="help", description="The help command for the bot")
    async def help_command(self, interaction: discord.Interaction):
        """Send a help message with what the bot can do
        :param interaction: The interaction that triggered this command"""
        # Note: You were missing `self` in the function signature
        await interaction.response.send_message(embed=make_embed("Available Commands", "These are the commands that you can use", 0xfa00f2, QUESTION_ICON, self.bot.commandDescriptions))

    @app_commands.command(name="add", description="Command group to add pings or events")
    @app_commands.describe(type="What to add", args="Event parameters")
    async def add(self, interaction: discord.Interaction, type: Literal['FortPing', 'CityPing', 'Event', 'Channel'], args: Optional[str]):
        """Command to add something into configuration
        :param interaction: The interaction that triggered the command
        :param type: The type to add
        :param args: Optional (may not be optional depending on type) parameters for the add"""
        this_guild = self.config.get(str(interaction.guild.id), {})
        if "FortPing" == type:
            if this_guild.get('fortPing') != '0':
                try:
                    role = get(interaction.guild.roles, id=int(this_guild['fortPing']))
                    await interaction.guild.get_member(interaction.user.id).add_roles(role)
                    await interaction.response.send_message("Role added")
                    if this_guild.get('logChannel') != '0':
                        await self.bot.get_channel(int(this_guild["logChannel"])).send(
                            "Added " + str(interaction.user.id) + " / " + str(interaction.user.display_name) + " to FortPings")
                except discord.Forbidden:
                    await interaction.guild.owner.send(
                        "Something went wrong when attempting to add a role or when trying to post to the log channel")
                except discord.HTTPException:
                    self.logger.error(HTTP_ERROR)
        elif "CityPing" == type:
            if this_guild.get('cityPing') != '0':
                try:
                    role = get(interaction.guild.roles, id=int(this_guild['cityPing']))
                    await interaction.guild.get_member(interaction.user.id).add_roles(role)
                    await interaction.response.send_message("Role added")
                    if this_guild.get('logChannel') != '0':
                        await self.bot.get_channel(int(this_guild["logChannel"])).send(
                            "Added " + str(interaction.user.id) + " / " + str(interaction.user.display_name) + " to CityPings")
                except discord.Forbidden:
                    await interaction.guild.owner.send(
                        "Something went wrong when attempting to add a role or when trying to post to the log channel")
                except discord.HTTPException:
                    self.logger.error(HTTP_ERROR)
        elif "Channel" == type:
            if interaction.guild.get_member(interaction.user.id).voice is not None:
                try:
                    channel_name = str(uuid.uuid4().hex) if args is None else args
                    channel = await interaction.guild.create_voice_channel(name=channel_name,
                                                        reason="Channel requested by user: {user}".format(user=interaction.user.display_name))
                    current_temp_channels = this_guild.get('tempChannels', [])
                    current_temp_channels.append(channel.id)
                    this_guild['tempChannels'] = current_temp_channels
                    self.config[str(interaction.guild.id)] = this_guild
                    save_conf(self)
                    await interaction.guild.get_member(interaction.user.id).move_to(channel)
                    await interaction.response.send_message("Temporary channel created and user moved to channel.")
                except (discord.Forbidden, TypeError):
                    await interaction.response.send_message("Something went wrong when attempting to either create the channel or move you to the channel.")
                except discord.HTTPException:
                    self.logger.error(HTTP_ERROR)
            else:
                await interaction.response.send_message(
                    "You need to be connected to a channel before issuing this command. The bot will move you to the channel when its created and remove the channel once its empty.")


    @app_commands.command(name="remove", description="Command group to remove pings or events")
    @app_commands.describe(type="What to remove", args="Event parameters")
    async def remove(self, interaction: discord.Interaction, type: Literal['FortPing', 'CityPing', 'Event'], args: Optional[str]):
        """Command to remove something from configuration
        :param interaction: The interaction that triggered this command
        :param type: The type to remove
        :param args: Optional (may not be optional depending on type) identifier for the removal"""
        this_guild = self.config.get(str(interaction.guild.id), {})
        if "FortPing" == type:
            if this_guild.get('fortPing') != '0':
                try:
                    role = get(interaction.guild.roles, id=int(this_guild['fortPing']))
                    await interaction.guild.get_member(interaction.user.id).remove_roles(role)
                    await interaction.response.send_message("Role removed")
                    if this_guild.get('logChannel') != '0':
                        await self.bot.get_channel(int(this_guild["logChannel"])).send(
                            "Removed " + str(interaction.user.id) + " / " + str(
                                interaction.user.display_name) + " from FortPings")
                except discord.Forbidden:
                    await interaction.guild.owner.send(
                        "Something went wrong when either removing a permission from a user or when trying to post it in the log channel")
                except discord.HTTPException:
                    self.logger.error(HTTP_ERROR)
        elif "CityPing" == type:
            if this_guild.get('cityPing') != '0':
                try:
                    role = get(interaction.guild.roles, id=int(this_guild['cityPing']))
                    await interaction.guild.get_member(interaction.user.id).remove_roles(role)
                    await interaction.response.send_message("Role removed")
                    if this_guild.get('logChannel') != '0':
                        await self.bot.get_channel(int(this_guild["logChannel"])).send(
                            "Removed " + str(interaction.user.id) + " / " + str(
                            interaction.user.display_name) + " from CityPings")
                except discord.Forbidden:
                    await interaction.guild.owner.send(
                        "Something went wrong when either removing a permission from a user or when trying to post it in the log channel")
                except discord.HTTPException:
                    self.logger.error(HTTP_ERROR)
        else:
            await interaction.response.send_message("No such remove option")


    @app_commands.command(name="announce", description="Announce things through all servers the bot is present on")
    @app_commands.describe(message="What to announce")
    @app_commands.guilds(discord.Object(id=173443661713899521))
    async def announce(self, interaction: discord.Interaction, message: str):
        """Announce command, this is only used by Nath to send info to all servers the bot is present on
        :param interaction: The interaction that triggered this command
        :param message: The message to announce"""
        if interaction.user.id == 173443339025121280:
            for guild in self.config:
                this_guild = self.config[guild]
                if this_guild.get('enabled') == '1' and this_guild.get('announceChannel') != '0':
                    try:
                        self.bot.lastAnnounceMessage[guild] = await self.bot.get_channel(int(this_guild['announceChannel'])).send(
                            embed=make_embed("Announcement from Natherul", message, 0x00ff00, ANNOUNCE_ICON,
                                             {}))
                    except (discord.Forbidden, ValueError, TypeError):
                        self.logger.warning("Announcement channel wrong in: " + str(this_guild) + " removing the announce channel from it")
                        this_guild['announceChannel'] = "0"
                        self.config[str(interaction.guild.id)] = this_guild
                        save_conf()
                    except discord.HTTPException:
                        self.logger.error(HTTP_ERROR)
        else:
            await interaction.response.send_message("This command is locked to only be useable by Natherul")


    @app_commands.command(name="configure", description="Command group to configure the bot on your server")
    @app_commands.describe(option="What setting to change", args="The setting for the option")
    @app_commands.default_permissions(administrator=True)
    async def configure(self, interaction: discord.Interaction, option: Literal['announceChannel', 'logChannel', 'welcomeMessage', 'leaveMessage', 'boardingChannel', 'fortPing', 'cityPing', 'moderator', 'chatModeration', 'allowTempChannels', 'removeAnnounce', 'announceServmsg', 'ignoredLogChannels', 'help'], args: Optional[str]):
        """Configure command for owners to configure their server
        :param interaction: The interaction that triggered this command
        :param option: The option to change
        :param args: Optional (may not be optional based on option) identifier"""
        if interaction.user.id == interaction.guild.owner.id or interaction.user.id == 173443339025121280:
            if str(interaction.guild.id) not in self.config.keys():
                this_guild = self.bot.allconf
                self.config[str(interaction.guild.id)] = this_guild
                save_conf(self)
                await interaction.response.send_message("The guild was missing from the internal database and it has been added with no values, please configure the bot with all info it needs. (The command you entered was not saved)")
            elif option == "help" or args is None:
                await interaction.response.send_message(embed=make_embed("Available Configure Commands", "These are the configure commands available", 0xfa00f2, QUESTION_ICON, self.bot.configDesc))
            elif option in ("announceChannel", "logChannel", "boardingChannel"):
                tmp_guild = interaction.guild
                tmp_channels = tmp_guild.text_channels
                for channel in tmp_channels:
                    if args == str(channel.id) or args == channel.name:
                        this_guild = self.config.get(str(interaction.guild.id), {})
                        this_guild[option] = args
                        self.config[str(interaction.guild.id)] = this_guild
                        await interaction.response.send_message(option + NOW_SET_TO_ + args)
                        save_conf(self)
                        return
                await interaction.response.send_message("No channel found with that name or ID")
            elif option in ("fortPing", "cityPing", "moderator"):
                tmp_guild = interaction.guild
                tmp_roles = tmp_guild.roles
                for role in tmp_roles:
                    if args == str(role.id) or args == role.name:
                        this_guild = self.config.get(str(interaction.guild.id), {})
                        this_guild[option] = args
                        self.config[str(interaction.guild.id)] = this_guild
                        await interaction.response.send_message(option + NOW_SET_TO_ + args)
                        save_conf(self)
                        return
                await interaction.response.send_message("No role with that name or ID was found")
            elif option in ("removeAnnounce", "announceServmsg", "chatModeration", "allowTempChannels"):
                if args != "1" and args != "0":
                    await interaction.response.send_message("For this setting you can only specify it being on (1) or off (0)")
                else:
                    this_guild = self.config.get(str(interaction.guild.id), {})
                    this_guild[option] = args
                    self.config[str(interaction.guild.id)] = this_guild
                    await interaction.response.send_message(option + NOW_SET_TO_ + args)
                    save_conf(self)
            elif option in ('ignoreLogChannels'):
                channels = args.split(',')
                this_guild = self.config.get(str(interaction.guild.id), {})
                this_guild[option] = channels
                self.config[str(interaction.guild.id)] = this_guild
                await interaction.response.send_message(option + NOW_SET_TO_ + args)
                save_conf(self)
            else:
                this_guild = self.config.get(str(interaction.guild.id), {})
                this_guild[option] = args
                self.config[str(interaction.guild.id)] = this_guild
                await interaction.response.send_message(option + NOW_SET_TO_ + args)
                save_conf(self)
        else:
            await interaction.response.send_message("You are neither a server owner nor Natherul so configuring the server is not allowed.")


    @app_commands.command(name="kick", description="Kick member from the server")
    @app_commands.describe(member="The member to kick", reason="The reason for the kick")
    @app_commands.default_permissions(kick_members=True)
    async def kick_member(self, interaction: discord.Interaction, member : discord.Member, reason : str):
        """Method to kick someone from the guild
        :param interaction: Context that triggered this command
        :param member: The member to kick
        :param reason: The reason for the kick (will be logged)"""
        try:
            if member.id == self.bot.user.id:
                await interaction.response.send_message("You cannot kick the bot")
                return
            this_guild = self.config.get(str(interaction.guild.id), {})
            if not is_mod(interaction.user.roles, this_guild):
                await interaction.response.send_message(NOT_MOD_STRING)
                return
            if interaction.guild.owner.id == member.id:
                await interaction.response.send_message("You cannot kick a server owner")
                return
            elif this_guild.get('logChannel') != '0':
                await self.bot.get_channel(int(this_guild['logChannel'])).send(
                    embed=make_embed("User Kicked", member.display_name + " was kicked by " +
                                     interaction.user.display_name, 0xfa0000, KICKED_ICON, {'Reason' : reason}))
            await member.kick(reason=reason)
            await interaction.response.send_message("User kicked")
        except discord.Forbidden:
            await interaction.guild.owner.send("Nath-bot is enabled on your server but does not have the permissions to kick someone even though a moderation group has been set.")
        except discord.HTTPException:
            self.logger.error(HTTP_ERROR)


    @app_commands.command(name="ban", description="Ban member from the server")
    @app_commands.describe(member="The member to ban", reason="The reason for the ban")
    @app_commands.default_permissions(ban_members=True)
    async def ban_member(self, interaction: discord.Interaction, member : discord.Member, reason : str):
        """Method to ban member from the guild
        :param interaction: The interaction that triggered this command
        :param member: The member to ban
        :param reason: The reason for the ban (will be logged)"""
        try:
            if member.id == self.bot.user.id:
                await interaction.response.send_message("You cannot ban the bot")
                return
            this_guild = self.config.get(str(interaction.guild.id), {})
            if not is_mod(interaction.user.roles, this_guild):
                await interaction.response.send_message(NOT_MOD_STRING)
                return
            if interaction.guild.owner.id == member.id:
                await interaction.response.send_message("You cannot ban a server owner")
                return
            elif this_guild.get('logChannel') != '0':
                await self.bot.get_channel(int(this_guild['logChannel'])).send(
                    embed=make_embed("User Banned", member.display_name + " was banned by " +
                                     interaction.user.display_name, 0xfa0000, BANNED_ICON, {'Reason' : reason}))
            await member.ban(reason=reason)
            await interaction.response.send_message("User banned")
        except discord.Forbidden:
            await interaction.guild.owner.send("Nath-bot is enabled on your server but does not have the permissions to ban someone even though a moderation group has been set.")
        except discord.HTTPException:
            self.logger.error(HTTP_ERROR)


    @app_commands.command(name="purge", description="Purges a set number of messages from the current channel")
    @app_commands.describe(number="The number of messages to delete", reason="The reason for the purge")
    @app_commands.default_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, number : int, reason : str):
        """Method to purge X amount of messages from a channel
        :param interaction: The interaction which triggered this command
        :param number: The number of messages to remove from the channel in the context
        :param reason: The reason for the purge (will be logged)"""
        this_guild = self.config.get(str(interaction.guild.id), {})
        if not is_mod(interaction.user.roles, this_guild):
            await interaction.response.send_message(NOT_MOD_STRING)
            return
        messages = [message async for message in interaction.channel.history(limit=number)]
        await interaction.response.send_message(str(number) + " messages will be purged")
        try:
            await interaction.channel.delete_messages(messages, reason=reason)
            if this_guild.get('logChannel') != '0':
                message = "{moderator} pruned {channel} of {number} of messages".format(
                    moderator=interaction.user.display_name, number=number, channel=interaction.channel.name)
                await self.bot.get_channel(int(this_guild['logChannel'])).send(
                    embed=make_embed("Channel Pruned", message, 0xfa0000, "", {'Reason': reason}))
        except discord.Forbidden:
            await interaction.guild.owner.send("Nath-bot is enabled on your server but does not have the permissions to purge messages though moderation group has been set.")
        except discord.HTTPException:
            self.logger.error(HTTP_ERROR)


    @app_commands.command(name="citystat", description="Command to return the stats for cities in RoR")
    async def citystat(self, interaction: discord.Interaction):
        """Command to get stats about city contests in RoR
        :param interaction: The interaction that triggered this command"""
        from discord import File # File must be imported from discord if used like this
        await interaction.response.send_message("Current gathered stats for cities", file=File('citystat.csv'))


    @app_commands.command(name="fortstat", description="Command to return the stats for forts in RoR")
    async def fortstat(self, interaction: discord.Interaction):
        """Command to get stats about fort wins in RoR
        :param interaction: The interaction that triggered this command"""
        from discord import File
        await interaction.response.send_message("Current gathered stats for forts", file=File('fortstat.csv'))


    @app_commands.command(name="debug", description="Debug command to print information that Nath will want to troubleshoot issues")
    @app_commands.default_permissions(administrator=True)
    async def debug(self, interaction: discord.Interaction):
        """Command to print all saved config of a guild
        :param interaction: The interaction of the trigger of command"""
        this_guild = self.config.get(str(interaction.guild.id), {})
        await interaction.response.send_message(embed=make_embed("These are the current settings for this server", "", 0xd8de0c,
                                                        QUESTION_ICON,
                                                        this_guild))


    @app_commands.command(name="editannounce", description="Edit previous announcement")
    @app_commands.describe(message="What to edit the message to")
    @app_commands.guilds(discord.Object(id=173443661713899521))
    async def edit_announce(self, interaction: discord.Interaction, message: str):
        """Method to edit prior announces, only used by Nath
        :param interaction: The interaction that triggered this command
        :param message: The new message content"""
        if interaction.user.id == 173443339025121280:
            for old_message in self.bot.lastAnnounceMessage:
                await self.bot.lastAnnounceMessage[old_message].edit(
                    embed=make_embed("Announcement from Natherul", message, 0x00ff00, ANNOUNCE_ICON, {}))
            await interaction.response.send_message("Announcement updated")
        else:
            await interaction.response.send_message("This command is locked to only be usable by Natherul")


async def setup(bot: commands.Bot):
    config_data = getattr(bot, 'confs', {})
    await bot.add_cog(Moderation(bot, config_data))
