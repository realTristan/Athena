from discord_components import *
from discord.ext import commands
import discord, asyncio, re
from functools import *
from _sql import *

# // Settings cog
class Settings(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    # // RETURN CORRESPONDING EMOJI TO SETTING
    # /////////////////////////////////////////
    def _guild_settings_status(self, option, row):
        # // MATCH CATEGORIES
        if option == "match_category":
            if row[2] == 1: # true
                return ["🟢", "Disable"]
            return ["🔴", "Enable"]

        # // MATCH LOGGING
        if option == "match_logging":
            if row[4] == 1: # false
                return ["🟢", "Disable"]
            return ["🔴", "Enable"]
        
        # // SELF RENAME
        if option == "self_rename":
            if row[7] == 1:
                return ["🟢", "Disable"]
            return ["🔴", "Enable"]


    # // RETURN CORRESPONDING EMOJI TO SETTING
    # /////////////////////////////////////////
    def _lobby_settings_status(self, option, row):
        # // MAP PICKING PHASE
        if option == "map_pick_phase":
            if row[2] == 1: # true
                return ["🟢", "Disable"]
            return ["🔴", "Enable"]

        # // TEAM PICKING PHASE
        if option == "team_pick_phase":
            if row[3] == 1: # true
                return ["🟢", "Disable"]
            return ["🔴", "Enable"]
        
        # // NEGATIVE ELO
        if option == "negative_elo":
            if row[7] == 1: # true
                return ["🟢", "Disable"]
            return ["🔴", "Enable"]
        
        
    # // CONVERT 0-1 TO FALSE-TRUE
    # /////////////////////////////////////
    def num_to_words(self, value:int):
        if value == 1:
            return 'ENABLED'
        return 'DISABLED'
    
    
    # // Check admin role or admin permissions
    # //////////////////////////////////////////
    async def check_admin_role(self, ctx: commands.Context):
        # // Get the admin role from settings
        admin_role = Cache.fetch(table="settings", guild=ctx.guild.id)[5]
        
        # // Check admin permissions
        if admin_role == 0 or ctx.author.guild_permissions.administrator:
            return ctx.author.guild_permissions.administrator
        return ctx.guild.get_role(admin_role) in ctx.author.roles
        
    # // ADD MAP TO THE DATABASE
    # /////////////////////////////////////////
    async def _add_map(self, ctx:commands.Context, map:str, lobby:int):
        maps = await SqlData.select_all(f"SELECT map FROM maps WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
        if not await SqlData.exists(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id} AND lobby_id = {lobby} AND map = '{map}'"):
            await SqlData.execute(f"INSERT INTO maps (guild_id, lobby_id, map) VALUES ({ctx.guild.id}, {lobby}, '{map}')")
            return await ctx.channel.send(embed=discord.Embed(description=f"**[{len(maps)+1}/20]** {ctx.author.mention} added **{map}** to the map pool", color=3066992))
        return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} **{map}** already exists", color=15158588))

    # // REMOVE MAP FROM THE DATABASE
    # /////////////////////////////////////////
    async def _del_map(self, ctx:commands.Context, map:str, lobby:int):
        if await SqlData.exists(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id} AND lobby_id = {lobby} AND map = '{map}'"):
            maps = await SqlData.select_all(f"SELECT map FROM maps WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
            await SqlData.execute(f"DELETE FROM maps WHERE map = '{map}' AND guild_id = {ctx.guild.id} AND lobby_id = {lobby}")
            return await ctx.channel.send(embed=discord.Embed(description=f"**[{len(maps)-1}/20]** {ctx.author.mention} removed **{map}** from the map pool", color=3066992))
        return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} **{map}** is not in the map pool", color=15158588))
    
    # // SET THE MOD ROLE
    # ////////////////////////
    @commands.command(name="modrole", description="`=modrole set @role, =modrole show, =modrole delete`")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 1, commands.BucketType.guild)
    async def modrole(self, ctx:commands.Context, *args):
        if args[0] in ["set", "create"]:
            role = ctx.guild.get_role(int(re.sub("\D","", args[1])))
            if role is not None:
                await SqlData.execute(f"UPDATE settings SET mod_role = {role.id} WHERE guild_id = {ctx.guild.id}")
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} successfully set the mod role to {role.mention}", color=3066992))
            else: raise Exception("Invalid role")
        
        elif args[0] in ["info", "show"]:
            role_id = await SqlData.select(f"SELECT mod_role FROM settings WHERE guild_id = {ctx.guild.id}")
            if role_id[0] != 0:
                role = ctx.guild.get_role(role_id[0])
                return await ctx.send(embed=discord.Embed(description=f"**Mod Role:** {role.mention}", color=33023))
            return await ctx.send(embed=discord.Embed(description=f"**Mod Role:** None", color=33023))
        
        elif args[0] in ["delete", "del", "reset", "remove"]:
            await SqlData.execute(f"UPDATE settings SET mod_role = 0 WHERE guild_id = {ctx.guild.id}")
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} successfully removed the mod role", color=3066992))
        else:
            raise Exception("Invalid option")
        
    # // SET THE ADMIN ROLE
    # ////////////////////////
    @commands.command(name="adminrole", description="`=adminrole set @role, =adminrole show, =adminrole delete`")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 1, commands.BucketType.guild)
    async def adminrole(self, ctx:commands.Context, *args):
        if args[0] in ["set", "create"]:
            role = ctx.guild.get_role(int(re.sub("\D","", args[1])))
            if role is not None:
                await SqlData.execute(f"UPDATE settings SET admin_role = {role.id} WHERE guild_id = {ctx.guild.id}")
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} successfully set the admin role to {role.mention}", color=3066992))
            else: raise Exception("Invalid role")
        
        elif args[0] in ["info", "show"]:
            role_id = await SqlData.select(f"SELECT admin_role FROM settings WHERE guild_id = {ctx.guild.id}")
            if role_id[0] != 0:
                role = ctx.guild.get_role(role_id[0])
                return await ctx.send(embed=discord.Embed(description=f"**Admin Role:** {role.mention}", color=33023))
            return await ctx.send(embed=discord.Embed(description=f"**Admin Role:** None", color=33023))
        
        elif args[0] in ["delete", "del", "reset", "remove"]:
            await SqlData.execute(f"UPDATE settings SET admin_role = 0 WHERE guild_id = {ctx.guild.id}")
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} successfully removed the admin role", color=3066992))
        else:
            raise Exception("Invalid option")
    
    
    # // GUILD LOBBIES COMMAND
    # /////////////////////////////
    @commands.command(name="lobby", description="`=lobby add`**,** `=lobby delete`**,** `=lobby list`**,** `=lobby settings`")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def lobby(self, ctx:commands.Context, action:str):
        if not ctx.author.bot:
            rows = await SqlData.select_all(f"SELECT lobby FROM lobbies WHERE guild_id = {ctx.guild.id}")
            if action in ["add", "create"]:
                if await self.check_admin_role(ctx):
                    if len(rows) < 10:
                        if not await SqlData.exists(f"SELECT * FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}"):
                            await SqlData.execute(f"INSERT INTO lobbies (guild_id, lobby) VALUES ({ctx.guild.id}, {ctx.channel.id})")
                            
                            if not await SqlData.exists(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}"):
                                await SqlData.execute(f"INSERT INTO lobby_settings (guild_id, lobby_id, map_pick_phase, team_pick_phase, win_elo, loss_elo, party_size, negative_elo, queue_size) VALUES ({ctx.guild.id}, {ctx.channel.id}, 0, 1, 5, 2, 1, 1, 10)")
                            return await ctx.send(embed=discord.Embed(description=f"**[{len(rows)+1}/10]** {ctx.author.mention} has created a new lobby **{ctx.channel.name}**", color=3066992))
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is already a lobby", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"**[10/10]** {ctx.author.mention} maximum amount of lobbies created", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
            
            # // DELETE AN EXISTING LOBBY
            if action in ["delete", "remove", "del"]:
                if await self.check_admin_role(ctx):
                    if await SqlData.exists(f"SELECT * FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}"):
                        await SqlData.execute(f"DELETE FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
                        await SqlData.execute(f"DELETE FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}")
                        return await ctx.send(embed=discord.Embed(description=f"**[{len(rows)-1}/10]** {ctx.author.mention} has removed the lobby **{ctx.channel.name}**", color=3066992))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
            
            if action in ["settings", "sets", "options", "opts", "setting"]:
                if not await self.check_admin_role(ctx):
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
                
                if not await SqlData.exists(f"SELECT * FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}"):
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))

                lobby_settings = await SqlData.select(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
                team_pick_phase = self._lobby_settings_status("team_pick_phase", lobby_settings)
                map_pick_phase = self._lobby_settings_status("map_pick_phase", lobby_settings)
                negative_elo = self._lobby_settings_status("negative_elo", lobby_settings)
                await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} ┃ **Ten Man's {ctx.channel.mention} Settings Menu**", color=33023),
                    components=[
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
                if len(rows) > 0:
                    embed=discord.Embed(title=f"Lobbies ┃ {ctx.guild.name}", color=33023)
                    for i in range(len(rows)):
                        try:
                            channel = ctx.guild.get_channel(int(rows[i][0]))
                            if channel is not None:
                                embed.add_field(name= f"{i+1}. " + channel.name, value=channel.mention)
                            else:
                                await SqlData.execute(f"DELETE FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {rows[i][0]}")
                                await SqlData.execute(f"DELETE FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {rows[i][0]}")
                        except Exception as e: print(f"Settings 208: {e}")
                    return await ctx.send(embed=embed)
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this server has no lobbies", color=15158588))
            
            # // SHOWS LOBBY INFO
            if action in ["info", "information", "about", "help"]:
                if await SqlData.exists(f"SELECT * FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}"):
                    rows = await SqlData.select(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
                    maps = await SqlData.select_all(f"SELECT map FROM maps WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
                    embed=discord.Embed(title=f"About #{ctx.channel.name}", color=33023)
                    embed.description = f"**Settings:**\n• Team Pick Phase: [**{self.num_to_words(rows[3])}**]\n• Map Pick Phase: [**{self.num_to_words(rows[2])}**]\n• Negative Elo: [**{self.num_to_words(rows[7])}**]\n• Win Elo: [**{rows[4]}**]\n• Loss Elo: [**{rows[5]}**]\n• Party Size: [**{rows[6]}**]\n• Queue Size: [**{rows[8]}**]\n\n**Maps:**\n"
                    embed.description = embed.description+"\n".join("• "+e[0] for e in maps)
                    return await ctx.send(embed=embed)
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
        
    # // ADD MAP COMMAND
    # /////////////////////////////////////////
    @commands.command(name="addmap", description="`=addmap (map name)`")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def addmap(self, ctx:commands.Context, map:str):
        if not ctx.author.bot:
            if await self.check_admin_role(ctx):
                if len((await SqlData.select_all(f"SELECT map FROM maps WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}"))) < 20:
                    if await SqlData.exists(f"SELECT * FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}"):
                        return await self._add_map(ctx, map, ctx.channel.id)
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"**[20/20]** {ctx.author.mention} maximum amount of maps reached", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
    # // DELETE MAP COMMAND
    # /////////////////////////////////////////
    @commands.command(name="delmap", aliases=["removemap", "deletemap"], description="`=delmap (map name)`")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def delmap(self, ctx:commands.Context, map:str):
        if not ctx.author.bot:
            if await self.check_admin_role(ctx):
                if await SqlData.exists(f"SELECT * FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}"):
                    return await self._del_map(ctx, map, ctx.channel.id)
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
    # // SHOW LIST OF MAPS COMMAND
    # /////////////////////////////////////////
    @commands.command(name="maps", description="`=maps`")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def maps(self, ctx:commands.Context):
        if not ctx.author.bot:
            if await SqlData.exists(f"SELECT * FROM lobbies WHERE guild_id = {ctx.guild.id} AND lobby = {ctx.channel.id}"):
                rows = await SqlData.select_all(f"SELECT map FROM maps WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
                return await ctx.send(embed=discord.Embed(title=f"Maps ┃ {ctx.guild.name}", description="\n".join(e[0] for e in rows), color=33023))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))

    # // SET THE REGISTER ROLE COMMAND
    # /////////////////////////////////////////
    @commands.command(name="regrole", description="`=regrole (@role)`")
    @commands.cooldown(1, 1, commands.BucketType.guild)
    async def regrole(self, ctx:commands.Context, role:discord.Role):
        if not ctx.author.bot:
            if await self.check_admin_role(ctx):
                if role < ctx.author.top_role or ctx.author.guild_permissions.administrator:
                    await SqlData.execute(f"UPDATE settings SET reg_role = {role.id} WHERE guild_id = {ctx.guild.id}")
                    return await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} set the register role to {role.mention}', color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} please choose a role lower than {ctx.author.top_role.mention}", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
    # // SHOW SETTINGS MENU COMMAND
    # /////////////////////////////////////////
    @commands.command(name="settings", aliases=["sets", "options"], description="`=settings`")
    @commands.cooldown(1, 1, commands.BucketType.guild)
    async def settings(self, ctx:commands.Context):
        if not ctx.author.bot:
            if not await SqlData.exists(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}"):
                await SqlData.execute(f"INSERT INTO settings (guild_id, reg_role, match_categories, reg_channel, match_logs, mod_role, admin_role, self_rename) VALUES ({ctx.guild.id}, 0, 0, 0, 0, 0, 0, 0)")
        
            if not await self.check_admin_role(ctx):
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
            
            settings = await SqlData.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
            match_category = self._guild_settings_status("match_category", settings)
            match_logging = self._guild_settings_status("match_logging", settings)
            self_rename = self._guild_settings_status("self_rename", settings)

            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} ┃ **Ten Man's Server Settings Menu**", color=33023),
                components=[
                    Select(
                        placeholder="View Settings",
                        options=[
                            SelectOption(emoji=f'🔵', label="Change Mod Role", value="change_mod_role"),
                            SelectOption(emoji=f'🔵', label="Change Admin Role", value="change_admin_role"),
                            SelectOption(emoji=f'🔵', label="Create Queue Embed", value="queue_embed"),
                            SelectOption(emoji=f'🔵', label="Change Register Role", value="change_reg_role"),
                            SelectOption(emoji=f'🔵', label="Change Register Channel", value="change_reg_channel"),
                            SelectOption(emoji=f'{self_rename[0]}', label=f"{self_rename[1]} Self Rename", value="self_rename"),
                            SelectOption(emoji=f'{match_logging[0]}', label=f"{match_logging[1]} Match Logging", value="match_logging"),
                            SelectOption(emoji=f'{match_category[0]}', label=f"{match_category[1]} Match Categories", value="match_category")
                        ])])

    # // SELECT MENU LISTENER
    # /////////////////////////////////////////
    @commands.Cog.listener()
    async def on_select_option(self, res:Interaction):
        if not res.author.bot:
            try:
                # // SELF RENAME
                if res.values[0] == "self_rename":
                    if await self.check_admin_role(res):
                        row = (await SqlData.select(f"SELECT self_rename FROM settings WHERE guild_id = {res.guild.id}"))[0]
                        if row == 0:
                            await SqlData.execute(f"UPDATE settings SET self_rename = 1 WHERE guild_id = {res.guild.id}")
                            return await res.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Self Rename**", color=3066992))

                        await SqlData.execute(f"UPDATE settings SET self_rename = 0 WHERE guild_id = {res.guild.id}")
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Self Rename**", color=3066992))
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))
                
                # // CHANGE MOD ROLE
                if res.values[0] == "change_admin_role":
                    if res.author.guild_permissions.administrator:
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} mention the role you want to use", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)
                        if "@" in str(c.content):
                            role = res.guild.get_role(int(re.sub("\D","", c.content)))
                            await SqlData.execute(f"UPDATE settings SET admin_role = {role.id} WHERE guild_id = {res.guild.id}")
                            return await res.send(embed=discord.Embed(description=f"{res.author.mention} successfully set the admin role to {role.mention}", color=3066992))
                        
                        await SqlData.execute(f"UPDATE settings SET admin_role = 0 WHERE guild_id = {res.guild.id}")
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} successfully set the admin role to None", color=3066992))
                
                # // CHANGE ADMIN ROLE
                if res.values[0] == "change_mod_role":
                    if res.author.guild_permissions.administrator:
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} mention the role you want to use", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)
                        if "@" in str(c.content):
                            role = res.guild.get_role(int(re.sub("\D","", c.content)))
                            await SqlData.execute(f"UPDATE settings SET mod_role = {role.id} WHERE guild_id = {res.guild.id}")
                            return await res.send(embed=discord.Embed(description=f"{res.author.mention} successfully set the mod role to {role.mention}", color=3066992))
                        
                        await SqlData.execute(f"UPDATE settings SET mod_role = 0 WHERE guild_id = {res.guild.id}")
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} successfully set the mod role to None", color=3066992))
                    
                
                # // CHANGE QUEUE SIZE
                if res.values[0] == "change_queue_size":
                    if await self.check_admin_role(res):
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} respond with the queue size **(4-20)**", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)
                        
                        if int(c.content) >= 4 and int(c.content) <= 20:
                            await SqlData.execute(f"UPDATE lobby_settings SET queue_size = {c.content} WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                            return await res.send(embed=discord.Embed(description=f"{res.author.mention} has set the queue size to **{c.content} players**", color=3066992))
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} please respond with a number from **4-20**", color=15158588))
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))
                
                # // MAP PICKING PHASE
                if res.values[0] == 'map_pick_phase':
                    if await self.check_admin_role(res):
                        row = (await SqlData.select(f"SELECT map_pick_phase FROM lobby_settings WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}"))[0]
                        if row == 0:
                            await SqlData.execute(f"UPDATE lobby_settings SET map_pick_phase = 1 WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                            return await res.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Map Picking Phase**", color=3066992))

                        await SqlData.execute(f"UPDATE lobby_settings SET map_pick_phase = 0 WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Map Picking Phase**", color=3066992))
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))

                # // MATCH LOGGING
                if res.values[0] == "match_logging":
                    if await self.check_admin_role(res):
                        row = (await SqlData.select(f"SELECT match_logs FROM settings WHERE guild_id = {res.guild.id}"))[0]
                        if row == 0:
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} mention the channel you want to use", color=33023))
                            c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)

                            if "#" in c.content:
                                channel = res.guild.get_channel(int(re.sub("\D","",str(c.content))))
                                if channel is not None:
                                    await SqlData.execute(f"UPDATE settings SET match_logs = {channel.id} WHERE guild_id = {res.guild.id}")
                                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Match Logging** in **{channel.mention}**", color=3066992))
                                return await res.send(embed=discord.Embed(description=f"{res.author.mention} we could not find the given channel", color=3066992))
                            return await res.send(embed=discord.Embed(description=f"{res.author.mention} invalid channel (please mention the channel)", color=15158588))

                        await SqlData.execute(f"UPDATE settings SET match_logs = 0 WHERE guild_id = {res.guild.id}")
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Match Logging**", color=3066992))
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))

                # // MATCH CATEGORIES
                if res.values[0] == 'match_category':
                    if await self.check_admin_role(res):
                        row = (await SqlData.select(f"SELECT match_categories FROM settings WHERE guild_id = {res.guild.id}"))[0]
                        if row == 0:
                            await SqlData.execute(f"UPDATE settings SET match_categories = 1 WHERE guild_id = {res.guild.id}")
                            return await res.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Match Categories**", color=3066992))

                        await SqlData.execute(f"UPDATE settings SET match_categories = 0 WHERE guild_id = {res.guild.id}")
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Match Categories**", color=3066992))
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))

                # // TEAM PICKING PHASE
                if res.values[0] == 'team_pick_phase':
                    if await self.check_admin_role(res):
                        row = (await SqlData.select(f"SELECT team_pick_phase FROM lobby_settings WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}"))[0]
                        if row == 0:
                            await SqlData.execute(f"UPDATE lobby_settings SET team_pick_phase = 1 WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                            return await res.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Team Picking Phase**", color=3066992))

                        await SqlData.execute(f"UPDATE lobby_settings SET team_pick_phase = 0 WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Team Picking Phase**", color=3066992))
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))

                # // CHANGE THE REGISTER ROLE
                if res.values[0] == "change_reg_role":
                    if res.author.guild_permissions.administrator:
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} mention the role you want to use", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)
                        if "@" in str(c.content):
                            role = res.guild.get_role(int(re.sub("\D","", c.content)))
                            await SqlData.execute(f"UPDATE settings SET reg_role = {role.id} WHERE guild_id = {res.guild.id}")
                            return await res.send(embed=discord.Embed(description=f"{res.author.mention} set the **Register Role** to {role.mention}", color=3066992))
                        
                        await SqlData.execute(f"UPDATE settings SET reg_role = 0 WHERE guild_id = {res.guild.id}")
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} set the **Register Role** to **None**", color=3066992))
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))

                # // ADD MAP
                if res.values[0] == "add_map":
                    if await self.check_admin_role(res):
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} respond with the map name", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)
                        return await self._add_map(res, c.content, res.channel.id)
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))

                # // REMOVE MAP
                if res.values[0] == "remove_map":
                    if await self.check_admin_role(res):
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} respond with the map name", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)
                        return await self._del_map(res, c.content, res.channel.id)
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))
                
                # // NEGATIVE ELO
                if res.values[0] == "negative_elo":
                    if await self.check_admin_role(res):
                        row = (await SqlData.select(f"SELECT negative_elo FROM lobby_settings WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}"))[0]
                        if row == 0:
                            await SqlData.execute(f"UPDATE lobby_settings SET negative_elo = 1 WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                            return await res.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Negative Elo**", color=3066992))

                        await SqlData.execute(f"UPDATE lobby_settings SET negative_elo = 0 WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Negative Elo**", color=3066992))
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))

                # // CHANGE THE REGISTER CHANNEL
                if res.values[0] == "change_reg_channel":
                    if await self.check_admin_role(res):
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} mention the channel you want to use", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)

                        if "<#" not in str(c.content):
                            await SqlData.execute(f"UPDATE settings SET reg_channel = 0 WHERE guild_id = {res.guild.id}")
                            return await res.send(embed=discord.Embed(description=f"{res.author.mention} set the **Register Channel** to **None**", color=3066992))

                        channel = res.guild.get_channel(int(re.sub("\D","",str(c.content))))
                        if channel is not None:
                            await SqlData.execute(f"UPDATE settings SET reg_channel = {channel.id} WHERE guild_id = {res.guild.id}")
                            return await res.send(embed=discord.Embed(description=f"{res.author.mention} set the **Register Channel** to {channel.mention}", color=3066992))
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} we could not find the given channel", color=3066992))
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))
                
                # // CHANGE THE ELO PER WIN
                if res.values[0] == "change_win_elo":
                    if await self.check_admin_role(res):
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} respond with the amount of elo you want to gain", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)

                        await SqlData.execute(f"UPDATE lobby_settings SET win_elo = {c.content} WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} has set the **Win Elo** to **{c.content}**", color=3066992))
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))
                    
                # // CHANGE THE ELO PER LOSS
                if res.values[0] == "change_loss_elo":
                    if await self.check_admin_role(res):
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} respond with the amount of elo you want to lose", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)

                        await SqlData.execute(f"UPDATE lobby_settings SET loss_elo = {c.content} WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} has set the **Loss Elo** to **{c.content}**", color=3066992))
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))

                # // QUEUE EMBED
                if res.values[0] == "queue_embed":
                    if await self.check_admin_role(res):
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} respond which lobby you want to use", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)
                        
                        channel = res.guild.get_channel(int(re.sub("\D","",str(c.content))))
                        if channel is not None:
                            if await SqlData.exists(f"SELECT * FROM lobbies WHERE guild_id = {res.guild.id} AND lobby = {channel.id}"):
                                await res.send(embed=discord.Embed(description=f"{res.author.mention} has created a new **Queue Embed**", color=3066992))
                                embed=discord.Embed(title=f'[0/10] {channel.name}', color=33023)
                                embed.set_footer(text=str(channel.id))

                                return await res.channel.send(embed=embed, components=[[
                                    Button(style=ButtonStyle.green, label='Join', custom_id='join_queue'),
                                    Button(style=ButtonStyle.red, label="Leave", custom_id='leave_queue')]])
                            return await res.send(embed=discord.Embed(description=f"{res.author.mention} that channel is not a lobby", color=15158588))
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} we could not find the given channel", color=3066992))
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))
                                
                # // CHANGE THE QUEUE PARTY SIZE
                if res.values[0] == "change_queue_party_size":
                    if await self.check_admin_role(res):
                        await res.send(embed=discord.Embed(description=f"{res.author.mention} respond with the maximum party size", color=33023))
                        c = await self.client.wait_for('message', check=lambda message: message.author == res.author and message.channel == res.channel, timeout=10)

                        await SqlData.execute(f"UPDATE lobby_settings SET party_size = {c.content} WHERE guild_id = {res.guild.id} AND lobby_id = {res.channel.id}")
                        return await res.send(embed=discord.Embed(description=f"{res.author.mention} has set the **Maximum Party Size** to **{c.content}**", color=3066992))
                    return await res.send(embed=discord.Embed(description=f"{res.author.mention} you do not have enough permissions", color=15158588))
            except asyncio.TimeoutError:
                return await res.send(embed=discord.Embed(description=f"{res.author.mention} you did not respond in time", color=15158588))
                
def setup(client: commands.Bot):
    client.add_cog(Settings(client))