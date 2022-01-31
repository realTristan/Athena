import discord, random, time, asyncio
from discord_components import *
from discord.ext import commands
from discord.utils import get
import datetime as datetime
from functools import *
from _sql import *

class Queue(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data = {}

    # // RESET THE GUILD'S VARIABLES FUNCTION
    # /////////////////////////////////////////
    async def _reset(self, ctx, lobby):
        self.data[ctx.guild.id][lobby] = {"queue": [], "blue_cap": "", "blue_team": [], "orange_cap": "", "orange_team": [], "pick_logic": [], "map": "", "parties": {}, "state": "queue"}

    # // CLEAN A PLAYERS NAME TO LOOK CLEANER
    # ////////////////////////////////////////////
    def _clean_name(self, name):
        return str(name[0]).upper() + str(name[1:]).lower()

    # // GET THE USERS ID FROM A STRING
    # /////////////////////////////////////////
    async def _clean(self, user):
        return int(str(user).strip("<").strip(">").strip("@").replace("!", ""))
        
    # // CHECK SELF.DATA FUNCTION
    # /////////////////////////////////////////
    async def _data_check(self, ctx, lobby):
        # // CHECK SETTINGS DATABASE
        if not await SQL_CLASS().exists(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}"):
            await SQL_CLASS().execute(f"INSERT INTO settings (guild_id, reg_role, match_categories, reg_channel, match_logs) VALUES ({ctx.guild.id}, 0, 0, 0, 0)")
        
        # // CHECK IF GUILD IS IN SELF.DATA
        if not ctx.guild.id in self.data:
            self.data[ctx.guild.id] = {}

        # // CHECK IF CHANNEL IS A LOBBY
        row = await SQL_CLASS().select(f"SELECT * FROM lobbies WHERE guild_id = {ctx.guild.id}")
        if row is not None:
            if str(lobby) in str(row[1]).split(","):
                if not lobby in self.data[ctx.guild.id]:
                    await self._reset(ctx, lobby)
                return True
        return False

    # // ADD OTHER PARTY MEMBERS TO THE QUEUE
    # ////////////////////////////////////////////
    async def _check_party(self, ctx, user, lobby):
        for party in self.data[ctx.guild.id][lobby]["parties"]:
            if user.id in self.data[ctx.guild.id][lobby]["parties"][party] and party != user.id:
                return False

        if user.id in self.data[ctx.guild.id][lobby]["parties"]:
            row = await SQL_CLASS().select(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {lobby}")
            if len(self.data[ctx.guild.id][lobby]["parties"][user.id]) + len(self.data[ctx.guild.id][lobby]["queue"]) <= row[8]:
                for player in self.data[ctx.guild.id][lobby]["parties"][user.id][1:]:
                    await self._join(ctx, ctx.guild.get_member(player), lobby)
                return True
            return False
        return True
    
    # // SEND MATCH LOGS TO THE GIVEN CHANNEL
    # //////////////////////////////////////////
    async def _match_log(self, ctx, embed):
        # // SEND THE MATCH LOGGING EMBED TO THE CHANNEL
        row = await SQL_CLASS().select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
        if row[4] != 0:
            channel = ctx.guild.get_channel(int(row[4]))
            await channel.send(
                embed=embed,
                components=[[
                    Button(style=ButtonStyle.blue, label="Blue", custom_id='blue_report'),
                    Button(style=ButtonStyle.blue, label="Orange", custom_id='orange_report'),
                    Button(style=ButtonStyle.red, label="Cancel", custom_id='match_cancel')
                ]])

    # // CREATE MATCH CATEGORY FUNCTION
    # /////////////////////////////////////////
    async def _match_category(self, ctx, match_id, lobby):
        row = await SQL_CLASS().select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
        if row[3] == 1:
            if not get(ctx.guild.categories, name=f'Match #{match_id}'):
                # // CREATING CATEGORY AND SETTING PERMISSIONS
                category = await ctx.guild.create_category(f'Match #{match_id}')
                await category.set_permissions(ctx.guild.default_role, connect=False, send_messages=False)

                # // CREATING CHANNELS INSIDE CATEGORY
                await ctx.guild.create_text_channel(f"match-{match_id}", category=category)
                await ctx.guild.create_voice_channel(f'🔹 Team ' + self.data[ctx.guild.id][lobby]["blue_cap"].name, category=category)
                await ctx.guild.create_voice_channel(f"🔸 Team " + self.data[ctx.guild.id][lobby]['orange_cap'].name, category=category)

                # // CREATING TEAMS
                blue_team = self.data[ctx.guild.id][lobby]["blue_team"]
                blue_team.append(self.data[ctx.guild.id][lobby]["blue_cap"])

                orange_team = self.data[ctx.guild.id][lobby]["orange_team"]
                orange_team.append(self.data[ctx.guild.id][lobby]["orange_cap"])
                
                # // RESET DATA PARAMS
                await self._reset(ctx, lobby)

                # // CHANGE PERMISSIONS FOR MATCH PLAYERS
                for user in list(dict.fromkeys(orange_team)):
                    await category.set_permissions(user, connect=True, send_messages=True)

                for user in list(dict.fromkeys(blue_team)):
                    await category.set_permissions(user, connect=True, send_messages=True)

    # // MATCH LOGGING FUNCTION
    # /////////////////////////////////////////
    async def _match(self, ctx, lobby):
        orange_team = ','.join(str(e.id) for e in self.data[ctx.guild.id][lobby]['orange_team'])
        blue_team = ','.join(str(e.id) for e in self.data[ctx.guild.id][lobby]['blue_team'])

        count = await SQL_CLASS().select_all(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id}")
        if count is None:
            count=[]
        await SQL_CLASS().execute(f"INSERT INTO matches (guild_id, match_id, lobby_id, map, orange_cap, orange_team, blue_cap, blue_team, status, winners) VALUES ({ctx.guild.id}, {len(count)+1}, {lobby}, '{self.data[ctx.guild.id][lobby]['map']}', '{self.data[ctx.guild.id][lobby]['orange_cap'].id}', '{orange_team}', '{self.data[ctx.guild.id][lobby]['blue_cap'].id}', '{blue_team}', 'ongoing', 'none')")

    # CREATE TEAM PICK LOGIC
    # /////////////////////////
    async def _pick_logic(self, ctx, lobby):
        for _ in range(round(len(self.data[ctx.guild.id][lobby]["queue"]) / 2)):
            self.data[ctx.guild.id][lobby]["pick_logic"].append(self.data[ctx.guild.id][lobby]["blue_cap"])
            self.data[ctx.guild.id][lobby]["pick_logic"].append(self.data[ctx.guild.id][lobby]["orange_cap"])

        if len(self.data[ctx.guild.id][lobby]["queue"]) > len(self.data[ctx.guild.id][lobby]["pick_logic"]):
            self.data[ctx.guild.id][lobby]["pick_logic"].append(self.data[ctx.guild.id][lobby]["orange_cap"])

    # // EMBED GENERATOR FUNCTION
    # /////////////////////////////////////////
    async def _embeds(self, ctx, lobby):
        # // QUEUE PHASE EMBED
        if self.data[ctx.guild.id][lobby]["state"] == "queue":
            current_queue = "None"
            if len(self.data[ctx.guild.id][lobby]["queue"]) != 0:
                current_queue = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id][lobby]["queue"])
            row = await SQL_CLASS().select(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {lobby}")
            return await ctx.send(embed=discord.Embed(title=f"[{len(self.data[ctx.guild.id][lobby]['queue'])}/{row[8]}] {ctx.channel.name}", description=current_queue, color=33023))

        # // TEAM PICKING PHASE EMBED
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
            return await ctx.send(f"**{self.data[ctx.guild.id][lobby]['pick_logic'][0].mention} it is your turn to pick**")

        # // MAP PICKING PHASE EMBED
        if self.data[ctx.guild.id][lobby]["state"] == "maps":
            row = await SQL_CLASS().select(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id} AND lobby_id = {lobby}")
            embed=discord.Embed(title="Map Picking Phase", color=33023)
            embed.add_field(name="Orange Captain", value=self.data[ctx.guild.id][lobby]["orange_cap"].mention)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=self.data[ctx.guild.id][lobby]["blue_cap"].mention)
            embed.add_field(name="Orange Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id][lobby]["orange_team"]))
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id][lobby]["blue_team"]))
            embed.add_field(name="Available Maps", value=str(row[2]).replace(",", "\n"))
            await ctx.send(embed=embed)
            return await ctx.send(f"**{self.data[ctx.guild.id][lobby]['blue_cap'].mention} select a map to play**")

        # // FINAL MATCH UP EMBED
        if self.data[ctx.guild.id][lobby]["state"] == "final":
            count = await SQL_CLASS().select_all(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id}")
            if count is None:
                count=[]

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
            await self._reset(ctx, lobby)

    # // WHEN QUEUE REACHES QUEUE SIZE FUNCTION
    # /////////////////////////////////////////
    async def _start(self, ctx, lobby):
        row = await SQL_CLASS().select(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id}  AND lobby_id = {lobby}")
        # // CREATING TEAM CAPTAINS
        self.data[ctx.guild.id][lobby]["blue_cap"] = random.choice(self.data[ctx.guild.id][lobby]["queue"])
        self.data[ctx.guild.id][lobby]["queue"].remove(self.data[ctx.guild.id][lobby]["blue_cap"])
        
        self.data[ctx.guild.id][lobby]["orange_cap"] = random.choice(self.data[ctx.guild.id][lobby]["queue"])
        self.data[ctx.guild.id][lobby]["queue"].remove(self.data[ctx.guild.id][lobby]["orange_cap"])

        if row[3] == 1:
            # // PICK PHASE ENABLED
            # // CREATING LOGIC AND CHANGING STATE
            self.data[ctx.guild.id][lobby]["state"] = "pick"
            await self._pick_logic(ctx, lobby)
            return await self._embeds(ctx, lobby)
        
        # // PICK PHASE DISABLED
        # // CREATING THE RANDOM TEAMS
        for _ in range(round(len(self.data[ctx.guild.id][lobby]["queue"]) / 2)):
            _user = random.choice(self.data[ctx.guild.id][lobby]["queue"])
            self.data[ctx.guild.id][lobby]['orange_team'].append(_user)
            self.data[ctx.guild.id][lobby]["queue"].remove(_user)
        
        for _ in range(round(len(self.data[ctx.guild.id][lobby]["queue"]))):
            _user = random.choice(self.data[ctx.guild.id][lobby]["queue"])
            self.data[ctx.guild.id][lobby]['blue_team'].append(_user)
            self.data[ctx.guild.id][lobby]["queue"].remove(_user)
        
        # // CHECKING IF MAP PHASE IS DISABLED/ENABLED
        if row[2] == 1:
            self.data[ctx.guild.id][lobby]["state"] = "maps"
        else:
            _row = await SQL_CLASS().select(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id} AND lobby_id = {lobby}")
            self.data[ctx.guild.id][lobby]["map"] = "None"
            
            if _row is not None:
                self.data[ctx.guild.id][lobby]["map"] = random.choice(str(_row[2]).split(","))
            self.data[ctx.guild.id][lobby]["state"] = "final"
        return await self._embeds(ctx, lobby)

    # // CHECK IF THE USER IS BANNED FUNCTION
    # /////////////////////////////////////////
    async def _ban_check(self, ctx, user):
        row = await SQL_CLASS().select(f"SELECT * FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
        if row is not None:
            if row[2] - time.time() > 0:
                await ctx.channel.send(embed=discord.Embed(title=f"{self._clean_name(user.name)} is banned", description=f"**Length:** {datetime.timedelta(seconds=int(row[2] - time.time()))}\n**Reason:** {row[3]}\n**Banned by:** {row[4]}", color=15158588))
                return False
            await SQL_CLASS().execute(f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
        return True

    # // WHEN AN USER JOINS THE QUEUE FUNCTION
    # /////////////////////////////////////////
    async def _join(self, ctx, user, lobby):
        if await self._data_check(ctx, lobby):
            if self.data[ctx.guild.id][lobby]["state"] == "queue":
                if await SQL_CLASS().exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
                    if await self._ban_check(ctx, user):
                        for l in self.data[ctx.guild.id]:
                            if user in self.data[ctx.guild.id][l]["queue"]:
                                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is already queued in {ctx.guild.get_channel(l).mention}", color=15158588))

                        if await self._check_party(ctx, user, lobby):
                            self.data[ctx.guild.id][lobby]["queue"].append(user)
                            row = await SQL_CLASS().select(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {lobby}")
                            if len(self.data[ctx.guild.id][lobby]["queue"]) == row[8]:
                                return await self._start(ctx, lobby)
                            return await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id][lobby]['queue'])}/{row[8]}]** {user.mention} has joined the queue", color=33023))
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not a party leader / party too full", color=15158588))
                    return False
                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} it is not the queueing phase", color=15158588))
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))

    # // WHEN AN USER LEAVES THE QUEUE FUNCTION
    # /////////////////////////////////////////
    async def _leave(self, ctx, user, lobby):
        if await self._data_check(ctx, lobby):
            if self.data[ctx.guild.id][lobby]["state"] == "queue":
                if user in self.data[ctx.guild.id][lobby]["queue"]:
                    self.data[ctx.guild.id][lobby]["queue"].remove(user)
                    row = await SQL_CLASS().select(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {lobby}")
                    return await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id][lobby]['queue'])}/{row[8]}]** {user.mention} has left the queue", color=33023))
                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not in the queue", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} it is not the queueing phase", color=15158588))
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))

    # // PICK TEAMMATES (TEAM CAPTAIN) COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["p"], description='`=pick (@user)`')
    async def pick(self, ctx, user:discord.Member):
        if not ctx.author.bot:
            if await self._data_check(ctx, ctx.channel.id):
                if self.data[ctx.guild.id][ctx.channel.id]["state"] == "pick":
                    if ctx.author == self.data[ctx.guild.id][ctx.channel.id]["pick_logic"][0]:
                        self.data[ctx.guild.id][ctx.channel.id]["pick_logic"].pop(0)
                        if self.data[ctx.guild.id][ctx.channel.id]["blue_cap"] == ctx.author:
                            self.data[ctx.guild.id][ctx.channel.id]["blue_team"].append(user)
                            self.data[ctx.guild.id][ctx.channel.id]["queue"].remove(user)
                        else:
                            self.data[ctx.guild.id][ctx.channel.id]["orange_team"].append(user)
                            self.data[ctx.guild.id][ctx.channel.id]["queue"].remove(user)
                        await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has picked {user.mention}", color=33023))

                        if len(self.data[ctx.guild.id][ctx.channel.id]["queue"]) == 1:
                            row = await SQL_CLASS().select(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
                            self.data[ctx.guild.id][ctx.channel.id]["orange_team"].append(self.data[ctx.guild.id][ctx.channel.id]["queue"][0])
                            self.data[ctx.guild.id][ctx.channel.id]["queue"].remove(self.data[ctx.guild.id][ctx.channel.id]["queue"][0])

                            if row[2] == 1:
                                self.data[ctx.guild.id][ctx.channel.id]["state"] = "maps"
                            else:
                                _row = await SQL_CLASS().select(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
                                self.data[ctx.guild.id][ctx.channel.id]["map"] = random.choice(str(_row[2]).split(","))
                                self.data[ctx.guild.id][ctx.channel.id]["state"] = "final"
                                
                        return await self._embeds(ctx, ctx.channel.id)
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not your turn to pick", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the picking phase", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
        
    # // PICK MAP TO PLAY (BLUE CAPTAIN) COMMAND
    # ///////////////////////////////////////////
    @commands.command(description='`=map (map name)`')
    async def map(self, ctx, map:str):
        if not ctx.author.bot:
            if await self._data_check(ctx, ctx.channel.id):
                if self.data[ctx.guild.id][ctx.channel.id]["state"] == "maps":
                    if ctx.author == self.data[ctx.guild.id][ctx.channel.id]["blue_cap"]:
                        row = await SQL_CLASS().select(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
                        maps = str(row[2]).split(",")
                        
                        if map in maps or self._clean_name(map) in maps:
                            self.data[ctx.guild.id][ctx.channel.id]["map"] = self._clean_name(map)
                            self.data[ctx.guild.id][ctx.channel.id]["state"] = "final"
                            return await self._embeds(ctx, ctx.channel.id)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} that map is not in the map pool", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not the blue team captain", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the map picking phase", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
    

    # // FORCE START THE QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["fs"], description='`=forcestart`')
    @commands.has_permissions(manage_messages=True)
    async def forcestart(self, ctx):
        if not ctx.author.bot:
            if self.data[ctx.guild.id][ctx.channel.id]["state"] == "queue":
                if await self._data_check(ctx, ctx.channel.id):
                    return await self._start(ctx, ctx.channel.id)
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the queueing phase", color=15158588))

    # // JOIN THE QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["j"], description='`=join`')
    async def join(self, ctx):
        if not ctx.author.bot:
            return await self._join(ctx, ctx.author, ctx.channel.id)

    # // FORCE ADD AN USER TO THE QUEUE COMMAND
    # //////////////////////////////////////////
    @commands.command(aliases=["fj"], description='`=forcejoin (@user)`')
    async def forcejoin(self, ctx, user:discord.Member):
        if not ctx.author.bot:
            return await self._join(ctx, user, ctx.channel.id)

    # // LEAVE THE QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["l"], description='`=leave`')
    async def leave(self, ctx):
        if not ctx.author.bot:
            return await self._leave(ctx, ctx.author, ctx.channel.id)

    # // FORCE REMOVE A PLAYER FROM THE QUEUE COMMAND
    # ////////////////////////////////////////////////
    @commands.command(aliases=["fl"], description='`=forceleave (@user)`')
    async def forceleave(self, ctx, user:discord.Member):
        if not ctx.author.bot:
            return await self._leave(ctx, user, ctx.channel.id)

    # // SHOW THE CURRENT QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["q"], description='`=queue`')
    async def queue(self, ctx):
        if not ctx.author.bot:
            if await self._data_check(ctx, ctx.channel.id):
                return await self._embeds(ctx, ctx.channel.id)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
    
    # // CLEAR THE CURRENT QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command(description='`=clear`')
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx):
        if not ctx.author.bot:
            if await self._data_check(ctx, ctx.channel.id):
                await self._reset(ctx, ctx.channel.id)
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has cleared the queue", color=3066992))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))

    # // PARTY COMMAND
    # ////////////////////////////
    @commands.command(aliases=["team"], description='`=party create`**,** `=party leave)`**,** `=party show`**,** `=party kick (@user)`**,** `=party invite (@user)`')
    async def party(self, ctx, action:str, *args):
        if await self._data_check(ctx, ctx.channel.id):
            parties = self.data[ctx.guild.id][ctx.channel.id]["parties"]
            lobby_settings = await SQL_CLASS().select(f"SELECT * FROM lobby_settings WHERE guild_id = {ctx.guild.id} AND lobby_id = {ctx.channel.id}")
            max_party_size = lobby_settings[6]

            # // INVITE USER TO YOUR PARTY
            if action in ["invite", "inv"]:
                if ctx.author.id in parties:
                    if len(parties[ctx.author.id])+1 <= max_party_size:
                        user = ctx.guild.get_member(await self._clean(list(args)[0]))

                        # CHECK IF USER IS IN A PARTY
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
                    return await ctx.send(embed=discord.Embed(description=f"**[{len(parties[ctx.author.id])}/{max_party_size}]** {ctx.author.mention} your party is full", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not a party leader", color=15158588))

            # // LEAVE PARTY ACTION
            if action in ["leave"]:
                # // DISBAND PARTY
                if ctx.author.id in parties:
                    del parties[ctx.author.id]
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has disbanded their party", color=3066992))

                # // LEAVE PARTY
                for party in parties:
                    if ctx.author.id in parties[party]:
                        parties[party].remove(ctx.author.id)
                        return await ctx.send(embed=discord.Embed(description=f"**[{len(parties[party])}/{max_party_size}]** {ctx.author.mention} has left the party", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not in a party", color=15158588))

            # // SHOW PARTY ACTION
            if action in ["show"]:
                if not args:
                    for party in parties:
                        if ctx.author.id in parties[party]:
                            return await ctx.send(embed=discord.Embed(title=f"[{len(parties[party])}/{max_party_size}] {self._clean_name(ctx.guild.get_member(party).name)}'s party", description="\n".join("<@" + str(e) + ">" for e in parties[party]), color=33023))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not in a party", color=15158588))
                
                # // SHOW ANOTHER PLAYER'S PARTY
                if "@" in list(args)[0]:
                    user = ctx.guild.get_member(await self._clean(list(args)[0]))
                    for party in parties:
                        if user.id in parties[party]:
                            return await ctx.send(embed=discord.Embed(title=f"[{len(parties[party])}/{max_party_size}] {self._clean_name(ctx.guild.get_member(party).name)}'s party", description="\n".join("<@" + str(e) + ">" for e in parties[user.id]), color=33023))
                    return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not in a party", color=15158588))

            # // CREATE PARTY
            if action in ["create"]:
                for party in parties:
                    if ctx.author.id in parties[party]:
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are already in a party", color=15158588))
                    
                if not ctx.author.id in parties:
                    parties[ctx.author.id] = [ctx.author.id]
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has created a party", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are already in a party", color=15158588))

            # // KICK AN USER FROM YOUR PARTY
            if action in ["kick", "remove"]:
                if ctx.author.id in parties:
                    user = ctx.guild.get_member(await self._clean(list(args)[0]))
                    if user.id in parties[ctx.author.id]:
                        parties[ctx.author.id].remove(user.id)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has kicked {user.mention} from the party", color=3066992))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} that player is not in your party", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not a party leader", color=15158588))
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))

    # // BUTTON CLICK LISTENER
    # /////////////////////////////////////////
    @commands.Cog.listener()
    async def on_button_click(self, res):
        if not res.author.bot:
            if res.component.id in ["join_queue", "leave_queue"]:
                lobby = res.guild.get_channel(int(res.message.embeds[0].footer.text))
                if await self._data_check(res, lobby.id):
                    if res.component.id == "join_queue":
                        await self._join(res, res.author, lobby.id)
                    else:
                        await self._leave(res, res.author, lobby.id)
                    
                    players = "\n".join(str(e.mention) for e in self.data[res.guild.id][lobby.id]["queue"])
                    row = await SQL_CLASS().select(f"SELECT * FROM lobby_settings WHERE guild_id = {res.guild.id} AND lobby_id = {lobby.id}")
                    embed = discord.Embed(title=f'[{len(self.data[res.guild.id][lobby.id]["queue"])}/{row[8]}] {lobby.name}', description=players, color=33023)
                    embed.set_footer(text=str(lobby.id))
                    return await res.message.edit(embed=embed)
                


def setup(client):
    client.add_cog(Queue(client))