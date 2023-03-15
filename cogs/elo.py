from discord_components import *
from discord.ext import commands
from functools import *
from data import *
import discord, re

# // Elo cog
class EloCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    # // ADD / REMOVE A NEW ELO ROLE
    # /////////////////////////////////
    @commands.command(name="elorole", description='`=elorole add (@role) [elo]`**,** `=elorole del (@role)`**,** `=elorole list`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def elorole(self, ctx: commands.Context, option: str, *args):
        # // Get the current elo roles and check to make sure the server has under 20
        elo_roles: dict = await Settings(ctx.guild.id).get("elo_roles")

        # // Add a new elo role
        if option in ["add", "create", "new"]:
            # // Check if the user has enough permissions
            if not User.is_admin(ctx.guild, ctx.author):
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} you do not have enough permissions", 
                        color = 15158588
                ))
            
            # // Get the role
            role: discord.Role = ctx.guild.get_role(int(re.sub("\D","", args[0])))
            if role is None:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} please provide a valid role",
                        color = 15158588
                ))
            
            # // Check if the new elorole is below their own
            if role.position >= ctx.author.top_role.position or not ctx.author.guild_permissions.administrator:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} please choose a role lower than {ctx.author.top_role.mention}", 
                        color = 15158588
                ))
            
            # // Check if the server has reached the maximum amount of roles
            if len(elo_roles) >= 20:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"**[20/20]** {ctx.author.mention} maximum amount of roles reached", 
                        color=15158588
                ))
            
            # // Check if the elo role already exists
            if role.id in elo_roles:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} {role.mention} already exists", 
                        color = 15158588
                ))
            
            # // Add the new elo role into the database
            Settings(ctx.guild.id).add_elo_role(role.id, int(args[1]), 5, 2)
            
            # // Send the success embed
            return await ctx.send(
                embed = discord.Embed(
                    description = f"**[{len(elo_roles) + 1}/20]** {ctx.author.mention} {role.mention} will now be given at **{int(args[1])} elo**", 
                    color = 3066992
            ))

            
        # // Delete an existing elo role
        if option in ["remove", "delete", "del"]:
            # // Check if the user has enough permissions
            if not User.is_admin(ctx.guild, ctx.author):
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} you do not have enough permissions", 
                        color = 15158588
                ))
            
            # // Get the role
            role: discord.Role = ctx.guild.get_role(int(re.sub("\D","", args[0])))
            if role is None:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} please provide a valid role",
                        color = 15158588
                ))

            # // If the role is not an elo role
            if role.id not in elo_roles:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} {role.mention} is not an elo role", 
                        color = 15158588
                ))
            
            # // Delete the elo role from the cache and database
            await Settings(ctx.guild.id).delete_elo_role(ctx.guild.id, role.id)

            # // Return the success embed
            return await ctx.send(
                embed = discord.Embed(
                    description = f"**[{len(elo_roles) - 1}/20]** {ctx.author.mention} {role.mention} has been removed", 
                    color = 3066992
            ))

        
        # // List all of the elo roles
        if option in ["list", "show"]:
            description: str = ""

            # // Get all of the elo roles
            elo_roles: list = await SqlData.select_all(f"SELECT * FROM elo_roles WHERE guild_id = {ctx.guild.id} ORDER BY elo_level ASC")
            
            # // For each elo role
            for i in range(len(elo_roles)):
                role: discord.Role = ctx.guild.get_role(elo_roles[i][1])
                
                # // Add the role to the embed description
                if role is not None:
                    description += f'**{i + 1}:** {role.mention} [**{elo_roles[i][2]}**]\n'
                    continue

                # // Delete the elo role from the cache and database
                await Settings(ctx.guild.id).delete_elo_role(ctx.guild.id, elo_roles[i][1])

            # // Send the elo role list embed
            return await ctx.send(
                embed = discord.Embed(
                    title = f"Elo Roles ┃ {ctx.guild.name}", 
                    description = description, 
                    color = 33023
            ))
        
        
    # // MATCH REPORT / CANCEL / UNDO / SHOW COMMAND
    # /////////////////////////////////////////
    @commands.command(name="match", description='`=match report (match id) [blue/orange]`**,** `=match cancel (match id)`**,** `=match undo (match id)`**,** `=match show (match id)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def match(self, ctx:commands.Context, action: str, match_id: int, *args):
        if ctx.author.bot:
            return
        
        # // Get the match from the cache and make sure it's not invalid
        match_data: dict = Matches.find(ctx.guild.id, match_id)

        # // If the match is invalid
        if match_data is None:
            return discord.Embed(
                description = f"We were unable to find **Match #{match_id}**", 
                color = 15158588
            )
        
        # // Get the lobby id from the match data
        lobby_id: int = match_data["lobby_id"]
        
        # // Show the match
        if action in ["show"]:
            return await Matches.show(ctx.guild.id, match_id)
        
        # // Check if the user has the mod role
        if not User.is_mod(ctx.guild, ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
        # // REPORTING AN ONGOING MATCH
        if action in ["report"]:
            # // If the match is ongoing
            if len(args) <= 0 and match_data["status"] != "ongoing":
                return await ctx.send(
                    embed = discord.Embed(
                    description = f"{ctx.author.mention} this match has already been reported", 
                    color = 15158588
                ))

            # // Update the match
            Matches.update(ctx.guild.id, match_id, status="reported", winner=args[0])
            
            # // Get the orange team
            orange_team = match_data["orange_team"]
            orange_team.append(match_data["orange_cap"])

            # // Get the blue team
            blue_team = match_data["blue_team"]
            blue_team.append(match_data["blue_cap"])

            # // If team is the winner
            if "blue" in args[0]:
                # // Add a loss for each orange team member
                for user in orange_team:
                    user: discord.Member = User.verify(ctx.guild, user)
                    if user is not None:
                        await User.lose(user, lobby_id)

                # // Add a win for each blue team member
                for user in blue_team:
                    user: discord.Member = User.verify(ctx.guild, user)
                    if user is not None:
                        await User.win(user, lobby_id)

            # // If orange team is the winner
            if "orange" in args[0]:
                # // Add a win for each orange team member
                for user in orange_team:
                    user: discord.Member = User.verify(ctx.guild, user)
                    if user is not None:
                        await User.win(user, lobby_id)

                # // Add a win for each blue team member
                for user in blue_team:
                    user: discord.Member = User.verify(ctx.guild, user)
                    if user is not None:
                        await User.lose(user, lobby_id)
                        
            # // Send the match info the current channel
            await ctx.send(Matches.show(ctx.guild.id, match_id))

            # // Delete the match channels
            return await Matches.delete_category(ctx.guild.id, match_id)


        # // CANCELLING AN ONGOING MATCH
        elif action == "cancel":
            # // Check if the match is currently ongoing (eg: not already reported, etc.)
            if match_data["status"] != "ongoing":
                return await ctx.send(
                    embed = discord.Embed(
                    description = f"{ctx.author.mention} this match has already been reported", 
                    color = 15158588
                ))
            
            # // Update the match data
            Matches.update(ctx.guild.id, match_id, status="cancelled", winner="none")
            
            # // Send the match info embed
            await ctx.send(Matches.show(ctx.guild.id, match_id))

            # // Delete the match channels
            return await Matches.delete_category(ctx.guild.id, match_id)
        
    
        # // UNDOING A REPORTED MATCH
        elif action in ["undo"]:
            if match_data["status"] not in ["reported", "cancelled"]:
                return await ctx.send(
                    embed = discord.Embed(
                    description = f"{ctx.author.mention} this match hasn't been reported yet", 
                    color = 15158588
                ))
            
            # // Update the match status and winners
            Matches.update(ctx.guild.id, match_id, status="ongoing", winner="none")

            # // Add the orange team and it's captains
            orange_team = match_data["orange_team"]
            orange_team.append(match_data["orange_cap"])
            
            # // Add the blue team and it's captains
            blue_team = match_data["blue_team"]
            blue_team.append(match_data["blue_cap"])

            # // Remove the win from the blue team
            if match_data["winners"] == "blue":
                await Matches.undo(ctx, lobby_id, blue_team, orange_team)
                
            # // Remove the win from the orange team
            if match_data["winners"] == "orange":
                await Matches.undo(ctx, lobby_id, orange_team, blue_team)
            
            # // Send the match embed
            return await ctx.send(Matches.show(ctx.guild.id, match_id))


    # // SET PLAYERS STATS COMMAND
    # /////////////////////////////////
    @commands.command(name="set", description='`=set elo (@user) (amount)`**,** `=set wins (@user) (amount)`**,** `=set losses (@user) (amount)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set(self, ctx: commands.Context, action: str, user: discord.Member, amount: int):
        if ctx.author.bot:
            return
        
        # // Check if the cmd author has the mod role
        if not User.is_mod(ctx.guild, ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
        # // Get the users data from the cache
        if not Users.exists(ctx.guild.id, user.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{user.mention} is not registered", 
                    color = 15158588
            ))
        
        # // SET A PLAYERS ELO
        if action in ["elo", "points"]:
            # // Set the users elo
            await Users.update(ctx.guild.id, user.id, elo=amount)

            # // Get the users nick_name from the cache
            nick_name: str = Users.info(ctx.guild.id, user.id)["nick_name"]

            # // Edit the users nickname
            await Users.change_nickname(ctx.guild, user, f"{nick_name} [{amount}]")
            
        # // SET A PLAYERS WINS
        elif action in ["wins", "win"]:
            # // Set the users wins
            await Users.update(ctx.guild.id, user.id, wins=amount)
            
        # // SET A PLAYERS LOSSES
        elif action in ["losses", "lose", "loss"]:
            # // Set the users losses
            await Users.update(ctx.guild.id, user.id, losses=amount)

        # // Send the user's stats embed
        return await ctx.send(embed=Users.stats(user))
    


    # // SHOW THE LAST MATCH PLAYED COMMAND
    # /////////////////////////////////////////
    @commands.command(name="lastmatch", aliases=["lm"], description='`=lastmatch`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def lastmatch(self, ctx:commands.Context):
        if ctx.author.bot:
            return
        
        # // Get the last match id
        match_id: int = Matches.count(ctx.guild.id)
        return await ctx.send(embed=Matches.show(ctx.guild.id, match_id))


    # // REPLACE / SUB TWO PLAYERS COMMAND
    # /////////////////////////////////////////
    @commands.command(name="replace", aliases=["sub", "swap"], description='`=replace (@user to be replaced) (@user replacing) (match id)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def replace(self, ctx:commands.Context, user1:discord.Member, user2:discord.Member, match_id:int):
        if ctx.author.bot:
            return
        
        # // Check if the cmd author has the mod role
        if not User.is_mod(ctx.guild, ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions",
                    color = 15158588
            ))
        
        # // Get the match data from the cache
        match_data: dict = Matches.info(ctx.guild.id, match_id)
        
        # // Check match status
        if match_data["status"] in ["reported", "cancelled", "rollbacked"]:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this match has already been reported",
                    color = 15158588
            ))
        
        # // Get the blue and orange teams
        blue_team: list = match_data["blue_team"]
        orange_team: list = match_data["orange_team"]

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
        if ctx.author.bot:
            return 
        
        # // Register the mentioned user
        if len(args) > 0 and "@" in args[0]:
            # // Check if the user has the mod role
            if not User.is_mod(ctx.author):
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
    client.add_cog(EloCog(client))