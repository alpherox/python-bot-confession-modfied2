import discord
from discord import app_commands
from discord.ext import commands
import asyncio

# ==== SETTINGS ====
TOKEN = "YOUR_BOT_TOKEN"  # ⚠️ Replace this
GUILD_ID = 1405101978446598184  # optional

# ==== INTENTS ====
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

Client = commands.Bot(command_prefix=".", intents=intents)
tree = Client.tree

confessionChannel = None
logChannel = None
confession_counter = 1


# ==== VIEW (Buttons) ====
class ConfessionButtons(discord.ui.View):
    def __init__(self, confession_id, author_id):
        super().__init__(timeout=None)
        self.confession_id = confession_id
        self.author_id = author_id

    @discord.ui.button(label="💬 Reply", style=discord.ButtonStyle.gray)
    async def reply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ReplyModal(self.confession_id, self.author_id))

    @discord.ui.button(label="📝 Submit a confession!", style=discord.ButtonStyle.blurple)
    async def submit_confession(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConfessionModal())


# ==== MODALS ====
class ConfessionModal(discord.ui.Modal, title="Submit an Anonymous Confession"):
    message = discord.ui.TextInput(label="Your confession", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        global confessionChannel, logChannel, confession_counter

        if not confessionChannel or not logChannel:
            await interaction.response.send_message("⚠️ The confession or log channel isn't set yet.", ephemeral=True)
            return

        confession_id = confession_counter
        confession_counter += 1

        # Create Embed
        embed = discord.Embed(
            title=f"Anonymous Confession (#{confession_id})",
            description=f"\"{self.message.value}\"",
            color=discord.Color.random()
        )

        await confessionChannel.send(embed=embed, view=ConfessionButtons(confession_id, interaction.user.id))

        # Log actual user
        await logChannel.send(f"🕵️ Confession #{confession_id} by {interaction.user} ({interaction.user.id}):\n{self.message.value}")

        await interaction.response.send_message("✅ Your confession has been sent anonymously!", ephemeral=True)


class ReplyModal(discord.ui.Modal, title="Reply to Confession"):
    reply = discord.ui.TextInput(label="Your reply", style=discord.TextStyle.paragraph)

    def __init__(self, confession_id, author_id):
        super().__init__()
        self.confession_id = confession_id
        self.author_id = author_id

    async def on_submit(self, interaction: discord.Interaction):
        global confessionChannel, logChannel

        # Send reply anonymously
        embed = discord.Embed(
            title=f"💬 Reply to Confession (#{self.confession_id})",
            description=f"\"{self.reply.value}\"",
            color=discord.Color.dark_grey()
        )

        await confessionChannel.send(embed=embed)

        # Log who replied
        await logChannel.send(
            f"🕵️ Reply to confession #{self.confession_id} by {interaction.user} ({interaction.user.id}):\n{self.reply.value}"
        )

        await interaction.response.send_message("✅ Your anonymous reply has been sent!", ephemeral=True)


# ==== COMMANDS ====
@tree.command(name="setchannel", description="Set the confession and log channels.")
@app_commands.describe(confession="Channel for public confessions", logs="Channel for private logs")
async def setchannel(interaction: discord.Interaction, confession: discord.TextChannel, logs: discord.TextChannel):
    global confessionChannel, logChannel
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Admin only command.", ephemeral=True)
        return
    confessionChannel = confession
    logChannel = logs
    await interaction.response.send_message(
        f"✅ Confession channel: {confession.mention}\n🕵️ Log channel: {logs.mention}",
        ephemeral=True
    )


# ==== STARTUP ====
@Client.event
async def on_ready():
    await Client.change_presence(activity=discord.Game(name="Listening to confessions 👀"))
    try:
        await tree.sync(guild=discord.Object(id=GUILD_ID))
        print("✅ Slash commands synced.")
    except Exception as e:
        print(f"❌ Sync failed: {e}")
    print(f"✅ Bot online as {Client.user}")


Client.run(TOKEN)
