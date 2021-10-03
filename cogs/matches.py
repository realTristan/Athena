from discord.ext.commands import has_permissions
from discord.ext import commands
import discord, sqlite3

db = sqlite3.connect('main.db')
cur = db.cursor()

class Matches(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.command()
    async def match(self, ctx, action:str, match_id):
        if action == "report":
            pass
        if action == "cancel":
            pass
        if action == "show":
            for row in cur.execute(f'SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}'):
                embed=discord.Embed(title=f"Match #{match_id} | {row[7].upper()}", description=f"**Map:** {row[2]}", color=65535)
                embed.add_field(name="Orange Captain", value=f"<@{row[3]}>")
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="Blue Captain", value=f"<@{row[5]}>")
                embed.add_field(name="Orange Team", value='\n'.join(f"<@{e}>" for e in str(row[4]).split(",")))
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="Blue Team", value='\n'.join(f"<@{e}>" for e in str(row[6]).split(",")))
                await ctx.send(embed=embed)


    @commands.command(aliases=["lm"])
    async def lastmatch(self, ctx):
        match_count=-1
        for _ in cur.execute(f'SELECT * FROM matches WHERE guild_id = {ctx.guild.id}'):
            match_count+=1

        for row in cur.execute(f'SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_count}'):
            embed=discord.Embed(title=f"Match #{match_count}", description=f"**Map:** {row[2]}", color=65535)
            embed.add_field(name="Orange Captain", value=f"<@{row[3]}>")
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=f"<@{row[5]}>")
            embed.add_field(name="Orange Team", value='\n'.join(f"<@{e}>" for e in str(row[4]).split(",")))
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value='\n'.join(f"<@{e}>" for e in str(row[6]).split(",")))
            await ctx.send(embed=embed)





        
def setup(client):
    client.add_cog(Matches(client))