import discord
from discord import Emoji, NotFound, HTTPException
from discord.ext import commands, tasks
from discord.ui import View, Modal, TextInput, Select
from discord import app_commands
import json
import os
from datetime import datetime, timezone, timedelta
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


class EventCreationStep1Modal(Modal):
    """Step 1: Title, Description, Faction"""

    def __init__(self, cog_instance):
        super().__init__(title="Create Event - Event Details", timeout=300)
        self.cog_instance = cog_instance

        self.title_input = TextInput(
            label="Event Title",
            placeholder="e.g., What you are doing",
            required=True,
            max_length=100
        )
        self.add_item(self.title_input)

        self.description_input = TextInput(
            label="Event Description",
            placeholder="Describe your event...",
            required=True,
            style=discord.TextStyle.paragraph,
            max_length=1000
        )
        self.add_item(self.description_input)

        self.faction_input = TextInput(
            label="Faction (Order or Destruction)",
            placeholder="Type: Order or Destruction",
            required=True,
            max_length=20
        )
        self.add_item(self.faction_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Validate faction
        faction = self.faction_input.value.strip().title()
        if faction not in ["Order", "Destruction"]:
            await interaction.response.send_message(
                "❌ Invalid faction! Please enter 'Order' or 'Destruction'.",
                ephemeral=True
            )
            return

        # Show next modal for date/time/duration/timezone
        modal = EventCreationStep2Modal(
            self.cog_instance,
            self.title_input.value,
            self.description_input.value,
            faction
        )

        # Need to send a message first, then show the modal via a button
        view = NextStepButtonView(modal)
        await interaction.response.send_message(
            "✅ Event details saved! Click 'Next' to set date and time. This need to be done within 5 minutes or the event is not created!",
            view=view,
            ephemeral=True
        )
        # This allows the on_timeout method to find and edit the message later
        view.message = await interaction.original_response()


class NextStepButtonView(View):
    """View with a Next button to open the next modal"""
    def __init__(self, next_modal):
        super().__init__(timeout=300)
        self.next_modal = next_modal

        button = discord.ui.Button(
            label="Next",
            style=discord.ButtonStyle.primary,
            emoji="▶️"
        )
        button.callback = self.open_modal
        self.add_item(button)

    async def open_modal(self, interaction: discord.Interaction):
        await interaction.response.send_modal(self.next_modal)
        # Store reference to this interaction's message so the modal can edit it later
        self.next_modal.next_button_interaction_message = interaction.message

    async def on_timeout(self):
        """Called when the view times out (5 minutes)"""
        # Disable all buttons when timeout occurs
        try:
            for item in self.children:
                item.disabled = True
            if self.message:
                await self.message.edit(view=self)
        except NotFound: # We have probably removed or edited the message in this case
            pass


class EventCreationStep2Modal(Modal):
    """Step 2: Date, Time, Duration, Timezone"""

    def __init__(self, cog_instance, title: str, description: str, faction: str):
        super().__init__(title="Create Event - Date & Time", timeout=300)
        self.cog_instance = cog_instance
        self.event_title = title
        self.event_description = description
        self.faction = faction
        self.next_button_interaction_message = None

        self.date_input = TextInput(
            label="Date (YYYY-MM-DD)",
            placeholder="e.g., 2026-01-15",
            required=True,
            max_length=10
        )
        self.add_item(self.date_input)

        self.time_input = TextInput(
            label="Time (HH:MM, 24-hour format)",
            placeholder="e.g., 19:30",
            required=True,
            max_length=5
        )
        self.add_item(self.time_input)

        self.duration_input = TextInput(
            label="Duration (in minutes)",
            placeholder="e.g., 120 for 2 hours",
            required=True,
            max_length=4,
            default="120"
        )
        self.add_item(self.duration_input)

        self.timezone_input = TextInput(
            label="Timezone",
            placeholder="e.g., Europe/Stockholm, America/New_York, UTC",
            required=True,
            max_length=50,
            default="UTC"
        )
        self.add_item(self.timezone_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Validate duration
        try:
            duration = int(self.duration_input.value)
            if duration <= 0 or duration > 1440:
                raise ValueError()
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid duration! Must be between 1 and 1440 minutes.",
                ephemeral=True
            )
            return

        date = self.date_input.value.strip()
        time = self.time_input.value.strip()
        timezone = self.timezone_input.value.strip()

        # Parse and validate the datetime
        try:
            from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

            naive_datetime_str = f"{date} {time}"
            naive_dt = datetime.strptime(naive_datetime_str, "%Y-%m-%d %H:%M")
            user_tz = ZoneInfo(timezone)
            aware_dt = naive_dt.replace(tzinfo=user_tz)
            timestamp = int(aware_dt.timestamp())

        except (ValueError, ZoneInfoNotFoundError) as e:
            if isinstance(e, ZoneInfoNotFoundError):
                await interaction.response.send_message(
                    f"❌ Invalid timezone '{timezone}'. Try 'UTC', 'Europe/Stockholm', or 'America/New_York'.",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "❌ Invalid date/time format! Use YYYY-MM-DD for date and HH:MM for time.",
                    ephemeral=True
                )
            return

        # Get organizer and guild info
        organizer = interaction.user
        guild = interaction.guild
        channel = interaction.channel

        # Create the event
        event_data = {
            'title': self.event_title,
            'description': self.event_description,
            'organizer_id': organizer.id,
            'organizer_name': organizer.display_name,
            'organizer_avatar': organizer.display_avatar.url,
            'signups': [],
            'faction': self.faction,
            'time': timestamp,
            'duration': duration,
            'guild': guild.id,
            'channel': channel.id,
            'has_announced': False
        }

        await interaction.response.defer(ephemeral=True)

        embed = create_event_embed(event_data, guild)
        view = EventView(
            organizer.id,
            self.cog_instance.events,
            self.faction,
            guild,
            self.cog_instance
        )

        # Send the event message to the original channel
        sent_message = await channel.send(embed=embed, view=view)

        # Save the event
        self.cog_instance.events[str(sent_message.id)] = event_data
        with open('warhammer_events.json', 'w') as file:
            json.dump(self.cog_instance.events, file, indent=4)

        # Delete the deferred response (the invisible acknowledgment)
        await interaction.delete_original_response()


# ============================================
# Cancel Event with Dropdown
# ============================================

class CancelEventView(View):
    """View for selecting which event to cancel"""

    def __init__(self, user_id: int, events: dict):
        super().__init__(timeout=300)

        # Filter events where user is the organizer
        user_events = {
            msg_id: event for msg_id, event in events.items()
            if event['organizer_id'] == user_id
        }

        if not user_events:
            return

        # Create dropdown options (max 25)
        options = []
        for msg_id, event in list(user_events.items())[:25]:
            # Format timestamp for display
            event_time = datetime.fromtimestamp(event['time'], tz=timezone.utc)
            time_str = event_time.strftime('%Y-%m-%d %H:%M')

            options.append(
                discord.SelectOption(
                    label=event['title'][:100],  # Discord limit
                    value=msg_id,
                    description=f"{event['faction']} - {time_str} UTC"
                )
            )

        self.event_select = Select(
            placeholder="Select event to cancel",
            options=options
        )
        self.event_select.callback = self.cancel_callback
        self.add_item(self.event_select)

        self.events = events

    async def cancel_callback(self, interaction: discord.Interaction):
        message_id = self.event_select.values[0]

        if message_id not in self.events:
            await interaction.response.send_message(
                "Event not found.",
                ephemeral=True
            )
            return

        event = self.events[message_id]

        # Delete the event message
        try:
            channel = interaction.guild.get_channel(event['channel'])
            message = await channel.fetch_message(int(message_id))
            await message.delete()
        except:
            pass

        # Remove from events dict
        title = event['title']
        self.events.pop(message_id)

        with open('warhammer_events.json', 'w') as f:
            json.dump(self.events, f, indent=4)

        # Edit the message to show completion (instead of send_message)
        await interaction.response.edit_message(
            content=f"✅ Event cancelled: **{title}**",
            view=None
        )


# ============================================
# Accept/Reject Signup with Dropdowns
# ============================================

class AcceptSignupView(View):
    """View for selecting event and member to accept"""

    def __init__(self, user_id: int, events: dict, cog_instance):
        super().__init__(timeout=300)
        self.cog_instance = cog_instance
        self.events = events
        self.user_id = user_id

        # Filter events where user is the organizer
        user_events = {
            msg_id: event for msg_id, event in events.items()
            if event['organizer_id'] == user_id
        }

        if not user_events:
            return

        # Create event dropdown
        options = []
        for msg_id, event in list(user_events.items())[:25]:
            event_time = datetime.fromtimestamp(event['time'], tz=timezone.utc)
            time_str = event_time.strftime('%Y-%m-%d %H:%M')

            options.append(
                discord.SelectOption(
                    label=event['title'][:100],
                    value=msg_id,
                    description=f"{event['faction']} - {time_str} UTC"
                )
            )

        self.event_select = Select(
            placeholder="Select event",
            options=options,
            row=0
        )
        self.event_select.callback = self.event_callback
        self.add_item(self.event_select)

        self.selected_event_id = None

    async def event_callback(self, interaction: discord.Interaction):
        self.selected_event_id = self.event_select.values[0]
        event = self.events[self.selected_event_id]

        # Get pending signups
        possible_candidates = [s for s in event['signups'] if s['status'] == 'Pending' or s['status'] == 'Rejected']

        if not possible_candidates:
            await interaction.response.edit_message(
                content="No pending signups for this event.",
                view=None
            )
            return

        # Create member dropdown
        member_options = []
        for signup in possible_candidates[:25]:
            member_options.append(
                discord.SelectOption(
                    label=signup['user_name'],
                    value=str(signup['user_id']),
                    description=f"{signup['career']['name']} - {signup.get('character_name', 'No name')}"
                )
            )

        member_select = Select(
            placeholder="Select member to accept",
            options=member_options,
            row=0
        )
        member_select.callback = self.accept_callback

        # Create new view with member dropdown
        new_view = View(timeout=300)
        new_view.add_item(member_select)
        new_view.events = self.events
        new_view.selected_event_id = self.selected_event_id
        new_view.cog_instance = self.cog_instance

        # Edit the existing message
        await interaction.response.edit_message(
            content="Now select the member to accept:",
            view=new_view
        )

    async def accept_callback(self, interaction: discord.Interaction):
        user_id = int(interaction.data['values'][0])
        event = self.events[self.selected_event_id]

        # Update signup status
        for signup in event['signups']:
            if signup['user_id'] == user_id:
                signup['status'] = 'Accepted'
                break

        # Update event message
        channel = interaction.guild.get_channel(event['channel'])
        message = await channel.fetch_message(int(self.selected_event_id))
        await self.cog_instance.update_event_embed(message, event)

        with open('warhammer_events.json', 'w') as f:
            json.dump(self.events, f, indent=4)

        # Edit message to show completion
        await interaction.response.edit_message(
            content="✅ Signup accepted!",
            view=None
        )

class RejectSignupView(View):
    """View for selecting event and member to reject"""

    def __init__(self, user_id: int, events: dict, cog_instance):
        super().__init__(timeout=300)
        self.cog_instance = cog_instance
        self.events = events
        self.user_id = user_id

        # Filter events where user is the organizer
        user_events = {
            msg_id: event for msg_id, event in events.items()
            if event['organizer_id'] == user_id
        }

        if not user_events:
            return

        # Create event dropdown
        options = []
        for msg_id, event in list(user_events.items())[:25]:
            event_time = datetime.fromtimestamp(event['time'], tz=timezone.utc)
            time_str = event_time.strftime('%Y-%m-%d %H:%M')

            options.append(
                discord.SelectOption(
                    label=event['title'][:100],
                    value=msg_id,
                    description=f"{event['faction']} - {time_str} UTC"
                )
            )

        self.event_select = Select(
            placeholder="Select event",
            options=options,
            row=0
        )
        self.event_select.callback = self.event_callback
        self.add_item(self.event_select)

        self.selected_event_id = None

    async def event_callback(self, interaction: discord.Interaction):
        self.selected_event_id = self.event_select.values[0]
        event = self.events[self.selected_event_id]

        # Get pending signups
        possible_candidates = [s for s in event['signups'] if s['status'] == 'Pending' or s['status'] == 'Accepted']

        if not possible_candidates:
            await interaction.response.edit_message(
                content="No pending signups for this event.",
                view=None
            )
            return

        # Create member dropdown
        member_options = []
        for signup in possible_candidates[:25]:
            member_options.append(
                discord.SelectOption(
                    label=signup['user_name'],
                    value=str(signup['user_id']),
                    description=f"{signup['career']['name']} - {signup.get('character_name', 'No name')}"
                )
            )

        member_select = Select(
            placeholder="Select member to reject",
            options=member_options,
            row=0
        )
        member_select.callback = self.reject_callback

        # Create new view with member dropdown
        new_view = View(timeout=300)
        new_view.add_item(member_select)
        new_view.events = self.events
        new_view.selected_event_id = self.selected_event_id
        new_view.cog_instance = self.cog_instance

        # Edit the existing message
        await interaction.response.edit_message(
            content="Now select the member to reject:",
            view=new_view
        )

    async def reject_callback(self, interaction: discord.Interaction):
        user_id = int(interaction.data['values'][0])
        event = self.events[self.selected_event_id]

        # Update signup status
        for signup in event['signups']:
            if signup['user_id'] == user_id:
                signup['status'] = 'Rejected'
                break

        # Update event message
        channel = interaction.guild.get_channel(event['channel'])
        message = await channel.fetch_message(int(self.selected_event_id))
        await self.cog_instance.update_event_embed(message, event)

        with open('warhammer_events.json', 'w') as f:
            json.dump(self.events, f, indent=4)

        # Edit message to show completion
        await interaction.response.edit_message(
            content="✅ Signup rejected!",
            view=None
        )

def generate_ics_file(event: dict) -> io.BytesIO:
    """Generate an iCalendar (.ics) file for an event"""

    # Convert Unix timestamp to datetime
    event_dt = datetime.fromtimestamp(event['time'], tz=timezone.utc)

    # Format datetime for iCalendar (format: YYYYMMDDTHHMMSSZ)
    dtstart = event_dt.strftime('%Y%m%dT%H%M%SZ')

    # Calculate end time using the event's duration (in minutes)
    duration_seconds = event.get('duration', 120) * 60
    end_dt = datetime.fromtimestamp(event['time'] + duration_seconds, tz=timezone.utc)
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
            row=3
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
        return f"**{get_career_emoji(guild, s['career']['icon'])} {s['career']['archtype']}: {char_name} - {s['user_name']}** ({s['career']['name']})"

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

    @discord.app_commands.command(name="create_ror_event", description="Create a new Warhammer Online event.")
    async def create_event(self, interaction: discord.Interaction):
        """Opens event creation modal."""
        modal = EventCreationStep1Modal(self)
        await interaction.response.send_modal(modal)

    @discord.app_commands.command(name="cancel_ror_event", description="Cancel an event")
    async def remove_event_cancellation(self, interaction: discord.Interaction):
        """Cancel an event using dropdown selection"""
        view = CancelEventView(interaction.user.id, self.events)

        if not view.children:
            await interaction.response.send_message(
                "You have no events to cancel.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Select an event to cancel:",
            view=view,
            ephemeral=True
        )

    @discord.app_commands.command(name="accept_ror_signup", description="Accept a sign-up for an event.")
    async def accept_signup(self, interaction: discord.Interaction):
        """Accept a user's sign-up using dropdown selection"""
        view = AcceptSignupView(interaction.user.id, self.events, self)

        if not view.children:
            await interaction.response.send_message(
                "You have no events to manage.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Select an event:",
            view=view,
            ephemeral=True
        )

    @discord.app_commands.command(name="reject_ror_signup", description="Reject a sign-up for an event.")
    async def reject_signup(self, interaction: discord.Interaction):
        """Reject a user's sign-up using dropdown selection"""
        view = RejectSignupView(interaction.user.id, self.events, self)

        if not view.children:
            await interaction.response.send_message(
                "You have no events to manage.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Select an event:",
            view=view,
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    """Loads the cog"""
    await bot.add_cog(WarhammerEvents(bot))
