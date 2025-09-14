import discord
from discord import Emoji
from discord.ext import commands, tasks
from discord.ui import View
from typing import Literal
import json
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import logging


events = {}
views = []

# Get a logger for this specific module
logging = logging.getLogger(__name__)

# Dictionary mapping careers to their full name and a suitable icon URL.
# Grouped by faction and realm for clarity.
CAREERS = {
    # Order Faction
    'knight_of_the_blazing_sun': {'name': 'Knight of the Blazing Sun', 'icon': 'kotbs', 'faction': 'Order', 'archtype': 'Tank', 'race': 'human'},
    'warrior_priest': {'name': 'Warrior Priest', 'icon': 'wp', 'faction': 'Order', 'archtype': 'Healer', 'race': 'human'},
    'bright_wizard': {'name': 'Bright Wizard', 'icon': 'bw', 'faction': 'Order', 'archtype': 'DPS', 'race': 'human'},
    'witch_hunter': {'name': 'Witch Hunter', 'icon': 'wh', 'faction': 'Order', 'archtype': 'DPS', 'race': 'human'},
    'ironbreaker': {'name': 'Ironbreaker', 'icon': 'ib', 'faction': 'Order', 'archtype': 'Tank', 'race': 'dwarf'},
    'runepriest': {'name': 'Runepriest', 'icon': 'rp', 'faction': 'Order', 'archtype': 'Healer', 'race': 'dwarf'},
    'engineer': {'name': 'Engineer', 'icon': 'eng', 'faction': 'Order', 'archtype': 'DPS', 'race': 'dwarf'},
    'slayer': {'name': 'Slayer', 'icon': 'slayer', 'faction': 'Order', 'archtype': 'DPS', 'race': 'dwarf'},
    'swordmaster': {'name': 'Swordmaster', 'icon': 'sm', 'faction': 'Order', 'archtype': 'Tank', 'race': 'high-elf'},
    'archmage': {'name': 'Archmage', 'icon': 'am', 'faction': 'Order', 'archtype': 'Healer', 'race': 'high-elf'},
    'shadow_warrior': {'name': 'Shadow Warrior', 'icon': 'sw', 'faction': 'Order', 'archtype': 'DPS', 'race': 'high-elf'},
    'white_lion': {'name': 'White Lion', 'icon': 'wl', 'faction': 'Order', 'archtype': 'DPS', 'race': 'high-elf'},

    # Destruction Faction
    'chosen': {'name': 'Chosen', 'icon': 'chosen', 'faction': 'Destruction', 'archtype': 'Tank', 'race': 'chaos'},
    'zealot': {'name': 'Zealot', 'icon': 'zeal', 'faction': 'Destruction', 'archtype': 'Healer', 'race': 'chaos'},
    'magus': {'name': 'Magus', 'icon': 'magus', 'faction': 'Destruction', 'archtype': 'DPS', 'race': 'chaos'},
    'marauder': {'name': 'Marauder', 'icon': 'mara', 'faction': 'Destruction', 'archtype': 'DPS', 'race': 'chaos'},
    'black_orc': {'name': 'Black Orc', 'icon': 'bo', 'faction': 'Destruction', 'archtype': 'Tank', 'race': 'greenskin'},
    'shaman': {'name': 'Shaman', 'icon': 'shaman', 'faction': 'Destruction', 'archtype': 'Healer', 'race': 'greenskin'},
    'squig_herder': {'name': 'Squig Herder', 'icon': 'sh', 'faction': 'Destruction', 'archtype': 'DPS', 'race': 'greenskin'},
    'choppa': {'name': 'Choppa', 'icon': 'choppa', 'faction': 'Destruction', 'archtype': 'DPS', 'race': 'greenskin'},
    'black_guard': {'name': 'Black Guard', 'icon': 'bg', 'faction': 'Destruction', 'archtype': 'Tank', 'race': 'dark-elf'},
    'disciple_of_khaine': {'name': 'Disciple of Khaine', 'icon': 'dok', 'faction': 'Destruction', 'archtype': 'Healer', 'race': 'dark-elf'},
    'sorcerer': {'name': 'Sorcerer', 'icon': 'sorc', 'faction': 'Destruction', 'archtype': 'DPS', 'race': 'dark-elf'},
    'witch_elf': {'name': 'Witch Elf', 'icon': 'we', 'faction': 'Destruction', 'archtype': 'DPS', 'race': 'dark-elf'},
}

