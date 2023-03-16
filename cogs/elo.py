from cache import Settings, Users, Lobby, Database, Matches
from discord_components import *
from discord.ext import commands
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
        elo_roles: dict = Settings.get(ctx.guild.id, "elo_roles")
        if elo_roles is None:
            elo_roles = {}

        # // Add a new elo role
        if option in ["add", "create", "new"]:
            # // Check if the user has enough permissions
            if not Users.is_admin(ctx.author):
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
            elo_level: int = int(args[1])
            await Settings.create_elo_role(ctx.guild.id, role.id, elo_level, 5, 2)
            
            # // Send the success embed
            return await ctx.send(
                embed = discord.Embed(
                    description = f"**[{len(elo_roles)}/20]** {ctx.author.mention} {role.mention} will now be given at **{elo_level} elo**", 
                    color = 3066992
            ))

            
        # // Delete an existing elo role
        if option in ["remove", "delete", "del"]:
            # // Check if the user has enough permissions
            if not Users.is_admin(ctx.author):
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
            await Settings.delete_elo_role(ctx.guild.id, role.id)

            # // Return the success embed
            return await ctx.send(
                embed = discord.Embed(
                    description = f"**[{len(elo_roles)}/20]** {ctx.author.mention} {role.mention} has been removed", 
                    color = 3066992
            ))

        
        # // List all of the elo roles
        if option in ["list", "show"]:
            description: str = ""

            # // Get all of the elo roles
            elo_roles: list = await Database.select_all(f"SELECT * FROM elo_roles WHERE guild_id = {ctx.guild.id} ORDER BY elo_level ASC")
            
            # // For each elo role
            for i in range(len(elo_roles)):
                role: discord.Role = ctx.guild.get_role(elo_roles[i][1])
                
                # // Add the role to the embed description
                if role is not None:
                    description += f'**{i + 1}:** {role.mention} [**{elo_roles[i][2]}**]\n'
                    continue

                # // Delete the elo role from the cache and database
                await Settings.delete_elo_role(ctx.guild.id, elo_roles[i][1])

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
    async def match(self, ctx: commands.Context, action: str, match_id: int, *args):
        if ctx.author.bot:
            return
        
        # // Get the match from the cache and make sure it's not invalid
        match_data: dict = Matches.get(ctx.guild.id, match_id)

        # // If the match is invalid
        if match_data is None:
            return discord.Embed(
                description = f"We were unable to find **Match #{match_id}**", 
                color = 15158588
            )
        
        # // Get the lobby id from the match data
        lobby_id: int = match_data.get("lobby_id")
        
        # // Show the match
        if action in ["show"]:
            return await Matches.embed(ctx.guild.id, match_id)
        
        # // Check if the user has the mod role
        if not Users.is_mod(ctx.author):
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
            await Matches.update(ctx.guild.id, match_id, status="reported", winner=args[0])
            
            # // Get the orange team
            orange_team: list = match_data.get("orange_team")
            orange_team.append(match_data["orange_cap"])

            # // Get the blue team
            blue_team: list = match_data.get("blue_team")
            blue_team.append(match_data["blue_cap"])

            # // If team is the winner
            if "blue" in args[0]:
                # // Add a loss for each orange team member
                for user in orange_team:
                    user: discord.Member = Users.verify(ctx.guild, user)
                    if user is not None:
                        await Users.lose(user, lobby_id)

                # // Add a win for each blue team member
                for user in blue_team:
                    user: discord.Member = Users.verify(ctx.guild, user)
                    if user is not None:
                        await Users.win(user, lobby_id)

            # // If orange team is the winner
            if "orange" in args[0]:
                # // Add a win for each orange team member
                for user in orange_team:
                    user: discord.Member = Users.verify(ctx.guild, user)
                    if user is not None:
                        await Users.win(user, lobby_id)

                # // Add a win for each blue team member
                for user in blue_team:
                    user: discord.Member = Users.verify(ctx.guild, user)
                    if user is not None:
                        await Users.lose(user, lobby_id)
                        
            # // Send the match info the current channel
            await ctx.send(Matches.embed(ctx.guild.id, match_id))

            # // Delete the match channels
            return await Matches.delete_category(ctx.guild, match_id)


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
            await Matches.update(ctx.guild.id, match_id, status="cancelled", winner="none")
            
            # // Send the match info embed
            await ctx.send(Matches.embed(ctx.guild.id, match_id))

            # // Delete the match channels
            return await Matches.delete_category(ctx.guild, match_id)
        
    
        # // UNDOING A REPORTED MATCH
        elif action == "undo":
            if match_data["status"] not in ["reported", "cancelled"]:
                return await ctx.send(
                    embed = discord.Embed(
                    description = f"{ctx.author.mention} this match hasn't been reported yet", 
                    color = 15158588
                ))
            
            # // Update the match status and winners
            await Matches.update(ctx.guild.id, match_id, status="ongoing", winner="none")

            # // Add the orange team and it's captains
            orange_team: list = match_data.get("orange_team")
            orange_team.append(match_data["orange_cap"])
            
            # // Add the blue team and it's captains
            blue_team: list = match_data.get("blue_team")
            blue_team.append(match_data["blue_cap"])

            # // Remove the win from the blue team
            if match_data["winners"] == "blue":
                await Matches.undo(ctx.guild, lobby_id, blue_team, orange_team)
                
            # // Remove the win from the orange team
            if match_data["winners"] == "orange":
                await Matches.undo(ctx.guild, lobby_id, orange_team, blue_team)
            
            # // Send the match embed
            return await ctx.send(Matches.embed(ctx.guild.id, match_id))


    # // SET PLAYERS STATS COMMAND
    # /////////////////////////////////
    @commands.command(name="set", description='`=set elo (@user) (amount)`**,** `=set wins (@user) (amount)`**,** `=set losses (@user) (amount)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def set(self, ctx: commands.Context, action: str, user: discord.Member, amount: int):
        if ctx.author.bot:
            return
        
        # // Check if the cmd author has the mod role
        if not Users.is_mod(ctx.author):
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
            nick_name: str = Users.get(ctx.guild.id, user.id).get("nick_name")

            # // Edit the users nickname
            await Users.change_nickname(user, f"{nick_name} [{amount}]")
            
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
    async def lastmatch(self, ctx: commands.Context):
        if ctx.author.bot:
            return
        
        # // Get the last match id
        match_id: int = Matches.count(ctx.guild.id)
        return await ctx.send(embed=Matches.embed(ctx.guild.id, match_id))


    # // REPLACE / SUB TWO PLAYERS COMMAND
    # /////////////////////////////////////////
    @commands.command(name="replace", aliases=["sub", "swap"], description='`=replace (@user to be replaced) (@user replacing) (match id)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def replace(self, ctx: commands.Context, user1: discord.Member, user2: discord.Member, match_id: int):
        if ctx.author.bot:
            return
        
        # // Check if the cmd author has the mod role
        if not Users.is_mod(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions",
                    color = 15158588
            ))
        
        # // Get the match data from the cache
        match_data: dict = Matches.get(ctx.guild.id, match_id)
        lobby_id: int = match_data.get("lobby_id")
        
        # // Check match status
        if match_data["status"] in ["reported", "cancelled", "rollbacked"]:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this match has already been reported",
                    color = 15158588
            ))
        
        # // Get the blue and orange teams
        blue_team: list = match_data.get("blue_team")
        orange_team: list = match_data.get("orange_team")

        # // Get the captains
        blue_cap: int = match_data.get("blue_cap")
        orange_cap: int = match_data.get("orange_cap")

        # // Replace the orange team captain
        if user1.id == orange_cap and user2.id != orange_cap:
            await Matches.update(ctx.guild.id, lobby_id, match_id, orange_cap=user2.id)
            
        # // Replace the blue team captain
        elif user1.id == blue_cap and user2.id != blue_cap:
            await Matches.update(ctx.guild.id, lobby_id, match_id, blue_cap=user2.id)
            
        # // Replace a player from the orange team
        elif user1.id in orange_team and user2.id not in orange_team:
            # // Replace the user1 with user2 in the orange team
            index: int = orange_team.index(user1.id)
            orange_team[index] = user2.id

            # // Set the orange team captain
            orange_team_str: str = ','.join(str(e) for e in orange_team)
            
            # // Update the match
            await Matches.update(ctx.guild.id, lobby_id, match_id, orange_team=orange_team_str)
            
        # // Replace a player from the blue team
        elif user1.id in blue_team and user2.id not in blue_team:
            # // Replace the user1 with user2 in the blue team
            index: int = blue_team.index(user1.id)
            blue_team[index] = user2.id

            # // Set the blue team captain
            blue_team_str: str = ','.join(str(e) for e in blue_team)
            
            # // Update the match
            await Matches.update(ctx.guild.id, lobby_id, match_id, blue_team=blue_team_str)
        
        # // If the user1 is not in the match
        else:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} player(s) not found/error", 
                    color = 15158588
            ))
        
        # // Send the success embed
        return await ctx.send(
            embed = discord.Embed(
                title = f"Match #{match_id}", 
                description = f"{ctx.author.mention} replaced {user1.mention} with {user2.mention}", 
                color = 3066992
        ))
    
    
    # // Modify your own nickname
    @commands.command(name="rename", description='`=rename (name)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def rename(self, ctx: commands.Context, name: str):
        if ctx.author.bot:
            return
        
        # // Check if the user is not a mod nor admin
        if not Users.is_mod(ctx.author):
            if Settings.get(ctx.guild.id, "self_rename") == 0:
                return await ctx.send(
                    embed = discord.Embed(
                    description = f"{ctx.author.mention} self renaming is not enabled", 
                    color = 15158588
                ))
        
        # // Get the user from the database and make sure the result is valid
        user_info: dict = Users.get(ctx.guild.id, ctx.author.id)
        if user_info is None:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} is not registered", 
                    color = 15158588
            ))
        
        # // Update the users nickname
        await Users.update(ctx.guild.id, ctx.author.id, user_name=name)
        
        # // Update the users nickname
        await Users.change_nickname(ctx.author, f"{name} [{user_info['elo']}]")

        # // Send the embeds
        return await ctx.send(
            embed = discord.Embed(
                description = f'{ctx.author.mention} renamed to **{name}**', 
                color = 3066992
        ))
            

    # // FORCE CHANGE A PLAYER'S USERNAME COMMAND
    # ////////////////////////////////////////////
    @commands.command(name="forcerename", aliases=["fr"], description='`=forcerename (@user) (name)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def forcerename(self, ctx: commands.Context, user:discord.Member, name:str):
        if ctx.author.bot:
            return
        
        # // Check if the user has the mod role
        if not Users.is_mod(ctx.author):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
        # // Get the user info
        user_info: dict = Users.get(ctx.guild.id, user.id)
        if user_info is None:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} is not registered", 
                    color = 15158588
            ))
        
        # // Update the users nickname
        await Users.update(ctx.guild.id, user.id, user_name=name)

        # // Update the users nickname
        await Users.change_nickname(user, f"{name} [{user_info['elo']}]")

        # // Send the embeds
        return await ctx.send(
            embed = discord.Embed(
                description = f'{ctx.author.mention} renamed {user.mention} to **{name}**',
                color = 3066992
        ))


    # // REGISTER USER INTO THE DATABASE COMMAND
    # ///////////////////////////////////////////
    @commands.command(name="register", aliases=["reg"], description='`=register (name)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def register(self, ctx: commands.Context, *args):
        if ctx.author.bot:
            return 
        
        # // Get the user
        user: discord.Member = ctx.author
        
        # // Register the message author
        if len(args) == 0:
            # // Get the name
            name: str = ctx.author.name
            if len(args) > 0: name = args[0]
                
            # // If the user doesn't already exist
            if Users.exists(ctx.guild.id, ctx.author.id):
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} is already registered", 
                        color = 15158588
                ))
            
            # // Register the user
            await Users.register(user, name)

            # // Edit the users nickname
            await Users.change_nickname(user, f"{name} [0]")
            
            # // Send the embeds
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{user.mention} has been registered as **{name}**", 
                    color = 3066992
            ))
        
        # // Register the mentioned user
        elif len(args) > 0 and "@" in args[0]:
            # // Check if the user has the mod role
            if not Users.is_mod(ctx.author):
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} you do not have enough permissions", 
                        color = 15158588
                ))
            
            # // Get the user
            user: discord.Member = ctx.guild.get_member(int(re.sub("\D","", args[0])))
            if user is None:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} user not found", 
                        color = 15158588
                ))
            
            # // Make sure user is not a bot
            if user.bot:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} you cannot register a bot", 
                        color = 15158588
                ))
            
            # // Check whether the user already exists
            if Users.exists(ctx.guild.id, user.id):
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{user.mention} is already registered", 
                        color = 15158588
                ))
            
            # // Modify the name
            name: str = user.name
            if len(args) > 1: name = args[1]
                
            # // Register the user
            await Users.register(user, name)

            # // Edit the users nickname
            await Users.change_nickname(user, f"{name} [0]")
            
            # // Send the embeds
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{user.mention} has been registered as **{name}**", 
                    color = 3066992
            ))

    
    # // UNREGISTER AN USER
    # ////////////////////////////////////////////////
    @commands.command(name="unregister", aliases=["unreg"], description='`=unreg (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def unregister(self, ctx: commands.Context, user:discord.Member):
        if ctx.author.bot:
            return
        
        # // Check if the user has admin role
        if not Users.is_admin(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
        # // Make sure the provided user exists
        if not Users.exists(ctx.guild.id, user.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{user.mention} is not registered",
                    color = 15158588
            ))
        
        # // Unregister the user
        await Users.delete(ctx.guild.id, user.id)
        
        # // Send the embeds
        return await ctx.send(
            embed = discord.Embed(
                description = f"{ctx.author.mention} unregistered {user.mention}", 
                color = 3066992
        ))


    # // GIVES AN USER A WIN COMMAND
    # /////////////////////////////////////////
    @commands.command(name="win", description='`=win (@users)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def win(self, ctx: commands.Context, users: commands.Greedy[discord.Member]):
        if ctx.author.bot:
            return
        
        # // Check if the user has the mod role
        if not Users.is_mod(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
        
        # // If the lobby is valid
        if not Lobby.exists(ctx.guild.id, ctx.channel.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby", 
                    color = 15158588
            ))
        
        # // Make sure the author provided users
        if len(users) <= 0:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} please mention atleast one player", 
                    color = 15158588
            ))
        
        # // Iterate over the users
        for user in users:
            await ctx.send(embed = await Users.win(user, ctx.channel.id))
            await ctx.send(embed = Users.stats(user))
            
        # // Send the embeds
        return await ctx.send(
            embed = discord.Embed(
                description = f"{ctx.author.mention} has successfully added wins", 
                color = 3066992
        ))


    # // GIVES AN USER A LOSS COMMAND
    # /////////////////////////////////////////
    @commands.command(name="lose", description='`=lose (@users)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def lose(self, ctx: commands.Context, users: commands.Greedy[discord.Member]):
        if ctx.author.bot:
            return
        
        # // Check if the author has mod role
        if not Users.is_mod(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions",
                    color = 15158588
            ))
        
        # // If the lobby is valid
        if not Lobby.exists(ctx.guild.id, ctx.channel.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby",
                    color = 15158588
            ))
        
        # // Make sure the author provided users
        if len(users) <= 0:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} please mention atleast one player",
                    color = 15158588
            ))
        
        # // Iterate over the users
        for user in users:
            await ctx.send(embed = await Users.lose(user, ctx.channel.id))
            await ctx.send(embed = Users.stats(user))
            
        # // Send the embeds
        return await ctx.send(
            embed = discord.Embed(
                description = f"{ctx.author.mention} has successfully added losses", 
                color = 3066992
        ))


    # // SHOW YOUR OR ANOTHER PLAYER'S STATS COMMAND
    # ////////////////////////////////////////////////
    @commands.command(name="stats", description='`=stats`**,** `=stats (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def stats(self, ctx: commands.Context, *args):
        if ctx.author.bot:
            return
        
        # // Default user
        user: discord.Member = ctx.author

        # // Get stats of another user
        if len(args) > 0 and "@" in args[0]:
            user = ctx.guild.get_member(int(re.sub("\D","", args[0])))
            if user is None:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} unknown player", 
                        color = 15158588
                ))
            
        # // Send the user stats
        return await ctx.send(embed = Users.stats(user))


    # // RESET AN USERS STATS COMMAND
    # /////////////////////////////////////////
    @commands.command(name="reset", description='`=reset all`**,** `=reset (@user)`')
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def reset(self, ctx: commands.Context, args: str):
        if ctx.author.bot:
            return
        
        # // Check if the author has admin role
        if not Users.is_admin(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions",
                    color = 15158588
            ))
            
        # // RESET EVERY PLAYERS STATS
        if args == "all":
            # // For each member in the guild
            for user in ctx.guild.members:
                if user.bot:
                    continue

                # // Check if the user is registered
                if not Users.exists(user):
                    continue

                # // Reset the users stats
                await Users.reset(ctx.guild.id, user.id)
            
            # // Send success embed
            return await ctx.send(
                embed = discord.Embed(
                    title = "Reset Stats", 
                    description = f"{ctx.author.mention} has reset every players stats", 
                    color = 3066992
            ))
    
    
        # // RESET THE MENTIONED USERS STATS
        elif "<@" in args:
            # // Get the user
            user: discord.Member= ctx.guild.get_member(int(re.sub("\D","", args)))
            user_name: str = Users.get(ctx.guild.id, user.id).get("user_name")
            
            # // Make sure user is not invalid
            if user_name is None:
                return await ctx.send(embed=discord.Embed(title="Reset Stats", description=f"{user.mention} is not registered", color=15158588))
            
            # // Reset the users stats
            await Users.reset(ctx.guild.id, user.id)

            # // Update the users name
            await Users.change_nickname(user, f"{user_name} [0]")
            
            # // Send the embeds
            return await ctx.send(
                embed = discord.Embed(
                    title = "Reset Stats", 
                    description = f"{ctx.author.mention} has reset {user.mention}'s stats", 
                    color = 3066992
            ))

    
    # // SHOW GUILD'S LEADERBOARD COMMAND
    # /////////////////////////////////////////
    @commands.command(name="leaderboard", aliases=["lb"], description='`=leaderboard`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def leaderboard(self, ctx: commands.Context):
        if ctx.author.bot:
            return
        
        # // Get the users from the database
        users: list = await Database.select_all(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} ORDER BY elo DESC")
        users_str: str = ""
        user_count: int = 0
        
        # // For each user in rows
        for i in range(len(users)):
            user: discord.Member = await Users.verify(ctx.guild, users[i][1])
            
            # // If the member exists
            if user is None:
                continue

            # // Increase counts and add to users string
            user_count += 1
            users_str += f'**{user_count}:** {user.mention} [**{users[i][3]}**]\n'
                
            # // Make sure only 20 members are displayed
            if user_count >= 20: 
                break

        # // Return the leaderboard
        return await ctx.send(
            embed = discord.Embed(
                title = f"Leaderboard ┃ {ctx.guild.name}", 
                description = users_str, 
                color = 33023
        ))
        
        
    # // ROLLBACK EVERY MATCH AN USER WAS IN
    # //////////////////////////////////////////
    @commands.command(name="rollback", aliases=["rb"], description='`=rollback (user id)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def rollback(self, ctx: commands.Context, user: int):
        '''
        REMOVE THE WIN IF CHEATER IS ON THE WINNING TEAM THEN REMOVE LOSS FOR OPPOSITE TEAM
        IF THE CHEATER IS NOT ON THE WINNING TEAM, THEN THE MATCH STILL COUNTS 
        (RAINBOW SIX SIEGE ROLLBACK SYSTEM)
        '''
        if ctx.author.bot:
            return
        
        # // Check if the user has admin role
        if not Users.is_admin(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions",
                    color = 15158588
            ))
        
        # // Get all of the matches by the guild
        matches: dict = Matches.get(ctx.guild.id)

        # // For each match
        for match in matches:
            if match["status"] in ["ongoing", "cancelled", "rollbacked"]:
                continue

            # // Blue team
            blue_team: list = match.get("blue_team")
            blue_team.append(match["blue_cap"])

            # // Orange team
            orange_team: list = match.get("orange_team")
            orange_team.append(match["orange_cap"])

            # // Get the lobby id
            lobby_id: int = match.get("lobby_id")

            # // Check if the user is in either of the teams
            if user in blue_team or user in orange_team:
                # // Check the match winners (in this case it's orange)
                if match["winners"] == "orange" and user in orange_team:
                    await Matches.undo(ctx.guild.id, lobby_id, orange_team, blue_team)
                
                # // Check the match winners (in this case it's blue)
                if match["winners"] == "blue" and user in blue_team:
                    await Matches.undo(ctx.guild.id, lobby_id, blue_team, orange_team)
                
                # // Update the match status
                await Matches.update(ctx.guild.id, lobby_id, match["match_id"], status="rollbacked")
                
                # // Send match rollback embed
                await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} Match **#{match[1]}** has been rollbacked", 
                        color = 3066992
                ))

        # // Send success embed
        return await ctx.send(
            embed = discord.Embed(
                description = f"{ctx.author.mention} has successfully rollbacked all matches with the user **{user}**",
                color = 3066992
        ))
            

    # // BUTTON CLICK LISTENER
    # /////////////////////////////////////////
    @commands.Cog.listener()
    async def on_button_click(self, res: discord.Interaction):
        if res.author.bot:
            return
        
        # // Check if the button is in the list
        if res.component.id in ['blue_report', 'orange_report', 'match_cancel']:
            # // Check if the user has the mod role
            if not Users.is_mod(res.author):
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} you do not have enough permissions", 
                        color = 15158588
                ))
            
            # // Get the match id
            match_id: int = int(str(res.message.embeds[0].title).replace("Match #", ""))
            lobby_id: int = int(res.message.embeds[0].footer.text)
            
            # // Get the match data and lobby settings
            match_data: dict = Matches.get(res.guild.id, match_id)

            # // Check match status
            if match_data.get("status") != "ongoing":
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} this match has already been reported", 
                        color = 15158588
                ))

                # // Delete the original embed
                await res.message.delete()

                # // Show the new match data
                await res.channel.send(embed = await Matches.embed(res.guild.id, match_id))

                # // Delete the match channels
                return await Matches.delete_category(res.guild, match_id)

            # // Create the blue team list and append the team captain
            blue_team: list = res.message.embeds[0].fields[5].value.split("\n")
            blue_team.append(int(re.sub("\D","", res.message.embeds[0].fields[2].value)))

            # // Create the orange team list and append the team captain
            orange_team: list = res.message.embeds[0].fields[3].value.split("\n")
            orange_team.append(int(re.sub("\D","", res.message.embeds[0].fields[0].value)))

            # // CANCEL THE MATCH
            if res.component.id == "match_cancel":
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} has cancelled **Match #{match_id}**", 
                        color = 3066992
                ))

                # // Update the match status and winners
                await Matches.update(res.guild.id, lobby_id, match_id, status="cancelled", winners="none")

            # // REPORT BLUE TEAM WIN
            if res.component.id == 'blue_report':
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} has reported **Match #{match_id}**", 
                        color = 3066992
                ))
                
                # // Update the match status and winners
                await Matches.update(res.guild.id, lobby_id, match_id, status="reported", winners="blue")
                
                # // Add a win to each blue team member
                for user in blue_team:
                    user: discord.Member = Users.verify(res.guild, user)
                    if user is not None:
                        await Users.win(user, lobby_id)

                # // Add a loss to each orange team member
                for user in orange_team:
                    user: discord.Member = Users.verify(res.guild, user)
                    if user is not None:
                        await Users.lose(user, lobby_id)

            
            # // REPORT ORANGE TEAM WIN
            if res.component.id == 'orange_report':
                # // Send reported embed
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} has reported **Match #{match_id}**", 
                        color = 3066992
                ))

                # // Update the match status and winners
                await Matches.update(res.guild.id, lobby_id, match_id, status="reported", winners="orange")

                # // Add a win to each orange team member
                for user in orange_team:
                    user: discord.Member = Users.verify(res.guild, user)
                    if user is not None:
                        await Users.win(user, lobby_id)

                # // Add a loss to each blue team member
                for user in blue_team:
                    user: discord.Member = Users.verify(res.guild, user)
                    if user is not None:
                        await Users.lose(user, lobby_id)


# // Setup the cog
def setup(client: commands.Bot):
    client.add_cog(EloCog(client))