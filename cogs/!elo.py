from discord_components import *
from discord.ext import commands
from functools import *
from _sql import *
import discord, re

# Elo cog
class Elo(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        
    # // Check if member is still in the server
    # //////////////////////////////////////////
    async def _check_member(self, ctx:commands.Context, member_id:int):
        member = ctx.guild.get_member(member_id)
        
        # // If the member is not valid (meaning they left the server, etc.)
        if member is None:
            if Cache.exists(table="users", guild=ctx.guild.id, key=member_id):
                await Cache.delete(
                    table="users", guild=ctx.guild.id, key=member_id, 
                    sqlcmds=[f"DELETE FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {member_id}"]
                )
        return member
        
    # // Check mod role or mod permissions
    # //////////////////////////////////////////
    async def check_mod_role(self, ctx: commands.Context):
        # // If the user has admin role, return true
        if await self.check_admin_role(ctx):
            return True
        
        # // Else, check for whether the user has mod role
        mod_role = Cache.fetch(table="settings", guild=ctx.guild.id)[4]
        return ctx.guild.get_role(mod_role) in ctx.author.roles
    
    
    # // Check admin role or admin permissions
    # //////////////////////////////////////////
    async def check_admin_role(self, ctx: commands.Context):
        # // Get the admin role from settings
        admin_role = Cache.fetch(table="settings", guild=ctx.guild.id)[5]
        
        # // Check admin permissions
        if admin_role == 0 or ctx.author.guild_permissions.administrator:
            return ctx.author.guild_permissions.administrator
        return ctx.guild.get_role(admin_role) in ctx.author.roles
    
    
    # // DELETE TEAM CAPTAIN VOICE CHANNELS FUNCTION
    # ///////////////////////////////////////////////
    async def _delete_channels(self, ctx:commands.Context, match_id:int):
        _category = discord.utils.get(ctx.guild.categories, name=f"Match #{match_id}")
        
        # // If the category exists
        if _category:
            for channel in _category.channels:
                await channel.delete()
            # // Delete the category
            return await _category.delete()


    # RESET AN USERS STATS
    # ///////////////////////////////////////
    async def _reset_stats(self, ctx:commands.Context, user:discord.Member):
        user_data = Cache.fetch(table="users", guild=ctx.guild.id, key=user.id)
        columns = ["wins", "loss", "elo"]
        
        # // Set the users wins loss and elo to 0
        for i in range(1, 3):
            user_data[i] = 0
            # // Update the cache and the database
            await Cache.update(
                table="users", guild=ctx.guild.id, key=user.id, data=user_data, 
                sqlcmds=[f"UPDATE users SET {columns[i]} = 0 WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"]
            )
        
        
    # // REGISTER USER INTO THE DATABASE FUNCTION
    # ///////////////////////////////////////////////
    async def _register_user(self, ctx:commands.Context, user:discord.Member, name:str, role:discord.Role):
        # // Add the user to the cache and database
        await Cache.update(
            sqlcmds=[f"INSERT INTO users (guild_id, user_id, user_name, elo, wins, loss) VALUES ({ctx.guild.id}, {user.id}, '{name}', 0, 0, 0)"],
            table="users", guild=ctx.guild.id, 
            data=[name, 0, 0, 0]
        )
        # // Add the register role to the user
        if role is not None and role not in user.roles:
            await self._user_edit(user, role=role)


    # // EDIT AN USERS NAME OR ROLE FUNCTION
    # ////////////////////////////////////////
    async def _user_edit(self, user:discord.Member, nick:str=None, role:discord.Role=None, remove_role:discord.Role=None):
        
        # // Change the users nickname
        if nick is not None:
            try: await user.edit(nick=nick)
            except Exception: pass

        # // Add a role to the user
        if role is not None:
            try: await user.add_roles(role)
            except Exception: pass
        
        # // Remove a role from the user
        if remove_role is not None:
            try: await user.remove_roles(remove_role)
            except Exception: pass


    # // EDIT AN USERS ELO ROLE
    # /////////////////////////////////////////
    async def edit_elo_role(self, ctx:commands.Context, user:discord.Member, elo_amount:int, option:str):
        roles = []
        
        # // Get the roles 
        if option == "remove":
            # Elo roles greater than the provided elo amount
            roles = await SqlData.select_all(f"SELECT role_id FROM elo_roles WHERE elo_level > {elo_amount} AND guild_id = {ctx.guild.id}")
        else:
            # Opposite of above
            roles = await SqlData.select_all(f"SELECT role_id FROM elo_roles WHERE elo_level <= {elo_amount} AND guild_id = {ctx.guild.id}")
            
        # // Check roles and add them
        if len(roles) > 0:
            for _role in roles:
                role = ctx.guild.get_role(_role[0])
                # // If the option is remove
                if option == "remove":
                    if role in user.roles:
                        await self._user_edit(user, remove_role=role)
                else:
                    # // else if the user has the role
                    if role not in user.roles:
                        # // add the role
                        await self._user_edit(user, role=role)


    # // GIVE AN USER A WIN FUNCTION
    # /////////////////////////////////////////
    async def _add_win(self, ctx:commands.Context, user:discord.Member, lobby_settings:list):
        # // Get the user data
        user_data = Cache.fetch(table="users", guild=ctx.guild.id, key=user.id)
        
        # // Make sure the user is in the cache, if they aren't it will return None
        if user_data is not None:
            # // Update users elo and wins
            user_data[1] = user_data[1]+lobby_settings[2]
            user_data[2] = user_data[2]+1
            
            # // Update the cache and SQL Database
            await Cache.update(
                table="users", guild=ctx.guild.id, key=user.id, data=user_data, 
                sqlcmds=[
                    f"UPDATE users SET elo = {user_data[1]} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}",
                    f"UPDATE users SET wins = {user_data[2]} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"
                ]
            )
            # // Edit the users elo roles
            await self.edit_elo_role(ctx, user, user_data[1], "add")
            
            # // Edit the users nickname
            return await self._user_edit(user, nick=f"{user_data[0]} [{user_data[1]}]")
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))


    # // GIVE AN USER A LOSS FUNCTION
    # /////////////////////////////////////////
    async def _add_loss(self, ctx:commands.Context, user:discord.Member, lobby_settings:list):
        # // Get the user data from the cache
        user_data = Cache.fetch(table="users", guild=ctx.guild.id, key=user.id)
        
        # // Make sure the user is in the cache, if they aren't it will return None
        if user_data is not None:
            member = await self._check_member(ctx, int(user.id))
            if member is not None:
                # // Check if negative elo is disabled
                if lobby_settings[5] == 0 and (user_data[1]-lobby_settings[3]) < 0:
                    # // Set the users elo
                    user_data[1] = 0
                else:
                    user_data[1] = user_data[3]-lobby_settings[3]
                # // Update the users losses
                user_data[3] = user_data[3]+1
                
                # // Update the users elo in the cache and the database
                await Cache.update(
                    table="users", guild=ctx.guild.id, key=user.id, data=user_data, 
                    sqlcmds=[
                        f"UPDATE users SET elo = {user_data[1]} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}",
                        f"UPDATE users SET loss = {user_data[3]+1} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"
                    ]
                )
                # // Change the users nickname
                await self._user_edit(user, nick=f"{user_data[0]} [{user_data[1]}]")
            
            # // Edit the users elo role
            return await self.edit_elo_role(ctx, user, user_data[1], "remove")
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))


    # // LOG A MATCH TO THE DATABASE FUNCTION
    # /////////////////////////////////////////
    async def _match_show(self, ctx:commands.Context, match_id:int):
        row = Cache.fetch(table="matches", guild=ctx.guild.id, key=match_id)
        
        # // Check to make sure the match is valid
        if row is not None:
            embed=discord.Embed(title=f"Match #{match_id} ┃ {row[8].upper()}", description=f"**Map:** {row[3]}\n**Winners:** {row[9][0].upper()+row[9][1:]}", color=33023)
            embed.add_field(name="Orange Captain", value=f"<@{row[4]}>")
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=f"<@{row[6]}>")
            embed.add_field(name="Orange Team", value='\n'.join(f"<@{e}>" for e in row[5].split(",")))
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value='\n'.join(f"<@{e}>" for e in row[7].split(",")))
            
            # // Send the embeds
            return await ctx.send(embed=embed)
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} we were unable to find **Match #{match_id}**", color=15158588))


    # // SHOW THE USERS STATS FUNCTION
    # /////////////////////////////////////////
    async def _stats(self, ctx:commands.Context, user:discord.Member):
        row = Cache.fetch(table="matches", guild=ctx.guild.id, key=user.id)
        
        # // Make sure the match exists
        if row is not None:
            # // Create an embed
            embed = discord.Embed(description=f"**Elo:** {row[3]}\n**Wins:** {row[4]}\n**Losses:** {row[5]}\n**Matches:** {row[5]+row[4]}", color=33023)
            embed.set_author(name=row[2], icon_url=user.avatar_url)
        
            # // Send the embeds
            return await ctx.send(embed=embed)
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))


    # // UNDO A WIN FOR THE ORANGE TEAM
    # ////////////////////////////////////
    async def _undo_win(self, ctx:commands.Context, lobby_id:int, winners:list, losers:list):
        lobby_settings = Cache.fetch(table="lobby_settings", guild=ctx.guild.id, key=lobby_id)

        # // REMOVE LOSS FROM LOSERS
        for _user_id in losers:
            # // Check if member is valid
            member = await self._check_member(ctx, int(_user_id))
            if member is not None:
                user_data = Cache.fetch(table="users", guild=ctx.guild.id, key=_user_id)
                # // Update users elo
                user_data[1] = user_data[1]+lobby_settings[2]
                # // Update users losses
                user_data[3] = user_data[3]-1
                
                # // Update the cache and SQL Database
                await Cache.update(
                    table="users", guild=ctx.guild.id, key=_user_id, data=user_data, 
                    sqlcmds=[
                        f"UPDATE users SET elo = {user_data[1]} WHERE guild_id = {ctx.guild.id} AND user_id = {_user_id}",
                        f"UPDATE users SET loss = {user_data[3]} WHERE guild_id = {ctx.guild.id} AND user_id = {_user_id}"
                    ]
                )
                # // Add elo roles
                await self.edit_elo_role(ctx, member, user_data[1], "add")
        
        # // REMOVE WIN FROM WINNERS
        for user_id in winners:
            # // Check to make sure the member is valid
            member = await self._check_member(ctx, int(user_id))
            if member is not None:
                user_data = Cache.fetch(table="users", guild=ctx.guild.id, key=user_id)
                
                # // Check whether negative elo is disabled
                # // Updating the users elo..
                if lobby_settings[5] == 0 and (user_data[1]-lobby_settings[2]) < 0:
                    user_data[1] = 0
                else:
                    user_data[1] = user_data[1]-lobby_settings[2]
                # // Update users losses
                user_data[3] = user_data[3]-1
                
                # // Update the cache and SQL Database
                await Cache.update(
                    table="users", guild=ctx.guild.id, key=_user_id, data=user_data, 
                    sqlcmds=[
                        f"UPDATE users SET elo = {user_data[1]} WHERE guild_id = {ctx.guild.id} AND user_id = {_user_id}",
                        f"UPDATE users SET wins = {user_data[3]} WHERE guild_id = {ctx.guild.id} AND user_id = {_user_id}"
                    ]
                )
                    
                # // Remove elo roles
                await self.edit_elo_role(ctx, member, user_data[1], "remove")
            
    
    # // ADD / REMOVE A NEW ELO ROLE
    # /////////////////////////////////
    @commands.command(name="elorole", description='`=elorole add (@role) [elo]`**,** `=elorole del (@role)`**,** `=elorole list`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def elorole(self, ctx:commands.Context, option:str, *args):
        if option in ["add", "create", "new", "remove", "delete", "del"]:
            role = ctx.guild.get_role(int(re.sub("\D","", args[0])))
        
        # // ADD AN ELO ROLE
        if option in ["add", "create", "new"]:
            if await self.check_admin_role(ctx):
                # // Check if the new elorole is below their own
                if role.position < ctx.author.top_role.position or ctx.author.guild_permissions.administrator:
                    # // Get the current elo roles and check to make sure the server has under 20
                    elo_roles = Cache.fetch(table="elo_roles", guild=ctx.guild.id)
                    if len(elo_roles) < 20:
                        if not Cache.exists(table="elo_roles", guild=ctx.guild.id, key=role.id):
                            elo_roles[0] = int(args[1])
                            elo_roles[1] = 5
                            elo_roles[2] = 2
                            
                            # // Add the new elo role into the cache and database
                            await Cache.update(
                                table="elo_roles", guild=ctx.guild.id, key=role.id, data=elo_roles, 
                                sqlcmds=[f"INSERT INTO elo_roles (guild_id, role_id, elo_level, win_elo, lose_elo) VALUES ({ctx.guild.id}, {role.id}, {int(args[1])}, 5, 2)"]
                            )
                            # // Send the success embed
                            return await ctx.send(embed=discord.Embed(description=f"**[{len(elo_roles)+1}/20]** {ctx.author.mention} {role.mention} will now be given at **{int(args[1])} elo**", color=3066992))
            
                        # // Send error embeds (all below)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} {role.mention} already exists", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"**[20/20]** {ctx.author.mention} maximum amount of roles reached", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} please choose a role lower than {ctx.author.top_role.mention}", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

        # // REMOVE AN ELO ROLE
        if option in ["remove", "delete", "del"]:
            if await self.check_admin_role(ctx):
                if Cache.exists(table="elo_roles", guild=ctx.guild.id, key=role.id):
                    elo_roles = Cache.fetch(table="elo_roles", guild=ctx.guild.id)
                    
                    # // Delete the elo role from the cache and database
                    await Cache.delete(
                        table="guild_id", guild=ctx.guild.id, key=role.id, 
                        sqlcmds=[f"DELETE FROM elo_roles WHERE guild_id = {ctx.guild.id} AND role_id = {role.id}"]
                    )
                    # // Return the success embed
                    return await ctx.send(embed=discord.Embed(description=f"**[{len(elo_roles)-1}/20]** {ctx.author.mention} {role.mention} has been removed", color=3066992))

                # // Return error embeds (all below)
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} {role.mention} is not an elo role", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
        # // SLIST ALL THE ELO ROLES
        if option in ["list", "show"]:
            description = ""
            rows = await SqlData.select_all(f"SELECT * FROM elo_roles WHERE guild_id = {ctx.guild.id} ORDER BY elo_level ASC")
            
            # // For each elo role
            for i in range(len(rows)):
                role = ctx.guild.get_role(rows[i][1])
                
                # // Add the role to the embed description
                if role is not None:
                    description += f'**{i+1}:** {role.mention} [**{rows[i][2]}**]\n'
                else:
                    # // Delete the elo role from the cache and database
                    await Cache.delete(
                        table="guild_id", guild=ctx.guild.id, key=rows[i][1], 
                        sqlcmds=[f"DELETE FROM elo_roles WHERE guild_id = {ctx.guild.id} AND role_id = {rows[i][1]}"]
                    )
            # // Send the elo role list embed
            return await ctx.send(embed=discord.Embed(title=f"Elo Roles ┃ {ctx.guild.name}", description=description, color=33023))
        
        
    # // MATCH REPORT / CANCEL / UNDO / SHOW COMMAND
    # /////////////////////////////////////////
    @commands.command(name="match", description='`=match report (match id) [blue/orange]`**,** `=match cancel (match id)`**,** `=match undo (match id)`**,** `=match show (match id)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def match(self, ctx:commands.Context, action:str, match_id:int, *args):
        if not ctx.author.bot:
            # // Get the match from the cache and make sure it's not invalid
            match_data = Cache.fetch(table="matches", guild=ctx.guild.id, key=match_id)
                    
            # // SHOWING A LOGGED MATCH
            if action in ["show"]:
                return await self._match_show(ctx, match_id)
            
            # // REPORTING AN ONGOING MATCH
            elif action in ["report"]:
                if match_data is not None:
                    # // Check if the user has the mod role
                    if await self.check_mod_role(ctx):
                        lobby_settings = Cache.fetch(table="lobby_settings", guild=ctx.guild.id, key=match_data[2])

                        # // If the match is ongoing
                        if len(args) > 0 and match_data[8] in ["ongoing"]:
                            match_data[6] = "reported"
                            match_data[7] = args[0]
                            
                            # // Update the cache and database
                            await Cache.update(
                                table="matches", guild=ctx.guild.id, key=match_id, data=match_data, 
                                sqlcmds=[
                                    f"UPDATE matches SET status = 'reported' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}",
                                    f"UPDATE matches SET winners = '{args[0]}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"
                                ]
                            )
                            
                            # // Get the orange team
                            orange_team = match_data[3].split(",")
                            orange_team.append(int(match_data[2]))
                            # // Get the blue team
                            blue_team = match_data[5].split(",")
                            blue_team.append(int(match_data[4]))

                            # // If team is the winner
                            if "blue" in args[0]:
                                # // Add a loss for each orange team member
                                for _user in orange_team:
                                    member = await self._check_member(ctx, int(_user))
                                    if member is not None:
                                        await self._add_loss(ctx, member, lobby_settings)

                                # // Add a win for each blue team member
                                for user in blue_team:
                                    member = await self._check_member(ctx, int(user))
                                    if member is not None:
                                        await self._add_win(ctx, member, lobby_settings)

                            # // If orange team is the winner
                            if "orange" in args[0]:
                                # // Add a win for each orange team member
                                for _user in orange_team:
                                    member = await self._check_member(ctx, int(_user))
                                    if member is not None:
                                        await self._add_win(ctx, member, lobby_settings)

                                # // Add a win for each blue team member
                                for user in blue_team:
                                    member = await self._check_member(ctx, int(user))
                                    if member is not None:
                                        await self._add_loss(ctx, member, lobby_settings)
                                        
                            # // Send the match info the current channel
                            await self._match_show(ctx, match_id)
                            # // Delete the match channels
                            return await self._delete_channels(ctx, match_id)

                        # // Send error embeds (all below)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} invalid match id", color=15158588))


            # // CANCELLING AN ONGOING MATCH
            elif action in ["cancel"]:
                # // Make sure the match is valid
                if match_data is not None:
                    if await self.check_mod_role(ctx):
                        # // Check if the match is currently ongoing (eg: not already reported, etc.)
                        if match_data[6] in ["ongoing"]:
                            match_data[6] = "cancelled"
                            match_data[7] = "none"
                            
                            # // Update the cache and database
                            await Cache.update(
                                table="matches", guild=ctx.guild.id, key=match_id, data=match_data, 
                                sqlcmds=[
                                    f"UPDATE matches SET status = 'cancelled' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}",
                                    f"UPDATE matches SET winners = 'none' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"
                                ]
                            )
                            # // Send the match info embed
                            await self._match_show(ctx, match_id)
                            # // Delete the match channels
                            return await self._delete_channels(ctx, match_id)
                        
                        # // Send error embeds (all below)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} invalid match id", color=15158588))
                
                
            # // UNDOING A REPORTED MATCH
            elif action in ["undo"]:
                if await self.check_mod_role(ctx):
                    # // Make sure match is valid
                    if match_data is not None:
                        if match_data[6] in ["reported", "cancelled"]:
                            # // Update the match status and winners
                            match_data[6] = "ongoing"
                            match_data[7] = "none"
                            
                            # // Update the cache and database
                            await Cache.update(
                                table="matches", guild=ctx.guild.id, key=match_id, data=match_data, 
                                sqlcmds=[
                                    f"UPDATE matches SET status = 'ongoing' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}",
                                    f"UPDATE matches SET winners = 'none' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"
                                ]
                            )
                            
                            # // Add the blue team and it's captains
                            blue_team = match_data[5].split(",")
                            blue_team.append(match_data[4])
                            # // Add the orange team and it's captains
                            orange_team = match_data[5].split(",")
                            orange_team.append(match_data[4])

                            # // REMOVE WIN FROM BLUE TEAM
                            if match_data[7] == "blue":
                                await self._undo_win(ctx, match_data[0], blue_team, orange_team)
                                
                            # // REMOVE LOSS FROM BLUE TEAM
                            if match_data[7] == "orange":
                                await self._undo_win(ctx, match_data[0], orange_team, blue_team)
                            
                            # // Send the embeds
                            return await self._match_show(ctx, match_id)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match hasn't been reported yet", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} invalid match id", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
            raise Exception("Invalid option")


    # // SET PLAYERS STATS COMMAND
    # /////////////////////////////////
    @commands.command(name="set", description='`=set elo (@user) (amount)`**,** `=set wins (@user) (amount)`**,** `=set losses (@user) (amount)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set(self, ctx:commands.Context, action:str, user:discord.Member, amount:int):
        if not ctx.author.bot:
            # // Check if the cmd author has the mod role
            if await self.check_mod_role(ctx):
                user_data = Cache.fetch(table="users", guild=ctx.guild.id, key=user.id)
                if user_data is not None:
                    # // SET A PLAYERS ELO
                    if action in ["elo", "points"]:
                        user_data[1] = amount
                        
                        # // Update the cache and database
                        await Cache.update(
                            table="users", guild=ctx.guild.id, key=user.id, data=user_data, 
                            sqlcmds=[f"UPDATE users SET elo = {amount} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"]
                        )
                        # // Edit the users nickname
                        await self._user_edit(user, nick=f"{user_data[0]} [{amount}]")
                        
                    # // SET A PLAYERS WINS
                    elif action in ["wins", "win"]:
                        # // Set the users wins
                        user_data[2] = amount
                        
                        # // Update the cache and database
                        await Cache.update(
                            table="users", guild=ctx.guild.id, key=user.id, data=user_data, 
                            sqlcmds=[f"UPDATE users SET wins = {amount} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"]
                        )
                        
                    # // SET A PLAYERS LOSSES
                    elif action in ["losses", "lose", "loss"]:
                        # // Set the users losses
                        user_data[3] = amount
                        
                        # // Update the cache and database
                        await Cache.update(
                            table="users", guild=ctx.guild.id, key=user.id, data=user_data, 
                            sqlcmds=[f"UPDATE users SET loss = {amount} WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"]
                        )
                    # // Return an invalid option exception
                    else: raise Exception("Invalid option")
                    # // Send the user's stats embed
                    return await self._stats(ctx, user)
            
                # // Send error embeds (all below)
                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))


    # // SHOW THE LAST MATCH PLAYED COMMAND
    # /////////////////////////////////////////
    @commands.command(name="lastmatch", aliases=["lm"], description='`=lastmatch`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def lastmatch(self, ctx:commands.Context):
        if not ctx.author.bot:
            count = Cache.fetch(table="matches", guild=ctx.guild.id)
            return await self._match_show(ctx, len(count))


    # // REPLACE / SUB TWO PLAYERS COMMAND
    # /////////////////////////////////////////
    @commands.command(name="replace", aliases=["sub", "swap"], description='`=replace (@user to be replaced) (@user replacing) (match id)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def replace(self, ctx:commands.Context, user1:discord.Member, user2:discord.Member, match_id:int):
        if not ctx.author.bot:
            if await self.check_mod_role(ctx):
                match_data = Cache.fetch(table="users", guild=ctx.guild.id, key=match_id)
                
                # // Check match status
                if "reported" not in match_data[6] and "cancelled" not in match_data[6] and "rollbacked" not in match_data[6]:
                    # // Get the blue and orange teams
                    blue_team = str(match_data[5]).split(",")
                    orange_team = str(match_data[3]).split(",")

                    # // REPLACE USER FROM ORANGE CAPTAIN
                    if str(user1.id) in str(match_data[2]) and str(user2.id) not in str(match_data[2]):
                        # // Set the orange team captain
                        match_data[2] = user2.id
                        
                        # // Update the cache and database
                        await Cache.update(
                            table="matches", guild=ctx.guild.id, key=match_id, data=match_data, 
                            sqlcmds=[f"UPDATE matches SET orange_cap = '{user2.id}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"]
                        )
                        
                    # // REPLACE USER FROM BLUE CAPTAIN
                    elif str(user1.id) in str(match_data[4]) and str(user2.id) not in str(match_data[4]):
                        # // Set the blue team captain
                        match_data[4] = user2.id
                        
                        # // Update the cache and database
                        await Cache.update(
                            table="matches", guild=ctx.guild.id, key=match_id, data=match_data, 
                            sqlcmds=[f"UPDATE matches SET blue_cap = '{user2.id}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"]
                        )
                        
                    
                    # // REPLACE USER FROM ORANGE TEAM
                    elif str(user1.id) in orange_team and str(user2.id) not in orange_team:
                        # // Replace the user1 with user2 in the orange team
                        orange_team[orange_team.index(str(user1.id))] = str(user2.id)
                        # // Set the orange team captain
                        match_data[3] = ','.join(str(e) for e in orange_team)
                        
                        # // Update the cache and database
                        await Cache.update(
                            table="matches", guild=ctx.guild.id, key=match_id, data=match_data, 
                            sqlcmds=[f"UPDATE matches SET orange_team = '{','.join(str(e) for e in orange_team)}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"]
                        )
                        
                    # // REPLACE USER FROM BLUE TEAM
                    elif str(user1.id) in blue_team and str(user2.id) not in blue_team:
                        # // Replace the user1 with user2 in the blue team
                        blue_team[blue_team.index(str(user1.id))] = str(user2.id)
                        # // Set the orange team captain
                        match_data[5] = ','.join(str(e) for e in blue_team)
                        
                        # // Update the cache and database
                        await Cache.update(
                            table="matches", guild=ctx.guild.id, key=match_id, data=match_data, 
                            sqlcmds=[f"UPDATE matches SET blue_team = '{','.join(str(e) for e in blue_team)}' WHERE guild_id = {ctx.guild.id} AND match_id = {match_id}"]
                        )
                    
                    # // Send error embeds (all below)
                    else:
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} player(s) not found/error", color=15158588))
                    return await ctx.send(embed=discord.Embed(title=f"Match #{match_id}", description=f"{ctx.author.mention} replaced {user1.mention} with {user2.mention}", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this match has already been reported", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))


    # SHOW THE PAST 10 MATCHES PLAYED
    # /////////////////////////////////
    @commands.command(name="recent", description='`=recent`**,** `=recent (amount)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def recent(self, ctx:commands.Context, *args):
        if not ctx.author.bot:
            # // Amount = the last match
            match_data = Cache.fetch(table="matches", guild=ctx.guild.id)
            amount = len(match_data)
            
            # // Else Amount = provided args
            if len(args) > 0: amount = int(args[0])

            # // Create a recent matches embed
            embed = discord.Embed(title=f"Recent Matches ┃ {ctx.guild.name}", color=33023)
            for i in range(amount):
                embed.add_field(name=f"Match #{match_data[-i-1][1]}", value=f"`{match_data[-i-1][8].upper()}`")
                
            # // Send the embed
            return await ctx.send(embed=embed)
    
    
    # // CHANGE YOUR USERNAME COMMAND
    # /////////////////////////////////////////
    @commands.command(name="rename", description='`=rename (name)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def rename(self, ctx:commands.Context, name:str):
        if not ctx.author.bot:
            # // RENAME THEMSELVES
            if not await self.check_admin_role(ctx) and not await self.check_mod_role(ctx):
                self_rename = Cache.fetch(table="settings", guild=ctx.guild.id)[6]
                if self_rename[0] == 0:
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} self renaming is not enabled", color=15158588))
            
            # // RENAME ANOTHER USER
            # // Get the user from the database and make sure the result is valid
            user_data = Cache.fetch(table="users", guild=ctx.guild.id, key=ctx.author.id)
            if user_data is not None:
                # // Set the users name
                user_data[0] = name
                
                # // Update the cache and database
                await Cache.update(
                    table="users", guild=ctx.guild.id, key=ctx.author.id, data=user_data, 
                    sqlcmds=[f"UPDATE users SET user_name = '{name}' WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}"]
                )
                
                # // Update the users nickname
                await self._user_edit(ctx.author, nick=f"{name} [{user_data[3]}]")
                # // Send the embeds
                return await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} renamed to **{name}**', color=3066992))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is not registered", color=15158588))
            

    # // FORCE CHANGE A PLAYER'S USERNAME COMMAND
    # ////////////////////////////////////////////
    @commands.command(name="forcerename", aliases=["fr"], description='`=forcerename (@user) (name)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def forcerename(self, ctx:commands.Context, user:discord.Member, name:str):
        if not ctx.author.bot:
            # // Check if the user has the mod role
            if await self.check_mod_role(ctx):
                user_data = Cache.fetch(table="users", guild=ctx.guild.id, key=user.id)
                
                # // If the user data is valid
                if user_data is not None:
                    # // Set the users name
                    user_data[0] = name
                    
                    # // Update the cache and database
                    await Cache.update(
                        table="users", guild=ctx.guild.id, key=ctx.author.id, data=user_data, 
                        sqlcmds=[f"UPDATE users SET user_name = '{name}' WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"]
                    )
                    # // Update the users nickname
                    await self._user_edit(user, nick=f"{name} [{user_data[3]}]")

                    # // Send the embeds
                    return await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} renamed {user.mention} to **{name}**', color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))


    # // REGISTER USER INTO THE DATABASE COMMAND
    # ///////////////////////////////////////////
    @commands.command(name="register", aliases=["reg"], description='`=register (name)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def register(self, ctx:commands.Context, *args):
        if not ctx.author.bot:
            settings = Cache.fetch(table="settings", guild=ctx.guild.id)
            
            # // GETTING THE REGISTER ROLE FROM SETTINGS
            if settings[3] not in [0, ctx.channel.id]:
                # // Get the register channel
                channel = ctx.guild.get_channel(settings[3])
                if channel is not None:
                    # // Direct the user to the correct register channel
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} {channel.mention}", color=33023))
                
            # // If register role is not invalid
            role = None
            if settings[1] != 0:
                role = ctx.guild.get_role(settings[1])
                # // If the role is expire / invalid, remvoe it from the database
                if role is None:
                    settings[0] = 0
                    
                    # // Update the cache and database
                    await Cache.update(
                        table="settings", guild=ctx.guild.id, key=ctx.author.id, data=settings, 
                        sqlcmds=[f"UPDATE settings SET reg_role = 0 WHERE guild_id = {ctx.guild.id}"]
                    )
                
        
            # // REGISTER THE MENTIONED USER
            if len(args) > 0 and "@" in args[0]:
                # // Check if the user has the mod role
                if await self.check_mod_role(ctx):
                    user = ctx.guild.get_member(int(re.sub("\D","", args[0])))
                    if user is not None:
                        # // Make sure user is not a bot
                        if not user.bot:
                            # // Check whether the user already exists
                            if not Cache.exists(table="users", guild=ctx.guild.id, key=user.id):
                                # // Modify the name
                                name = user.name
                                if len(args) > 1: name = args[1]
                                    
                                # // Register the user
                                await self._register_user(ctx, user, name, role)
                                # // Edit the users nickname
                                await self._user_edit(user, nick=f"{name} [0]")
                                
                                # // Send the embeds
                                return await ctx.send(embed=discord.Embed(description=f"{user.mention} has been registered as **{name}**", color=3066992))
                            return await ctx.send(embed=discord.Embed(description=f"{user.mention} is already registered", color=15158588))
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you cannot register a bot", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} unknown player", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))


            # // REGISTER THE MESSAGE AUTHOR
            else:
                # // Mody the name
                name = ctx.author.name
                if len(args) > 0: name = args[0]
                    
                # // If the user doesn't already exist
                if not Cache.exists(table="users", guild=ctx.guild.id, key=ctx.author.id):
                    # // Register the user
                    await self._register_user(ctx, ctx.author, name, role)
                    # // Edit the users nickname
                    await self._user_edit(ctx.author, nick=f"{name} [0]")
                    
                    # // Send the embeds
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has been registered as **{name}**", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is already registered", color=15158588))
    
    
    # // UNREGISTER AN USER FROM THE DATABASE COMMAND
    # ////////////////////////////////////////////////
    @commands.command(name="unregister", aliases=["unreg"], description='`=unreg (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def unregister(self, ctx:commands.Context, user:discord.Member):
        if not ctx.author.bot:
            # // Check if the user has admin role
            if await self.check_admin_role(ctx):
                # // Make sure the provided user exists
                if Cache.exists(table="users", guild=ctx.guild.id, key=user.id):
                    # // Delete the elo role from the cache and database
                    await Cache.delete(
                        table="users", guild=ctx.guild.id, key=user.id, 
                        sqlcmds=[f"DELETE FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"]
                    )
                    
                    # // Send the embeds
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} unregistered {user.mention}", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))


    # // GIVES AN USER A WIN COMMAND
    # /////////////////////////////////////////
    @commands.command(name="win", description='`=win (@users)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def win(self, ctx:commands.Context, users:commands.Greedy[discord.Member]):
        if not ctx.author.bot:
            # // Check if the user has the mod role
            if await self.check_mod_role(ctx):
                lobby_settings = Cache.fetch(table="lobby_settings", guild=ctx.guild.id, key=ctx.channel.id)
                
                # // If the lobby is valid
                if lobby_settings is not None:
                    # // Make sure the author provided users
                    if len(users) > 0:
                        for user in users:
                            # // Add a win to the user
                            await self._add_win(ctx, user, lobby_settings)
                            # // Then send their stats
                            await self._stats(ctx, user)
                            
                        # // Send the embeds
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has successfully added wins", color=3066992))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} please mention atleast one player", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))


    # // GIVES AN USER A LOSS COMMAND
    # /////////////////////////////////////////
    @commands.command(name="lose", description='`=lose (@users)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def lose(self, ctx:commands.Context, users:commands.Greedy[discord.Member]):
        if not ctx.author.bot:
            # // Check if the author has mod role
            if await self.check_mod_role(ctx):
                lobby_settings = Cache.fetch(table="lobby_settings", guild=ctx.guild.id, key=ctx.channel.id)
                
                # // If the lobby is valid
                if lobby_settings is not None:
                    # // Make sure the author provided users
                    if len(users) > 0:
                        for user in users:
                            # // Add a loss to the user
                            await self._add_loss(ctx, user, lobby_settings)
                            # // Send the users stats
                            await self._stats(ctx, user)
                            
                        # // Send the embeds
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has successfully added losses", color=3066992))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} please mention at least one player", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))


    # // SHOW YOUR OR ANOTHER PLAYER'S STATS COMMAND
    # ////////////////////////////////////////////////
    @commands.command(name="stats", description='`=stats`**,** `=stats (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def stats(self, ctx:commands.Context, *args):
        if not ctx.author.bot:
            user = ctx.author
            
            # // Get stats of another user
            if len(args) > 0 and "@" in args[0]:
                user = ctx.guild.get_member(int(re.sub("\D","", args[0])))
                if user is None:
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} unknown player", color=15158588))
            # // Get stats of the command author
            return await self._stats(ctx, user)


    # // RESET AN USERS STATS COMMAND
    # /////////////////////////////////////////
    @commands.command(name="reset", description='`=reset all`**,** `=reset (@user)`')
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def reset(self, ctx:commands.Context, args:str):
        if not ctx.author.bot:
            if await self.check_admin_role(ctx):
                
                # // RESET EVERY PLAYERS STATS
                if args == "all":
                    # // For each member in the guild
                    for user in ctx.guild.members:
                        if not user.bot:
                            # // Check if the user exists in the database
                            if Cache.exists(table="users", guild=ctx.guild.id, key=user.id):
                                # // Reset their stats
                                await self._reset_stats(ctx, user)
                    # // Send success embed
                    return await ctx.send(embed=discord.Embed(title="Reset Stats", description=f"{ctx.author.mention} has reset every players stats", color=3066992))
            
            
                # // RESET THE MENTIONED USERS STATS
                if "<@" in args:
                    # // Get the user
                    user = ctx.guild.get_member(int(re.sub("\D","", args)))
                    user_name = Cache.fetch(table="users", guild=ctx.guild.id, key=user.id)[0]
                    
                    # // Make sure user is not invalid
                    if user_name is not None:
                        # // Reset the users stats
                        await self._reset_stats(ctx, user)
                        # // Edit the users nickname
                        await self._user_edit(user, nick=f"{user_name} [0]")
                        
                        # // Send the embeds
                        return await ctx.send(embed=discord.Embed(title="Reset Stats", description=f"{ctx.author.mention} has reset {user.mention}'s stats", color=3066992))
                    return await ctx.send(embed=discord.Embed(title="Reset Stats", description=f"{user.mention} is not registered", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} incorrect command usage", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
    
    
    # // SHOW GUILD'S LEADERBOARD COMMAND
    # /////////////////////////////////////////
    @commands.command(name="leaderboard", aliases=["lb"], description='`=leaderboard`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def leaderboard(self, ctx:commands.Context):
        if not ctx.author.bot:
            users = ""; _count=0
            rows = await SqlData.select_all(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} ORDER BY elo DESC")
            
            # // For each user in rows
            for i in range(len(rows)):
                member = await self._check_member(ctx, rows[i][1])
                
                # // If the member exists
                if member is not None:
                    # // Increase counts and add to users string
                    _count+=1
                    users += f'**{_count}:** {member.mention} [**{rows[i][3]}**]\n'
                    
                # // Make sure only 20 members are displayed
                if _count >= 20: break
            # // Return the leaderboard
            return await ctx.send(embed=discord.Embed(title=f"Leaderboard ┃ {ctx.guild.name}", description=users, color=33023))
        
        
    # // ROLLBACK EVERY MATCH AN USER WAS IN
    # //////////////////////////////////////////
    @commands.command(name="rollback", aliases=["rb"], description='`=rollback (user id)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def rollback(self, ctx:commands.Context, user:str):
        '''
        REMOVE THE WIN IF CHEATER IS ON THE WINNING TEAM THEN REMOVE LOSS FOR OPPOSITE TEAM
        IF THE CHEATER IS NOT ON THE WINNING TEAM, THEN THE MATCH STILL COUNTS 
        (RAINBOW SIX SIEGE ROLLBACK SYSTEM)
        '''
        if not ctx.author.bot:
            # // Check if the user has admin role
            if await self.check_admin_role(ctx):
                matches = Cache.fetch(table="matches", guild=ctx.guild.id)
                # // For each match
                for match in matches:
                    if "ongoing" not in match[6] and "rollbacked" not in match[6] and "cancelled" not in match[6]:
                        # // Create the blue team and orange team lists
                        blue_team = str(match[5]).split(","); blue_team.append(match[4])
                        orange_team =str(match[3]).split(","); orange_team.append(match[2])

                        # // Check if the user is in either of the teams
                        if user in blue_team or user in orange_team:
                            # // Check the match winners (in this case it's orange)
                            if match[7] == "orange":
                                if user in orange_team:
                                    await self._undo_win(ctx, match[0], orange_team, blue_team)
                            
                            # // Check the match winners (in this case it's blue)
                            if match[7] == "blue":
                                if user in blue_team:
                                    await self._undo_win(ctx, match[0], blue_team, orange_team)
                            
                            # // Update the match status and winners
                            match[6] = "ongoing"
                            # // Update the cache and database
                            await Cache.update(
                                table="matches", guild=ctx.guild.id, key=match[0], data=match, 
                                sqlcmds=[f"UPDATE matches SET status = 'rollbacked' WHERE guild_id = {ctx.guild.id} AND match_id = {match[0]}"]
                            )
                            
                            # // Send match rollback embed
                            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} Match **#{match[1]}** has been rollbacked", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has successfully rollbacked all matches with the user **{user}**", color=3066992))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
                

    # // BUTTON CLICK LISTENER
    # /////////////////////////////////////////
    @commands.Cog.listener()
    async def on_button_click(self, res:Interaction):
        if not res.author.bot:
            if res.component.id in ['blue_report', 'orange_report', 'match_cancel']:
                # // Check if the user has the mod role
                if await self.check_mod_role(res):
                    # // GETTING THE MATCH ID
                    match_id = int(str(res.message.embeds[0].title).replace("Match #", ""))
                    lobby_id = int(res.message.embeds[0].footer.text)
                    
                    # // GETTING THE ROWS FROM DATABASE
                    match_data = Cache.fetch(table="matches", guild=res.guild.id, key=match_id)
                    lobby_settings = Cache.fetch(table="lobby_settings", guild=res.guild.id, key=lobby_id)

                    # // Check match status
                    if match_data[6] not in ["ongoing"]:
                        # // Send error embed
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} this match has already been reported", color=15158588))
                    else:
                        # // CREATE TEAM LIST AND APPEND TEAM CAPTAIN
                        blue_team = res.message.embeds[0].fields[5].value.split("\n")
                        blue_team.append(int(re.sub("\D","", res.message.embeds[0].fields[2].value)))

                        # // CREATE TEAM LIST AND APPEND TEAM CAPTAIN
                        orange_team = res.message.embeds[0].fields[3].value.split("\n")
                        orange_team.append(int(re.sub("\D","", res.message.embeds[0].fields[0].value)))

                        # // CANCEL THE MATCH
                        if res.component.id == "match_cancel":
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} has cancelled **Match #{match_id}**", color=3066992))
                            # // Update the match status and winners
                            match_data[6] = "reported"
                            match_data[7] = "none"
                            
                            # // Update the cache and database
                            await Cache.update(
                                table="matches", guild=res.guild.id, key=match_id, data=match_data, 
                                sqlcmds=[
                                    f"UPDATE matches SET status = 'cancelled' WHERE guild_id = {res.guild.id} AND match_id = {match_id}",
                                    f"UPDATE matches SET winners = 'none' WHERE guild_id = {res.guild.id} AND match_id = {match_id}"
                                ]
                            )

                        # // REPORT BLUE TEAM WIN
                        if res.component.id == 'blue_report':
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} has reported **Match #{match_id}**", color=3066992))
                            
                            # // Update the match status and winners
                            match_data[6] = "reported"
                            match_data[7] = "blue"
                            
                            # // Update the cache and database
                            await Cache.update(
                                table="matches", guild=res.guild.id, key=match_id, data=match_data, 
                                sqlcmds=[
                                    f"UPDATE matches SET status = 'reported' WHERE guild_id = {res.guild.id} AND match_id = {match_id}",
                                    f"UPDATE matches SET winners = 'blue' WHERE guild_id = {res.guild.id} AND match_id = {match_id}"
                                ]
                            )
                            
                            # // Add a win to each blue team member
                            for user in blue_team:
                                member = await self._check_member(res, int(re.sub("\D","", user)))
                                if member is not None:
                                    await self._add_win(res.channel, member, lobby_settings)

                            # // Add a loss to each orange team member
                            for _user in orange_team:
                                member = await self._check_member(res, int(re.sub("\D","", _user)))
                                if member is not None:
                                    await self._add_loss(res.channel, member, lobby_settings)

                        
                        # // REPORT ORANGE TEAM WIN
                        if res.component.id == 'orange_report':
                            # // Send reported embed
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} has reported **Match #{match_id}**", color=3066992))

                            # // Update the match status and winners
                            match_data[6] = "reported"
                            match_data[7] = "orange"
                            # // Update the cache and database
                            await Cache.update(
                                table="matches", guild=res.guild.id, key=match_id, data=match_data, 
                                sqlcmds=[
                                    f"UPDATE matches SET status = 'reported' WHERE guild_id = {res.guild.id} AND match_id = {match_id}",
                                    f"UPDATE matches SET winners = 'orange' WHERE guild_id = {res.guild.id} AND match_id = {match_id}"
                                ]
                            )
                            # // Add a loss to each blue team member
                            for user in blue_team:
                                member = await self._check_member(res, int(re.sub("\D","", user)))
                                if member is not None:
                                    await self._add_loss(res.channel, member, lobby_settings)

                            # // Add a win to each orange team member
                            for _user in orange_team:
                                member = await self._check_member(res, int(re.sub("\D","", _user)))
                                if member is not None:
                                    await self._add_win(res.channel, member, lobby_settings)
                    
                    # // Delete the original embed
                    await res.message.delete()
                    # // Show the new match data
                    await self._match_show(res.channel, match_id)
                    # // Delete the match channels
                    return await self._delete_channels(res.channel, match_id)
                # // Permissions error embed
                return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))


# // Setup the cog
def setup(client: commands.Bot):
    client.add_cog(Elo(client))