class signup_button(discord.ui.Button):
    def __init__(self, label: str, id: str, emoji: Emoji):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=id,
            disabled=False,
            emoji=emoji,
            row=0 if CAREERS[id]['race'] in ["human", "chaos"] else 1 if CAREERS[id]['race'] in ["dwarf", "greenskin"] else 2
        )


    # This method is called whenever a button is pressed.
    async def callback(self, interaction: discord.Interaction):
        """Callback for when a button is pressed"""
        # Find the event data from our global dictionary using the message ID.
        event_id = interaction.message.id
        # Access the events dictionary via the instance attribute
        if event_id not in events:
            await interaction.response.send_message(
                "This event no longer exists.", ephemeral=True
            )
            return

        user = interaction.user
        career_id = interaction.data['custom_id']
        event = events[event_id]

        # Check if the user is already signed up.
        found = False
        removed = False
        for signup in event['signups']:
            if signup['user_id'] == user.id:
                found = True
                if signup['career'] == CAREERS[career_id]:
                    event['signups'] = [signup for signup in event['signups'] if signup['user_id'] != user.id]
                    removed = True
                    break
                else:
                    for signup in event['signups']:
                        if signup['user_id'] == user.id:
                            signup['career'] = CAREERS[career_id]
                            break

        # Add the user to the sign-up list with a 'pending' status.
        if not found:
            event['signups'].append({
                'user_id': user.id,
                'user_name': user.display_name,
                'career': CAREERS[career_id],
                'status': 'Pending',
                'icon': CAREERS[career_id]['icon']
            })

        # Update the event message with the new sign-up list.
        await update_event_embed(interaction.message, event)
        with open('warhammer_events.json', 'w') as f:
            json.dump(events, f, indent=4)

        # Send an ephemeral message to the user confirming their sign-up.
        if not removed:
            message_part = "signed up" if not found else "updated"
            await interaction.response.send_message(
                f"You have {message_part} as a **{CAREERS[career_id]['name']}**.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("You have removed your signup", ephemeral=True)


# A subclass of View that will hold our sign-up buttons.
class EventView(View):
    def __init__(self, organizer_id: int, events_dict: dict, faction: str, guild: discord.Guild):
        super().__init__(timeout=None)
        self.organizer_id = organizer_id
        self.events_dict = events_dict # Store the events dictionary

        # Add a button for each career in our dictionary.
        for career_id, data in CAREERS.items():
            if data['faction'] != faction:
                continue
            custom_emoji = discord.utils.get(guild.emojis, name=data['icon'])
            self.add_item(signup_button(data['name'], career_id, custom_emoji))


def get_career_emoji(guild: discord.Guild, icon: str):
    """Helper method to get an emoji"""
    return discord.utils.get(guild.emojis, name=icon)


# Helper function to create/update the embed.
def create_event_embed(event: dict, guild: discord.Guild):
    """create an embed for an event"""
    embed = discord.Embed(
        title=event['title'],
        description=event['description'],
        color=discord.Color.blue()
    )
    embed.set_author(name=f"Event by {event['organizer_name']}", icon_url=event['organizer_avatar'])
    embed.set_footer(text="Click a button below to sign up!")
    embed.add_field(name="📅 When", value=f"<t:{event['time']}:F>", inline=False)

    # Group sign-ups by status.
    pending_signups = sorted([s for s in event['signups'] if s['status'] == 'Pending'],
                             key=lambda s: s['career']['archtype'])
    accepted_tank_signups = sorted([s for s in event['signups'] if s['status'] == 'Accepted' and s['career']['archtype'] == 'Tank'],
                              key=lambda s: s['career'])
    accepted_healer_signups = sorted([s for s in event['signups'] if s['status'] == 'Accepted' and s['career']['archtype'] == 'Healer'],
                              key=lambda s: s['career'])
    accepted_dps_signups = sorted([s for s in event['signups'] if s['status'] == 'Accepted' and s['career']['archtype'] == 'DPS'],
                              key=lambda s: s['career'])
    rejected_signups = sorted([s for s in event['signups'] if s['status'] == 'Rejected'],
                              key=lambda s: s['career']['archtype'])

    # Create the fields for the embed.
    accepted_tank_text = "\n".join([
        f"**{get_career_emoji(guild, s['career']['icon'])} {s['career']['archtype']}: {s['user_name']}** ({s['career']['name']})" for s in accepted_tank_signups
    ]) or "No one has been accepted yet."
    embed.add_field(name=f"✅ Accepted Tanks ({str(len(accepted_tank_signups))})", value=accepted_tank_text, inline=False)

    accepted_healer_text = "\n".join([
        f"**{get_career_emoji(guild, s['career']['icon'])} {s['career']['archtype']}: {s['user_name']}** ({s['career']['name']})" for s in accepted_healer_signups
    ]) or "No one has been accepted yet."
    embed.add_field(name=f"✅ Accepted Healers ({str(len(accepted_healer_signups))})", value=accepted_healer_text, inline=False)

    accepted_dps_text = "\n".join([
        f"**{get_career_emoji(guild, s['career']['icon'])} {s['career']['archtype']}: {s['user_name']}** ({s['career']['name']})" for s in accepted_dps_signups
    ]) or "No one has been accepted yet."
    embed.add_field(name=f"✅ Accepted DPS ({str(len(accepted_dps_signups))})", value=accepted_dps_text, inline=False)

    pending_text = "\n".join([
        f"**{get_career_emoji(guild, s['career']['icon'])} {s['career']['archtype']}: {s['user_name']}** ({s['career']['name']})" for s in pending_signups
    ]) or "No pending sign-ups."
    embed.add_field(name=f"⏳ Pending ({str(len(pending_signups))})", value=pending_text, inline=False)

    rejected_text = "\n".join([
        f"**{get_career_emoji(guild, s['career']['icon'])} {s['career']['archtype']}: {s['user_name']}** ({s['career']['name']})" for s in rejected_signups
    ]) or "No rejected sign-ups."
    # Only add the rejected field if there are rejected people to keep it clean.
    if rejected_signups:
        embed.add_field(name=f"❌ Rejected ({str(len(rejected_signups))})", value=rejected_text, inline=False)

    return embed

# Helper function to update an existing event message.
async def update_event_embed(message: discord.Message, event: dict):
    """Method to update an existing embed"""
    embed = create_event_embed(event, message.guild)
    await message.edit(embed=embed, view=EventView(event['organizer_id'], events, event['faction'], message.guild))


class WarhammerEvents(commands.Cog):
    def __init__(self, bot: commands.Bot, events: dict):
        self.bot = bot
        self.events = events
        self.cleanup_passed_events.start()
        self.alert_event.start()

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f'Cog {self.qualified_name} is ready.')


    @tasks.loop(minutes=5)
    async def cleanup_passed_events(self):
        """Checks every 5 minutes for events that have passed and removes them."""
        # It's important to not modify a dictionary while iterating over it.
        # So, we'll first find which events to remove and then remove them.
        events_to_remove = []
        current_utc_timestamp = datetime.now(timezone.utc).timestamp()

        for message_id, event_data in self.events.items():
            if event_data.get("time", 0) < current_utc_timestamp:
                events_to_remove.append(message_id)

        if events_to_remove:
            for message_id in events_to_remove:
                logging.info(f'Removing event {message_id}')
                del self.events[message_id]

            # Save the updated events list to the JSON file
            with open('warhammer_events.json', 'w') as f:
                json.dump(self.events, f, indent=4)

    @cleanup_passed_events.before_loop
    async def before_cleanup(self):
        """Waits until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()


    @tasks.loop(minutes=10)
    async def alert_event(self):
        """Task to alert accepted people that an event is about to start"""
        current_utc_timestamp = datetime.now(timezone.utc)
        future_30_minutes_timestamp = (current_utc_timestamp + timedelta(minutes=30)).timestamp()

        for event in events.values():
            if not event['has_announced'] and current_utc_timestamp.timestamp() <= event['time'] <= future_30_minutes_timestamp:
                accepted_users = [s['user_id'] for s in event['signups'] if s['status'] == 'Accepted']

                if not accepted_users:
                    continue

                formatted_mentions = " ".join([f"<@{user_id}>" for user_id in accepted_users])
                guild = self.bot.get_guild(event['guild'])
                if not guild:
                    continue  # Make sure the guild exists

                channel = guild.get_channel(event['channel'])
                if not channel:
                    continue  # Make sure the channel exists

                await channel.send(f"{formatted_mentions} The event {event['title']} is starting in less than 30 minutes!")
                event['has_announced'] = True


    @alert_event.before_loop
    async def before_alert(self):
        """waits until bot is read before starting the loop"""
        await self.bot.wait_until_ready()


    @discord.app_commands.command(name="cancel_ror_event", description="Cancel an event")
    async def remove_event_cancellation(self, interaction: discord.Interaction, message_id: str):
        """Cancel an event"""
        if not message_id.isdigit():
            await interaction.response.send_message("Invalid message ID. Please provide a numeric ID.", ephemeral=True)
            return

        message_id = int(message_id)

        if message_id not in events:
            await interaction.response.send_message("Event not found. Please check the message ID.", ephemeral=True)
            return

        event = events[message_id]
        if event['organizer_id'] != interaction.user.id:
            await interaction.response.send_message("You are not the owner of this event.", ephemeral=True)
            return

        await interaction.response.defer()
        await (await interaction.channel.fetch_message(message_id)).delete()
        title = event['title']
        events.pop(message_id)
        with open('warhammer_events.json', 'w') as f:
            json.dump(events, f, indent=4)
        await interaction.followup.send(f"Event cancelled: {title}", ephemeral=True)


    @discord.app_commands.command(name="create_ror_event", description="Create a new Warhammer Online event.")
    @discord.app_commands.describe(title="The name of the event", description="Description for the event", faction="What faction the event is for", date="Date for the event (YYYY-MM-DD)", time="Time of event (HH:MM)", timezone="Your timezone (I.E. 'Europe/Stockholm')")
    async def create_event(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        faction: Literal['Destruction', 'Order'],
        date: str,
        time: str,
        timezone: str
    ):
        """
        Creates a new Warhammer Online event with an interactive sign-up embed.
        """
        try:
            # 1. Combine date and time strings from user input
            naive_datetime_str = f"{date} {time}"

            # 2. Create a "naive" datetime object (no timezone info yet)
            naive_dt = datetime.strptime(naive_datetime_str, "%Y-%m-%d %H:%M")

            # 3. Find the user's timezone and make the datetime "aware"
            user_tz = ZoneInfo(timezone)
            aware_dt = naive_dt.astimezone(user_tz)

            # 4. Get the Unix timestamp (seconds since 1970-01-01), which is what Discord needs
            timestamp = int(aware_dt.timestamp())

        except (ValueError, ZoneInfoNotFoundError) as e:
            # Handle errors if the user provides a bad date, time, or timezone
            error_message = ""
            if isinstance(e, ValueError):
                error_message = "❌ **Invalid Format!** Please use `YYYY-MM-DD` for the date and `HH:MM` for the time."
            elif isinstance(e, ZoneInfoNotFoundError):
                error_message = f"❌ **Invalid Timezone!** I couldn't find the timezone `{timezone}`. Please use a valid TZ identifier like 'Europe/London' or 'America/Los_Angeles'."

            await interaction.response.send_message(error_message, ephemeral=True)
            return

        organizer = interaction.user

        # Create the initial event data structure.
        event_data = {
            'title': title,
            'description': description,
            'organizer_id': organizer.id,
            'organizer_name': organizer.display_name,
            'organizer_avatar': organizer.display_avatar.url,
            'signups': [],
            'faction': faction,
            'time': timestamp,
            'guild': interaction.guild.id,
            'channel': interaction.channel.id,
            'has_announced': False
        }

        # Create the initial embed and view.
        embed = create_event_embed(event_data, interaction.guild)
        
        # Pass the global `events` dictionary to the view.
        view = EventView(organizer.id, events, faction, interaction.guild)
        views.append(view) # save pointer

        # Defer the response first to avoid the 3-second timeout.
        await interaction.response.defer()
        
        # Now send the message as a follow-up.
        sent_message = await interaction.followup.send(embed=embed, view=view)
        
        # Store the event data using the message ID as the key.
        events[sent_message.id] = event_data
        with open('warhammer_events.json', 'w') as file:
            json.dump(events, file, indent=4)


    @discord.app_commands.command(name="accept_ror_signup", description="Accept a sign-up for an event.")
    async def accept_signup(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        message_id: str
    ):
        """
        Accepts a user's sign-up for a specified event.
        """
        if not message_id.isdigit():
            await interaction.response.send_message("Invalid message ID. Please provide a numeric ID.", ephemeral=True)
            return

        message_id = int(message_id)

        if message_id not in events:
            await interaction.response.send_message("Event not found. Please check the message ID.", ephemeral=True)
            return

        event = events[message_id]

        # Check if the command user is the event organizer.
        if interaction.user.id != event['organizer_id']:
            await interaction.response.send_message("You are not the organizer of this event.", ephemeral=True)
            return

        # Find the user in the sign-up list.
        for signup in event['signups']:
            if signup['user_id'] == user.id:
                signup['status'] = 'Accepted'
                await update_event_embed(await interaction.channel.fetch_message(message_id), event)
                await interaction.response.send_message(f"Accepted {signup['user_name']}'s sign-up.", ephemeral=True)
                return

        await interaction.response.send_message(f"{user.display_name} is not in the sign-up list.", ephemeral=True)


    @discord.app_commands.command(name="reject_ror_signup", description="Reject a sign-up for an event.")
    async def reject_signup(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        message_id: str
    ):
        """
        Rejects a user's sign-up for a specified event.
        """
        if not message_id.isdigit():
            await interaction.response.send_message("Invalid message ID. Please provide a numeric ID.", ephemeral=True)
            return

        message_id = int(message_id)

        if message_id not in events:
            await interaction.response.send_message("Event not found. Please check the message ID.", ephemeral=True)
            return

        event = events[message_id]

        # Check if the command user is the event organizer.
        if interaction.user.id != event['organizer_id']:
            await interaction.response.send_message("You are not the organizer of this event.", ephemeral=True)
            return

        # Find the user in the sign-up list.
        for signup in event['signups']:
            if signup['user_id'] == user.id:
                signup['status'] = 'Rejected'
                await update_event_embed(await interaction.channel.fetch_message(message_id), event)
                await interaction.response.send_message(f"Rejected {signup['user_name']}'s sign-up.", ephemeral=True)
                return

        await interaction.response.send_message(f"{user.display_name} is not in the sign-up list.", ephemeral=True)


async def setup(bot: commands.Bot):
    """Loads the cog"""
    events = {}
    if os.path.isfile('warhammer_events.json'):
        with open('warhammer_events.json', 'r') as file:
            events = json.load(file)
    await bot.add_cog(WarhammerEvents(bot, events))
