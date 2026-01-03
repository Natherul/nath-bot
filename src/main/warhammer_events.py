import discord
from discord import Emoji, NotFound, HTTPException
from discord.ext import commands, tasks
from discord.ui import View, Modal, TextInput
from discord import app_commands
from typing import Literal
import json
import os
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import logging
import io


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


def generate_ics_file(event: dict) -> io.BytesIO:
    """Generate an iCalendar (.ics) file for an event"""

    # Convert Unix timestamp to datetime
    event_dt = datetime.fromtimestamp(event['time'], tz=timezone.utc)

    # Format datetime for iCalendar (format: YYYYMMDDTHHMMSSZ)
    dtstart = event_dt.strftime('%Y%m%dT%H%M%SZ')

    # Calculate end time (assume 2 hours duration)
    # TODO: make this configurable
    end_dt = datetime.fromtimestamp(event['time'] + 7200, tz=timezone.utc)
    dtend = end_dt.strftime('%Y%m%dT%H%M%SZ')

    # Create timestamp for when the file was created
    dtstamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    # Create a unique identifier for the event
    uid = f"warhammer-event-{event['time']}-{event['organizer_id']}@discord"

    # Build the iCalendar content
    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Warhammer Online Events//Discord Bot//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART:{dtstart}",
        f"DTEND:{dtend}",
        f"SUMMARY:{event['title']}",
        f"DESCRIPTION:{event['description'].replace(',', '\\,')}",
        f"ORGANIZER;CN={event['organizer_name']}:invalid:nomail",
        f"LOCATION:Warhammer Online - {event['faction']}",
        "STATUS:CONFIRMED",
        "SEQUENCE:0",
        "BEGIN:VALARM",
        "TRIGGER:-PT30M",
        "ACTION:DISPLAY",
        "DESCRIPTION:Event starting in 30 minutes",
        "END:VALARM",
        "END:VEVENT",
        "END:VCALENDAR"
    ]

    # Join with CRLF as per iCalendar specification
    ics_text = "\r\n".join(ics_content)

    # Create a BytesIO object to send as a file
    ics_file = io.BytesIO(ics_text.encode('utf-8'))
    ics_file.seek(0)

    return ics_file


