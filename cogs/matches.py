from discord.ext.commands import has_permissions
from discord.ext import commands
import discord, sqlite3

db = sqlite3.connect('main.db')
cur = db.cursor()

class Matches(commands.Cog):
    def __init__(self, client):
        self.client = client



def setup(client):
    client.add_cog(Matches(client))