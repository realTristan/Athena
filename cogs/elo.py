from discord.ext import commands
import discord, sqlite3

class Elo(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def _win(self, ctx, user):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                    cur.execute(f"UPDATE users SET elo = {row[3]+5} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    cur.execute(f"UPDATE users SET wins = {row[4]+1} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    db.commit()
                    try: await user.edit(nick=f"{row[2]} [{row[3]}]")
                    except Exception: pass
            
                _blue_vc = discord.utils.get(ctx.guild.channels, name=f"🔹 Team {user.name}")
                if _blue_vc:
                    await _blue_vc.delete()
                
                _orange_vc = discord.utils.get(ctx.guild.channels, name=f"🔸 Team {user.name}")
                if _orange_vc:
                    await _orange_vc.delete()
                return True
            return await ctx.send(discord.Embed(description=f"{user.mention} was not found", color=65535))

    async def _loss(self, ctx, user):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                    cur.execute(f"UPDATE users SET elo = {row[3]-2} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    cur.execute(f"UPDATE users SET loss = {row[5]+1} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    db.commit()
                    try: 
                        await user.edit(nick=f"{row[2]} [{row[3]}]")
                    except Exception: pass
                return True
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} was not found", color=65535))

    async def _match(self, ctx, match_id):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            for row in cur.execute(f'SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}'):
                embed=discord.Embed(title=f"Match #{match_id} | {row[7].upper()}", description=f"**Map:** {row[2]}", color=65535)
                embed.add_field(name="Orange Captain", value=f"<@{row[3]}>")
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="Blue Captain", value=f"<@{row[5]}>")
                embed.add_field(name="Orange Team", value='\n'.join(f"<@{e}>" for e in str(row[4]).split(",")))
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="Blue Team", value='\n'.join(f"<@{e}>" for e in str(row[6]).split(",")))
            return await ctx.send(embed=embed)

    async def _stats(self, ctx, user):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                    embed = discord.Embed(description=f"**Elo:** {row[3]}\n**Wins:** {row[4]}\n**Losses:** {row[5]}", color=65535)
                    embed.set_author(name=row[2], url=f'https://r6.tracker.network/profile/pc/{row[2]}', icon_url=user.avatar_url)
                return await ctx.send(embed=embed)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} player not found", color=65535))

    @commands.command()
    async def match(self, ctx, action:str, match_id:int, *args):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if action == "report":
                if ctx.author.guild_permissions.manage_messages:
                    for row in cur.execute(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"):
                        if "reported" not in row[7] and "cancelled" not in row[7]:
                            cur.execute(f"UPDATE matches SET status = 'reported' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                            cur.execute(f"UPDATE matches SET winners = '{list(args)[0]}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                            db.commit()

                            if "blue" in list(args)[0]:
                                for user in str(row[4]).split(","):
                                    await self._loss(ctx, ctx.guild.get_member(int(user)))
                                await self._loss(ctx, ctx.guild.get_member(int(row[3])))

                                for user in str(row[6]).split(","):
                                    await self._win(ctx, ctx.guild.get_member(int(user)))
                                await self._win(ctx, ctx.guild.get_member(int(row[5])))


                            if "orange" in list(args)[0]:
                                for user in str(row[4]).split(","):
                                    await self._win(ctx, ctx.guild.get_member(int(user)))
                                await self._win(ctx, ctx.guild.get_member(int(row[3])))

                                for user in str(row[6]).split(","):
                                    await self._loss(ctx, ctx.guild.get_member(int(user)))
                                await self._loss(ctx, ctx.guild.get_member(int(row[5])))
                            return await self._match(ctx, match_id)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=65535))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=65535))

            if action == "cancel":
                if ctx.author.guild_permissions.manage_messages:
                    for row in cur.execute(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"):
                        if "reported" not in row[7] and "cancelled" not in row[7]:
                            cur.execute(f"UPDATE matches SET status = 'cancelled' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                            db.commit()
                            return await self._match(ctx, match_id)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=65535))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=65535))

            if action == "show":
                return await self._match(ctx, match_id)

            if action == "undo":
                if ctx.author.guild_permissions.manage_messages:
                    for row in cur.execute(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"):
                        if "reported" in row[7] or "cancelled" in row[7]:
                            blue_team = str(row[6]).split(",")
                            blue_team.append(row[5])
                            orange_team = str(row[4]).split(",")
                            orange_team.append(row[3])

                            if str(row[8]) == "blue":
                                cur.execute(f"UPDATE matches SET status = 'ongoing' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                                for user in blue_team:
                                    for _row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user}'):
                                        cur.execute(f"UPDATE users SET elo = {_row[3]-5} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
                                        cur.execute(f"UPDATE users SET wins = {_row[4]-1} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
                                        db.commit()
                                
                                for user in orange_team:
                                    for _row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user}'):
                                        cur.execute(f"UPDATE users SET elo = {_row[3]+2} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
                                        cur.execute(f"UPDATE users SET loss = {_row[4]-1} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
                                        db.commit()
                            
                            elif str(row[8]) == "orange":
                                cur.execute(f"UPDATE matches SET status = 'ongoing' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                                for user in blue_team:
                                    for _row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user}'):
                                        cur.execute(f"UPDATE users SET elo = {_row[3]+3} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
                                        cur.execute(f"UPDATE users SET loss = {_row[4]-1} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
                                        db.commit()
                                
                                for user in orange_team:
                                    for _row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user}'):
                                        cur.execute(f"UPDATE users SET elo = {_row[3]-5} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
                                        cur.execute(f"UPDATE users SET wins = {_row[4]-1} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
                                        db.commit()
                            return await self._match(ctx, match_id)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match hasn't been reported yet", color=65535))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=65535))


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setelo(self, ctx, user:discord.Member, amount:int):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor() 
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                    cur.execute(f"UPDATE users SET elo = {amount} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    db.commit()
                    try: 
                        await user.edit(nick=f"{row[2]} [{row[3]}]")
                    except: pass
                return await self._stats(ctx, user)
            return await ctx.send(discord.Embed(description=f"{user.mention} was not found", color=65535))


    @commands.command(aliases=["setwin"])
    @commands.has_permissions(administrator=True)
    async def setwins(self, ctx, user:discord.Member, amount:int):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                    cur.execute(f"UPDATE users SET wins = {amount} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    db.commit()
                    try: 
                        await user.edit(nick=f"{row[2]} [{row[3]}]")
                    except: pass
                return await self._stats(ctx, user)
            return await ctx.send(discord.Embed(description=f"{user.mention} was not found", color=65535))

    @commands.command(aliases=["setlose", "setloss"])
    @commands.has_permissions(administrator=True)
    async def setlosses(self, ctx, user:discord.Member, amount:int):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                    cur.execute(f"UPDATE users SET loss = {amount} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    db.commit()
                    try: 
                        await user.edit(nick=f"{row[2]} [{row[3]}]")
                    except: pass
                return await self._stats(ctx, user)
            return await ctx.send(discord.Embed(description=f"{user.mention} was not found", color=65535))

    @commands.command(aliases=["lm"])
    async def lastmatch(self, ctx):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            match_count=-1
            for _ in cur.execute(f'SELECT * FROM matches WHERE guild_id = {ctx.guild.id}'):
                match_count+=1
            return await self._match(ctx, match_count)

    @commands.command(aliases=["sub", "swap"])
    @commands.has_permissions(manage_messages=True)
    async def replace(self, ctx, match_id:int, user1:discord.Member, user2:discord.Member):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
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
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} player not found"))
                    return await ctx.send(embed=discord.Embed(title=f"Match #{match_id}", description=f"{ctx.author.mention} replaced {user1.mention} with {user2.mention}", color=65535))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=65535))

    @commands.command()
    async def rename(self, ctx, name:str):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            cur.execute(f"UPDATE users SET user_name = '{name}' WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}")
            db.commit()
            for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}'):
                try:
                    await ctx.author.edit(nick=f"{row[2]} [{row[3]}]")
                except Exception: pass
            return await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} renamed to **{name}**', color=65535))

    @commands.command(aliases=["fr"])
    @commands.has_permissions(manage_messages=True)
    async def forcerename(self, ctx, user:discord.Member, name:str):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            cur.execute(f"UPDATE users SET user_name = '{name}' WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            db.commit()
            for row in cur.execute(f'SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                try:
                    await user.edit(nick=f"{row[2]} [{row[3]}]")
                except Exception: pass
            return await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} renamed {user.mention} to **{name}**', color=65535))
    
    @commands.command(aliases=["reg"])
    async def register(self, ctx, name:str):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id});").fetchall()[0] == (0,):
                for row in cur.execute(f'SELECT * FROM settings WHERE guild_id = {ctx.guild.id}'):
                    if row[6] == 0 or ctx.message.channel.id == row[6]:
                        cur.execute(f"INSERT INTO users VALUES ({ctx.guild.id}, {ctx.author.id}, '{name}', 0, 0, 0)")
                        db.commit()
                        try:
                            await ctx.author.add_roles(ctx.guild.get_role(row[1]))
                            await ctx.author.edit(nick=f"{name} [0]")
                        except Exception: pass
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has registered as **{name}**", color=65535))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} register in {ctx.guild.get_channel(row[6]).mention}", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is already registered", color=65535))
                
    @commands.command(aliases=["unreg"])
    @commands.has_permissions(administrator=True)
    async def unregister(self, ctx, user:discord.Member):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                cur.execute(f"DELETE FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id};")
                db.commit()
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} unregistered {user.mention}", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=65535))

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def win(self, ctx, users:commands.Greedy[discord.Member]):
        for user in users:
            await self._win(ctx, user)
            await self._stats(ctx, user)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def lose(self, ctx, users:commands.Greedy[discord.Member]):
        for user in users:
            await self._loss(ctx, user)
            await self._stats(ctx, user)

    @commands.command()
    async def stats(self, ctx, *args):
        user = ctx.author
        if "<@" in str(list(args)[0]):
            user = ctx.guild.get_member(int(str(list(args)[0]).strip("<").strip(">").strip("@").replace("!", "")))
        return await self._stats(ctx, user)
                
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx, user:discord.Member):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                cur.execute(f"UPDATE users SET elo = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                cur.execute(f"UPDATE users SET wins = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                cur.execute(f"UPDATE users SET loss = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                db.commit()
                return await ctx.send(embed=discord.Embed(title="Reset Stats", description=f"{ctx.author.mention} has reset {user.mention}'s stats", color=65535))
            return await ctx.send(embed=discord.Embed(title="Reset Stats", description=f"{ctx.author.mention} player not found", color=65535))
        
    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
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