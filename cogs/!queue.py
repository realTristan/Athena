import discord, random, time, asyncio, re
from discord_components import *
from discord.ext import commands
from discord.utils import get
import datetime as datetime
from functools import *
from _sql import *

class Queue(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.data = {}

    # Reset guilds variables function
    def _reset(self, ctx:commands.Context, lobby):
        self.data[ctx.guild.id][lobby] = {"queue": [], "blue_cap": "", "blue_team": [], "orange_cap": "", "orange_team": [], "pick_logic": [], "map": "None", "parties": {}, "state": "queue"}

    # Clean a players name to look more professional
    def _clean_name(self, name):
        return str(name[0]).upper() + str(name[1:]).lower()
    
    
    # Check if a member is still in the server
    async def _check_member(self, ctx:commands.Context, member_id:int):
        member = ctx.guild.get_member(member_id)
        if member is None:
            if Cache.exists(table="users", guild=ctx.guild.id, key=member_id):
                await Cache.delete(
                    table="users", guild=ctx.guild.id, key=member_id, 
                    sqlcmds=[f"DELETE FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {member_id}"]
                )
        return member
    
    
    # Check if channel is a valid queue lobby
    async def is_valid_lobby(self, ctx:commands.Context, lobby: int):
        if ctx.guild.id not in self.data:
            self.data[ctx.guild.id] = {}
            
        lobbies = Cache.fetch(table="lobby_settings", guild=ctx.guild.id).keys()
        if lobby in lobbies:
            if lobby not in self.data[ctx.guild.id]:
                self._reset(ctx, lobby)
            return True
        return False
    
    
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


    # Add other party members to the queue
    async def _check_party(self, ctx:commands.Context, user, lobby):
        for party in self.data[ctx.guild.id][lobby]["parties"]:
            if user.id in self.data[ctx.guild.id][lobby]["parties"][party] and party != user.id:
                return False

        if user.id in self.data[ctx.guild.id][lobby]["parties"]:
            lobby_settings = Cache.fetch(table="lobby_settings", guild=ctx.guild.id, key=lobby)
            if len(self.data[ctx.guild.id][lobby]["parties"][user.id]) + len(self.data[ctx.guild.id][lobby]["queue"]) <= lobby_settings[6]:
                for player in self.data[ctx.guild.id][lobby]["parties"][user.id][1:]:
                    member = await self._check_member(ctx, player)
                    if member is not None:
                        await self._join(ctx, member, lobby)
                return True
            return False
        return True
    
    
    # Send match logs to the given match logs channel
    async def _match_log(self, ctx:commands.Context, embed:discord.Embed):
        settings = Cache.fetch(table="settings", guild=ctx.guild.id)
        if settings[2] != 0:
            channel = ctx.guild.get_channel(settings[2])
            if channel is None:
                settings[3] = 0
                return (await Cache.update(
                    table="settings", guild=ctx.guild.id, data=settings, 
                    sqlcmds=[f"UPDATE settings SET match_logs = 0 WHERE guild_id = {ctx.guild.id}"]
                ))
            return await channel.send(
                embed=embed,
                components=[[
                    Button(style=ButtonStyle.blue, label="Blue", custom_id='blue_report'),
                    Button(style=ButtonStyle.blue, label="Orange", custom_id='orange_report'),
                    Button(style=ButtonStyle.red, label="Cancel", custom_id='match_cancel')
                ]])
                

    # Create the match category function
    async def _match_category(self, ctx:commands.Context, match_id, lobby):
        settings = Cache.fetch(table="settings", guild=ctx.guild.id)
        if settings[1] == 1:
            if not get(ctx.guild.categories, name=f'Match #{match_id}'):
                # Creating category and setting permissions
                category = await ctx.guild.create_category(f'Match #{match_id}')
                await category.set_permissions(ctx.guild.default_role, connect=False, send_messages=False)

                # Creating channels inside category
                await ctx.guild.create_text_channel(f"match-{match_id}", category=category)
                await ctx.guild.create_voice_channel(f'🔹 Team ' + self.data[ctx.guild.id][lobby]["blue_cap"].name, category=category)
                await ctx.guild.create_voice_channel(f"🔸 Team " + self.data[ctx.guild.id][lobby]['orange_cap'].name, category=category)

                # /Create the teams
                blue_team = self.data[ctx.guild.id][lobby]["blue_team"]
                blue_team.append(self.data[ctx.guild.id][lobby]["blue_cap"])
                orange_team = self.data[ctx.guild.id][lobby]["orange_team"]
                orange_team.append(self.data[ctx.guild.id][lobby]["orange_cap"])
                self._reset(ctx, lobby)

                # Edit the permissions for each player in the teams
                for user in orange_team:
                    await category.set_permissions(user, connect=True, send_messages=True)

                for _user in blue_team:
                    await category.set_permissions(_user, connect=True, send_messages=True)


    # Match logging function
    async def _match(self, ctx:commands.Context, lobby):
        orange_team = ','.join(str(e.id) for e in self.data[ctx.guild.id][lobby]['orange_team'])
        blue_team = ','.join(str(e.id) for e in self.data[ctx.guild.id][lobby]['blue_team'])
        count = len(Cache.fetch(table="matches", guild=ctx.guild.id))+1
        await Cache.update(
            sqlcmds=[f"INSERT INTO matches (guild_id, match_id, lobby_id, map, orange_cap, orange_team, blue_cap, blue_team, status, winners) VALUES ({ctx.guild.id}, {count}, {lobby}, '{self.data[ctx.guild.id][lobby]['map']}', '{self.data[ctx.guild.id][lobby]['orange_cap'].id}', '{orange_team}', '{self.data[ctx.guild.id][lobby]['blue_cap'].id}', '{blue_team}', 'ongoing', 'none')"],
            table="matches", guild=ctx.guild.id, key=count, 
            data=[
                lobby, self.data[ctx.guild.id][lobby]['map'], self.data[ctx.guild.id][lobby]['orange_cap'].id, 
                orange_team, self.data[ctx.guild.id][lobby]['blue_cap'].id, blue_team, 'ongoing', 'none'
            ]
        )


    # Create team pick logic function
    async def _pick_logic(self, ctx:commands.Context, lobby):
        for _ in range(round(len(self.data[ctx.guild.id][lobby]["queue"]) / 2)):
            self.data[ctx.guild.id][lobby]["pick_logic"].append(self.data[ctx.guild.id][lobby]["blue_cap"])
            self.data[ctx.guild.id][lobby]["pick_logic"].append(self.data[ctx.guild.id][lobby]["orange_cap"])

        if len(self.data[ctx.guild.id][lobby]["queue"]) > len(self.data[ctx.guild.id][lobby]["pick_logic"]):
            self.data[ctx.guild.id][lobby]["pick_logic"].append(self.data[ctx.guild.id][lobby]["orange_cap"])


    # Embed generator function (for queue)
    async def _embeds(self, ctx:commands.Context, lobby):
        # Queue phase embed
        if self.data[ctx.guild.id][lobby]["state"] == "queue":
            current_queue = "None"
            if len(self.data[ctx.guild.id][lobby]["queue"]) != 0:
                current_queue = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id][lobby]["queue"])
            settings = Cache.fetch(table="lobby_settings", guild=ctx.guild.id, key=lobby)
            return await ctx.send(embed=discord.Embed(title=f"[{len(self.data[ctx.guild.id][lobby]['queue'])}/{settings[6]}] {ctx.channel.name}", description=current_queue, color=33023))

        # Team picking phase embed
        if self.data[ctx.guild.id][lobby]["state"] == "pick":
            orange_team="None"
            blue_team="None"
            if len(self.data[ctx.guild.id][lobby]["orange_team"]) != 0:
                orange_team = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id][lobby]["orange_team"])

            if len(self.data[ctx.guild.id][lobby]["blue_team"]) != 0:
                blue_team = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id][lobby]["blue_team"])

            embed=discord.Embed(title="Team Picking Phase", color=33023)
            embed.add_field(name="Orange Captain", value=self.data[ctx.guild.id][lobby]["orange_cap"].mention)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=self.data[ctx.guild.id][lobby]["blue_cap"].mention)
            embed.add_field(name="Orange Team", value=orange_team)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value=blue_team)
            embed.add_field(name="Available Players", value="\n".join(str(e.mention) for e in self.data[ctx.guild.id][lobby]["queue"]))
            await ctx.send(embed=embed)
            return await ctx.send(f"**{self.data[ctx.guild.id][lobby]['pick_logic'][0].mention} it is your turn to pick (=pick [@user])**")

        # Map picking phase embed
        if self.data[ctx.guild.id][lobby]["state"] == "maps":
            maps = Cache.fetch(table="maps", guild=ctx.guild.id, key=lobby)
            embed=discord.Embed(title="Map Picking Phase", color=33023)
            embed.add_field(name="Orange Captain", value=self.data[ctx.guild.id][lobby]["orange_cap"].mention)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=self.data[ctx.guild.id][lobby]["blue_cap"].mention)
            embed.add_field(name="Orange Team", value='\n'.join(str(p.mention) for p in self.data[ctx.guild.id][lobby]["orange_team"]))
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value='\n'.join(str(p.mention) for p in self.data[ctx.guild.id][lobby]["blue_team"]))
            embed.add_field(name="Available Maps", value="\n".join(m for m in maps))
            await ctx.send(embed=embed)
            return await ctx.send(f"**{self.data[ctx.guild.id][lobby]['blue_cap'].mention} select a map to play (=pickmap [map])**")

        # Final match up embed
        if self.data[ctx.guild.id][lobby]["state"] == "final":
            count = len(Cache.fetch(table="matches", guild=ctx.guild.id))
            embed=discord.Embed(title=f"Match #{len(count)+1}", description=f"**Map:** {self.data[ctx.guild.id][lobby]['map']}", color=33023)
            embed.add_field(name="Orange Captain", value=self.data[ctx.guild.id][lobby]["orange_cap"].mention)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=self.data[ctx.guild.id][lobby]["blue_cap"].mention)
            embed.add_field(name="Orange Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id][lobby]["orange_team"]))
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id][lobby]["blue_team"]))
            embed.set_footer(text=str(lobby))
            await ctx.send(embed=embed)

            await self._match(ctx, lobby)
            await self._match_log(ctx, embed)
            await self._match_category(ctx, len(count)+1, lobby)
            self._reset(ctx, lobby)


    # When the queue reaches max capacity function
    async def _start(self, ctx:commands.Context, lobby):
        settings = Cache.fetch(table="lobby_settings", guild=ctx.guild.id, key=lobby)
        
        # Create team captains (blue)
        blue_cap = random.choice(self.data[ctx.guild.id][lobby]["queue"])
        self.data[ctx.guild.id][lobby]["blue_cap"] = blue_cap
        self.data[ctx.guild.id][lobby]["queue"].remove(blue_cap)
        
        # Create team captains (orange)
        orange_cap = random.choice(self.data[ctx.guild.id][lobby]["queue"])
        self.data[ctx.guild.id][lobby]["orange_cap"] = orange_cap
        self.data[ctx.guild.id][lobby]["queue"].remove(orange_cap)

        # Pick phase enabled
        if settings[1] == 1:
            self.data[ctx.guild.id][lobby]["state"] = "pick"
            await self._pick_logic(ctx, lobby)
            return await self._embeds(ctx, lobby)
        
        # Pick phase disabled (create random teams)
        for _ in range(len(self.data[ctx.guild.id][lobby]["queue"]) // 2):
            _user = random.choice(self.data[ctx.guild.id][lobby]["queue"])
            self.data[ctx.guild.id][lobby]['orange_team'].append(_user)
            self.data[ctx.guild.id][lobby]["queue"].remove(_user)
        
        for _ in range(len(self.data[ctx.guild.id][lobby]["queue"])):
            _user = random.choice(self.data[ctx.guild.id][lobby]["queue"])
            self.data[ctx.guild.id][lobby]['blue_team'].append(_user)
            self.data[ctx.guild.id][lobby]["queue"].remove(_user)
        
        # Check if maps is enabled/disabled
        if settings[0] == 1:
            self.data[ctx.guild.id][lobby]["state"] = "maps"
        else:
            maps = Cache.fetch(table="maps", guild=ctx.guild.id, key=lobby)
            self.data[ctx.guild.id][lobby]["map"] = "None"
            
            if len(maps) > 0:
                self.data[ctx.guild.id][lobby]["map"] = random.choice(maps)
            self.data[ctx.guild.id][lobby]["state"] = "final"
        return await self._embeds(ctx, lobby)


    # Check if user is banned function
    async def _ban_check(self, ctx:commands.Context, user):
        if Cache.exists(table="bans", guild=ctx.guild.id, key=user.id):
            ban_data = Cache.fetch(table="bans", guild=ctx.guild.id, key=ctx.author.id)
            if ban_data[0] - time.time() > 0:
                await ctx.channel.send(embed=discord.Embed(title=f"{self._clean_name(user.name)} is banned", description=f"**Length:** {datetime.timedelta(seconds=int(ban_data[0] - time.time()))}\n**Reason:** {ban_data[1]}\n**Banned by:** {ban_data[2]}", color=15158588))
                return False
            await Cache.delete(
                table="bans", guild=ctx.guild.id, key=user.id,
                sqlcmds=[f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"]
            )
        return True


    # When an user joins the queue function
    async def _join(self, ctx:commands.Context, user, lobby):
        if not await self.is_valid_lobby(ctx, lobby):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
        
        if not self.data[ctx.guild.id][lobby]["state"] == "queue":
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} it is not the queueing phase", color=15158588))
        
        if not Cache.exists(table="users", guild=ctx.guild.id, key=user.id):
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))
        
        if not await self._check_party(ctx, user, lobby):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not a party leader / party too full", color=15158588))
        
        for l in self.data[ctx.guild.id]:
            if user in self.data[ctx.guild.id][l]["queue"]:
                channel = ctx.guild.get_channel(int(l))
                if channel is not None:
                    return await ctx.send(embed=discord.Embed(description=f"{user.mention} is already queued in {channel.mention}", color=15158588))
                else: del self.data[ctx.guild.id][l]

        if await self._ban_check(ctx, user):
            queue_size = Cache.fetch(table="lobby_settings", guild=ctx.guild.id, key=lobby)[6]
            self.data[ctx.guild.id][lobby]["queue"].append(user)
            if len(self.data[ctx.guild.id][lobby]["queue"]) == queue_size:
                return await self._start(ctx, lobby)
            return await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id][lobby]['queue'])}/{queue_size}]** {user.mention} has joined the queue", color=33023))
        
            
    # When an user leaves the queue function
    async def _leave(self, ctx:commands.Context, user, lobby):
        if not await self.is_valid_lobby(ctx, lobby):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
        
        if not self.data[ctx.guild.id][lobby]["state"] == "queue":
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} it is not the queueing phase", color=15158588))
        
        if user in self.data[ctx.guild.id][lobby]["queue"]:
            queue_size = Cache.fetch(table="lobby_settings", guild=ctx.guild.id, key=lobby)[6]
            self.data[ctx.guild.id][lobby]["queue"].remove(user)
            return await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id][lobby]['queue'])}/{queue_size}]** {user.mention} has left the queue", color=33023))
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not in the queue", color=15158588))
        

    # Pick teammates (team captain) command
    @commands.command(name="pick", aliases=["p"], description='`=pick (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def pick(self, ctx:commands.Context, user:discord.Member):
        if not ctx.author.bot:
            if not await self.is_valid_lobby(ctx, ctx.channel.id):
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
            
            if not self.data[ctx.guild.id][ctx.channel.id]["state"] == "pick":
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the picking phase", color=15158588))
            
            if not ctx.author == self.data[ctx.guild.id][ctx.channel.id]["pick_logic"][0]:
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not your turn to pick", color=15158588))
            
            if user in self.data[ctx.guild.id][ctx.channel.id]["queue"]:
                self.data[ctx.guild.id][ctx.channel.id]["pick_logic"].pop(0)
                if self.data[ctx.guild.id][ctx.channel.id]["blue_cap"] == ctx.author:
                    self.data[ctx.guild.id][ctx.channel.id]["blue_team"].append(user)
                    self.data[ctx.guild.id][ctx.channel.id]["queue"].remove(user)
                else:
                    self.data[ctx.guild.id][ctx.channel.id]["orange_team"].append(user)
                    self.data[ctx.guild.id][ctx.channel.id]["queue"].remove(user)
                await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has picked {user.mention}", color=33023))

                if len(self.data[ctx.guild.id][ctx.channel.id]["queue"]) == 1:
                    map_pick_phase = Cache.fetch(table="lobby_settings", guild=ctx.guild.id, key=ctx.channel.id)[0]
                    self.data[ctx.guild.id][ctx.channel.id]["orange_team"].append(self.data[ctx.guild.id][ctx.channel.id]["queue"][0])
                    self.data[ctx.guild.id][ctx.channel.id]["queue"].remove(self.data[ctx.guild.id][ctx.channel.id]["queue"][0])

                    if map_pick_phase == 1:
                        self.data[ctx.guild.id][ctx.channel.id]["state"] = "maps"
                    else:
                        maps = Cache.fetch(table="maps", guild=ctx.guild.id, key=ctx.channel.id)
                        if len(maps) > 0:
                            self.data[ctx.guild.id][ctx.channel.id]["map"] = random.choice(maps)[0]
                        self.data[ctx.guild.id][ctx.channel.id]["state"] = "final"
                return await self._embeds(ctx, ctx.channel.id)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} that player is not in this queue", color=15158588))
            
            
            
    # Pick map to play (blue captain) command
    @commands.command(name="pickmap", description='`=pickmap (map name)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def pickmap(self, ctx:commands.Context, map:str):
        if not ctx.author.bot:
            if not await self.is_valid_lobby(ctx, ctx.channel.id):
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
            
            if not self.data[ctx.guild.id][ctx.channel.id]["state"] == "maps":
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the map picking phase", color=15158588))
            
            if ctx.author == self.data[ctx.guild.id][ctx.channel.id]["blue_cap"]:
                maps = Cache.fetch(table="maps", guild=ctx.guild.id, key=ctx.channel.id)
                for m in maps:
                    if map.lower() in m[0].lower():
                        self.data[ctx.guild.id][ctx.channel.id]["map"] = self._clean_name(map)
                        self.data[ctx.guild.id][ctx.channel.id]["state"] = "final"
                        return await self._embeds(ctx, ctx.channel.id)
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} that map is not in the map pool", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not the blue team captain", color=15158588))
            
        
    # Join the queue command
    @commands.command(name="join", aliases=["j"], description='`=join`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def join(self, ctx:commands.Context):
        if not ctx.author.bot:
            return await self._join(ctx, ctx.author, ctx.channel.id)

    # Force join an user to the queue command
    @commands.command(name="forcejoin", aliases=["fj"], description='`=forcejoin (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def forcejoin(self, ctx:commands.Context, user:discord.Member):
        if not ctx.author.bot:
            if await self.check_mod_role(ctx):
                return await self._join(ctx, user, ctx.channel.id)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

    # Leave the queue command
    @commands.command(name="leave", aliases=["l"], description='`=leave`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def leave(self, ctx:commands.Context):
        if not ctx.author.bot:
            return await self._leave(ctx, ctx.author, ctx.channel.id)

    # Force remove an user from the queue command
    @commands.command(name="forceleave", aliases=["fl"], description='`=forceleave (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def forceleave(self, ctx:commands.Context, user:discord.Member):
        if not ctx.author.bot:
            if await self.check_mod_role(ctx):
                return await self._leave(ctx, user, ctx.channel.id)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))

    # Show the current queue command
    @commands.command(name="queue", aliases=["q"], description='`=queue`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def queue(self, ctx:commands.Context):
        if not ctx.author.bot:
            if await self.is_valid_lobby(ctx, ctx.channel.id):
                return await self._embeds(ctx, ctx.channel.id)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
    
    # Clear the current queue command
    @commands.command(name="clear", description='`=clear`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def clear(self, ctx:commands.Context):
        if not ctx.author.bot:
            if await self.check_mod_role(ctx):
                if await self.is_valid_lobby(ctx, ctx.channel.id):
                    self._reset(ctx, ctx.channel.id)
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has cleared the queue", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
    # Party commands
    @commands.command(name="party", aliases=["team"], description='`=party create`**,** `=party leave)`**,** `=party show`**,** `=party kick (@user)`**,** `=party invite (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def party(self, ctx:commands.Context, action:str, *args):
        if not ctx.author.bot:
            if not await self.is_valid_lobby(ctx, ctx.channel.id):
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
            
            parties = self.data[ctx.guild.id][ctx.channel.id]["parties"]
            max_party_size = Cache.fetch(table="lobby_settings", guild=ctx.guild.id, key=ctx.channel.id)[4]

            # Invite a player to your party
            if action in ["invite", "inv"]:
                if ctx.author.id in parties:
                    if len(parties[ctx.author.id])+1 <= max_party_size:
                        user = ctx.guild.get_member(int(re.sub("\D","", args[0])))
                        if user is not None:
                            for party in parties:
                                if user.id in parties[party]:
                                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this player is already in a party", color=15158588))
                            try:
                                await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} a party invite has been sent to {user.mention}", color=3066992))
                                message = await user.send(embed=discord.Embed(description=f"{ctx.author.mention} has invited you to join their party", color=33023),
                                components=[[
                                        Button(style=ButtonStyle.green, label="Accept", custom_id='accept_party'),
                                        Button(style=ButtonStyle.red, label="Decline", custom_id='decline_party')
                                    ]])
                                res = await self.client.wait_for("button_click", check=lambda m: m.author == user and m.message.id == message.id, timeout=10)

                                if res.component.id == "accept_party":
                                    parties[ctx.author.id].append(user.id)
                                    await res.send(embed=discord.Embed(description=f"{res.author.mention} you have accepted {ctx.author.mention}'s party invite", color=3066992))
                                    return await ctx.send(embed=discord.Embed(description=f"**[{len(parties[ctx.author.id])}/{max_party_size}]** {user.mention} has accepted {ctx.author.mention}'s party invite", color=3066992))
                                
                                await res.send(embed=discord.Embed(description=f"{res.author.mention} you have declined {ctx.author.mention}'s party invite", color=15158588))
                                return await ctx.send(embed=discord.Embed(description=f"{user.mention} has declined {ctx.author.mention}'s party invite", color=15158588))

                            except asyncio.TimeoutError:
                                return await ctx.send(embed=discord.Embed(description=f"{user.mention} did not answer {ctx.author.mention}'s invite in time", color=15158588))
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} unknown player", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"**[{len(parties[ctx.author.id])}/{max_party_size}]** {ctx.author.mention} your party is full", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not a party leader", color=15158588))

            # Leave/Disband party
            if action in ["leave"]:
                # Disband party
                if ctx.author.id in parties:
                    del parties[ctx.author.id]
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has disbanded their party", color=3066992))

                # Leave party
                for party in parties:
                    if ctx.author.id in parties[party]:
                        parties[party].remove(ctx.author.id)
                        return await ctx.send(embed=discord.Embed(description=f"**[{len(parties[party])}/{max_party_size}]** {ctx.author.mention} has left the party", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not in a party", color=15158588))

            # Show party
            if action in ["show"]:
                if not args:
                    for party in parties:
                        if ctx.author.id in parties[party]:
                            member = await self._check_member(ctx, party)
                            if member is not None:
                                return await ctx.send(embed=discord.Embed(title=f"[{len(parties[party])}/{max_party_size}] {self._clean_name(member.name)}'s party", description="\n".join("<@" + str(e) + ">" for e in parties[party]), color=33023))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not in a party", color=15158588))
                
                # Show another players party
                if "@" in args[0]:
                    user = ctx.guild.get_member(int(re.sub("\D","", args[0])))
                    for party in parties:
                        if user.id in parties[party]:
                            member = await self._check_member(ctx, party)
                            if member is not None:
                                return await ctx.send(embed=discord.Embed(title=f"[{len(parties[party])}/{max_party_size}] {self._clean_name(member.name)}'s party", description="\n".join("<@" + str(e) + ">" for e in parties[user.id]), color=33023))
                    return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not in a party", color=15158588))

            # Create a new party
            if action in ["create"]:
                for party in parties:
                    if ctx.author.id in parties[party]:
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are already in a party", color=15158588))
                    
                if not ctx.author.id in parties:
                    parties[ctx.author.id] = [ctx.author.id]
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has created a party", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are already in a party", color=15158588))

            # Kick an user from the party
            if action in ["kick", "remove"]:
                if ctx.author.id in parties:
                    user = ctx.guild.get_member(int(re.sub("\D","", args[0])))
                    if user is not None:
                        if user.id in parties[ctx.author.id]:
                            parties[ctx.author.id].remove(user.id)
                            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has kicked {user.mention} from the party", color=3066992))
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} that player is not in your party", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} unknown player", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not a party leader", color=15158588))

    # Listen to the queue embed buttons
    @commands.Cog.listener()
    async def on_button_click(self, res:Interaction):
        if not res.author.bot:
            if res.component.id in ["join_queue", "leave_queue"]:
                lobby = res.guild.get_channel(int(res.message.embeds[0].footer.text))
                if lobby is None:
                    await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} unknown lobby", color=3066992))
                    return await res.message.delete()
                if await self.is_valid_lobby(res, lobby.id):
                    if res.component.id == "join_queue":
                        await self._join(res, res.author, lobby.id)
                    else:
                        await self._leave(res, res.author, lobby.id)
                    
                    players = "\n".join(str(e.mention) for e in self.data[res.guild.id][lobby.id]["queue"])
                    queue_size = Cache.fetch(table="lobby_settings", guild=res.guild.id, key=lobby.id)[6]
                    embed = discord.Embed(title=f'[{len(self.data[res.guild.id][lobby.id]["queue"])}/{queue_size}] {lobby.name}', description=players, color=33023)
                    embed.set_footer(text=str(lobby.id))
                    return await res.message.edit(embed=embed)
                

def setup(client: commands.Bot):
    client.add_cog(Queue(client))