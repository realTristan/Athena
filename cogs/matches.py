from discord.ext.commands import has_permissions
from discord.ext import commands
import discord, sqlite3

db = sqlite3.connect('main.db')
cur = db.cursor()

class Matches(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.command()
    async def match(self, ctx, action:str, match_id:int):
        if action == "report":
            for row in cur.execute(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"):
                cur.execute(f"UPDATE matches SET status = 'reported' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                db.commit()

        if action == "cancel":
            for row in cur.execute(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"):
                cur.execute(f"UPDATE matches SET status = 'cancelled' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                db.commit()
            
                embed=discord.Embed(title=f"Match #{match_id} | CANCELLED", description=f"**Map:** {row[2]}", color=65535)
                embed.add_field(name="Orange Captain", value=f"<@{row[3]}>")
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="Blue Captain", value=f"<@{row[5]}>")
                embed.add_field(name="Orange Team", value='\n'.join(f"<@{e}>" for e in str(row[4]).split(",")))
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="Blue Team", value='\n'.join(f"<@{e}>" for e in str(row[6]).split(",")))
                await ctx.send(embed=embed)

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



    @commands.command(aliases=["sub"])
    async def replace(self, ctx, match_id:int, user1:discord.Member, user2:discord.Member):
        pass

         





def setup(client):
    client.add_cog(Matches(client))