from discord.ext import commands
from _sql import *
import discord
SQL = SQL()

class Elo(commands.Cog):
    def __init__(self, client):
        self.client = client

    # // DELETE TEAM CAPTAIN VOICE CHANNELS FUNCTION
    # ///////////////////////////////////////////////
    async def _delete_channels(self, ctx, user, match_id):
        try:
            _blue_vc = discord.utils.get(ctx.guild.channels, name=f"🔹 Team {user.name}")
            if _blue_vc:
                await _blue_vc.delete()

            _orange_vc = discord.utils.get(ctx.guild.channels, name=f"🔸 Team {user.name}")
            if _orange_vc:
                await _orange_vc.delete()

            text_channel = discord.utils.get(ctx.guild.channels, name=f"match-{match_id}")
            await text_channel.delete()

            category = discord.utils.get(ctx.guild.categories, name=f"Match #{match_id}")
            await category.delete()
        except Exception as e:
            print(e)

    # // EDIT AN USERS NAME OR ROLE FUNCTION
    # ////////////////////////////////////////
    async def _user_edit(self, ctx, user, nick=None, role=None):
        try:
            if nick is not None:
                await user.edit(nick=nick)

            if role is not None:
                await ctx.author.add_roles(role)
        except Exception as e:
            print(e)

    # // GET THE USERS ID FROM A STRING
    # /////////////////////////////////////////
    async def _clean(self, user):
        return int(str(user).strip("<").strip(">").strip("@").replace("!", ""))

    # // GIVE AN USER A WIN FUNCTION
    # /////////////////////////////////////////
    async def _win(self, ctx, user):
        if SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
            settings = SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
            row = SQL.select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")

            SQL.execute(f"UPDATE users SET elo = {row[3]+settings[7]} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            SQL.execute(f"UPDATE users SET wins = {row[4]+1} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            
            return await self._user_edit(ctx, user, nick=f"{row[2]} [{row[3]+settings[7]}]")
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} was not found", color=15158588))

    # // GIVE AN USER A LOSS FUNCTION
    # /////////////////////////////////////////
    async def _loss(self, ctx, user):
        if SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
            settings = SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
            row = SQL.select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")

            SQL.execute(f"UPDATE users SET elo = {row[3]-settings[8]} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            SQL.execute(f"UPDATE users SET loss = {row[5]+1} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")

            return await self._user_edit(ctx, user, nick=f"{row[2]} [{row[3]-settings[8]}]")
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} was not found", color=15158588))


    # // LOG A MATCH TO THE DATABASE FUNCTION
    # /////////////////////////////////////////
    async def _match(self, ctx, match_id):
        row = SQL.select(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")

        embed=discord.Embed(title=f"Match #{match_id} | {row[7].upper()}", description=f"**Map:** {row[2]}", color=33023)
        embed.add_field(name="Orange Captain", value=f"<@{row[3]}>")
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Blue Captain", value=f"<@{row[5]}>")
        embed.add_field(name="Orange Team", value='\n'.join(f"<@{e}>" for e in str(row[4]).split(",")))
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Blue Team", value='\n'.join(f"<@{e}>" for e in str(row[6]).split(",")))
        return await ctx.send(embed=embed)

    # // SHOW THE USERS STATS FUNCTION
    # /////////////////////////////////////////
    async def _stats(self, ctx, user):
        if SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
            row = SQL.select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            embed = discord.Embed(description=f"**Elo:** {row[3]}\n**Wins:** {row[4]}\n**Losses:** {row[5]}", color=33023)
            embed.set_author(name=row[2], url=f'https://r6.tracker.network/profile/pc/{row[2]}', icon_url=user.avatar_url)
            return await ctx.send(embed=embed)
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} player not found", color=15158588))

    # // UNDO A WIN FOR THE BLUE TEAM
    # ////////////////////////////////////
    async def _undo_blue_win(self, ctx, blue_team, orange_team, match_id):
        settings = SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
        SQL.execute(f"UPDATE matches SET status = 'ongoing' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")

        # // REMOVE WIN FROM BLUE TEAM
        for user in blue_team:
            _row = SQL.select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
            SQL.execute(f"UPDATE users SET elo = {_row[3]-settings[7]} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
            SQL.execute(f"UPDATE users SET wins = {_row[4]-1} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
        
        # // REMOVE LOSS FROM ORANGE TEAM
        for user in orange_team:
            _row = SQL.select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
            SQL.execute(f"UPDATE users SET elo = {_row[3]+settings[8]} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
            SQL.execute(f"UPDATE users SET loss = {_row[5]-1} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")

    # // UNDO A WIN FOR THE ORANGE TEAM
    # ////////////////////////////////////
    async def _undo_orange_win(self, ctx, blue_team, orange_team, match_id):
        settings = SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
        SQL.execute(f"UPDATE matches SET status = 'ongoing' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")

        # // REMOVE LOSS FROM BLUE TEAM
        for user in blue_team:
            _row = SQL.select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
            SQL.execute(f"UPDATE users SET elo = {_row[3]+settings[8]} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
            SQL.execute(f"UPDATE users SET loss = {_row[5]-1} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
        
        # // REMOVE WIN FROM ORANGE TEAM
        for user in orange_team:
            _row = SQL.select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
            SQL.execute(f"UPDATE users SET elo = {_row[3]-settings[7]} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")
            SQL.execute(f"UPDATE users SET wins = {_row[4]-1} WHERE guild_id = {ctx.guild.id} AND user_id = {user}")


    # // MATCH REPORT/CANCEL/UNDO/SHOW COMMAND
    # /////////////////////////////////////////
    @commands.command()
    async def match(self, ctx, action:str, match_id:int, *args):
        # // REPORTING AN ONGOING MATCH
        if action == "report":
            if ctx.author.guild_permissions.manage_messages:
                row = SQL.select(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                if "reported" not in row[7] and "cancelled" not in row[7] and "rollbacked" not in row[7]:
                    SQL.execute(f"UPDATE matches SET status = 'reported' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                    SQL.execute(f"UPDATE matches SET winners = '{list(args)[0]}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")

                    orange_team = str(row[4]).split(",")
                    orange_team.append(int(row[3]))

                    blue_team = str(row[6]).split(",")
                    blue_team.append(int(row[5]))

                    if "blue" in list(args)[0]:
                        for user in orange_team:
                            await self._loss(ctx, ctx.guild.get_member(int(user)))
                            await self._delete_channels(ctx, ctx.guild.get_member(int(user)), match_id)

                        for user in blue_team:
                            await self._win(ctx, ctx.guild.get_member(int(user)))
                            await self._delete_channels(ctx, ctx.guild.get_member(int(user)), match_id)

                    if "orange" in list(args)[0]:
                        for user in orange_team:
                            await self._win(ctx, ctx.guild.get_member(int(user)))
                            await self._delete_channels(ctx, ctx.guild.get_member(int(user)), match_id)

                        for user in blue_team:
                            await self._loss(ctx, ctx.guild.get_member(int(user)))
                            await self._delete_channels(ctx, ctx.guild.get_member(int(user)), match_id)

                    return await self._match(ctx, match_id)
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

        # // CANCELLING AN ONGOING MATCH
        if action == "cancel":
            if ctx.author.guild_permissions.manage_messages:
                row = SQL.select(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                if "reported" not in row[7] and "cancelled" not in row[7] and "rollbacked" not in row[7]:
                    SQL.execute(f"UPDATE matches SET status = 'cancelled' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")

                    return await self._match(ctx, match_id)
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

        # // SHOWING A LOGGED MATCH
        if action == "show":
            return await self._match(ctx, match_id)

        # // UNDOING A REPORTED MATCH
        if action == "undo":
            if ctx.author.guild_permissions.manage_messages:
                row = SQL.select(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                if "reported" in row[7] or "cancelled" in row[7]:
                    # // ADD THE CAPTAINS TO EACH TEAM
                    blue_team = str(row[6]).split(",")
                    blue_team.append(row[5])
                    orange_team = str(row[4]).split(",")
                    orange_team.append(row[3])

                    # // REMOVE WIN FROM BLUE TEAM
                    if str(row[8]) == "blue":
                        await self._undo_blue_win(ctx, blue_team, orange_team, match_id)
                    
                    # // REMOVE LOSS FROM BLUE TEAM
                    elif str(row[8]) == "orange":
                        await self._undo_orange_win(ctx, blue_team, orange_team, match_id)

                    return await self._match(ctx, match_id)
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match hasn't been reported yet", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

    # // SET PLAYERS STATS COMMAND
    # /////////////////////////////////
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set(self, ctx, action, user:discord.Member, amount:int):
        # // SET A PLAYERS ELO
        if action in ["elo"]:
            if SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
                row = SQL.select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                SQL.execute(f"UPDATE users SET elo = {amount} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                await self._user_edit(ctx, user, nick=f"{row[2]} [{amount}]")
            
                return await self._stats(ctx, user)
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} was not found", color=15158588))

        # // SET A PLAYERS WINS
        if action in ["wins", "win"]:
            if SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
                SQL.execute(f"UPDATE users SET wins = {amount} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                return await self._stats(ctx, user)
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} was not found", color=15158588))

        # // SET A PLAYERS LOSSES
        if action in ["losses", "lose", "loss"]:
            if SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
                SQL.execute(f"UPDATE users SET loss = {amount} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                return await self._stats(ctx, user)
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} was not found", color=15158588))

    # // SHOW THE LAST MATCH PLAYED COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["lm"])
    async def lastmatch(self, ctx):
        count = SQL.select_all(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id}")
        return await self._match(ctx, len(count))

    # // REPLACE / SUB TWO PLAYERS COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["sub", "swap"])
    @commands.has_permissions(manage_messages=True)
    async def replace(self, ctx, match_id:int, user1:discord.Member, user2:discord.Member):
        row = SQL.select(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
        if "reported" not in row[7] and "cancelled" not in row[7] and "rollbacked" not in row[7]:
            blue_team = str(row[6]).split(",")
            orange_team = str(row[4]).split(",")

            # // REPLACE USER FROM ORANGE CAPTAIN
            if str(user1.id) in str(row[3]):
                SQL.execute(f"UPDATE matches SET orange_cap = '{user2.id}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")

            # // REPLACE USER FROM BLUE CAPTAIN
            elif str(user1.id) in str(row[5]):
                SQL.execute(f"UPDATE matches SET blue_cap = '{user2.id}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
            
            # // REPLACE USER FROM ORANGE TEAM
            elif str(user1.id) in orange_team:
                orange_team.remove(str(user1.id))
                orange_team.append(str(user2.id))
                SQL.execute(f"UPDATE matches SET orange_team = '{','.join(str(e) for e in orange_team)}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")

            # // REPLACE USER FROM BLUE TEAM
            elif str(user1.id) in blue_team:
                blue_team.remove(str(user1.id))
                blue_team.append(str(user2.id))
                SQL.execute(f"UPDATE matches SET blue_team = '{','.join(str(e) for e in blue_team)}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
            else:
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} player not found", color=15158588))
            return await ctx.send(embed=discord.Embed(title=f"Match #{match_id}", description=f"{ctx.author.mention} replaced {user1.mention} with {user2.mention}", color=3066992))
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=15158588))

    # SHOW THE PAST 10 MATCHES PLAYED
    # /////////////////////////////////
    @commands.command()
    async def recent(self, ctx, *args):
        row = SQL.select_all(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id}")
        amount = len(row)
        if args:
            amount = list(args)[0]
        
        embed=discord.Embed(title=f"Recent Matches ┃ {ctx.guild.name}", color=33023)
        for i in range(int(amount)):
            try:
                embed.add_field(name=f"Match #{row[-i-1][1]}", value=f"`{str(row[-i-1][7]).upper()}`")
            except Exception as e:
                print(e)
        return await ctx.send(embed=embed)
    
    # // CHANGE YOUR USERNAME COMMAND
    # /////////////////////////////////////////
    @commands.command()
    async def rename(self, ctx, name:str):
        if SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}"):
            SQL.execute(f"UPDATE users SET user_name = '{name}' WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}")
            row = SQL.select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}")
            await self._user_edit(ctx, ctx.author, nick=f"{row[2]} [{row[3]}]")

            return await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} renamed to **{name}**', color=3066992))
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is not registered", color=15158588))

    # // FORCE CHANGE A PLAYER'S USERNAME COMMAND
    # ////////////////////////////////////////////
    @commands.command(aliases=["fr"])
    @commands.has_permissions(manage_messages=True)
    async def forcerename(self, ctx, user:discord.Member, name:str):
        if SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
            SQL.execute(f"UPDATE users SET user_name = '{name}' WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            row = SQL.select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            try:
                await user.edit(nick=f"{row[2]} [{row[3]}]")
            except Exception as e:
                print(e)
            return await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} renamed {user.mention} to **{name}**', color=3066992))
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} player not found", color=15158588))
    
    # // REGISTER USER INTO THE DATABASE COMMAND
    # ///////////////////////////////////////////
    @commands.command(aliases=["reg"])
    async def register(self, ctx, name:str):
        if not SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}"):
            row = SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
            if row[6] == 0 or row[6] == ctx.message.channel.id:
                SQL.execute(f"INSERT INTO users (guild_id, user_id, user_name, elo, wins, loss) VALUES ({ctx.guild.id}, {ctx.author.id}, '{name}', 0, 0, 0)")
                
                await self._user_edit(ctx, ctx.author, nick=f"{name} [0]")
                if row[1] != 0:
                    await self._user_edit(ctx, ctx.author, role=ctx.guild.get_role(row[1]))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has registered as **{name}**", color=3066992))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} {ctx.guild.get_channel(row[6]).mention}", color=33023))
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is already registered", color=15158588))
    
    # // UNREGISTER AN USER FROM THE DATABASE COMMAND
    # ////////////////////////////////////////////////
    @commands.command(aliases=["unreg"])
    @commands.has_permissions(administrator=True)
    async def unregister(self, ctx, user:discord.Member):
        if SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
            SQL.execute(f"DELETE FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} unregistered {user.mention}", color=3066992))
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))

    # // GIVES AN USER A WIN COMMAND
    # /////////////////////////////////////////
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def win(self, ctx, users:commands.Greedy[discord.Member]):
        for user in users:
            await self._win(ctx, user)
            await self._stats(ctx, user)

    # // GIVES AN USER A LOSS COMMAND
    # /////////////////////////////////////////
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def lose(self, ctx, users:commands.Greedy[discord.Member]):
        for user in users:
            await self._loss(ctx, user)
            await self._stats(ctx, user)

    # // SHOW YOUR OR ANOTHER PLAYER'S STATS COMMAND
    # ////////////////////////////////////////////////
    @commands.command()
    async def stats(self, ctx, *args):
        user = ctx.author
        if len(list(args)) > 0 and "<@" in str(list(args)[0]):
            user = ctx.guild.get_member(await self._clean(list(args)[0]))
        return await self._stats(ctx, user)

    # // RESET AN USERS STATS COMMAND
    # /////////////////////////////////////////
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx, user:discord.Member):
        if SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
            SQL.execute(f"UPDATE users SET elo = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            SQL.execute(f"UPDATE users SET wins = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            SQL.execute(f"UPDATE users SET loss = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            return await ctx.send(embed=discord.Embed(title="Reset Stats", description=f"{ctx.author.mention} has reset {user.mention}'s stats", color=3066992))
        return await ctx.send(embed=discord.Embed(title="Reset Stats", description=f"{ctx.author.mention} player not found", color=15158588))
    
    # // SHOW YOUR GUILD'S LEADERBOARD COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx):
        users={}; names = ""
        rows = SQL.select_all(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} ORDER BY elo DESC")
        for row in rows:
            users[ctx.guild.get_member(list(row)[1])] = list(row)[3]

        for postion, user in enumerate(users):
            names += f'**{postion+1}:** {user.mention} [**{users[user]}**]\n'
            if postion+1 > 19:
                break
        await ctx.send(embed=discord.Embed(title=f"Leaderboard ┃ {ctx.guild.name}", description=names, color=33023))
        
    # // ROLLBACK EVERY MATCH AN USER WAS IN
    # //////////////////////////////////////////
    @commands.command(aliases=["rb"])
    @commands.has_permissions(manage_messages=True)
    async def rollback(self, ctx, user:str):
        '''
        REMOVE THE WIN IF CHEATER IS ON THE WINNING TEAM THEN REMOVE LOSS FOR OPPOSITE TEAM
        IF THE CHEATER IS NOT ON THE WINNING TEAM, THEN THE MATCH STILL COUNTS 
        (RAINBOW SIX SIEGE ROLLBACK SYSTEM)
        '''
        rows = SQL.select_all(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id}")
        for row in rows:
            if "ongoing" not in row[7] and "rollbacked" not in row[7]:
                blue_team = str(row[6]).split(","); blue_team.append(row[5])
                orange_team =str(row[4]).split(","); orange_team.append(row[3])

                if user in orange_team or user in blue_team:
                    if user in orange_team:
                        if row[8] == "orange":
                            await self._undo_orange_win(ctx, blue_team, orange_team, row[1])
                    
                    if user in blue_team:
                        if row[8] == "blue":
                            await self._undo_blue_win(ctx, blue_team, orange_team, row[1])
                    
                    SQL.execute(f"UPDATE matches SET status = 'rollbacked' WHERE guild_id = {ctx.guild.id} AND match_id = {row[1]}")
                    await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} Match **#{row[1]}** has been rollbacked", color=3066992))
                        

    # // BUTTON CLICK LISTENER
    # /////////////////////////////////////////
    @commands.Cog.listener()
    async def on_button_click(self, res):
        if res.component.id == 'blue_report' or res.component.id == 'orange_report' or res.component.id == 'match_cancel':
            if res.author.guild_permissions.manage_messages:
                # // GETTING THE MATCH ID
                match_id = int(str(res.message.embeds[0].title).replace("Match #", ""))

                # // CREATE TEAM LIST AND APPEND TEAM CAPTAIN
                blue_team=res.message.embeds[0].fields[5].value.split("\n")
                blue_team.append(await self._clean(res.message.embeds[0].fields[2].value))

                # // CREATE TEAM LIST AND APPEND TEAM CAPTAIN
                orange_team=res.message.embeds[0].fields[3].value.split("\n")
                orange_team.append(await self._clean(res.message.embeds[0].fields[0].value))

                if res.component.id == "match_cancel":
                    SQL.execute(f"UPDATE matches SET status = 'cancelled' WHERE guild_id = {res.guild.id} AND match_id = {match_id}")

                if res.component.id == 'blue_report':
                    SQL.execute(f"UPDATE matches SET status = 'reported' WHERE guild_id = {res.guild.id} AND match_id = {match_id}")
                    SQL.execute(f"UPDATE matches SET winners = 'blue' WHERE guild_id = {res.guild.id} AND match_id = {match_id}")

                    # // ADDING A WIN FOR EACH BLUE TEAM PLAYER
                    for user in blue_team:
                        member = res.guild.get_member(await self._clean(user))
                        await self._win(res.channel, res.guild.get_member(member))
                        await self._delete_channels(res.channel, res.guild.get_member(member), match_id)

                    # // ADDING A LOSS FOR EACH ORANGE TEAM PLAYER
                    for user in orange_team:
                        member = res.guild.get_member(await self._clean(user))
                        await self._loss(res.channel, res.guild.get_member(member), match_id)
                        await self._delete_channels(res.channel, res.guild.get_member(member), match_id)

                if res.component.id == 'orange_report':
                    SQL.execute(f"UPDATE matches SET status = 'reported' WHERE guild_id = {res.guild.id} AND match_id = {match_id}")
                    SQL.execute(f"UPDATE matches SET winners = 'orange' WHERE guild_id = {res.guild.id} AND match_id = {match_id}")

                    for user in blue_team:
                        member = res.guild.get_member(await self._clean(user))
                        await self._loss(res.channel, res.guild.get_member(member), match_id)
                        await self._delete_channels(res.channel, res.guild.get_member(member), match_id)

                    for user in orange_team:
                        member = res.guild.get_member(await self._clean(user))
                        await self._win(res.channel, res.guild.get_member(member), match_id)
                        await self._delete_channels(res.channel, res.guild.get_member(member), match_id)

                await res.message.delete()
                return await self._match(res.channel, match_id)
            return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))

def setup(client):
    client.add_cog(Elo(client))