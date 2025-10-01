import requests
from discord.ext import commands, tasks
import logging

guild_id = 982
warhammer_guild_role = 543777242103414789
officer_role_id = 345176321065746432
logging = logging.getLogger(__name__)


def get_guild_members(guild_id):
    """Method to parse RoR API for members
    :param guild_id: Guild ID
    :type guild_id: int
    :return: List of Guild members
    :rtype: list"""
    url = "https://production-api.waremu.com/graphql"


    headers = {"Content-Type": "application/json"}

    data_template = '''{
      "query": "query GetGuildMembers($guildId: ID!, $first: Int!, $after: String) { guild(id: $guildId) { members(first: $first, after: $after) { edges { cursor node { character { name } } } pageInfo { hasNextPage endCursor } } } }",
      "variables": {
        "guildId": GUILD_ID,
        "first": 50, "after": null
      }
    }'''.replace('GUILD_ID', str(guild_id))
    initial = requests.post(url, headers=headers, data=data_template).json()
    members = []
    for member in initial["data"]["guild"]["members"]['edges']:
        members.append(member['node']['character']['name'])

    has_more = initial["data"]["guild"]["members"]['pageInfo']['hasNextPage']

    while has_more:
        after_value = initial["data"]["guild"]["members"]['pageInfo']['endCursor']
        more_template = data_template.replace('GUILD_ID', str(guild_id)).replace("null", f'"{after_value}"')
        initial = requests.post(url, headers=headers, data=more_template).json()
        for member in initial["data"]["guild"]["members"]['edges']:
            members.append(member['node']['character']['name'])
        has_more = initial["data"]["guild"]["members"]['pageInfo']['hasNextPage']

    return members


class TUESpecifics(commands.Cog):
    def __init__(self, bot: commands.Bot, conf: dict):
        self.bot = bot
        self.config = conf
        self.check_members.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog {self.qualified_name} is ready.')


    @tasks.loop(minutes=10)
    async def check_members(self):
        """Main method that checks if there needs to be any modifications to roles"""
        try:
            guild = self.bot.get_guild(self.bot.TUE)
            tue_conf = self.config.get(self.bot.TUE)
            members = guild.members
            warhammer_role = guild.get_role(warhammer_guild_role)
            officer_role = guild.get_role(officer_role_id)
            to_add_role_to = []
            to_remove_role_from = []
            member_list = get_guild_members(guild_id)
            members_with_role = [member for member in members if any(role.id == warhammer_role.id for role in member.roles)]
            members_without_role = [member for member in members if all(role.id != warhammer_role.id for role in member.roles)]
            channel = None
            if tue_conf["logChannel"] != 0:
                channel = self.bot.get_channel(tue_conf["logChannel"])
            for member in members_with_role:
                if member.display_name.replace('[TUE]', '').strip() not in member_list and officer_role not in member.roles:
                    to_remove_role_from.append(member)
            for member in members_without_role:
                if member.display_name.replace('[TUE]', '').strip() in member_list:
                    to_add_role_to.append(member)
            for member in to_add_role_to:
                logging.info(f"Adding role to {member.display_name}")
                await member.add_roles(warhammer_role)
                if channel is not None:
                    await channel.send(f"Added guild role to {member.display_name}")
            for member in to_remove_role_from:
                logging.info(f"Removing role from {member.display_name}")
                await member.remove_roles(warhammer_role)
                if channel is not None:
                    await channel.send(f"Removed guild role from {member.display_name}")
        except Exception as e:
            logging.error(e)


    @check_members.before_loop
    async def before_check_members(self):
        """Waits until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    config_data = getattr(bot, 'confs', {})
    await bot.add_cog(TUESpecifics(bot, config_data))