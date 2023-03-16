from cache import Cache, Settings, Users, Lobby
from discord_components import *
from discord.ext import commands
import discord, asyncio, re

# // Settings cog
class SettingsCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    # // RETURN CORRESPONDING EMOJI TO SETTING
    # /////////////////////////////////////////
    def get_settings_option(self, option: str, settings: dict):
        if settings[option] == 1:
            return ["🟢", "Disable"]
        return ["🔴", "Enable"]
        
    # // CONVERT 0-1 TO ENABLED/DISABLED
    # /////////////////////////////////////
    def num_to_words(self, value:int):
        if value == 1:
            return 'ENABLED'
        return 'DISABLED'
    
    # // SET THE MOD ROLE
    # ////////////////////////
    @commands.command(name="modrole", description="`=modrole set @role, =modrole show, =modrole delete`")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 1, commands.BucketType.guild)
    async def modrole(self, ctx: commands.Context, *args):
        # // SET THE MOD ROLE
        if args[0] in ["set", "add"]:
            # // Get the role and check if it exists
            role: discord.Role = ctx.guild.get_role(int(re.sub("\D","", args[1])))
            if role is None:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} invalid role", 
                        color = 15158588
                ))
            
            # // Update the settings
            await Settings.update(ctx.guild.id, mod_role=role.id)

            # // Send the success embed
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} successfully set the mod role to {role.mention}", 
                    color = 3066992
            ))
        

        # // SHOW THE MOD ROLE
        elif args[0] in ["info", "show"]:
            # // Get the role
            role_id: int = Settings.get(ctx.guild.id, "mod_role")

            # // Check if the role exists
            if role_id == 0:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"**Mod Role:** None", 
                        color = 33023
                ))
            
            # // Get the role and send it to the channel
            role: discord.Role = ctx.guild.get_role(role_id)
            return await ctx.send(
                embed = discord.Embed(
                    description = f"**Mod Role:** {role.mention}", 
                    color = 33023
            ))


        # // REMOVE THE MOD ROLE
        elif args[0] in ["delete", "del", "reset", "remove"]:
            # // Update the settings
            await Settings.update(ctx.guild.id, mod_role=0)

            # // Send the success embed
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} successfully removed the mod role", 
                    color = 3066992
            ))
        
        # // Send the invalid option embed
        return await ctx.send(
            embed = discord.Embed(
                description = f"{ctx.author.mention} invalid option", 
                color = 15158588
        ))
        
    # // SET THE ADMIN ROLE
    # ////////////////////////
    @commands.command(name="adminrole", description="`=adminrole set @role, =adminrole show, =adminrole delete`")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 1, commands.BucketType.guild)
    async def adminrole(self, ctx: commands.Context, *args):
        # // SET THE ADMIN ROLE
        if args[0] in ["set", "create"]:
            # // Get the role
            role: discord.Role = ctx.guild.get_role(int(re.sub("\D","", args[1])))
            if role is None:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} invalid role", 
                        color = 15158588
                ))
            
            # // Update the settings
            await Settings.update(ctx.guild.id, admin_role=role.id)

            # // Send the success embed
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} successfully set the admin role to {role.mention}", 
                    color = 3066992
            ))
        
        # // SHOW THE ADMIN ROLE
        elif args[0] in ["info", "show"]:
            # // Get the role
            role_id: int = Settings.get(ctx.guild.id, "admin_role")
            if role_id == 0:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"**Admin Role:** None", 
                        color = 33023
                ))
            
            # // Send the admin role
            role: discord.Role = ctx.guild.get_role(role_id)
            return await ctx.send(
                embed = discord.Embed(
                    description = f"**Admin Role:** {role.mention}", 
                    color = 33023
            ))
        
        # // DELETE THE ADMIN ROLE
        elif args[0] in ["delete", "del", "reset", "remove"]:
            # // Update the settings
            await Settings.update(ctx.guild.id, admin_role=0)

            # // Send the success embed
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} successfully removed the admin role", 
                    color = 3066992
            ))
        
        # // Send the invalid option embed
        return await ctx.send(
            embed=discord.Embed(
                description=f"{ctx.author.mention} invalid option", 
                color=15158588
        ))
    
    
    # // GUILD LOBBIES COMMAND
    # /////////////////////////////
    @commands.command(name="lobby", description="`=lobby add`**,** `=lobby delete`**,** `=lobby list`**,** `=lobby settings`")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def lobby(self, ctx: commands.Context, action: str):
        if ctx.author.bot:
            return
        
        # // Get the amount of lobbies
        lobby_count: int = Lobby.count(ctx.guild.id)

        # // ADD A LOBBY
        if action in ["add", "create"]:
            # // If the user doesn't have admin role
            if not Users.is_admin(ctx.author):
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} you do not have enough permissions", 
                        color = 15158588
                ))
            
            # // If there's already 10 lobbies
            if lobby_count >= 10:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"**[10/10]** {ctx.author.mention} maximum amount of lobbies created", 
                        color = 15158588
                ))
            
            # // If the lobby already exists
            if Lobby.exists(ctx.guild.id, ctx.channel.id):
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} this channel is already a lobby", 
                        color = 15158588
                ))
            
            # // Create the new lobby
            await Lobby.create(ctx.guild.id, ctx.channel.id)

            # // Send the success embed
            return await ctx.send(
                embed = discord.Embed(
                    description = f"**[{lobby_count + 1}/10]** {ctx.author.mention} has created a new lobby **{ctx.channel.name}**", 
                    color = 3066992
            ))
        

        # // DELETE AN EXISTING LOBBY
        if action in ["delete", "remove", "del"]:
            # // If the user doesn't have admin role
            if not Users.is_admin(ctx.author):
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} you do not have enough permissions", 
                        color = 15158588
                ))
            
            # // If the lobby doesn't exist
            if not Lobby.exists(ctx.guild.id, ctx.channel.id):
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} this channel is not a lobby", 
                        color = 15158588
                ))

            # // Delete the lobby
            await Lobby.delete(ctx.guild.id, ctx.channel.id)

            # // Send the success embed
            return await ctx.send(
                embed = discord.Embed(
                    description = f"**[{lobby_count - 1}/10]** {ctx.author.mention} has removed the lobby **{ctx.channel.name}**", 
                    color = 3066992
            ))

        
        # // MODIFY LOBBY SETTINGS
        if action in ["settings", "sets", "options", "opts", "setting"]:
            if not Users.is_admin(ctx.author):
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} you do not have enough permissions",
                        color = 15158588
                ))
            
            if not Lobby.exists(ctx.guild.id, ctx.channel.id):
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} this channel is not a lobby", 
                        color = 15158588
                ))

            lobby_settings: dict = Lobby.get(ctx.guild.id, ctx.channel.id)
            team_pick_phase = self.get_settings_option("team_pick_phase", lobby_settings)
            map_pick_phase = self.get_settings_option("map_pick_phase", lobby_settings)
            negative_elo = self.get_settings_option("negative_elo", lobby_settings)

            
            # // Send the lobby settings menu
            await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} ┃ **Ten Man's {ctx.channel.mention} Settings Menu**", 
                    color = 33023
                ),
                components = [
                    Select(
                        placeholder="View Settings",
                        options=[
                            SelectOption(emoji=f'🔵', label="Add Map", value="add_map"),
                            SelectOption(emoji=f'🔵', label="Remove Map", value="remove_map"),
                            SelectOption(emoji=f'🔵', label="Change Queue Size", value="change_queue_size"),
                            SelectOption(emoji=f'🔵', label="Change Elo Per Win", value="change_win_elo"),
                            SelectOption(emoji=f'🔵', label="Change Elo Per Loss", value="change_loss_elo"),
                            SelectOption(emoji=f'🔵', label="Change Queue Party Size", value="change_queue_party_size"),
                            SelectOption(emoji=f'{negative_elo[0]}', label=f"{negative_elo[1]} Negative Elo", value="negative_elo"),
                            SelectOption(emoji=f'{map_pick_phase[0]}', label=f"{map_pick_phase[1]} Map Picking Phase", value="map_pick_phase"),
                            SelectOption(emoji=f'{team_pick_phase[0]}', label=f"{team_pick_phase[1]} Team Picking Phase", value="team_pick_phase")
            ])])
        
        # // SHOW ALL GUILD LOBBIES
        if action in ["show", "list"]:
            # // If there are no lobbies
            if lobby_count == 0:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} this server has no lobbies", 
                        color = 15158588
                ))
            
            # // Create the embed
            embed: discord.Embed = discord.Embed(
                title = f"Lobbies ┃ {ctx.guild.name}", 
                color = 33023
            )

            # // Get all the lobbies for the guild
            lobbies: list = Lobby.get_all(ctx.guild.id)

            # // Iterate over the lobbies
            for i, lobby in enumerate(lobbies):
                channel: discord.Channel = ctx.guild.get_channel(lobby)

                # // If the channel exists
                if channel is not None:
                    embed.add_field(name= f"{i + 1}. " + channel.name, value=channel.mention)
                    continue
                
                # // If the channel is None
                await Lobby.delete(ctx.guild.id, lobby)
                    
            # // Send the embed
            return await ctx.send(embed = embed)
        
        # // SHOWS LOBBY INFO
        if action in ["info", "information", "about", "help"]:
            # // If the lobby doesn't exist
            if not Lobby.exists(ctx.guild.id, ctx.channel.id):
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} this channel is not a lobby", 
                        color = 15158588
                ))
            
            # // Fetch the lobby settings and maps
            lobby_settings: dict = Lobby.get(ctx.guild.id, ctx.channel.id)
            team_pick_phase: str = self.num_to_words(lobby_settings['team_pick_phase'])
            map_pick_phase: str = self.num_to_words(lobby_settings['map_pick_phase'])
            negative_elo: str = self.num_to_words(lobby_settings['negative_elo'])
            win_elo: int = lobby_settings.get("win_elo")
            loss_elo: int = lobby_settings.get("loss_elo")
            party_size: int = lobby_settings.get("party_size")
            queue_size: int = lobby_settings.get("queue_size")
            maps: list = lobby_settings.get("maps")

            # // Send the embed
            return await ctx.send(
                embed = discord.Embed(
                    title = f"About #{ctx.channel.name}", 
                    color = 33023,
                    description = f"**Settings:**\n• Team Pick Phase: [**{team_pick_phase}**]\n• Map Pick Phase: [**{map_pick_phase}**]\n• Negative Elo: [**{negative_elo}**]\n• Win Elo: [**{win_elo}**]\n• Loss Elo: [**{loss_elo}**]\n• Party Size: [**{party_size}**]\n• Queue Size: [**{queue_size}**]\n\n**Maps:**\n" + "\n".join("• " + m for m in maps)
            ))
                
        
    # // ADD MAP COMMAND
    # /////////////////////////////////////////
    @commands.command(name="addmap", description="`=addmap (map name)`")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def addmap(self, ctx: commands.Context, map: str):
        if ctx.author.bot:
            return
        
        # // Check if the user has admin role
        if not Users.is_admin(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
        # // If the lobby doesn't exist
        if not Lobby.exists(ctx.guild.id, ctx.channel.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby", 
                    color = 15158588
            ))
        
        # // Fetch the maps
        maps: list = Lobby.get(ctx.guild.id, ctx.channel.id, "maps")
        if len(maps) >= 20:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"**[20/20]** {ctx.author.mention} maximum number of maps reached", 
                    color = 15158588
            ))

        # // If the map already exists
        if map in maps:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this map already exists", 
                    color = 15158588
            ))

        # // Add the map
        await Lobby.add_map(ctx.guild.id, ctx.channel.id, map)

        # // Send the embed
        return await ctx.send(
            embed = discord.Embed(
                description = f"{ctx.author.mention} has added **{map}** to the map pool", 
                color = 33023
        ))

    # // DELETE MAP COMMAND
    # /////////////////////////////////////////
    @commands.command(name="delmap", aliases=["removemap", "deletemap"], description="`=delmap (map name)`")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def delmap(self, ctx: commands.Context, map:str):
        if ctx.author.bot:
            return
        
        # // Check if the user has admin role
        if not Users.is_admin(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
        # // If the lobby doesn't exist
        if not Lobby.exists(ctx.guild.id, ctx.channel.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby", 
                    color = 15158588
            ))
        
        # // Fetch the maps
        maps: list = Lobby.get(ctx.guild.id, ctx.channel.id, "maps")

        # // If the map already exists
        if map not in maps:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this map isn't in the map pool", 
                    color = 15158588
            ))

        # // Delete the map
        await Lobby.delete_map(ctx.guild.id, ctx.channel.id, map)

        # // Send the embed
        return await ctx.send(
            embed = discord.Embed(
                description = f"{ctx.author.mention} has removed **{map}** from the map pool", 
                color = 33023
        ))
        

    # // SHOW LIST OF MAPS COMMAND
    # /////////////////////////////////////////
    @commands.command(name="maps", description="`=maps`")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def maps(self, ctx: commands.Context):
        if ctx.author.bot:
            return
        
        # // If the lobby doesn't exist
        if not Lobby.exists(ctx.guild.id, ctx.channel.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby", 
                    color = 15158588
            ))
        
        # // Fetch the maps
        maps: list = Lobby.get(ctx.guild.id, ctx.channel.id, "maps")

        # // If there are no maps
        description: str = "None"
        if len(maps) > 0:
            description = "\n".join(m[0].upper() + m[1:].lower() for m in maps)

        # // Return the maps embed
        return await ctx.send(
            embed = discord.Embed(
                title = f"Maps ┃ {ctx.channel.name}", 
                description = description, 
                color = 33023
            )
        )
        
    # // SET THE REGISTER ROLE COMMAND
    # /////////////////////////////////////////
    @commands.command(name="regrole", description="`=regrole (@role)`")
    @commands.cooldown(1, 1, commands.BucketType.guild)
    async def regrole(self, ctx: commands.Context, role:discord.Role):
        if ctx.author.bot:
            return
        
        # // Check if the user has admin role
        if not Users.is_admin(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
        # // Check if the role is lower than the author's top role
        if role >= ctx.author.top_role or not ctx.author.guild_permissions.administrator:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you cannot set a role higher than your top role", 
                    color = 15158588
            ))
        
        # // Update the register role
        await Settings.update(ctx.guild.id, reg_role=role.id)

        # // Send the success embed
        return await ctx.send(
            embed = discord.Embed(
                description = f"{ctx.author.mention} set the register role to {role.mention}", 
                color = 33023
        ))


    # // SHOW SETTINGS MENU COMMAND
    # /////////////////////////////////////////
    @commands.command(name="settings", aliases=["sets", "options"], description="`=settings`")
    @commands.cooldown(1, 1, commands.BucketType.guild)
    async def settings(self, ctx: commands.Context):
        if ctx.author.bot:
            return
        
        # // If the settings table doesn't exist
        if not Settings.exists(ctx.guild.id):
            await Settings.setup(ctx.guild.id)

        # // Check if the user has admin role
        if not Users.is_admin(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
        # // Get the guild settings
        settings: dict = Settings.get(ctx.guild.id)
        match_categories: list = self.get_settings_option("match_categories", settings)
        match_logs: list = self.get_settings_option("match_logs", settings)
        self_rename: list = self.get_settings_option("self_rename", settings)

        # // Send the settings menu
        await ctx.send(
            embed = discord.Embed(
                description = f"{ctx.author.mention} ┃ **Ten Man's Server Settings Menu**",
                color = 33023
            ),
            components = [
                Select(
                    placeholder="View Settings",
                    options=[
                        SelectOption(emoji=f'🔵', label="Change Mod Role", value="change_mod_role"),
                        SelectOption(emoji=f'🔵', label="Change Admin Role", value="change_admin_role"),
                        SelectOption(emoji=f'🔵', label="Create Queue Embed", value="queue_embed"),
                        SelectOption(emoji=f'🔵', label="Change Register Role", value="change_reg_role"),
                        SelectOption(emoji=f'🔵', label="Change Register Channel", value="change_reg_channel"),
                        SelectOption(emoji=f'{self_rename[0]}', label=f"{self_rename[1]} Self Rename", value="self_rename"),
                        SelectOption(emoji=f'{match_logs[0]}', label=f"{match_logs[1]} Match Logging", value="match_logging"),
                        SelectOption(emoji=f'{match_categories[0]}', label=f"{match_categories[1]} Match Categories", value="match_category")
        ])])


    # // SELECT MENU LISTENER
    # /////////////////////////////////////////
    @commands.Cog.listener()
    async def on_select_option(self, res: discord.Interaction):
        if res.author.bot:
            return
        try:
            # // SELF RENAME
            if res.values[0] == "self_rename":
                if not Users.is_admin(res.author):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get the self rename status
                self_rename: int = Settings.get(res.guild.id, "self_rename")

                # // If the self rename is disabled, enable it
                if self_rename == 0:
                    # // Update the settings
                    await Settings.update(res.guild.id, self_rename=1)

                    # // Send the success embed
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} has enabled **Self Rename**", 
                            color = 33023
                    ))
                
                # // Update the settings. (self rename is enabled, so disable it)
                await Settings.update(res.guild.id, self_rename=0)

                # // Send the success embed
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} has disabled **Self Rename**", 
                        color = 33023
                ))

            # // CHANGE MOD ROLE
            if res.values[0] == "change_admin_role":
                if not res.author.guild_permissions.administrator:
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get the admin role
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} mention the role you want to use", 
                        color = 33023
                ))

                # // Wait for the user to mention a role
                msg: discord.Message = await self.client.wait_for(
                    'message',
                    timeout = 10,
                    check = lambda message: message.author == res.author and message.channel == res.channel, 
                )
                
                # // If the user mentioned a role
                if "@" in str(msg.content):
                    # // Get the role
                    role: discord.Role = res.guild.get_role(int(re.sub("\D","", msg.content)))

                    # // Update the admin role
                    await Settings.update(res.guild.id, admin_role=role.id)

                    # // Send the success embed
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} successfully set the admin role to {role.mention}", 
                            color = 3066992
                    ))
                
                # // If the user didn't mention a role... set the admin role to none (0)
                await Settings.update(res.guild.id, admin_role=0)

                # // Send the embed
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} you did not mention a role", 
                        color = 15158588
                ))


            # // CHANGE ADMIN ROLE
            if res.values[0] == "change_mod_role":
                if not res.author.guild_permissions.administrator:
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get the mod role
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} mention the role you want to use", 
                        color = 33023
                ))

                # // Wait for the user to mention a role
                msg: discord.Message = await self.client.wait_for(
                    'message',
                    timeout = 10,
                    check = lambda message: message.author == res.author and message.channel == res.channel, 
                )

                # // If the user mentioned a role
                if "@" in str(msg.content):
                    role: discord.Role = res.guild.get_role(int(re.sub("\D","", msg.content)))

                    # // Update the mod role
                    await Settings.update(res.guild.id, mod_role=role.id)
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} successfully set the mod role to {role.mention}", 
                            color = 3066992
                    ))
                
                # // If the user did not mention a role... set the mod role to none (0)
                await Settings.update(res.guild.id, mod_role=0)

                # // Send the embed
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} you did not mention a role", 
                        color = 15158588
                ))
            

            # // CHANGE QUEUE SIZE
            if res.values[0] == "change_queue_size":
                if not Users.is_admin(res.author):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get the queue size
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} respond with the queue size", 
                        color = 33023
                ))

                # // Wait for the user to respond
                msg: discord.Message = await self.client.wait_for(
                    'message',
                    timeout = 10,
                    check = lambda message: message.author == res.author and message.channel == res.channel, 
                )

                # // If the queue size is valid
                queue_size: int = int(msg.content)
                if queue_size < 4 and queue_size > 20:
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} the queue size must be between 4 and 20", 
                            color = 15158588
                    ))
                
                # // Update the settings
                await Settings.update(res.guild.id, queue_size=queue_size)

                # // Send the success embed
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} successfully set the queue size to {queue_size}", 
                        color = 3066992
                ))

            # // MAP PICKING PHASE
            if res.values[0] == 'map_pick_phase':
                if not Users.is_admin(res.author):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get whether the map picking phase is enabled or disabled
                map_pick_phase: int = Settings.get(res.guild.id, "map_pick_phase")
                
                # // If map picking phase is disabled, enable it
                if map_pick_phase == 0:
                    await Settings.update(res.guild.id, map_pick_phase=1)
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} has enabled **Map Picking Phase**", 
                            color = 3066992
                    ))
                
                # // Set the map picking phase to disabled
                await Settings.update(res.guild.id, map_pick_phase=0)
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} has disabled **Map Picking Phase**", 
                        color = 15158588
                ))

            # // MATCH LOGGING
            if res.values[0] == "match_logging":
                if not Users.is_admin(res.author):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get whether the match logging is enabled or disabled
                match_logs: int = Settings.get(res.guild.id, "match_logs")

                # // If match logging is disabled
                if match_logs == 0:
                    await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} mention the channel you want to use", 
                            color = 33023
                    ))

                    # // Wait for the user to mention a channel
                    msg: discord.Message = await self.client.wait_for(
                        'message',
                        timeout = 10,
                        check = lambda message: message.author == res.author and message.channel == res.channel, 
                    )

                    # // If the user mentioned a channel
                    if "#" not in msg.content:
                        return await res.send(
                            embed = discord.Embed(
                                description = f"{res.author.mention} you did not mention a channel", 
                                color = 15158588
                        ))
                    
                    # // Get the channel
                    channel: discord.Channel = res.guild.get_channel(
                        int(re.sub("\D", "", str(msg.content)))
                    )

                    # // If the channel is not valid
                    if channel is None:
                        return await res.send(
                            embed = discord.Embed(
                                description = f"{res.author.mention} you did not mention a valid channel", 
                                color = 15158588
                        ))
                    
                    # // Update the settings
                    await Settings.update(res.guild.id, match_logs=channel.id)
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} has enabled **Match Logging**", 
                            color = 3066992
                    ))
                
                # // Set the match logging to disabled
                await Settings.update(res.guild.id, match_logs=0)
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} has disabled **Match Logging**", 
                        color = 15158588
                ))

            # // MATCH CATEGORIES
            if res.values[0] == 'match_category':
                if not Users.is_admin(res.author):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get whether the match categories is enabled or disabled
                match_categories: int = Settings.get(res.guild.id, "match_categories")

                # // If match categories is disabled
                if match_categories == 0:
                    await Settings.update(res.guild.id, match_categories=1)
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} has enabled **Match Categories**", 
                            color = 3066992
                    ))
                
                # // Set the match categories to disabled
                await Settings.update(res.guild.id, match_categories=0)
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} has disabled **Match Categories**", 
                        color = 15158588
                ))

            # // TEAM PICKING PHASE
            if res.values[0] == 'team_pick_phase':
                if not Users.is_admin(res.author):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get whether the team picking phase is enabled or disabled
                team_pick_phase: int = Settings.get(res.guild.id, "team_pick_phase")
                
                # // If team picking phase is disabled
                if team_pick_phase == 0:
                    await Settings.update(res.guild.id, team_pick_phase=1)
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} has enabled **Team Picking Phase**", 
                            color = 3066992
                    ))
                
                # // Set the team picking phase to disabled
                await Settings.update(res.guild.id, team_pick_phase=0)
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} has disabled **Team Picking Phase**", 
                        color = 15158588
                ))

            # // CHANGE THE REGISTER ROLE
            if res.values[0] == "change_reg_role":
                if not res.author.guild_permissions.administrator:
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get the register role
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} mention the role you want to use", 
                        color = 33023
                ))

                # // Wait for the user to mention a role
                msg: discord.Message = await self.client.wait_for(
                    'message',
                    timeout = 10,
                    check = lambda message: message.author == res.author and message.channel == res.channel, 
                )

                # // If the user mentioned a role
                if "@" in str(msg.content):
                    role: discord.Role = res.guild.get_role(int(re.sub("\D","", msg.content)))
                    if role is None:
                        return await res.send(
                            embed = discord.Embed(
                                description = f"{res.author.mention} you did not mention a valid role", 
                                color = 15158588
                        ))
                    
                    # // Update the settings
                    await Settings.update(res.guild.id, reg_role=role.id)
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} set the **Register Role** to **{role.mention}**", 
                            color = 3066992
                    ))
                
                # // If the user did not mention a role, set it to 0
                await Settings.update(res.guild.id, reg_role=0)
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} you did not mention a role", 
                        color = 15158588
                ))

            # // ADD MAP
            if res.values[0] == "add_map":
                if not Users.is_admin(res.author):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get the map name
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} respond with the map name", 
                        color = 33023
                ))

                # // Wait for the user to send a map
                msg: discord.Message = await self.client.wait_for(
                    'message',
                    timeout = 10,
                    check = lambda message: message.author == res.author and message.channel == res.channel, 
                )

                # // Add the map
                return await Lobby.add_map(res.guild.id, res.channel.id, msg.content)
            
            # // REMOVE MAP
            if res.values[0] == "remove_map":
                if not Users.is_admin(res.author):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get the map name
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} respond with the map name", 
                        color = 33023
                ))

                # // Wait for the user to send a map
                msg: discord.Message = await self.client.wait_for(
                    'message',
                    timeout = 10,
                    check = lambda message: message.author == res.author and message.channel == res.channel, 
                )

                # // Remove the map
                return await Lobby.delete_map(res.guild.id, res.channel.id, msg.content)
            
            # // NEGATIVE ELO
            if res.values[0] == "negative_elo":
                if not Users.is_admin(res.author):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get whether the negative elo is enabled or disabled
                negative_elo: int = Settings.get(res.guild.id, "negative_elo")

                # // If negative elo is disabled
                if negative_elo == 0:
                    await Settings.update(res.guild.id, negative_elo=1)
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} has enabled **Negative Elo**", 
                            color = 3066992
                    ))
                
                # // Set the negative elo to disabled
                await Settings.update(res.guild.id, negative_elo=0)
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} has disabled **Negative Elo**", 
                        color = 15158588
                ))
            
            # // CHANGE THE REGISTER CHANNEL
            if res.values[0] == "change_reg_channel":
                if not Users.is_admin(res.author):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get the register channel
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} mention the channel you want to use", 
                        color = 33023
                ))

                # // Wait for the user to mention a channel
                msg: discord.Message = await self.client.wait_for(
                    'message',
                    timeout = 10,
                    check = lambda message: message.author == res.author and message.channel == res.channel, 
                )

                # // If the user did not mention a channel
                if "<#" not in str(msg.content):
                    await Settings.update(res.guild.id, reg_channel=0)
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you did not mention a channel", 
                            color = 15158588
                    ))
                
                # // If the user mentioned a channel
                channel: discord.Channel = res.guild.get_channel(int(re.sub("\D","",str(msg.content))))
                if channel is None:
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you did not mention a valid channel", 
                            color = 15158588
                    ))
                
                # // Update the register channel
                await Settings.update(res.guild.id, reg_channel=channel.id)
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} set the **Register Channel** to **{channel.mention}**", 
                        color = 3066992
                ))
            
            # // CHANGE THE ELO PER WIN
            if res.values[0] == "change_win_elo":
                if not Users.is_admin(res.author):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get the win elo
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} respond with the win elo", 
                        color = 33023
                ))

                # // Wait for the user to send a win elo
                msg: discord.Message = await self.client.wait_for(
                    'message',
                    timeout = 10,
                    check = lambda message: message.author == res.author and message.channel == res.channel, 
                )

                # // If the win elo is not a number
                if not msg.content.isdigit():
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you did not send a number", 
                            color = 15158588
                    ))
                
                # // Update the win elo
                win_elo: int = int(msg.content)
                await Lobby.update(res.guild.id, res.channel.id, win_elo=win_elo)

                # // Send the embed
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} set the **Win Elo** to **{win_elo}**", 
                        color = 3066992
                ))
            

            # // CHANGE THE ELO PER LOSS
            if res.values[0] == "change_loss_elo":
                if not Users.is_admin(res.author):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get the loss elo
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} respond with the loss elo", 
                        color = 33023
                ))

                # // Wait for the user to send a loss elo
                msg: discord.Message = await self.client.wait_for(
                    'message',
                    timeout = 10,
                    check = lambda message: message.author == res.author and message.channel == res.channel, 
                )

                # // If the loss elo is not a number
                if not msg.content.isdigit():
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you did not send a number", 
                            color = 15158588
                    ))
                
                # // Update the loss elo
                loss_elo: int = int(msg.content)

                # // Update the loss elo
                await Lobby.update(res.guild.id, res.channel.id, loss_elo=loss_elo)

                # // Send the embed
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} set the **Loss Elo** to **{loss_elo}**", 
                        color = 3066992
                ))
            
            # // CHANGE THE QUEUE PARTY SIZE
            if res.values[0] == "change_queue_party_size":
                if not Users.is_admin(res.author):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get the queue party size
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} respond with the maximum party size", 
                        color = 33023
                ))

                # // Wait for the user to send a queue party size
                msg: discord.Message = await self.client.wait_for(
                    'message',
                    timeout = 10,
                    check = lambda message: message.author == res.author and message.channel == res.channel, 
                )

                # // If the queue party size is not a number
                if not msg.content.isdigit():
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you did not send a number", 
                            color = 15158588
                    ))
                
                # // Update the queue party size
                party_size: int = int(msg.content)
                await Lobby.update(res.guild.id, res.channel.id, party_size=party_size)
                
                # // Send the embed
                return await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} set the **Queue Party Size** to **{party_size}**", 
                        color = 3066992
                ))
            
            # // QUEUE EMBED
            if res.values[0] == "queue_embed":
                if not Users.is_admin(res.author):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you do not have enough permissions", 
                            color = 15158588
                    ))
                
                # // Get the lobby
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} respond with the lobby channel", 
                        color = 33023
                ))

                # // Wait for the user to send a lobby channel
                msg: discord.Message = await self.client.wait_for(
                    'message',
                    timeout = 10,
                    check = lambda message: message.author == res.author and message.channel == res.channel, 
                )

                # // Get the channel
                channel: discord.Channel = res.guild.get_channel(int(re.sub("\D","",str(msg.content))))
                if channel is None:
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} that is not a valid channel", 
                            color = 15158588
                    ))
                
                # // Check if the channel is a lobby
                if not Lobby.exists(res.guild.id, channel.id):
                    return await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} that is not a lobby",
                            color = 15158588
                    ))
                
                # // Create the embed
                await res.send(
                    embed = discord.Embed(
                        description=f"{res.author.mention} has created a new **Queue Embed**", 
                        color=3066992
                ))
                embed: discord.Embed = discord.Embed(
                    title = f'[0/10] {channel.name}', 
                    color = 33023
                )
                embed.set_footer(text=str(channel.id))

                # // Return the queue embed
                return await res.channel.send(embed=embed, components=[[
                    Button(style=ButtonStyle.green, label='Join', custom_id='join_queue'),
                    Button(style=ButtonStyle.red, label="Leave", custom_id='leave_queue')
                ]])
        
        # // If the user did not respond in time
        except asyncio.TimeoutError:
            return await res.send(
                embed = discord.Embed(
                    description = f"{res.author.mention} you did not respond in time", 
                    color = 15158588
            ))
                


def setup(client: commands.Bot):
    client.add_cog(SettingsCog(client))