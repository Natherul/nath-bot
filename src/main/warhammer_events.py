import discord
from discord.ext import commands
from discord.ui import Button, View
from typing import Literal


# A simple in-memory dictionary to store event data.
# For a production bot, you would want to use a database like MongoDB or SQLite.
events = {}
views = []

# Dictionary mapping careers to their full name and a suitable icon URL.
# Grouped by faction and realm for clarity.
CAREERS = {
    # Order Faction
    'knight_of_the_blazing_sun': {'name': 'Knight of the Blazing Sun', 'icon': 'https://imgur.com/1TIekrQ', 'faction': 'Order'},
    'warrior_priest': {'name': 'Warrior Priest', 'icon': 'https://imgur.com/lv0rcPE', 'faction': 'Order'},
    'bright_wizard': {'name': 'Bright Wizard', 'icon': 'https://imgur.com/UFgGTCe', 'faction': 'Order'},
    'witch_hunter': {'name': 'Witch Hunter', 'icon': 'https://imgur.com/eXs9iXk', 'faction': 'Order'},
    'ironbreaker': {'name': 'Ironbreaker', 'icon': 'https://imgur.com/aEGUPDI', 'faction': 'Order'},
    'runepriest': {'name': 'Runepriest', 'icon': 'https://imgur.com/BWYAe6N', 'faction': 'Order'},
    'engineer': {'name': 'Engineer', 'icon': 'https://imgur.com/fPLygxr', 'faction': 'Order'},
    'slayer': {'name': 'Slayer', 'icon': 'https://imgur.com/FhcOzTb', 'faction': 'Order'},
    'swordmaster': {'name': 'Swordmaster', 'icon': 'https://imgur.com/0SPd9np', 'faction': 'Order'},
    'archmage': {'name': 'Archmage', 'icon': 'https://imgur.com/mpZh2yo', 'faction': 'Order'},
    'shadow_warrior': {'name': 'Shadow Warrior', 'icon': 'https://imgur.com/R1CZH6g', 'faction': 'Order'},
    'white_lion': {'name': 'White Lion', 'icon': 'https://imgur.com/TEZXP7c', 'faction': 'Order'},

    # Destruction Faction
    'chosen': {'name': 'Chosen', 'icon': 'https://i.imgur.com/qWCnhQ7.png', 'faction': 'Destruction'},
    'zealot': {'name': 'Zealot', 'icon': 'https://i.imgur.com/oWA7Xzp.png', 'faction': 'Destruction'},
    'magus': {'name': 'Magus', 'icon': 'https://i.imgur.com/yyvFCyY.png', 'faction': 'Destruction'},
    'marauder': {'name': 'Marauder', 'icon': 'https://imgur.com/NGgyo7T', 'faction': 'Destruction'},
    'black_orc': {'name': 'Black Orc', 'icon': 'https://imgur.com/O87YNFi', 'faction': 'Destruction'},
    'shaman': {'name': 'Shaman', 'icon': 'https://imgur.com/gMjTisu', 'faction': 'Destruction'},
    'squig_herder': {'name': 'Squig Herder', 'icon': 'https://imgur.com/Giraxb1', 'faction': 'Destruction'},
    'choppa': {'name': 'Choppa', 'icon': 'https://imgur.com/OAwH25N', 'faction': 'Destruction'},
    'black_guard': {'name': 'Black Guard', 'icon': 'https://imgur.com/2AJnVb4', 'faction': 'Destruction'},
    'disciple_of_khaine': {'name': 'Disciple of Khaine', 'icon': 'https://imgur.com/hfh8IMa', 'faction': 'Destruction'},
    'sorcerer': {'name': 'Sorcerer', 'icon': 'https://imgur.com/ozhl6i7', 'faction': 'Destruction'},
    'witch_elf': {'name': 'Witch Elf', 'icon': 'https://imgur.com/R71iEFc', 'faction': 'Destruction'},
}

