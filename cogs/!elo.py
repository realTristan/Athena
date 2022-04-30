from discord.ext import commands
from functools import *
from _sql import *
import discord

class Elo(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    # // Check mod role or mod permissions
    # //////////////////////////////////////////
    async def check_mod_role(self, ctx:commands.Context):
        if await self.check_admin_role(ctx):
            return True
        mod_role = (await SQL_CLASS().select(f"SELECT mod_role FROM settings WHERE guild_id = {ctx.guild.id}"))[0]
        if mod_role == 0:
            return ctx.author.guild_permissions.manage_messages
        return ctx.guild.get_role(mod_role) in ctx.author.roles
    
    # // Check admin role or admin permissions
    # //////////////////////////////////////////
    async def check_admin_role(self, ctx):
        admin_role = (await SQL_CLASS().select(f"SELECT admin_role FROM settings WHERE guild_id = {ctx.guild.id}"))[0]
        if admin_role == 0 or ctx.author.guild_permissions.administrator:
            return ctx.author.guild_permissions.administrator
        return ctx.guild.get_role(admin_role) in ctx.author.roles
    
    # // DELETE TEAM CAPTAIN VOICE CHANNELS FUNCTION
    # ///////////////////////////////////////////////
    async def _delete_channels(self, ctx:commands.Context, match_id:int):
        _category = discord.utils.get(ctx.guild.categories, name=f"Match #{match_id}")
        if _category:
            for channel in _category.channels:
                await channel.delete()
            return await _category.delete()

    # RESET AN USERS STATS
    # ///////////////////////////////////////
    async def _reset_stats(self, ctx:commands.Context, user:discord.Member):
        await SQL_CLASS().execute(f"UPDATE users SET elo = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
        await SQL_CLASS().execute(f"UPDATE users SET wins = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
        await SQL_CLASS().execute(f"UPDATE users SET loss = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")

    # // REGISTER USER INTO THE DATABASE FUNCTION
    # ///////////////////////////////////////////////
    async def _register_user(self, ctx:commands.Context, user:discord.Member, name:str, role:discord.Role):
        await SQL_CLASS().execute(f"INSERT INTO users (guild_id, user_id, user_name, elo, wins, loss) VALUES ({ctx.guild.id}, {user.id}, '{name}', 0, 0, 0)")
        if role is not None and role not in user.roles:
            await self._user_edit(user, role=role)

    # // EDIT AN USERS NAME OR ROLE FUNCTION
    # ////////////////////////////////////////
    async def _user_edit(self, user:discord.Member, nick:str=None, role:discord.Role=None, remove_role:discord.Role=None):
        if nick is not None:
            try: await user.edit(nick=nick)
            except Exception as e: print(f"Elo 56: {e}")

        if role is not None:
            try: await user.add_roles(role)
            except Exception as e: print(f"Elo 60: {e}")
            
        if remove_role is not None:
            try: await user.remove_roles(remove_role)
            except Exception as e: print(f"Elo 64: {e}")

    # // CLEAN USER/ROLE
    # ////////////////////////
    def _clean_user(self, user:str):
        return int(str(user).strip("<").strip(">").strip("@").replace("!", ""))
    
    def _clean_role(self, role:str):
        return role.strip("<").strip(">").replace("@&", "").replace("!", "")
    
    # // EDIT AN USERS ELO ROLE
    # /////////////////////////////////////////
    async def edit_elo_role(self, ctx:commands.Context, user:discord.Member, elo_amount:int, option:str):
        roles = await SQL_CLASS().select_all(f"SELECT role_id FROM elo_roles WHERE elo_level <= {elo_amount} AND guild_id = {ctx.guild.id}")
        if option == "remove":
            roles = await SQL_CLASS().select_all(f"SELECT role_id FROM elo_roles WHERE elo_level > {elo_amount} AND guild_id = {ctx.guild.id}")
        
        # // Check roles and add them
        if len(roles) > 0:
            for _role in roles:
                role = ctx.guild.get_role(_role[0])
                if option == "remove":
                    if role in user.roles:
                        await self._user_edit(user, remove_role=role)
                else:
                    if role not in user.roles:
                        await self._user_edit(user, role=role)

    # // GIVE AN USER A WIN FUNCTION
    # /////////////////////////////////////////
    async def _win(self, ctx:commands.Context, user:discord.Member, lobby_settings:list):
        row = await SQL_CLASS().select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
        if row is not None:
            await SQL_CLASS().execute(f"UPDATE users SET elo = {row[3]+lobby_settings[4]} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            await SQL_CLASS().execute(f"UPDATE users SET wins = {row[4]+1} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            await self.edit_elo_role(ctx, user, row[3]+lobby_settings[4], "add")
            
            return await self._user_edit(user, nick=f"{row[2]} [{row[3]+lobby_settings[4]}]")
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))

    # // GIVE AN USER A LOSS FUNCTION
    # /////////////////////////////////////////
    async def _loss(self, ctx:commands.Context, user:discord.Member, lobby_settings:list):
        row = await SQL_CLASS().select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
        if row is not None:
            if lobby_settings[7] == 0 and (row[3]-lobby_settings[5]) < 0:
                await SQL_CLASS().execute(f"UPDATE users SET elo = {0} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                await self._user_edit(user, nick=f"{row[2]} [0]")
            else:
                await SQL_CLASS().execute(f"UPDATE users SET elo = {row[3]-lobby_settings[5]} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                await self._user_edit(user, nick=f"{row[2]} [{row[3]-lobby_settings[5]}]")
            await self.edit_elo_role(ctx, user, row[3]-lobby_settings[5], "remove")
            return await SQL_CLASS().execute(f"UPDATE users SET loss = {row[5]+1} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))


    # // LOG A MATCH TO THE DATABASE FUNCTION
    # /////////////////////////////////////////
    async def _match_show(self, ctx:commands.Context, match_id:int):
        row = await SQL_CLASS().select(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
        if row is not None:
            embed=discord.Embed(title=f"Match #{match_id} ┃ {row[8].upper()}", description=f"**Map:** {row[3]}\n**Winners:** {row[9][0].upper()+row[9][1:]}", color=33023)
            embed.add_field(name="Orange Captain", value=f"<@{row[4]}>")
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=f"<@{row[6]}>")
            embed.add_field(name="Orange Team", value='\n'.join(f"<@{e}>" for e in row[5].split(",")))
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value='\n'.join(f"<@{e}>" for e in row[7].split(",")))
            return await ctx.send(embed=embed)
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} we were unable to find **Match #{match_id}**", color=15158588))

    # // SHOW THE USERS STATS FUNCTION
    # /////////////////////////////////////////
    async def _stats(self, ctx:commands.Context, user:discord.Member):
        row = await SQL_CLASS().select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
        if row is not None:
            embed = discord.Embed(description=f"**Elo:** {row[3]}\n**Wins:** {row[4]}\n**Losses:** {row[5]}\n**Matches:** {row[5]+row[4]}", color=33023)
            embed.set_author(name=row[2], icon_url=user.avatar_url)
            return await ctx.send(embed=embed)
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))

    # // UNDO A WIN FOR THE ORANGE TEAM
    # ////////////////////////////////////
    async def _undo_win(self, ctx:commands.Context, lobby_id:int, winners:list, losers:list):
        lobby_settings = await SQL_CLASS().select(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {lobby_id}")

        # // REMOVE LOSS FROM LOSERS
        for _user_id in losers:
            _row = await SQL_CLASS().select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {_user_id}")
            await SQL_CLASS().execute(f"UPDATE users SET elo = {_row[3]+lobby_settings[5]} WHERE guild_id = {ctx.guild.id} AND user_id = {_user_id}")
            await SQL_CLASS().execute(f"UPDATE users SET loss = {_row[5]-1} WHERE guild_id = {ctx.guild.id} AND user_id = {_user_id}")
            
            member = ctx.guild.get_member(int(_user_id))
            if member is not None:
                await self.edit_elo_role(ctx, member, _row[3]+lobby_settings[5], "add")
        
        # // REMOVE WIN FROM WINNERS
        for user_id in winners:
            _row = await SQL_CLASS().select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user_id}")
            if lobby_settings[7] == 0 and (_row[3]-lobby_settings[4]) < 0:
                await SQL_CLASS().execute(f"UPDATE users SET elo = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user_id}")
            else:
                await SQL_CLASS().execute(f"UPDATE users SET elo = {_row[3]-lobby_settings[4]} WHERE guild_id = {ctx.guild.id} AND user_id = {user_id}")
            await SQL_CLASS().execute(f"UPDATE users SET wins = {_row[4]-1} WHERE guild_id = {ctx.guild.id} AND user_id = {user_id}")
            
            member = ctx.guild.get_member(int(user_id))
            if member is not None:
                await self.edit_elo_role(ctx, member, _row[3]-lobby_settings[4], "remove")
            
    
    # // ADD / REMOVE A NEW ELO ROLE
    # /////////////////////////////////
    @commands.command(name="elorole", description='`=elorole add (@role) [elo]`**,** `=elorole del (@role)`**,** `=elorole list`')
    async def elorole(self, ctx:commands.Context, option:str, *args):
        if option in ["add", "create", "new", "remove", "delete", "del"]:
            role_id = self._clean_role(list(args)[0])
            role = ctx.guild.get_role(int(role_id))
            
        if option in ["add", "create", "new"]:
            if await self.check_admin_role(ctx):
                elo_roles = await SQL_CLASS().select_all(f"SELECT * FROM elo_roles WHERE guild_id = {ctx.guild.id}")
                if len(elo_roles) < 20:
                    elo_amount = int(list(args)[1])
                    if not await SQL_CLASS().exists(f"SELECT * FROM elo_roles WHERE guild_id = {ctx.guild.id} AND role_id = {role.id}"):
                        await SQL_CLASS().execute(f"INSERT INTO elo_roles (guild_id, role_id, elo_level, win_elo, lose_elo) VALUES ({ctx.guild.id}, {role.id}, {elo_amount}, 5, 2)")
                        return await ctx.send(embed=discord.Embed(description=f"**[{len(elo_roles)+1}/20]** {ctx.author.mention} {role.mention} will now be given at **{elo_amount} elo**", color=3066992))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} {role.mention} already exists", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"**[20/20]** {ctx.author.mention} maximum amount of roles reached", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
        if option in ["remove", "delete", "del"]:
            if await self.check_admin_role(ctx):
                if await SQL_CLASS().exists(f"SELECT * FROM elo_roles WHERE guild_id = {ctx.guild.id} AND role_id = {role.id}"):
                    elo_roles = await SQL_CLASS().select_all(f"SELECT * FROM elo_roles WHERE guild_id = {ctx.guild.id}")
                    
                    await SQL_CLASS().execute(f"DELETE FROM elo_roles WHERE guild_id = {ctx.guild.id} AND role_id = {role.id}")
                    return await ctx.send(embed=discord.Embed(description=f"**[{len(elo_roles)-1}/20]** {ctx.author.mention} {role.mention} has been removed", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} {role.mention} is not an elo role", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
        if option in ["list", "show"]:
            description = ""
            rows = await SQL_CLASS().select_all(f"SELECT * FROM elo_roles WHERE guild_id = {ctx.guild.id} ORDER BY elo_level ASC")
            for i in range(len(rows)):
                role = ctx.guild.get_role(rows[i][1])
                try: description += f'**{i+1}:** {role.mention} [**{rows[i][2]}**]\n'
                except Exception as e: print(f"Elo 210: {e}")
            return await ctx.send(embed=discord.Embed(title=f"Elo Roles ┃ {ctx.guild.name}", description=description, color=33023))
        
    # // MATCH REPORT/CANCEL/UNDO/SHOW COMMAND
    # /////////////////////////////////////////
    @commands.command(name="match", description='`=match report (match id) [blue/orange]`**,** `=match cancel (match id)`**,** `=match undo (match id)`**,** `=match show (match id)`')
    async def match(self, ctx:commands.Context, action:str, match_id:int, *args):
        if not ctx.author.bot:
            # // REPORTING AN ONGOING MATCH
            if action in ["report"]:
                if await self.check_mod_role(ctx):
                    match = await SQL_CLASS().select(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                    if match is not None:
                        lobby_settings = await SQL_CLASS().select(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {match[2]}")

                        if len(args) > 0 and match[8] in ["ongoing"]:
                            await SQL_CLASS().execute(f"UPDATE matches SET status = 'reported' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                            await SQL_CLASS().execute(f"UPDATE matches SET winners = '{list(args)[0]}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")

                            orange_team = match[5].split(",")
                            orange_team.append(int(match[4]))

                            blue_team = match[7].split(",")
                            blue_team.append(int(match[6]))

                            if "blue" in list(args)[0]:
                                for _user in orange_team:
                                    member = ctx.guild.get_member(int(_user))
                                    if member is not None:
                                        await self._loss(ctx, member, lobby_settings)

                                for user in blue_team:
                                    member = ctx.guild.get_member(int(user))
                                    if member is not None:
                                        await self._win(ctx, member, lobby_settings)
                                    
                            if "orange" in list(args)[0]:
                                for _user in orange_team:
                                    member = ctx.guild.get_member(int(_user))
                                    if member is not None:
                                        await self._win(ctx, member, lobby_settings)

                                for user in blue_team:
                                    member = ctx.guild.get_member(int(user))
                                    if member is not None:
                                        await self._loss(ctx, member, lobby_settings)
                            await self._match_show(ctx, match_id)
                            return await self._delete_channels(ctx, match_id)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} invalid match id", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

            # // CANCELLING AN ONGOING MATCH
            elif action in ["cancel"]:
                if await self.check_mod_role(ctx):
                    status = (await SQL_CLASS().select(f"SELECT status FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"))[0]
                    if status is not None:
                        if status in ["ongoing"]:
                            await SQL_CLASS().execute(f"UPDATE matches SET status = 'cancelled' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                            await SQL_CLASS().execute(f"UPDATE matches SET winners = 'none' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                            await self._match_show(ctx, match_id)

                            return await self._delete_channels(ctx, match_id)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} invalid match id", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

            # // SHOWING A LOGGED MATCH
            elif action in ["show"]:
                return await self._match_show(ctx, match_id)

            # // UNDOING A REPORTED MATCH
            elif action in ["undo"]:
                if await self.check_mod_role(ctx):
                    match = await SQL_CLASS().select(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                    if match is not None:
                        if match[8] in ["reported", "cancelled"]:
                            # // UPDATING THE DATABASE
                            await SQL_CLASS().execute(f"UPDATE matches SET status = 'ongoing' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                            await SQL_CLASS().execute(f"UPDATE matches SET winners = 'none' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")

                            # // ADD THE CAPTAINS TO EACH TEAM
                            blue_team = match[7].split(",")
                            blue_team.append(match[6])
                            orange_team = match[5].split(",")
                            orange_team.append(match[4])

                            # // REMOVE WIN FROM BLUE TEAM
                            if match[9] == "blue":
                                await self._undo_win(ctx, match[2], blue_team, orange_team)
                            
                            # // REMOVE LOSS FROM BLUE TEAM
                            if match[9] == "orange":
                                await self._undo_win(ctx, match[2], orange_team, blue_team)

                            return await self._match_show(ctx, match_id)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match hasn't been reported yet", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} invalid match id", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
            raise Exception("Invalid option")

    # // SET PLAYERS STATS COMMAND
    # /////////////////////////////////
    @commands.command(name="set", description='`=set elo (@user) (amount)`**,** `=set wins (@user) (amount)`**,** `=set losses (@user) (amount)`')
    async def set(self, ctx:commands.Context, action:str, user:discord.Member, amount:int):
        if not ctx.author.bot:
            if await self.check_admin_role(ctx):
                user_name = (await SQL_CLASS().select(f"SELECT user_name FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"))[0]
                if user_name is not None:
                    # // SET A PLAYERS ELO
                    if action in ["elo", "points"]:
                        await SQL_CLASS().execute(f"UPDATE users SET elo = {amount} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                        await self._user_edit(user, nick=f"{user_name} [{amount}]")
                        
                    # // SET A PLAYERS WINS
                    elif action in ["wins", "win"]:
                        await SQL_CLASS().execute(f"UPDATE users SET wins = {amount} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")

                    # // SET A PLAYERS LOSSES
                    elif action in ["losses", "lose", "loss"]:
                        await SQL_CLASS().execute(f"UPDATE users SET loss = {amount} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    else:
                        raise Exception("Invalid option")
                    return await self._stats(ctx, user)
                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

    # // SHOW THE LAST MATCH PLAYED COMMAND
    # /////////////////////////////////////////
    @commands.command(name="lastmatch", aliases=["lm"], description='`=lastmatch`')
    async def lastmatch(self, ctx:commands.Context):
        if not ctx.author.bot:
            count = await SQL_CLASS().select_all(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id}")
            return await self._match_show(ctx, len(count))

    # // REPLACE / SUB TWO PLAYERS COMMAND
    # /////////////////////////////////////////
    @commands.command(name="replace", aliases=["sub", "swap"], description='`=replace (@user to be replaced) (@user replacing) (match id)`')
    async def replace(self, ctx:commands.Context, user1:discord.Member, user2:discord.Member, match_id:int):
        if not ctx.author.bot:
            if await self.check_mod_role(ctx):
                row = await SQL_CLASS().select(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                if "reported" not in row[8] and "cancelled" not in row[8] and "rollbacked" not in row[8]:
                    blue_team = str(row[7]).split(",")
                    orange_team = str(row[5]).split(",")

                    # // REPLACE USER FROM ORANGE CAPTAIN
                    if str(user1.id) in str(row[4]) and str(user2.id) not in str(row[4]):
                        await SQL_CLASS().execute(f"UPDATE matches SET orange_cap = '{user2.id}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")

                    # // REPLACE USER FROM BLUE CAPTAIN
                    elif str(user1.id) in str(row[6]) and str(user2.id) not in str(row[6]):
                        await SQL_CLASS().execute(f"UPDATE matches SET blue_cap = '{user2.id}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                    
                    # // REPLACE USER FROM ORANGE TEAM
                    elif str(user1.id) in orange_team and str(user2.id) not in orange_team:
                        orange_team[orange_team.index(str(user1.id))] = str(user2.id)
                        await SQL_CLASS().execute(f"UPDATE matches SET orange_team = '{','.join(str(e) for e in orange_team)}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")

                    # // REPLACE USER FROM BLUE TEAM
                    elif str(user1.id) in blue_team and str(user2.id) not in blue_team:
                        blue_team[blue_team.index(str(user1.id))] = str(user2.id)
                        await SQL_CLASS().execute(f"UPDATE matches SET blue_team = '{','.join(str(e) for e in blue_team)}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}")
                    else:
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} player(s) not found/error", color=15158588))
                    return await ctx.send(embed=discord.Embed(title=f"Match #{match_id}", description=f"{ctx.author.mention} replaced {user1.mention} with {user2.mention}", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

    # SHOW THE PAST 10 MATCHES PLAYED
    # /////////////////////////////////
    @commands.command(name="recent", description='`=recent`**,** `=recent (amount)`')
    async def recent(self, ctx:commands.Context, *args):
        if not ctx.author.bot:
            row = await SQL_CLASS().select_all(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id}")
            amount = len(row)
            if len(args) > 0:
                amount = int(list(args)[0])
            
            embed=discord.Embed(title=f"Recent Matches ┃ {ctx.guild.name}", color=33023)
            for i in range(amount):
                embed.add_field(name=f"Match #{row[-i-1][1]}", value=f"`{row[-i-1][8].upper()}`")
            return await ctx.send(embed=embed)
    
    # // CHANGE YOUR USERNAME COMMAND
    # /////////////////////////////////////////
    @commands.command(name="rename", description='`=rename (name)`')
    @commands.has_permissions(change_nickname=True)
    async def rename(self, ctx:commands.Context, name:str):
        if not ctx.author.bot:
            row = await SQL_CLASS().select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}")
            if row is not None:
                await SQL_CLASS().execute(f"UPDATE users SET user_name = '{name}' WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}")
                await self._user_edit(ctx.author, nick=f"{name} [{row[3]}]")

                return await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} renamed to **{name}**', color=3066992))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is not registered", color=15158588))

    # // FORCE CHANGE A PLAYER'S USERNAME COMMAND
    # ////////////////////////////////////////////
    @commands.command(name="forcerename", aliases=["fr"], description='`=forcerename (@user) (name)`')
    async def forcerename(self, ctx:commands.Context, user:discord.Member, name:str):
        if not ctx.author.bot:
            if await self.check_mod_role(ctx):
                row = await SQL_CLASS().select(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                if row is not None:
                    await SQL_CLASS().execute(f"UPDATE users SET user_name = '{name}' WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    await self._user_edit(user, nick=f"{name} [{row[3]}]")

                    return await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} renamed {user.mention} to **{name}**', color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

    # // REGISTER USER INTO THE DATABASE COMMAND
    # ///////////////////////////////////////////
    @commands.command(name="register", aliases=["reg"], description='`=register (name)`')
    async def register(self, ctx:commands.Context, *args):
        if not ctx.author.bot:
            settings = await SQL_CLASS().select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
            if settings is None:
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} please reinvite the bot to the server", color=15158588))

            # // GETTING THE REGISTER ROLE FROM SETTINGS
            if settings[3] in [0, ctx.channel.id]:
                role = None
                if settings[1] != 0:
                    role = ctx.guild.get_role(settings[1])
            
                # // REGISTER THE MENTIONED USER
                if len(args) > 0 and "@" in list(args)[0]:
                    if await self.check_mod_role(ctx):
                        user = ctx.guild.get_member(self._clean_user(list(args)[0]))
                        if user is not None:
                            if not user.bot:
                                if not await SQL_CLASS().exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
                                    name = user.name
                                    if len(args) > 1:
                                        name = list(args)[1]
                                    await self._register_user(ctx, user, name, role)
                                    await self._user_edit(user, nick=f"{name} [0]")
                                    return await ctx.send(embed=discord.Embed(description=f"{user.mention} has been registered as **{name}**", color=3066992))
                                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is already registered", color=15158588))
                            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you cannot register a bot", color=15158588))
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} unknown player", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

                # // REGISTER THE MESSAGE AUTHOR
                else:
                    name = ctx.author.name
                    if len(args) > 0:
                        name = list(args)[0]
                    if not await SQL_CLASS().exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}"):
                        await self._register_user(ctx, ctx.author, name, role)
                        await self._user_edit(ctx.author, nick=f"{name} [0]")
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has been registered as **{name}**", color=3066992))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is already registered", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} {ctx.guild.get_channel(settings[3]).mention}", color=33023))
        
    # // UNREGISTER AN USER FROM THE DATABASE COMMAND
    # ////////////////////////////////////////////////
    @commands.command(name="unregister", aliases=["unreg"], description='`=unreg (@user)`')
    async def unregister(self, ctx:commands.Context, user:discord.Member):
        if not ctx.author.bot:
            if await self.check_admin_role(ctx):
                if await SQL_CLASS().exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
                    await SQL_CLASS().execute(f"DELETE FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} unregistered {user.mention}", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

    # // GIVES AN USER A WIN COMMAND
    # /////////////////////////////////////////
    @commands.command(name="win", description='`=win (@users)`')
    async def win(self, ctx:commands.Context, users:commands.Greedy[discord.Member]):
        if not ctx.author.bot:
            if await self.check_mod_role(ctx):
                lobby_settings = await SQL_CLASS().select(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
                if lobby_settings is not None:
                    if len(users) > 0:
                        for user in users:
                            await self._win(ctx, user, lobby_settings)
                            await self._stats(ctx, user)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has successfully added wins", color=3066992))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} please mention atleast one player", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

    # // GIVES AN USER A LOSS COMMAND
    # /////////////////////////////////////////
    @commands.command(name="lose", description='`=lose (@users)`')
    async def lose(self, ctx:commands.Context, users:commands.Greedy[discord.Member]):
        if not ctx.author.bot:
            if await self.check_mod_role(ctx):
                lobby_settings = await SQL_CLASS().select(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
                if lobby_settings is not None:
                    if len(users) > 0:
                        for user in users:
                            await self._loss(ctx, user, lobby_settings)
                            await self._stats(ctx, user)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has successfully added losses", color=3066992))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} please mention at least one player", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

    # // SHOW YOUR OR ANOTHER PLAYER'S STATS COMMAND
    # ////////////////////////////////////////////////
    @commands.command(name="stats", description='`=stats`**,** `=stats (@user)`')
    async def stats(self, ctx:commands.Context, *args):
        if not ctx.author.bot:
            user = ctx.author
            if len(args) > 0 and "@" in list(args)[0]:
                user = ctx.guild.get_member(self._clean_user(list(args)[0]))
                if user is None:
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} unknown player", color=15158588))
            return await self._stats(ctx, user)

    # // RESET AN USERS STATS COMMAND
    # /////////////////////////////////////////
    @commands.command(name="reset", description='`=reset all`**,** `=reset (@user)`')
    async def reset(self, ctx:commands.Context, args:str):
        if not ctx.author.bot:
            if await self.check_admin_role(ctx):
                # // RESET EVERY PLAYERS STATS
                if args == "all":
                    for user in ctx.guild.members:
                        if not user.bot:
                            if await SQL_CLASS().exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
                                await self._reset_stats(ctx, user)
                    return await ctx.send(embed=discord.Embed(title="Reset Stats", description=f"{ctx.author.mention} has reset every players stats", color=3066992))
            
                # // RESET THE MENTIONED USERS STATS
                if "<@" in args:
                    user = ctx.guild.get_member(self._clean_user(args))
                    user_name = (await SQL_CLASS().select(f"SELECT user_name FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"))[0]
                    if user_name is not None:
                        await self._reset_stats(ctx, user)
                        await self._user_edit(user, nick=f"{user_name} [0]")
                        return await ctx.send(embed=discord.Embed(title="Reset Stats", description=f"{ctx.author.mention} has reset {user.mention}'s stats", color=3066992))
                    return await ctx.send(embed=discord.Embed(title="Reset Stats", description=f"{user.mention} is not registered", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} incorrect command usage", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
    
    # // SHOW YOUR GUILD'S LEADERBOARD COMMAND
    # /////////////////////////////////////////
    @commands.command(name="leaderboard", aliases=["lb"], description='`=leaderboard`')
    async def leaderboard(self, ctx:commands.Context):
        if not ctx.author.bot:
            users = ""; _count=0
            rows = await SQL_CLASS().select_all(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} ORDER BY elo DESC")
            for i in range(len(rows)):
                user = ctx.guild.get_member(rows[i][1])
                if user is not None:
                    _count+=1
                    users += f'**{_count}:** {user.mention} [**{rows[i][3]}**]\n'
                if _count >= 20:
                    break
            return await ctx.send(embed=discord.Embed(title=f"Leaderboard ┃ {ctx.guild.name}", description=users, color=33023))
        
    # // ROLLBACK EVERY MATCH AN USER WAS IN
    # //////////////////////////////////////////
    @commands.command(name="rollback", aliases=["rb"], description='`=rollback (user id)`')
    async def rollback(self, ctx:commands.Context, user:str):
        '''
        REMOVE THE WIN IF CHEATER IS ON THE WINNING TEAM THEN REMOVE LOSS FOR OPPOSITE TEAM
        IF THE CHEATER IS NOT ON THE WINNING TEAM, THEN THE MATCH STILL COUNTS 
        (RAINBOW SIX SIEGE ROLLBACK SYSTEM)
        '''
        if not ctx.author.bot:
            if await self.check_mod_role(ctx):
                rows = await SQL_CLASS().select_all(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id}")
                for row in rows:
                    if "ongoing" not in row[8] and "rollbacked" not in row[8] and "cancelled" not in row[8]:
                        blue_team = str(row[7]).split(","); blue_team.append(row[6])
                        orange_team =str(row[5]).split(","); orange_team.append(row[4])

                        if user in [blue_team, orange_team]:
                            if row[9] == "orange":
                                if user in orange_team:
                                    await self._undo_win(ctx, row[2], orange_team, blue_team)
                            
                            if row[9] == "blue":
                                if user in blue_team:
                                    await self._undo_win(ctx, row[2], blue_team, orange_team)
                                
                            await SQL_CLASS().execute(f"UPDATE matches SET status = 'rollbacked' WHERE guild_id = {ctx.guild.id} AND match_id = {row[1]}")
                            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} Match **#{row[1]}** has been rollbacked", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has successfully rollbacked all matches with the user **{user}**", color=3066992))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
                

    # // BUTTON CLICK LISTENER
    # /////////////////////////////////////////
    @commands.Cog.listener()
    async def on_button_click(self, res):
        if not res.author.bot:
            if res.component.id in ['blue_report', 'orange_report', 'match_cancel']:
                if await self.check_mod_role(res):
                    # // GETTING THE MATCH ID
                    match_id = int(str(res.message.embeds[0].title).replace("Match #", ""))
                    lobby_id = int(res.message.embeds[0].footer.text)
                    
                    # // GETTING THE ROWS FROM DATABASE
                    status = (await SQL_CLASS().select(f"SELECT status FROM matches WHERE guild_id = {res.guild.id} AND match_id = {match_id}"))[0]
                    lobby_settings = await SQL_CLASS().select(f"SELECT * FROM lobby_settings WHERE guild_id = {res.guild.id} AND lobby_id = {lobby_id}")

                    if status in ["ongoing"]:
                        # // CREATE TEAM LIST AND APPEND TEAM CAPTAIN
                        blue_team=res.message.embeds[0].fields[5].value.split("\n")
                        blue_team.append(self._clean_user(res.message.embeds[0].fields[2].value))

                        # // CREATE TEAM LIST AND APPEND TEAM CAPTAIN
                        orange_team=res.message.embeds[0].fields[3].value.split("\n")
                        orange_team.append(self._clean_user(res.message.embeds[0].fields[0].value))

                        if res.component.id == "match_cancel":
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} has cancelled **Match #{match_id}**", color=3066992))
                            await SQL_CLASS().execute(f"UPDATE matches SET status = 'cancelled' WHERE guild_id = {res.guild.id} AND match_id = {match_id}")
                            await SQL_CLASS().execute(f"UPDATE matches SET winners = 'none' WHERE guild_id = {res.guild.id} AND match_id = {match_id}")

                        if res.component.id == 'blue_report':
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} has reported **Match #{match_id}**", color=3066992))

                            await SQL_CLASS().execute(f"UPDATE matches SET status = 'reported' WHERE guild_id = {res.guild.id} AND match_id = {match_id}")
                            await SQL_CLASS().execute(f"UPDATE matches SET winners = 'blue' WHERE guild_id = {res.guild.id} AND match_id = {match_id}")

                            # // ADDING A WIN FOR EACH BLUE TEAM PLAYER
                            for user in blue_team:
                                member = res.guild.get_member(self._clean_user(user))
                                if member is not None:
                                    await self._win(res.channel, member, lobby_settings)

                            # // ADDING A LOSS FOR EACH ORANGE TEAM PLAYER
                            for _user in orange_team:
                                member = res.guild.get_member(self._clean_user(_user))
                                if member is not None:
                                    await self._loss(res.channel, member, lobby_settings)

                        if res.component.id == 'orange_report':
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} has reported **Match #{match_id}**", color=3066992))

                            await SQL_CLASS().execute(f"UPDATE matches SET status = 'reported' WHERE guild_id = {res.guild.id} AND match_id = {match_id}")
                            await SQL_CLASS().execute(f"UPDATE matches SET winners = 'orange' WHERE guild_id = {res.guild.id} AND match_id = {match_id}")

                            for user in blue_team:
                                member = res.guild.get_member(self._clean_user(user))
                                if member is not None:
                                    await self._loss(res.channel, member, lobby_settings)

                            for _user in orange_team:
                                member = res.guild.get_member(self._clean_user(_user))
                                if member is not None:
                                    await self._win(res.channel, member, lobby_settings)
                    else:
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} this match has already been reported", color=15158588))

                    await res.message.delete()
                    await self._match_show(res.channel, match_id)
                    return await self._delete_channels(res.channel, match_id)
                return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))

def setup(client):
    client.add_cog(Elo(client))