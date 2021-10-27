import discord, random, time, asyncio
from discord_components import *
from discord.ext import commands
from discord.utils import get
import datetime as datetime
from _sql import *
SQL = SQL()

class Queue(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data = {}

    # // RESET THE GUILD'S VARIABLES FUNCTION
    # /////////////////////////////////////////
    async def _reset(self, ctx):
        self.data[ctx.guild.id] = {"queue": [], "blue_cap": "", "blue_team": [], "orange_cap": "", "orange_team": [], "pick_logic": [], "map": "", "parties": {}, "state": "queue"}

    # // CLEAN A PLAYERS NAME TO LOOK CLEANER
    # ////////////////////////////////////////////
    def _clean_name(self, name):
        return str(name[0]).upper() + str(name[1:]).lower()

    # // GET THE USERS ID FROM A STRING
    # /////////////////////////////////////////
    async def _clean(self, user):
        return int(str(user).strip("<").strip(">").strip("@").replace("!", ""))
        
    # // CHECK IF GUILD IS IN "self.data" FUNCTION
    # /////////////////////////////////////////
    async def _data_check(self, ctx):
        if not await SQL.exists(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}"):
            await SQL.execute(f"INSERT INTO settings (guild_id, reg_role, map_pick_phase, team_categories, picking_phase, queue_channel, reg_channel, win_elo, loss_elo, match_logs, party_size) VALUES ({ctx.guild.id}, 0, 'true', 'false', 'true', 0, 0, 5, 2, 0, 1)")

        if ctx.guild.id not in self.data:
            await self._reset(ctx)
        return True

    # // ADD OTHER PARTY MEMBERS TO THE QUEUE
    # ////////////////////////////////////////////
    async def _check_party(self, ctx, user):
        for party in self.data[ctx.guild.id]["parties"]:
            if user.id in self.data[ctx.guild.id]["parties"][party] and party != user.id:
                return False

        if user.id in self.data[ctx.guild.id]["parties"]:
            if len(self.data[ctx.guild.id]["parties"][user.id]) + len(self.data[ctx.guild.id]["queue"]) <= 10:
                for player in self.data[ctx.guild.id]["parties"][user.id][1:]:
                    await self._join(ctx, ctx.guild.get_member(player))
                return True
            return False
        return True
    
    # // SEND MATCH LOGS TO THE GIVEN CHANNEL
    # //////////////////////////////////////////
    async def _match_log(self, ctx, embed):
        # // SEND THE MATCH LOGGING EMBED TO THE CHANNEL
        row = await SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
        if row[9] != 0:
            channel = ctx.guild.get_channel(int(row[9]))
            await channel.send(
                embed=embed,
                components=[[
                    Button(style=ButtonStyle.blue, label="Blue", custom_id='blue_report'),
                    Button(style=ButtonStyle.blue, label="Orange", custom_id='orange_report'),
                    Button(style=ButtonStyle.red, label="Cancel", custom_id='match_cancel')
                ]])

    # // CREATE MATCH CATEGORY FUNCTION
    # /////////////////////////////////////////
    async def _match_category(self, ctx, match_id):
        row = await SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
        if row[3] == "true":
            if not get(ctx.guild.categories, name=f'Match #{match_id}'):
                # // CREATING CATEGORY AND SETTING PERMISSIONS
                category = await ctx.guild.create_category(f'Match #{match_id}')
                await category.set_permissions(ctx.guild.default_role, connect=False, send_messages=False)

                # // CREATING CHANNELS INSIDE CATEGORY
                await ctx.guild.create_text_channel(f"match-{match_id}", category=category)
                await ctx.guild.create_voice_channel(f'🔹 Team ' + self.data[ctx.guild.id]["blue_cap"].name, category=category)
                await ctx.guild.create_voice_channel(f"🔸 Team " + self.data[ctx.guild.id]['orange_cap'].name, category=category)

                # // CREATING TEAMS
                blue_team = self.data[ctx.guild.id]["blue_team"]
                blue_team.append(self.data[ctx.guild.id]["blue_cap"])

                orange_team = self.data[ctx.guild.id]["orange_team"]
                orange_team.append(self.data[ctx.guild.id]["orange_cap"])
                
                # // RESET DATA PARAMS
                await self._reset(ctx)

                # // CHANGE PERMISSIONS FOR MATCH PLAYERS
                for user in list(dict.fromkeys(orange_team)):
                    await category.set_permissions(user, connect=True, send_messages=True)

                for user in list(dict.fromkeys(blue_team)):
                    await category.set_permissions(user, connect=True, send_messages=True)
    
    # CREATE TEAM PICK LOGIC
    # /////////////////////////
    async def _pick_logic(self, ctx):
        for _ in range(round(len(self.data[ctx.guild.id]["queue"]) / 2)):
            self.data[ctx.guild.id]["pick_logic"].append(self.data[ctx.guild.id]["blue_cap"])
            self.data[ctx.guild.id]["pick_logic"].append(self.data[ctx.guild.id]["orange_cap"])

        if len(self.data[ctx.guild.id]["queue"]) > len(self.data[ctx.guild.id]["pick_logic"]):
            self.data[ctx.guild.id]["pick_logic"].append(self.data[ctx.guild.id]["orange_cap"])

    # // EMBED GENERATOR FUNCTION
    # /////////////////////////////////////////
    async def _embeds(self, ctx):
        # // QUEUE PHASE EMBED
        if self.data[ctx.guild.id]["state"] == "queue":
            current_queue = "None"
            if len(self.data[ctx.guild.id]["queue"]) != 0:
                current_queue = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["queue"])
            return await ctx.send(embed=discord.Embed(title=f"[{len(self.data[ctx.guild.id]['queue'])}/10] Queue", description=current_queue, color=33023))

        # // TEAM PICKING PHASE EMBED
        if self.data[ctx.guild.id]["state"] == "pick":
            orange_team="None"
            blue_team="None"
            if len(self.data[ctx.guild.id]["orange_team"]) != 0:
                orange_team = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["orange_team"])

            if len(self.data[ctx.guild.id]["blue_team"]) != 0:
                blue_team = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["blue_team"])

            embed=discord.Embed(title="Team Picking Phase", color=33023)
            embed.add_field(name="Orange Captain", value=self.data[ctx.guild.id]["orange_cap"].mention)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=self.data[ctx.guild.id]["blue_cap"].mention)
            embed.add_field(name="Orange Team", value=orange_team)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value=blue_team)
            embed.add_field(name="Available Players", value="\n".join(str(e.mention) for e in self.data[ctx.guild.id]["queue"]))
            await ctx.send(embed=embed)
            return await ctx.send(f"**{self.data[ctx.guild.id]['pick_logic'][0].mention} it is your turn to pick**")

        # // MAP PICKING PHASE EMBED
        if self.data[ctx.guild.id]["state"] == "maps":
            row = await SQL.select(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id}")
            embed=discord.Embed(title="Map Picking Phase", color=33023)
            embed.add_field(name="Orange Captain", value=self.data[ctx.guild.id]["orange_cap"].mention)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=self.data[ctx.guild.id]["blue_cap"].mention)
            embed.add_field(name="Orange Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["orange_team"]))
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["blue_team"]))
            embed.add_field(name="Available Maps", value=str(row[1]).replace(",", "\n"))
            await ctx.send(embed=embed)
            return await ctx.send(f"**{self.data[ctx.guild.id]['blue_cap'].mention} select a map to play**")

        # // FINAL MATCH UP EMBED
        if self.data[ctx.guild.id]["state"] == "final":
            count = await SQL.select_all(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id}")
            if count is None:
                count=[]

            embed=discord.Embed(title=f"Match #{len(count)+1}", description=f"**Map:** {self.data[ctx.guild.id]['map']}", color=33023)
            embed.add_field(name="Orange Captain", value=self.data[ctx.guild.id]["orange_cap"].mention)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=self.data[ctx.guild.id]["blue_cap"].mention)
            embed.add_field(name="Orange Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["orange_team"]))
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["blue_team"]))
            await ctx.send(embed=embed)

            await self._match(ctx)
            await self._match_log(ctx, embed)
            await self._match_category(ctx, len(count)+1)
            await self._reset(ctx)


    # // MATCH LOGGING FUNCTION
    # /////////////////////////////////////////
    async def _match(self, ctx):
        orange_team = ','.join(str(e.id) for e in self.data[ctx.guild.id]['orange_team'])
        blue_team = ','.join(str(e.id) for e in self.data[ctx.guild.id]['blue_team'])

        count = await SQL.select_all(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id}")
        if count is None:
            count=[]
        await SQL.execute(f"""INSERT INTO matches (guild_id, match_id, map, orange_cap, orange_team, blue_cap, blue_team, status, winners) VALUES ({ctx.guild.id}, {len(count)+1}, '{self.data[ctx.guild.id]['map']}', '{self.data[ctx.guild.id]['orange_cap'].id}', '{orange_team}', '{self.data[ctx.guild.id]['blue_cap'].id}', '{blue_team}', 'ongoing', 'none')""")

    # // WHEN QUEUE REACHES 10 PEOPLE FUNCTION
    # /////////////////////////////////////////
    async def _start(self, ctx):
        row = await SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
        # // CREATING TEAM CAPTAINS
        self.data[ctx.guild.id]["blue_cap"] = random.choice(self.data[ctx.guild.id]["queue"]); self.data[ctx.guild.id]["queue"].remove(self.data[ctx.guild.id]["blue_cap"])
        self.data[ctx.guild.id]["orange_cap"] = random.choice(self.data[ctx.guild.id]["queue"]); self.data[ctx.guild.id]["queue"].remove(self.data[ctx.guild.id]["orange_cap"])

        if row[4] == "true":
            # // PICK PHASE ENABLED
            # // CREATING LOGIC AND CHANGING STATE
            self.data[ctx.guild.id]["state"] = "pick"
            await self._pick_logic(ctx)
            return await self._embeds(ctx)
        
        # // PICK PHASE DISABLED
        # // CREATING THE RANDOM TEAMS
        for _ in range(round(len(self.data[ctx.guild.id]["queue"]) / 2)):
            _user = random.choice(self.data[ctx.guild.id]["queue"])
            self.data[ctx.guild.id]['orange_team'].append(_user)
            self.data[ctx.guild.id]["queue"].remove(_user)
        
        for _ in range(round(len(self.data[ctx.guild.id]["queue"]))):
            _user = random.choice(self.data[ctx.guild.id]["queue"])
            self.data[ctx.guild.id]['blue_team'].append(_user)
            self.data[ctx.guild.id]["queue"].remove(_user)
        
        # // CHECKING IF MAP PHASE IS DISABLED/ENABLED
        if row[2] == "true":
            self.data[ctx.guild.id]["state"] = "maps"
        else:
            _row = await SQL.select(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id}")
            self.data[ctx.guild.id]["map"] = random.choice(str(_row[1]).split(","))
            self.data[ctx.guild.id]["state"] = "final"
        return await self._embeds(ctx)

    # // CHECK IF THE USER IS BANNED FUNCTION
    # /////////////////////////////////////////
    async def _ban_check(self, ctx, user):
        row = await SQL.select(f"SELECT * FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
        if row is not None:
            if row[2] - time.time() < 0:
                await SQL.execute(f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
                return False
            await ctx.channel.send(embed=discord.Embed(title=f"{self._clean_name(user.name)} is banned", description=f"**Length:** {datetime.timedelta(seconds=int(row[2] - time.time()))}\n**Reason:** {row[3]}\n**Banned by:** {row[4]}", color=15158588))
        return True

    # // WHEN AN USER JOINS THE QUEUE FUNCTION
    # /////////////////////////////////////////
    async def _join(self, ctx, user):
        if await self._data_check(ctx):
            if self.data[ctx.guild.id]["state"] == "queue":
                if await SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
                    if await self._ban_check(ctx, user):
                        row = await SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
                        if row[5] == 0 or ctx.message.channel.id == row[5]:
                            if not user in self.data[ctx.guild.id]["queue"]:
                                if await self._check_party(ctx, user):
                                    self.data[ctx.guild.id]["queue"].append(user)
                                    if len(self.data[ctx.guild.id]["queue"]) == 10:
                                        return await self._start(ctx)
                                    return await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id]['queue'])}/10]** {user.mention} has joined the queue", color=33023))
                                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not a party leader / party too full", color=15158588))
                            return await ctx.send(embed=discord.Embed(description=f"{user.mention} is already in the queue", color=15158588))
                        return await ctx.send(embed=discord.Embed(description=f"{user.mention} {ctx.guild.get_channel(row[5]).mention}", color=33023))
                    return False
                return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} it is not the queueing phase", color=15158588))
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} an internal error has occured!", color=15158588))

    # // WHEN AN USER LEAVES THE QUEUE FUNCTION
    # /////////////////////////////////////////
    async def _leave(self, ctx, user):
        if await self._data_check(ctx):
            row = await SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
            if row[5] == 0 or ctx.message.channel.id == row[5]:
                if self.data[ctx.guild.id]["state"] == "queue":
                    if user in self.data[ctx.guild.id]["queue"]:
                        self.data[ctx.guild.id]["queue"].remove(user)
                        return await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id]['queue'])}/10]** {user.mention} has left the queue", color=33023))
                    return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not in the queue", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{user.mention} it is not the queueing phase", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} {ctx.guild.get_channel(row[5]).mention}", color=33023))
        return await ctx.send(embed=discord.Embed(description=f"{user.mention} an internal error has occured!", color=15158588))

    
    # // FORCE START THE QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["fs"])
    @commands.has_permissions(manage_messages=True)
    async def forcestart(self, ctx):
        if not ctx.author.bot:
            if await self._data_check(ctx):
                return await self._start(ctx)

    # // PICK TEAMMATES (TEAM CAPTAIN) COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["p"])
    async def pick(self, ctx, user:discord.Member):
        if not ctx.author.bot:
            if await self._data_check(ctx):
                if self.data[ctx.guild.id]["state"] == "pick":
                    if ctx.author == self.data[ctx.guild.id]["pick_logic"][0]:
                        self.data[ctx.guild.id]["pick_logic"].pop(0)
                        if self.data[ctx.guild.id]["blue_cap"] == ctx.author:
                            self.data[ctx.guild.id]["blue_team"].append(user)
                            self.data[ctx.guild.id]["queue"].remove(user)
                        else:
                            self.data[ctx.guild.id]["orange_team"].append(user)
                            self.data[ctx.guild.id]["queue"].remove(user)
                        await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has picked {user.mention}", color=33023))

                        if len(self.data[ctx.guild.id]["queue"]) == 1:
                            row = await SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
                            self.data[ctx.guild.id]["orange_team"].append(self.data[ctx.guild.id]["queue"][0])
                            self.data[ctx.guild.id]["queue"].remove(self.data[ctx.guild.id]["queue"][0])

                            if row[2] == "true":
                                self.data[ctx.guild.id]["state"] = "maps"
                            else:
                                _row = await SQL.select(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id}")
                                self.data[ctx.guild.id]["map"] = random.choice(str(_row[1]).split(","))
                                self.data[ctx.guild.id]["state"] = "final"
                                
                        return await self._embeds(ctx)
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not your turn to pick", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the picking phase", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=15158588))
        
    # // PICK MAP TO PLAY (BLUE CAPTAIN) COMMAND
    # ///////////////////////////////////////////
    @commands.command()
    async def map(self, ctx, map:str):
        if not ctx.author.bot:
            if self.data[ctx.guild.id]["state"] == "maps":
                if ctx.author == self.data[ctx.guild.id]["blue_cap"]:
                    row = await SQL.select(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id}")
                    maps = str(row[1]).split(",")
                    
                    if map in maps or self._clean_name(map) in maps:
                        self.data[ctx.guild.id]["map"] = self._clean_name(map)
                        self.data[ctx.guild.id]["state"] = "final"
                        return await self._embeds(ctx)
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} that map is not in the map pool", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not the blue team captain", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the map picking phase", color=15158588))
    
    # // JOIN THE QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["j"])
    async def join(self, ctx):
        if not ctx.author.bot:
            return await self._join(ctx, ctx.author)

    # // FORCE ADD AN USER TO THE QUEUE COMMAND
    # //////////////////////////////////////////
    @commands.command(aliases=["fj"])
    async def forcejoin(self, ctx, user:discord.Member):
        if not ctx.author.bot:
            return await self._join(ctx, user)

    # // LEAVE THE QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["l"])
    async def leave(self, ctx):
        if not ctx.author.bot:
            return await self._leave(ctx, ctx.author)

    # // FORCE REMOVE A PLAYER FROM THE QUEUE COMMAND
    # ////////////////////////////////////////////////
    @commands.command(aliases=["fl"])
    async def forceleave(self, ctx, user:discord.Member):
        if not ctx.author.bot:
            return await self._leave(ctx, user)

    # // SHOW THE CURRENT QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        if not ctx.author.bot:
            if await self._data_check(ctx):
                return await self._embeds(ctx)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=15158588))
    
    # // CLEAR THE CURRENT QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx):
        if not ctx.author.bot:
            if await self._data_check(ctx):
                await self._reset(ctx)
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has cleared the queue", color=3066992))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=15158588))

    # // PARTY COMMAND
    # ////////////////////////////
    @commands.command(aliases=["team"])
    async def party(self, ctx, action:str, *args):
        if await self._data_check(ctx):
            parties = self.data[ctx.guild.id]["parties"]
            settings = await SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
            max_party_size = settings[10]

            # // INVITE USER TO YOUR PARTY
            if action == "invite" or action == "inv":
                if ctx.author.id in parties:
                    if len(parties[ctx.author.id])+1 <= max_party_size:
                        user = ctx.guild.get_member(await self._clean(list(args)[0]))
                        # CHECK IF USER IS IN A PARTY
                        if user.id in parties:
                            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this player is already in a party", color=15158588))

                        for party in parties:
                            # CHECK IF USER IS IN A PARTY
                            if user.id in parties[party]:
                                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this player is already in a party", color=15158588))
                        try:
                            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} the party invite has been sent to {user.mention}", color=3066992))
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
                            
                            await res.send(embed=discord.Embed(description=f"{res.author.mention} you have declined {ctx.author.mention}'s party invite", color=3066992))
                            return await ctx.send(embed=discord.Embed(description=f"{user.mention} has declined {ctx.author.mention}'s party invite", color=15158588))

                        except asyncio.TimeoutError:
                            return await ctx.send(embed=discord.Embed(description=f"{user.mention} did not answer {ctx.author.mention}'s invite in time", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"**[{len(parties[ctx.author.id])}/{max_party_size}]** {ctx.author.mention} your party is full", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not a party leader", color=15158588))

            # // LEAVE PARTY ACTION
            if action == "leave":
                # CHECK IF AUTHOR IS IN A PARTY
                if ctx.author.id in parties:
                    del parties[ctx.author.id]
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has disbanded their party", color=3066992))
                
                # // CHECK IF AUTHOR IS IN ANY OTHER PARTIES
                for party in parties:
                    if ctx.author.id in parties[party]:
                        parties[party].remove(ctx.author.id)
                        return await ctx.send(embed=discord.Embed(description=f"**[{len(parties[party])}/{max_party_size}]** {ctx.author.mention} has left the party", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not in a party", color=15158588))

            # // SHOW PARTY ACTION
            if action == "show":
                # // SHOW AUTHOR'S PARTY
                if not args:
                    for party in parties:
                        if ctx.author.id in parties[party]:
                            return await ctx.send(embed=discord.Embed(title=f"[{len(parties[party])}/{max_party_size}] {self._clean_name(ctx.guild.get_member(party).name)}'s party", description="\n".join("<@" + str(e) + ">" for e in parties[party]), color=33023))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not in a party", color=15158588))
                
                # // SHOW ANOTHER PLAYER'S PARTY
                elif "@" in args:
                    user = ctx.guild.get_member(await self._clean(list(args)[0]))
                    for party in parties:
                        if user.id in parties[party]:
                            return await ctx.send(embed=discord.Embed(title=f"{self._clean_name(ctx.guild.get_member(party).name)}'s party ┃ {ctx.guild.name}", description="\n".join("<@" + str(e) + ">" for e in parties[user.id]), color=33023))
                    return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not in a party", color=15158588))

            # // CREATE PARTY
            if action == "create":
                for party in parties:
                    if ctx.author.id in parties[party]:
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are already in a party", color=15158588))
                    
                if not ctx.author.id in parties:
                    parties.update({ctx.author.id: []})
                    parties[ctx.author.id].append(ctx.author.id)
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has created their own party", color=3066992))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are already in a party", color=15158588))

            # // KICK AN USER FROM YOUR PARTY
            if action == "kick":
                if ctx.author.id in parties:
                    user = ctx.guild.get_member(await self._clean(list(args)[0]))
                    if user.id in parties[ctx.author.id]:
                        parties[ctx.author.id].remove(user.id)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has kicked {user.mention} from their party", color=3066992))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} that player is not in your party", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not a party leader", color=15158588))


    # // BUTTON CLICK LISTENER
    # /////////////////////////////////////////
    @commands.Cog.listener()
    async def on_button_click(self, res):
        if not res.author.bot:
            if res.component.id == "join_queue" or res.component.id == "leave_queue":
                if await self._data_check(res):
                    if res.component.id == "join_queue":
                        await self._join(res, res.author)
                    else:
                        await self._leave(res, res.author)
                        
                    players = "\n".join(str(enum.mention) for enum in self.data[res.guild.id]["queue"])
                    await res.message.edit(embed=discord.Embed(title=f'[{len(self.data[res.guild.id]["queue"])}/10] Queue', description=players, color=33023))


def setup(client):
    client.add_cog(Queue(client))