class signup_button(discord.ui.Button):
    def __init__(self, label: str, id: str):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            custom_id=id,
            disabled=False
        )


    # This method is called whenever a button is pressed.
    async def callback(self, interaction: discord.Interaction):
        # Find the event data from our global dictionary using the message ID.
        event_id = interaction.message.id
        # Access the events dictionary via the instance attribute
        if event_id not in events:
            print("SAD")
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
            if signup['user'].id == user.id:
                found = True
                if signup['career'] == CAREERS[career_id]:
                    event['signups'] = [signup for signup in event['signups'] if signup['user'] != user]
                    removed = True
                    break
                else:
                    for signup in event['signups']:
                        if signup['user'] == user:
                            signup['career'] = CAREERS[career_id]
                            break

        # Add the user to the sign-up list with a 'pending' status.
        if not found:
            event['signups'].append({
                'user': user,
                'career': CAREERS[career_id],
                'status': 'Pending'
            })

        # Update the event message with the new sign-up list.
        await update_event_embed(interaction.message, event)

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
    def __init__(self, organizer_id: int, events_dict: dict, faction: str):
        super().__init__(timeout=None)
        self.organizer_id = organizer_id
        self.events_dict = events_dict # Store the events dictionary

        # Add a button for each career in our dictionary.
        for career_id, data in CAREERS.items():
            if data['faction'] != faction:
                continue
            self.add_item(signup_button(data['name'], career_id))


# Helper function to create/update the embed.
def create_event_embed(event: dict):
    embed = discord.Embed(
        title=event['title'],
        description=event['description'],
        color=discord.Color.blue()
    )
    embed.set_author(name=f"Event by {event['organizer'].name}", icon_url=event['organizer'].avatar)
    embed.set_footer(text="Click a button below to sign up!")

    # Group sign-ups by status.
    pending_signups = [s for s in event['signups'] if s['status'] == 'Pending']
    accepted_signups = [s for s in event['signups'] if s['status'] == 'Accepted']
    rejected_signups = [s for s in event['signups'] if s['status'] == 'Rejected']

    # Create the fields for the embed.
    accepted_text = "\n".join([
        f"**{s['user'].display_name}** ({s['career']['name']})" for s in accepted_signups
    ]) or "No one has been accepted yet."
    embed.add_field(name="✅ Accepted", value=accepted_text, inline=False)

    pending_text = "\n".join([
        f"**{s['user'].display_name}** ({s['career']['name']})" for s in pending_signups
    ]) or "No pending sign-ups."
    embed.add_field(name="⏳ Pending", value=pending_text, inline=False)

    rejected_text = "\n".join([
        f"**{s['user'].display_name}** ({s['career']['name']})" for s in rejected_signups
    ]) or "No rejected sign-ups."
    # Only add the rejected field if there are rejected people to keep it clean.
    if rejected_signups:
        embed.add_field(name="❌ Rejected", value=rejected_text, inline=False)

    return embed

# Helper function to update an existing event message.
async def update_event_embed(message: discord.Message, event: dict):
    embed = create_event_embed(event)
    await message.edit(embed=embed, view=EventView(event['organizer'].id, events, event['faction']))

class WarhammerEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog {self.qualified_name} is ready.')


    @discord.app_commands.command(name="create_ror_event", description="Create a new Warhammer Online event.")
    async def create_event(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        faction: Literal['Destruction', 'Order']
    ):
        """
        Creates a new Warhammer Online event with an interactive sign-up embed.
        """
        organizer = interaction.user

        # Create the initial event data structure.
        event_data = {
            'title': title,
            'description': description,
            'organizer': organizer,
            'signups': [],
            'faction': faction
        }

        # Create the initial embed and view.
        embed = create_event_embed(event_data)
        
        # Pass the global `events` dictionary to the view.
        view = EventView(organizer.id, events, faction)
        views.append(view) # save pointer

        # Defer the response first to avoid the 3-second timeout.
        await interaction.response.defer()
        
        # Now send the message as a follow-up.
        sent_message = await interaction.followup.send(embed=embed, view=view)
        
        # Store the event data using the message ID as the key.
        events[sent_message.id] = event_data


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
        if interaction.user.id != event['organizer'].id:
            await interaction.response.send_message("You are not the organizer of this event.", ephemeral=True)
            return

        # Find the user in the sign-up list.
        for signup in event['signups']:
            if signup['user'].id == user.id:
                signup['status'] = 'Accepted'
                await update_event_embed(await interaction.channel.fetch_message(message_id), event)
                await interaction.response.send_message(f"Accepted {signup['user'].display_name}'s sign-up.", ephemeral=True)
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
        if interaction.user.id != event['organizer'].id:
            await interaction.response.send_message("You are not the organizer of this event.", ephemeral=True)
            return

        # Find the user in the sign-up list.
        for signup in event['signups']:
            if signup['user'].id == user.id:
                signup['status'] = 'Rejected'
                await update_event_embed(await interaction.channel.fetch_message(message_id), event)
                await interaction.response.send_message(f"Rejected {signup['user'].display_name}'s sign-up.", ephemeral=True)
                return

        await interaction.response.send_message(f"{user.display_name} is not in the sign-up list.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(WarhammerEvents(bot))
