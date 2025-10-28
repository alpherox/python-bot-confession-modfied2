import discord
from discord import app_commands
from discord.ext import commands
import asyncio

# ==== SETTINGS ====
TOKEN = "MTQyMDQyMzc3ODA2Mzg3NjE0Nw.G-oCcW.4kAQYjTWIB4kdquy22oAo4NgqU2xcpC3_uytLk"  # 🔹 Replace this with your bot token
GUILD_ID = 1405101978446598184  # Optional: put your server ID here for faster sync, or leave None

# ==== INTENTS ====
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

Client = commands.Bot(command_prefix=".", intents=intents)
tree = Client.tree  # Slash command tree

confessionChannel = None
logChannel = None


# ==== WHEN BOT STARTS ====
@Client.event
async def on_ready():
    await Client.change_presence(activity=discord.Game(name="Confession Time 👀"))
    try:
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID)) if GUILD_ID else await tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Sync failed: {e}")
    print(f"✅ Bot is online as {Client.user}")


# ==== /setchannel COMMAND ====
@tree.command(name="setchannel", description="Set the confession and log channels.")
@app_commands.describe(
    confession="Channel where confessions will be sent anonymously",
    logs="Private channel where confessions will be logged"
)
async def setchannel(interaction: discord.Interaction, confession: discord.TextChannel, logs: discord.TextChannel):
    global confessionChannel, logChannel
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ You need admin permissions to use this command.", ephemeral=True)
        return

    confessionChannel = confession
    logChannel = logs
    await interaction.response.send_message(
        f"✅ Confession channel set to {confession.mention}, logs to {logs.mention}",
        ephemeral=True
    )


# ==== /confess COMMAND ====
@tree.command(name="confess", description="Send an anonymous confession.")
@app_commands.describe(message="Type your confession message")
async def confess(interaction: discord.Interaction, message: str):
    global confessionChannel, logChannel

    if not confessionChannel or not logChannel:
        await interaction.response.send_message(
            "⚠️ The confession or log channel hasn't been set yet! Use `/setchannel` first.",
            ephemeral=True
        )
        return

    # Public anonymous confession
    await confessionChannel.send(f"💭 **Anonymous Confession:**\n{message}")

    # Private log for admins
    author_info = f"{interaction.user} ({interaction.user.id})"
    await logChannel.send(f"🕵️‍♂️ Confession by {author_info}:\n{message}")

    await interaction.response.send_message("✅ Your confession has been sent anonymously!", ephemeral=True)


Client.run(TOKEN)
