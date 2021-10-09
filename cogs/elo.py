from discord.ext.commands import has_permissions
from discord.ext import commands
import discord, sqlite3

db = sqlite3.connect('main.db')
cur = db.cursor()

class Elo(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def add_win(self, guild, user):
        _user = guild.get_member(int(user))
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {guild.id} AND user_id = {user});").fetchall()[0] == (1,):
            for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {guild.id} AND user_id = {user}'):
                cur.execute(f"UPDATE users SET elo = {row[3]+5} WHERE guild_id = {guild.id} AND user_id = {user}")
                cur.execute(f"UPDATE users SET wins = {row[4]+1} WHERE guild_id = {guild.id} AND user_id = {user}")
                db.commit()
                for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {guild.id} AND user_id = {user}'):
                    try: await _user.edit(nick=f"{row[2]} [{row[3]}]")
                    except: pass
                    return discord.Embed(title="Added Win", description=f"{_user.mention} [**{row[4]-1}**] ➜ {_user.mention} [**{row[4]}**]", color=65535)
        return discord.Embed(description=f"{_user.mention} was not found", color=65535)

    async def add_loss(self, guild, user):
        _user = guild.get_member(int(user))
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {guild.id} AND user_id = {user});").fetchall()[0] == (1,):
            for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {guild.id} AND user_id = {user}'):
                cur.execute(f"UPDATE users SET elo = {row[3]-2} WHERE guild_id = {guild.id} AND user_id = {user}")
                cur.execute(f"UPDATE users SET loss = {row[5]+1} WHERE guild_id = {guild.id} AND user_id = {user}")
                db.commit()

            for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {guild.id} AND user_id = {user}'):
                try: 
                    await _user.edit(nick=f"{row[2]} [{row[3]}]")
                except Exception: 
                    pass
                return discord.Embed(title="Added Loss", description=f"{_user.mention} [**{row[5]-1}**] ➜ {_user.mention} [**{row[5]}**]", color=65535)
        return discord.Embed(description=f"{_user.mention} was not found", color=65535)

    async def display_match(self, match_id, guild):
        for row in cur.execute(f'SELECT * FROM matches WHERE guild_id = {guild.id} AND match_id = {match_id}'):
            embed=discord.Embed(title=f"Match #{match_id} | {row[7].upper()}", description=f"**Map:** {row[2]}", color=65535)
            embed.add_field(name="Orange Captain", value=f"<@{row[3]}>")
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=f"<@{row[5]}>")
            embed.add_field(name="Orange Team", value='\n'.join(f"<@{e}>" for e in str(row[4]).split(",")))
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value='\n'.join(f"<@{e}>" for e in str(row[6]).split(",")))
            return embed

    @commands.command()
    async def match(self, ctx, action:str, match_id:int, *args):
        if action == "report":
            if ctx.author.guild_permissions.manage_messages:
                for row in cur.execute(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"):
                    if "reported" not in row[7] and "cancelled" not in row[7]:
                        cur.execute(f"UPDATE matches SET status = 'reported' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                        db.commit()

                        if "blue" in list(args)[0]:
                            for user in str(row[4]).split(","):
                                await ctx.send(await self.add_loss(ctx.guild, user))
                            await ctx.send(await self.add_loss(ctx.guild, int(row[3])))

                            for user in str(row[6]).split(","):
                                await ctx.send(await self.add_win(ctx.guild, user))
                            await ctx.send(await self.add_win(ctx.guild, int(row[5])))


                        if "orange" in list(args)[0]:
                            for user in str(row[4]).split(","):
                                await ctx.send(await self.add_win(ctx.guild, user))
                            await ctx.send(await self.add_win(ctx.guild, int(row[3])))

                            for user in str(row[6]).split(","):
                                await ctx.send(await self.add_loss(ctx.guild, user))
                            await ctx.send(await self.add_loss(ctx.guild, int(row[5])))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=65535))

        if action == "cancel":
            if ctx.author.guild_permissions.manage_messages:
                for row in cur.execute(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"):
                    if "reported" not in row[7] and "cancelled" not in row[7]:
                        cur.execute(f"UPDATE matches SET status = 'cancelled' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                        db.commit()
                        return await ctx.send(embed=await self.display_match(match_id, ctx.guild))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=65535))

        if action == "show":
            return await ctx.send(embed=await self.display_match(match_id, ctx.guild))


    @commands.command(aliases=["lm"])
    async def lastmatch(self, ctx):
        match_count=-1
        for _ in cur.execute(f'SELECT * FROM matches WHERE guild_id = {ctx.guild.id}'):
            match_count+=1
        return await ctx.send(embed=await self.display_match(match_count, ctx.guild))

    @commands.command(aliases=["sub", "swap"])
    @has_permissions(manage_messages=True)
    async def replace(self, ctx, match_id:int, user1:discord.Member, user2:discord.Member):
        for row in cur.execute(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"):
            if "reported" not in row[7] and "cancelled" not in row[7]:
                blue_team = str(row[6]).split(",")
                orange_team = str(row[4]).split(",")

                if str(user1.id) in str(row[3]):
                    cur.execute(f"UPDATE matches SET orange_cap = '{user2.id}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                    db.commit()

                elif str(user1.id) in str(row[5]):
                    cur.execute(f"UPDATE matches SET blue_cap = '{user2.id}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                    db.commit()
                
                elif str(user1.id) in orange_team:
                    orange_team.remove(str(user1.id))
                    orange_team.append(str(user1.id))
                    cur.execute(f"UPDATE matches SET orange_team = '{','.join(str(e) for e in orange_team)}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                    db.commit()

                elif str(user1.id) in blue_team:
                    blue_team.remove(str(user1.id))
                    blue_team.append(str(user2.id))
                    cur.execute(f"UPDATE matches SET blue_team = '{','.join(str(e) for e in blue_team)}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                    db.commit()
                else:
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} player not found")); return
                return await ctx.send(embed=discord.Embed(title=f"Match #{match_id}", description=f"{ctx.author.mention} replaced {user1.mention} with {user2.mention}", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=65535))

    @commands.command()
    async def rename(self, ctx, name:str):
        cur.execute(f"UPDATE users SET user_name = '{name}' WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}")
        db.commit()
        for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}'):
            await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} renamed to **{name}**', color=65535))
            try: 
                await ctx.author.edit(nick=f"{row[2]} [{row[3]}]")
            except Exception: pass

    @commands.command(aliases=["fr"])
    @has_permissions(manage_messages=True)
    async def forcerename(self, ctx, user:discord.Member, name:str):
        cur.execute(f"UPDATE users SET user_name = '{name}' WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
        db.commit()
        for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}'):
            await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} renamed {user.mention} to **{name}**', color=65535))
            try:
                return await ctx.author.edit(nick=f"{row[2]} [{row[3]}]")
            except Exception: pass
        

    @commands.command(aliases=["reg"])
    async def register(self, ctx, name:str):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id});").fetchall()[0] == (1,):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is already registered", color=65535))
            
        cur.execute(f"INSERT INTO users VALUES ({ctx.guild.id}, {ctx.author.id}, '{name}', 0, 0, 0)")
        db.commit()
        for row in cur.execute(f'SELECT * FROM settings WHERE guild_id = {ctx.guild.id}'):
            await ctx.author.add_roles(ctx.guild.get_role(row[1]))
        await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has registered as **{name}**", color=65535))
        try:
            return await ctx.author.edit(nick=f"{name} [0]")
        except Exception: pass

    @commands.command(aliases=["unreg"])
    @has_permissions(administrator=True)
    async def unregister(self, ctx, user:discord.Member):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
            cur.execute(f"DELETE FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id};")
            db.commit()
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} unregistered {user.mention}", color=65535))
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=65535))

    @commands.command()
    @has_permissions(manage_messages=True)
    async def win(self, ctx, users:commands.Greedy[discord.Member]):
        for user in users:
            await ctx.send(embed=await self.add_win(ctx.guild, user.id))

    @commands.command()
    @has_permissions(manage_messages=True)
    async def lose(self, ctx, users:commands.Greedy[discord.Member]):
        for user in users:
            await ctx.send(embed=await self.add_loss(ctx.guild, user.id))

    @commands.command()
    async def stats(self, ctx, *args):
        if len(list(args)) == 0:
            user = ctx.author.id
        else:
            user = str(list(args)[0]).strip("<").strip(">").strip("@").replace("!", "")

        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user});").fetchall()[0] == (1,):
            for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user}'):
                embed = discord.Embed(description=f"**Elo:** {row[3]}\n**Wins:** {row[4]}\n**Losses:** {row[5]}", color=65535)
                embed.set_author(name=row[2], url=f'https://r6.tracker.network/profile/pc/{row[2]}', icon_url=ctx.guild.get_member(int(row[1])).avatar_url)
                return await ctx.send(embed=embed)
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} player not found", color=65535))
                
    @commands.command()
    @has_permissions(administrator=True)
    async def reset(self, ctx, user:discord.Member):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
            cur.execute(f"UPDATE users SET elo = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            cur.execute(f"UPDATE users SET wins = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            cur.execute(f"UPDATE users SET loss = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            db.commit()
            return await ctx.send(embed=discord.Embed(title="Reset Stats", description=f"{ctx.author.mention} has reset {user.mention}'s stats", color=65535))
        return await ctx.send(embed=discord.Embed(title="Reset Stats", description=f"{ctx.author.mention} player not found", color=65535))
        
    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx):
        users={}; names = ""
        for row in cur.execute(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} ORDER BY elo DESC;"):
            users[ctx.guild.get_member(row[1])] = row[3]

        for postion, user in enumerate(users):
            names += f'**{postion+1}:** {user.mention} [**{users[user]}**]\n'
            if postion+1 > 19:
                break
        await ctx.send(embed=discord.Embed(title=f"Leaderboard", description=names, color=65535))



def setup(client):
    client.add_cog(Elo(client))