import os
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread

# ===================== KEEP ALIVE SERVER =====================
app = Flask('')

@app.route('/')
def home():
    return "✅ The Confession Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()


# ===================== DISCORD BOT SETUP =====================
TOKEN = os.getenv("DISCORD_TOKEN")  # Put this in Replit Secrets
GUILD_ID = 1405101978446598184  # Replace with your actual server ID

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents)
confession_channel_id = None
log_channel_id = None


# ===================== MODALS =====================
class ConfessModal(discord.ui.Modal, title="Submit a Confession"):
    confession = discord.ui.TextInput(
        label="What's your confession?",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        global confession_channel_id, log_channel_id

        if not confession_channel_id:
            await interaction.response.send_message("⚠️ Confession channel not set yet!", ephemeral=True)
            return

        confession_channel = interaction.client.get_channel(confession_channel_id)
        if not confession_channel:
            await interaction.response.send_message("⚠️ Confession channel not found!", ephemeral=True)
            return

        embed = discord.Embed(
            title="💭 Anonymous Confession",
            description=self.confession.value,
            color=discord.Color.green()
        )
        embed.set_footer(text="Reply anonymously below 👇")

        await confession_channel.send(embed=embed, view=ReplyButtonView())

        # Log for admin/mod
        if log_channel_id:
            log_channel = interaction.client.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(
                    f"🕵️ **Confession by {interaction.user} ({interaction.user.id})**:\n{self.confession.value}"
                )

        await interaction.response.send_message("✅ Confession sent anonymously!", ephemeral=True)


class ReplyModal(discord.ui.Modal, title="Reply Anonymously"):
    reply = discord.ui.TextInput(
        label="Your anonymous reply",
        style=discord.TextStyle.paragraph,
        max_length=1000,
        required=True
    )

    def __init__(self, original_message: discord.Message):
        super().__init__()
        self.original_message = original_message

    async def on_submit(self, interaction: discord.Interaction):
        global log_channel_id

        embed = discord.Embed(
            title="💭 Anonymous Reply",
            description=self.reply.value,
            color=discord.Color.blurple()
        )

        # Send publicly as anonymous reply
        await self.original_message.reply(embed=embed)

        # Log who sent the anonymous reply
        if log_channel_id:
            log_channel = interaction.client.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(
                    f"🕵️ **Anonymous reply by {interaction.user} ({interaction.user.id})** "
                    f"on message ID `{self.original_message.id}`:\n{self.reply.value}"
                )

        await interaction.response.send_message("✅ Reply sent anonymously!", ephemeral=True)


# ===================== BUTTON VIEWS =====================
class ConfessButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Submit a Confession", style=discord.ButtonStyle.green)
    async def submit_confession(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConfessModal())


class ReplyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Reply Anonymously", style=discord.ButtonStyle.blurple)
    async def reply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReplyModal(interaction.message))


# ===================== EVENTS =====================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced {len(synced)} slash commands for guild {GUILD_ID}")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")


# ===================== SLASH COMMANDS =====================
@bot.tree.command(name="setchannel", description="Set confession and log channels", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(confession="Channel where confessions go", logs="Optional log channel")
async def setchannel(interaction: discord.Interaction, confession: discord.TextChannel, logs: discord.TextChannel = None):
    global confession_channel_id, log_channel_id

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You must be an admin to use this command.", ephemeral=True)
        return

    confession_channel_id = confession.id
    log_channel_id = logs.id if logs else None

    await interaction.response.send_message(
        f"✅ Confession channel set to {confession.mention}" +
        (f" and logs to {logs.mention}" if logs else ""),
        ephemeral=True
    )


@bot.tree.command(name="confess", description="Send a confession form (via button)", guild=discord.Object(id=GUILD_ID))
async def confess_button(interaction: discord.Interaction):
    if not confession_channel_id:
        await interaction.response.send_message("⚠️ Confession channel not set yet! Use `/setchannel` first.", ephemeral=True)
        return

    embed = discord.Embed(
        title="💌 Confession Portal",
        description="Click the button below to submit your **anonymous confession.**",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, view=ConfessButtonView(), ephemeral=True)


@bot.tree.command(name="confessmsg", description="Send your confession directly (no button)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(message="Type your confession message")
async def confess_direct(interaction: discord.Interaction, message: str):
    global confession_channel_id, log_channel_id

    if not confession_channel_id:
        await interaction.response.send_message("⚠️ Confession channel not set yet! Use `/setchannel` first.", ephemeral=True)
        return

    confession_channel = interaction.client.get_channel(confession_channel_id)
    if not confession_channel:
        await interaction.response.send_message("⚠️ Confession channel not found!", ephemeral=True)
        return

    embed = discord.Embed(
        title="💭 Anonymous Confession",
        description=message,
        color=discord.Color.green()
    )
    embed.set_footer(text="Reply anonymously below 👇")
    await confession_channel.send(embed=embed, view=ReplyButtonView())

    # Log confession sender
    if log_channel_id:
        log_channel = interaction.client.get_channel(log_channel_id)
        if log_channel:
            await log_channel.send(f"🕵️ **Confession by {interaction.user} ({interaction.user.id})**:\n{message}")

    await interaction.response.send_message("✅ Your confession has been sent anonymously!", ephemeral=True)


@bot.tree.command(name="sync", description="Force sync slash commands", guild=discord.Object(id=GUILD_ID))
async def sync(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You must be an admin to use this command.", ephemeral=True)
        return

    synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    await interaction.response.send_message(f"✅ Synced {len(synced)} commands.", ephemeral=True)


# ===================== RUN =====================
keep_alive()
bot.run(TOKEN)
