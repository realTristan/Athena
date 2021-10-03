from discord.ext.commands import has_permissions
from discord.ext import commands
import discord, sqlite3

db = sqlite3.connect('main.db')
cur = db.cursor()

class Elo(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def rename(self, ctx, name:str):
        cur.execute(f"UPDATE users SET user_name = {name} WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}")
        db.commit()
        await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} renamed to **{name}**', color=65535))

    @commands.command(aliases=["fr"])
    @has_permissions(manage_messages=True)
    async def forcerename(self, ctx, user:discord.Member, name:str):
        cur.execute(f"UPDATE users SET user_name = {name} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
        db.commit()
        await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} renamed {user.mention} to **{name}**', color=65535))

    @commands.command(aliases=["reg"])
    async def register(self, ctx, name:str):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id});").fetchall()[0] == (1,):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is already registered", color=65535))

        cur.execute(f"INSERT INTO users VALUES ({ctx.guild.id}, {ctx.author.id}, '{name}', 0, 0, 0)")
        db.commit()
        await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has registered as **{name}**", color=65535))
        await ctx.author.edit(nick=f"{name} [0]")

    @commands.command(aliases=["unreg"])
    @has_permissions(administrator=True)
    async def unregister(self, ctx, user:discord.Member):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
            cur.execute(f"DELETE FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});")
            db.commit()
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} unregistered {user.mention}", color=65535))
        await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=65535))

    @commands.command()
    @has_permissions(manage_messages=True)
    async def win(self, ctx, users:commands.Greedy[discord.Member]):
        for user in users:
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                    cur.execute(f"UPDATE users SET elo = {row[3]+5} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    cur.execute(f"UPDATE users SET wins = {row[4]+1} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    db.commit()
                    for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                        await user.edit(nick=f"{row[2]} [{row[3]}]")
                        await ctx.send(embed=discord.Embed(title="Added Win", description=f"{user.mention} [**{row[4]-1}**] ➜ {user.mention} [**{row[4]}**]", color=65535))

    @commands.command()
    @has_permissions(manage_messages=True)
    async def lose(self, ctx, users:commands.Greedy[discord.Member]):
        for user in users:
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                    cur.execute(f"UPDATE users SET elo = {row[3]-2} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    cur.execute(f"UPDATE users SET loss = {row[5]+1} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    db.commit()
                    for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                        await user.edit(nick=f"{row[2]} [{row[3]}]")
                        await ctx.send(embed=discord.Embed(title="Added Loss", description=f"{user.mention}[**{row[5]-1}**] ➜ {user.mention} [**{row[5]}**]", color=65535))

    @commands.command()
    async def stats(self, ctx, *args):
        if len(list(args)) == 0:
            user = ctx.author.id
        else:
            user = str(list(args)[0]).strip("<").strip(">").strip("@").replace("!", "")

        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user});").fetchall()[0] == (1,):
            for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user}'):
                await ctx.send(embed=discord.Embed(title=f"**{row[2]}**", description=f"**Elo:** {row[3]}\n**Wins:** {row[4]}\n**Losses:** {row[5]}", color=65535))

    @commands.command()
    @has_permissions(administrator=True)
    async def reset(self, ctx, user:discord.Member):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
            cur.execute(f"UPDATE users SET elo = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            cur.execute(f"UPDATE users SET wins = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            cur.execute(f"UPDATE users SET loss = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            db.commit()
            await ctx.send(embed=discord.Embed(title="Reset Stats", description=f"{ctx.author.mention} has reset {user.mention}'s stats", color=65535))
        


def setup(client):
    client.add_cog(Elo(client))