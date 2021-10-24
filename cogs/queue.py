from discord_components import *
from discord.ext import commands
from discord.utils import get
import discord, random, time
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
        self.data[ctx.guild.id] = {"queue": [], "blue_cap": "", "blue_team": [], "orange_cap": "", "orange_team": [], "pick_logic": [], "map": "", "state": "queue"}

    # // CHECK IF GUILD IS IN "self.data" FUNCTION
    # /////////////////////////////////////////
    async def _data_check(self, ctx):
        if not await SQL.exists(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}"):
            await SQL.execute(f"INSERT INTO settings (guild_id, reg_role, map_pick_phase, team_categories, picking_phase, queue_channel, reg_channel, win_elo, loss_elo, match_logs) VALUES ({ctx.guild.id}, 0, 'true', 'false', 'true', 0, 0, 5, 2, 0)")

        if ctx.guild.id not in self.data:
            await self._reset(ctx)
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
            self.data[ctx.guild.id]["pick_logic"] = [
                self.data[ctx.guild.id]["blue_cap"], self.data[ctx.guild.id]["orange_cap"], self.data[ctx.guild.id]["orange_cap"], self.data[ctx.guild.id]["blue_cap"],
                self.data[ctx.guild.id]["blue_cap"], self.data[ctx.guild.id]["orange_cap"], self.data[ctx.guild.id]["blue_cap"]]
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
            await ctx.channel.send(embed=discord.Embed(title=f"{user.name} is banned", description=f"**Length:** {datetime.timedelta(seconds=int(row[2] - time.time()))}\n**Reason:** {row[3]}\n**Banned by:** {row[4]}", color=15158588))
        return True
    
    # // WHEN AN USER JOINS THE QUEUE FUNCTION
    # /////////////////////////////////////////
    async def _join(self, ctx, user):
        if await self._data_check(ctx):
            if self.data[ctx.guild.id]["state"] == "queue":
                if await SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}"):
                    if await self._ban_check(ctx, user):
                        row = await SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
                        if row[5] == 0 or ctx.message.channel.id == row[5]:
                            if not user in self.data[ctx.guild.id]["queue"]:
                                self.data[ctx.guild.id]["queue"].append(user)
                                if len(self.data[ctx.guild.id]["queue"]) == 10:
                                    return await self._start(ctx)
                                return await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id]['queue'])}/10]** {user.mention} has joined the queue", color=33023))
                            return await ctx.send(embed=discord.Embed(description=f"{user.mention} is already in the queue", color=15158588))
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} {ctx.guild.get_channel(row[5]).mention}", color=33023))
                    return False
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is not registered", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} it is not the queueing phase", color=15158588))
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=15158588))

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
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} {ctx.guild.get_channel(row[5]).mention}", color=33023))
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=15158588))

    
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
            if await self._data_check(ctx):
                if self.data[ctx.guild.id]["state"] == "maps":
                    if ctx.author == self.data[ctx.guild.id]["blue_cap"]:
                        row = await SQL.select(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id}")
                        maps = str(row[1]).split(",")
                        for m in maps:
                            maps.append(str(m[0].lower() + m[1:]))
                            
                        if map in maps:
                            self.data[ctx.guild.id]["map"] = map
                            self.data[ctx.guild.id]["state"] = "final"
                            return await self._embeds(ctx)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} that map is not in the map pool", color=15158588))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not the blue team captain", color=15158588))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the map picking phase", color=15158588))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=15158588))
    
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