class CalendarButton(discord.ui.Button):
    """Button to download calendar file"""

    def __init__(self, event_dict: dict):
        super().__init__(
            label="Add to Calendar",
            style=discord.ButtonStyle.primary,
            emoji="📅",
            custom_id="download_calendar",
            row=3  # Place it on a separate row
        )
        self.events = event_dict

    async def callback(self, interaction: discord.Interaction):
        """Handle calendar download request"""
        event_id = str(interaction.message.id)

        if event_id not in self.events:
            await interaction.response.send_message(
                "This event no longer exists.",
                ephemeral=True
            )
            return

        event = self.events[event_id]

        # Generate the .ics file
        ics_file = generate_ics_file(event)

        # Create a safe filename
        safe_title = "".join(c for c in event['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_title}.ics"

        # Send the file to the user
        await interaction.response.send_message(
            "Here's your calendar file! Import it into your calendar app.",
            file=discord.File(ics_file, filename=filename),
            ephemeral=True
        )


class MemberOrIdTransformer(app_commands.Transformer):
    """Transformer that accepts either a Member mention or a user ID string"""

    async def transform(self, interaction: discord.Interaction, value: str) -> int:
        """
        Transforms the input to a user ID.
        Accepts: @mentions (Member objects), user IDs as strings, or raw IDs
        """
        # If Discord already resolved it to a Member object, just return the ID
        if isinstance(value, discord.Member):
            return value.id

        # If it's a string, try to parse it
        if isinstance(value, str):
            # Try to extract user ID from mention format <@123456789>
            if value.startswith('<@') and value.endswith('>'):
                user_id_str = value.strip('<@!>')
                if user_id_str.isdigit():
                    return int(user_id_str)

            # Try to parse as direct ID
            if value.isdigit():
                return int(value)

        raise app_commands.AppCommandError("Invalid user. Please mention a user or provide their ID.")

    @property
    def type(self) -> discord.AppCommandOptionType:
        """Specify that this accepts string input for proper autocomplete"""
        return discord.AppCommandOptionType.string


class CharacterNameModal(Modal):
    """Modal dialog for entering character name"""
    def __init__(self, career_id: str, event_dict: dict, cog_instance: commands.Cog, existing_name: str = None):
        super().__init__(title=f"Sign up as {CAREERS[career_id]['name']}")
        self.career_id = career_id
        self.events = event_dict
        self.cog_instance = cog_instance
        
        # Add text input for character name
        self.character_name = TextInput(
            label="Character Name",
            placeholder="Enter your character name...",
            required=True,
            max_length=50,
            default=existing_name
        )
        self.add_item(self.character_name)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission"""
        event_id = str(interaction.message.id)
        
        if event_id not in self.events:
            await interaction.response.send_message(
                "This event no longer exists.", ephemeral=True
            )
            return
        
        user = interaction.user
        event = self.events[event_id]
        character_name = self.character_name.value.strip()
        
        # Check if the user is already signed up
        found = False
        for signup in event['signups']:
            if signup['user_id'] == user.id:
                found = True
                # Update existing signup
                signup['career'] = CAREERS[self.career_id]
                signup['status'] = 'Pending'
                signup['icon'] = CAREERS[self.career_id]['icon']
                signup['character_name'] = character_name
                break
        
        # Add new signup if not found
        if not found:
            event['signups'].append({
                'user_id': user.id,
                'user_name': user.display_name,
                'career': CAREERS[self.career_id],
                'status': 'Pending',
                'icon': CAREERS[self.career_id]['icon'],
                'character_name': character_name
            })
        
        # Update the event message
        await self.cog_instance.update_event_embed(interaction.message, event)
        
        # Save to JSON
        with open('warhammer_events.json', 'w') as f:
            json.dump(self.events, f, indent=4)
        
        # Send confirmation
        message_part = "signed up" if not found else "updated your signup"
        await interaction.response.send_message(
            f"You have {message_part} as **{CAREERS[self.career_id]['name']}** with character name **{character_name}**.",
            ephemeral=True
        )


class signup_button(discord.ui.Button):
    def __init__(self, label: str, id: str, emoji: Emoji, event_dict: dict, cog_instance: commands.Cog):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=id,
            disabled=False,
            emoji=emoji,
            row=0 if CAREERS[id]['race'] in ["human", "chaos"] else 1 if CAREERS[id]['race'] in ["dwarf", "greenskin"] else 2
        )
        self.events = event_dict
        self.cog_instance = cog_instance

    async def callback(self, interaction: discord.Interaction):
        """Callback for when a button is pressed"""
        event_id = str(interaction.message.id)
        
        if event_id not in self.events:
            await interaction.response.send_message(
                "This event no longer exists.", ephemeral=True
            )
            return

        user = interaction.user
        career_id = interaction.data['custom_id']
        event = self.events[event_id]

        # Check if user is already signed up for this exact career
        existing_signup = None
        for signup in event['signups']:
            if signup['user_id'] == user.id:
                existing_signup = signup
                break
        
        # If clicking the same career button, remove signup
        if existing_signup and existing_signup['career']['icon'] == CAREERS[career_id]['icon']:
            event['signups'] = [s for s in event['signups'] if s['user_id'] != user.id]
            
            await self.cog_instance.update_event_embed(interaction.message, event)
            with open('warhammer_events.json', 'w') as f:
                json.dump(self.events, f, indent=4)
            
            await interaction.response.send_message(
                "You have removed your signup", ephemeral=True
            )
        else:
            # Show modal for character name (either new signup or career change)
            existing_char_name = existing_signup['character_name'] if existing_signup else None
            modal = CharacterNameModal(career_id, self.events, self.cog_instance, existing_char_name)
            await interaction.response.send_modal(modal)


# A subclass of View that will hold our sign-up buttons.
class EventView(View):
    def __init__(self, organizer_id: int, events_dict: dict, faction: str, guild: discord.Guild, cog_instance: commands.Cog):
        super().__init__(timeout=None)
        self.organizer_id = organizer_id
        self.events_dict = events_dict
        self.cog_instance = cog_instance

        # Add a button for each career in our dictionary.
        for career_id, data in CAREERS.items():
            if data['faction'] != faction:
                continue
            custom_emoji = discord.utils.get(guild.emojis, name=data['icon'])
            self.add_item(signup_button(data['name'], career_id, custom_emoji, self.events_dict, self.cog_instance))

        self.add_item(CalendarButton(self.events_dict))


def get_career_emoji(guild: discord.Guild, icon: str):
    """Helper method to get an emoji"""
    return discord.utils.get(guild.emojis, name=icon)


def create_event_embed(event: dict, guild: discord.Guild):
    """create an embed for an event"""
    embed = discord.Embed(
        title=event['title'],
        description=event['description'],
        color=discord.Color.blue()
    )
    embed.set_author(name=f"Event by {event['organizer_name']}", icon_url=event['organizer_avatar'])
    embed.set_footer(text="Click a button below to sign up with your character name!")
    embed.add_field(name="📅 When", value=f"<t:{event['time']}:F>", inline=False)

    # Group sign-ups by status
    pending_signups = sorted([s for s in event['signups'] if s['status'] == 'Pending'],
                             key=lambda s: s['career']['archtype'])
    accepted_tank_signups = sorted([s for s in event['signups'] if s['status'] == 'Accepted' and s['career']['archtype'] == 'Tank'],
                              key=lambda s: s['career']['name'])
    accepted_healer_signups = sorted([s for s in event['signups'] if s['status'] == 'Accepted' and s['career']['archtype'] == 'Healer'],
                              key=lambda s: s['career']['name'])
    accepted_dps_signups = sorted([s for s in event['signups'] if s['status'] == 'Accepted' and s['career']['archtype'] == 'DPS'],
                              key=lambda s: s['career']['name'])
    rejected_signups = sorted([s for s in event['signups'] if s['status'] == 'Rejected'],
                              key=lambda s: s['career']['archtype'])

    # Helper function to format signup text with character name
    def format_signup(s):
        char_name = s.get('character_name', 'No name')
        return f"**{get_career_emoji(guild, s['career']['icon'])} {s['career']['archtype']}: {char_name} - {s['user_name']}({s['user_id']})** ({s['career']['name']})"

    # Create the fields for the embed
    accepted_tank_text = "\n".join([format_signup(s) for s in accepted_tank_signups]) or "No one has been accepted yet."
    embed.add_field(name=f"✅ Accepted Tanks ({str(len(accepted_tank_signups))})", value=accepted_tank_text, inline=False)

    accepted_healer_text = "\n".join([format_signup(s) for s in accepted_healer_signups]) or "No one has been accepted yet."
    embed.add_field(name=f"✅ Accepted Healers ({str(len(accepted_healer_signups))})", value=accepted_healer_text, inline=False)

    accepted_dps_text = "\n".join([format_signup(s) for s in accepted_dps_signups]) or "No one has been accepted yet."
    embed.add_field(name=f"✅ Accepted DPS ({str(len(accepted_dps_signups))})", value=accepted_dps_text, inline=False)

    pending_text = "\n".join([format_signup(s) for s in pending_signups]) or "No pending sign-ups."
    embed.add_field(name=f"⏳ Pending ({str(len(pending_signups))})", value=pending_text, inline=False)

    rejected_text = "\n".join([format_signup(s) for s in rejected_signups]) or "No rejected sign-ups."
    if rejected_signups:
        embed.add_field(name=f"❌ Rejected ({str(len(rejected_signups))})", value=rejected_text, inline=False)

    return embed


def load_events():
    if os.path.isfile('warhammer_events.json'):
        with open('warhammer_events.json', 'r') as file:
            return json.load(file)
    else:
        return {}


class WarhammerEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cleanup_passed_events.start()
        self.alert_event.start()
        self.events = load_events()

        # Restore persistent views for events after restart
        try:
            for message_id, event in list(self.events.items()):
                try:
                    guild = self.bot.get_guild(event.get("guild"))
                    if guild is None:
                        continue
                    organizer_id = event.get("organizer_id")
                    faction = event.get("faction")
                    view = EventView(organizer_id, self.events, faction, guild, self)
                    self.bot.add_view(view, message_id=int(message_id))
                except Exception as e:
                    logging.exception(f"Failed to restore EventView for message_id={message_id}: {e}")
        except Exception as e:
            logging.exception(f"Error while restoring persistent EventViews: {e}")

    async def update_event_embed(self, message: discord.Message, event: dict):
        """Method to update an existing embed"""
        embed = create_event_embed(event, message.guild)
        await message.edit(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f'Cog {self.qualified_name} is ready.')
        for message_id, event_data in self.events.items():
            guild = self.bot.get_guild(event_data['guild'])
            if guild:
                view = EventView(
                    organizer_id=event_data['organizer_id'],
                    events_dict=self.events,
                    faction=event_data['faction'],
                    guild=guild,
                    cog_instance=self
                )
                self.bot.add_view(view, message_id=int(message_id))

    @tasks.loop(minutes=5)
    async def cleanup_passed_events(self):
        """Checks every 5 minutes for events that have passed and removes them."""
        events_to_remove = []
        current_utc_timestamp = datetime.now(timezone.utc).timestamp()

        for message_id, event_data in self.events.items():
            if event_data.get("time", 0) < current_utc_timestamp:
                events_to_remove.append(message_id)

        if events_to_remove:
            for message_id in events_to_remove:
                logging.info(f'Removing event {message_id}')
                del self.events[message_id]

            with open('warhammer_events.json', 'w') as f:
                json.dump(self.events, f, indent=4)

    @cleanup_passed_events.before_loop
    async def before_cleanup(self):
        """Waits until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=1)
    async def alert_event(self):
        """Task to alert accepted people that an event is about to start"""
        current_utc_timestamp = datetime.now(timezone.utc)
        future_30_minutes_timestamp = (current_utc_timestamp + timedelta(minutes=30)).timestamp()

        for event in self.events.values():
            if not event['has_announced'] and current_utc_timestamp.timestamp() <= event['time'] <= future_30_minutes_timestamp:
                accepted_users = [s['user_id'] for s in event['signups'] if s['status'] == 'Accepted']

                if not accepted_users:
                    continue

                formatted_mentions = " ".join([f"<@{user_id}>" for user_id in accepted_users])
                guild = self.bot.get_guild(event['guild'])
                if not guild:
                    continue

                channel = guild.get_channel(event['channel'])
                if not channel:
                    continue

                await channel.send(f"{formatted_mentions} The event {event['title']} is starting in less than 30 minutes!")
                event['has_announced'] = True
                try:
                    hoster = await guild.fetch_member(event['organizer_id'])
                    accepted_characters = [s['character_name'] for s in event['signups'] if s['status'] == 'Accepted' and s['user_id'] != event['organizer_id']]

                    # Format with proper newlines and code block
                    invite_commands = "\n/invite ".join(accepted_characters)
                    message_text = f"Here is a little helpful message to do the invites:\n```\n/invite {invite_commands}\n```"

                    await hoster.send(message_text)
                except (NotFound, HTTPException):
                    logging.error("Something went wrong when attempting to get organizer member")

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

        if message_id not in self.events:
            await interaction.response.send_message("Event not found. Please check the message ID.", ephemeral=True)
            return

        event = self.events[message_id]
        if event['organizer_id'] != interaction.user.id:
            await interaction.response.send_message("You are not the owner of this event.", ephemeral=True)
            return

        await interaction.response.defer()
        await (await interaction.channel.fetch_message(int(message_id))).delete()
        title = event['title']
        self.events.pop(message_id)
        with open('warhammer_events.json', 'w') as f:
            json.dump(self.events, f, indent=4)
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
        """Creates a new Warhammer Online event with an interactive sign-up embed."""
        try:
            naive_datetime_str = f"{date} {time}"
            naive_dt = datetime.strptime(naive_datetime_str, "%Y-%m-%d %H:%M")
            user_tz = ZoneInfo(timezone)
            aware_dt = naive_dt.replace(tzinfo=user_tz)
            timestamp = int(aware_dt.timestamp())
        except (ValueError, ZoneInfoNotFoundError) as e:
            error_message = ""
            if isinstance(e, ValueError):
                error_message = "❌ **Invalid Format!** Please use `YYYY-MM-DD` for the date and `HH:MM` for the time."
            elif isinstance(e, ZoneInfoNotFoundError):
                error_message = f"❌ **Invalid Timezone!** I couldn't find the timezone `{timezone}`. Please use a valid TZ identifier like 'Europe/London' or 'America/Los_Angeles'."
            await interaction.response.send_message(error_message, ephemeral=True)
            return

        organizer = interaction.user

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

        embed = create_event_embed(event_data, interaction.guild)
        view = EventView(organizer.id, self.events, faction, interaction.guild, self)

        await interaction.response.defer()
        sent_message = await interaction.followup.send(embed=embed, view=view)
        
        self.events[str(sent_message.id)] = event_data
        with open('warhammer_events.json', 'w') as file:
            json.dump(self.events, file, indent=4)


    @discord.app_commands.command(name="accept_ror_signup", description="Accept a sign-up for an event.")
    @discord.app_commands.describe(
        user="Select a user from the list or type their user ID",
        message_id="The message ID of the event"
    )
    async def accept_signup(
            self,
            interaction: discord.Interaction,
            user: str,  # Accept as string to handle both cases
            message_id: str
    ):
        """Accepts a user's sign-up for a specified event."""
        if not message_id.isdigit():
            await interaction.response.send_message("Invalid message ID. Please provide a numeric ID.", ephemeral=True)
            return

        if message_id not in self.events:
            await interaction.response.send_message("Event not found. Please check the message ID.", ephemeral=True)
            return

        event = self.events[message_id]

        if interaction.user.id != event['organizer_id']:
            await interaction.response.send_message("You are not the organizer of this event.", ephemeral=True)
            return

        # Parse the user input - could be a mention or an ID
        user_id = None
        if user.startswith('<@') and user.endswith('>'):
            # It's a mention format
            user_id_str = user.strip('<@!>')
            if user_id_str.isdigit():
                user_id = int(user_id_str)
        elif user.isdigit():
            # It's a direct ID
            user_id = int(user)

        if user_id is None:
            await interaction.response.send_message("Invalid user format. Please mention a user or provide their ID.",
                                                    ephemeral=True)
            return

        # Try to fetch the member for display name
        try:
            member = await interaction.guild.fetch_member(user_id)
            user_display_name = member.display_name
        except discord.NotFound:
            user_display_name = f"User ID {user_id}"

        for signup in event['signups']:
            if signup['user_id'] == user_id:
                signup['status'] = 'Accepted'
                message = await interaction.channel.fetch_message(int(message_id))
                await self.update_event_embed(message, event)
                with open('warhammer_events.json', 'w') as f:
                    json.dump(self.events, f, indent=4)
                await interaction.response.send_message(f"Accepted {user_display_name}'s sign-up.", ephemeral=True)
                return

        await interaction.response.send_message(f"{user_display_name} is not in the sign-up list.", ephemeral=True)


    @discord.app_commands.command(name="reject_ror_signup", description="Reject a sign-up for an event.")
    @discord.app_commands.describe(
        user="Select a user from the list or type their user ID",
        message_id="The message ID of the event"
    )
    async def reject_signup(
            self,
            interaction: discord.Interaction,
            user: str,  # Accept as string to handle both cases
            message_id: str
    ):
        """Rejects a user's sign-up for a specified event."""
        if not message_id.isdigit():
            await interaction.response.send_message("Invalid message ID. Please provide a numeric ID.", ephemeral=True)
            return

        if message_id not in self.events:
            await interaction.response.send_message("Event not found. Please check the message ID.", ephemeral=True)
            return

        event = self.events[message_id]

        if interaction.user.id != event['organizer_id']:
            await interaction.response.send_message("You are not the organizer of this event.", ephemeral=True)
            return

        # Parse the user input - could be a mention or an ID
        user_id = None
        if user.startswith('<@') and user.endswith('>'):
            # It's a mention format
            user_id_str = user.strip('<@!>')
            if user_id_str.isdigit():
                user_id = int(user_id_str)
        elif user.isdigit():
            # It's a direct ID
            user_id = int(user)

        if user_id is None:
            await interaction.response.send_message("Invalid user format. Please mention a user or provide their ID.",
                                                    ephemeral=True)
            return

        # Try to fetch the member for display name
        try:
            member = await interaction.guild.fetch_member(user_id)
            user_display_name = member.display_name
        except discord.NotFound:
            user_display_name = f"User ID {user_id}"

        for signup in event['signups']:
            if signup['user_id'] == user_id:
                signup['status'] = 'Rejected'
                message = await interaction.channel.fetch_message(int(message_id))
                await self.update_event_embed(message, event)
                with open('warhammer_events.json', 'w') as f:
                    json.dump(self.events, f, indent=4)
                await interaction.response.send_message(f"Rejected {user_display_name}'s sign-up.", ephemeral=True)
                return

        await interaction.response.send_message(f"{user_display_name} is not in the sign-up list.", ephemeral=True)


    # Add this autocomplete function to the WarhammerEvents class
    @accept_signup.autocomplete('user')
    @reject_signup.autocomplete('user')
    async def user_autocomplete(
            self,
            interaction: discord.Interaction,
            current: str,
    ) -> list[app_commands.Choice[str]]:
        """Provide autocomplete suggestions for users"""
        # Get all members in the guild
        members = interaction.guild.members

        # Filter members based on what the user is typing
        filtered = [
            member for member in members
            if current.lower() in member.display_name.lower() or current.lower() in member.name.lower()
        ][:25]  # Discord limits to 25 choices

        return [
            app_commands.Choice(name=member.display_name, value=str(member.id))
            for member in filtered
        ]


async def setup(bot: commands.Bot):
    """Loads the cog"""
    await bot.add_cog(WarhammerEvents(bot))
