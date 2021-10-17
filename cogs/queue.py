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
        if SQL.exists(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}"):
            SQL.execute(f"INSERT INTO settings (guild_id, reg_role, map_pick_phase, team_cap_vcs, picking_phase, queue_channel, reg_channel, win_elo, loss_elo, match_logs) VALUES ({ctx.guild.id}, 0, 'true', 'false', 'true', 0, 0, 5, 2, 0)")

        if ctx.guild.id not in self.data:
            await self._reset(ctx)
        return True

    # // EMBED GENERATOR FUNCTION
    # /////////////////////////////////////////
    async def _embeds(self, ctx):
        # // QUEUE PHASE EMBED
        if self.data[ctx.guild.id]["state"] == "queue":
            current_queue = "None"
            if len(self.data[ctx.guild.id]["queue"]) != 0:
                current_queue = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["queue"])
            return await ctx.channel.send(embed=discord.Embed(title=f"[{len(self.data[ctx.guild.id]['queue'])}/10] Queue", description=current_queue, color=65535))

        # // TEAM PICKING PHASE EMBED
        if self.data[ctx.guild.id]["state"] == "pick":
            orange_team="None"
            blue_team="None"
            if len(self.data[ctx.guild.id]["orange_team"]) != 0:
                orange_team = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["orange_team"])

            if len(self.data[ctx.guild.id]["blue_team"]) != 0:
                blue_team = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["blue_team"])

            embed=discord.Embed(title="Team Picking Phase", color=65535)
            embed.add_field(name="Orange Captain", value=self.data[ctx.guild.id]["orange_cap"].mention)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=self.data[ctx.guild.id]["blue_cap"].mention)
            embed.add_field(name="Orange Team", value=orange_team)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value=blue_team)
            embed.add_field(name="Available Players", value="\n".join(str(e.mention) for e in self.data[ctx.guild.id]["queue"]))
            await ctx.channel.send(embed=embed)
            return await ctx.channel.send(f"**{self.data[ctx.guild.id]['pick_logic'][0].mention} it is your turn to pick**")

        # // MAP PICKING PHASE EMBED
        if self.data[ctx.guild.id]["state"] == "maps":
            row = SQL.select(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id}")
            embed=discord.Embed(title="Map Picking Phase", color=65535)
            embed.add_field(name="Orange Captain", value=self.data[ctx.guild.id]["orange_cap"].mention)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=self.data[ctx.guild.id]["blue_cap"].mention)
            embed.add_field(name="Orange Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["orange_team"]))
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["blue_team"]))
            embed.add_field(name="Available Maps", value=str(row[1]).replace(",", "\n"))
            await ctx.channel.send(embed=embed)
            return await ctx.channel.send(f"**{self.data[ctx.guild.id]['blue_cap'].mention} select a map to play**")

        # // FINAL MATCH UP EMBED
        if self.data[ctx.guild.id]["state"] == "final":
            count = SQL.select_all(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id}")
            if count is None:
                count=[]

            embed=discord.Embed(title=f"Match #{len(count)+1}", description=f"**Map:** {self.data[ctx.guild.id]['map']}", color=65535)
            embed.add_field(name="Orange Captain", value=self.data[ctx.guild.id]["orange_cap"].mention)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=self.data[ctx.guild.id]["blue_cap"].mention)
            embed.add_field(name="Orange Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["orange_team"]))
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["blue_team"]))

            await self._match(ctx)
            await self._team_channels(ctx, len(count)+1)
            await self._reset(ctx)

            row = SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
            if row[9] != 0:
                channel = ctx.guild.get_channel(int(row[9]))
                await channel.send(
                    embed=embed,
                    components=[[
                        Button(style=ButtonStyle.blue, label="Blue", custom_id='blue_report'),
                        Button(style=ButtonStyle.blue, label="Orange", custom_id='orange_report'),
                        Button(style=ButtonStyle.red, label="Cancel", custom_id='match_cancel')
                    ]])
            return await ctx.channel.send(embed=embed)

    # // CREATE TEAM VOICE CHANNELS FUNCTION
    # /////////////////////////////////////////
    async def _team_channels(self, ctx, match_id):
        row = SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
        if row[3] == "true":
            # // CREATE MATCH CATEGORY
            category = get(ctx.guild.categories, name=f'Match #{match_id}')
            if not category:
                category = await ctx.guild.create_category(f'Match #{match_id}')
                await category.set_permissions(ctx.guild.default_role, connect=False)

                # // CREATE MATCH TEXT CHANNEL
                text_channel = await ctx.guild.create_text_channel(f"match-{match_id}", category=category)
                await text_channel.set_permissions(ctx.guild.default_role, view_channel=False)

                # // CREATE BLUE TEAM VOICE CHANNEL
                blue_vc = await ctx.guild.create_voice_channel(f'🔹 Team {self.data[ctx.guild.id]["blue_cap"].name}', category=category)
                for user in self.data[ctx.guild.id]["blue_team"]:
                    await blue_vc.set_permissions(user, connect=True)
                    await text_channel.set_permissions(user, view_channel=True)
                await blue_vc.set_permissions(self.data[ctx.guild.id]["blue_cap"], connect=True)
                await text_channel.set_permissions(self.data[ctx.guild.id]["blue_cap"], view_channel=True)

                # // CREATE ORANGE TEAM VOICE CHANNEL
                orange_vc = await ctx.guild.create_voice_channel(f"🔸 Team {self.data[ctx.guild.id]['orange_cap'].name}", category=category)
                for user in self.data[ctx.guild.id]["orange_team"]:
                    await orange_vc.set_permissions(user, connect=True)
                    await text_channel.set_permissions(user, view_channel=True)
                await orange_vc.set_permissions(self.data[ctx.guild.id]["orange_cap"], connect=True)
                await text_channel.set_permissions(self.data[ctx.guild.id]["orange_cap"], view_channel=True)

    # // MATCH LOGGING FUNCTION
    # /////////////////////////////////////////
    async def _match(self, ctx):
        orange_team = ','.join(str(e.id) for e in self.data[ctx.guild.id]['orange_team'])
        blue_team = ','.join(str(e.id) for e in self.data[ctx.guild.id]['blue_team'])

        count = SQL.select_all(f"SELECT * FROM matches WHERE guild_id = {ctx.guild.id}")
        if count is None:
            count=[]
        SQL.execute(f"""INSERT INTO matches (guild_id, match_id, map, orange_cap, orange_team, blue_cap, blue_team, status, winners) VALUES ({ctx.guild.id}, {len(count)+1}, '{self.data[ctx.guild.id]['map']}', '{self.data[ctx.guild.id]['orange_cap'].id}', '{orange_team}', '{self.data[ctx.guild.id]['blue_cap'].id}', '{blue_team}', 'ongoing', 'none')""")

    # // WHEN QUEUE REACHES 10 PEOPLE FUNCTION
    # /////////////////////////////////////////
    async def _start(self, ctx):
        row = SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
        if row[4] == "true":
            # // PICK PHASE ENABLED
            # // CREATING TEAM CAPTAINS AND LOGIC
            self.data[ctx.guild.id]["state"] = "pick"
            self.data[ctx.guild.id]["blue_cap"] = random.choice(self.data[ctx.guild.id]["queue"]); self.data[ctx.guild.id]["queue"].remove(self.data[ctx.guild.id]["blue_cap"])
            self.data[ctx.guild.id]["orange_cap"] = random.choice(self.data[ctx.guild.id]["queue"]); self.data[ctx.guild.id]["queue"].remove(self.data[ctx.guild.id]["orange_cap"])
            self.data[ctx.guild.id]["pick_logic"] = [
                self.data[ctx.guild.id]["blue_cap"], self.data[ctx.guild.id]["orange_cap"], self.data[ctx.guild.id]["orange_cap"], self.data[ctx.guild.id]["blue_cap"],
                self.data[ctx.guild.id]["blue_cap"], self.data[ctx.guild.id]["orange_cap"], self.data[ctx.guild.id]["blue_cap"]]
        else: 
            # // PICK PHASE DISABLED
            # // CREATING TEAM CAPTAINS
            self.data[ctx.guild.id]["blue_cap"] = random.choice(self.data[ctx.guild.id]["queue"]); self.data[ctx.guild.id]["queue"].remove(self.data[ctx.guild.id]["blue_cap"])
            self.data[ctx.guild.id]["orange_cap"] = random.choice(self.data[ctx.guild.id]["queue"]); self.data[ctx.guild.id]["queue"].remove(self.data[ctx.guild.id]["orange_cap"])

            # // CREATING THE RANDOM TEAMS
            for _ in range(round(len(self.data[ctx.guild.id]["queue"]) / 2)):
                _user = random.choice(self.data[ctx.guild.id]["queue"])
                self.data[ctx.guild.id]['orange_team'].append(_user); self.data[ctx.guild.id]["queue"].remove(_user)
            
            for _ in range(round(len(self.data[ctx.guild.id]["queue"]))):
                _user = random.choice(self.data[ctx.guild.id]["queue"])
                self.data[ctx.guild.id]['blue_team'].append(_user); self.data[ctx.guild.id]["queue"].remove(_user)
            
            # // CHECKING IF MAP PHASE IS DISABLED/ENABLED
            if row[2] == "true":
                self.data[ctx.guild.id]["state"] = "maps"
            else:
                _row = SQL.select(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id}")
                self.data[ctx.guild.id]["map"] = random.choice(str(_row[1]).split(","))
                self.data[ctx.guild.id]["state"] = "final"

    # // CHECK IF THE USER IS BANNED FUNCTION
    # /////////////////////////////////////////
    async def _ban_check(self, ctx, user):
        if SQL.exists(f"SELECT * FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}"):
            row = SQL.select(f"SELECT * FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
            if row[2] - time.time() > 0:
                await ctx.channel.send(embed=discord.Embed(title=f"{user.name} is banned", description=f"**Length:** {datetime.timedelta(seconds=int(row[2] - time.time()))}\n**Reason:** {row[3]}\n**Banned by:** {row[4]}", color=65535))
                return False
            SQL.execute(f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}")
        return True
    
    # // WHEN AN USER JOINS THE QUEUE FUNCTION
    # /////////////////////////////////////////
    async def _join(self, ctx, user):
        if await self._data_check(ctx):
            if SQL.exists(f"SELECT * FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}"):
                row = SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
                if await self._ban_check(ctx, user):
                    if row[5] == 0 or ctx.message.channel.id == row[5]:
                        if self.data[ctx.guild.id]["state"] == "queue":
                            if not user in self.data[ctx.guild.id]["queue"]:
                                self.data[ctx.guild.id]["queue"].append(user)
                                if len(self.data[ctx.guild.id]["queue"]) == 10:
                                    await self._start(ctx)
                                    return await self._embeds(ctx)
                                return await ctx.channel.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id]['queue'])}/10]** {user.mention} has joined the queue", color=65535))
                            return await ctx.channel.send(embed=discord.Embed(description=f"{user.mention} is already in the queue", color=65535))
                        return await ctx.channel.send(embed=discord.Embed(description=f"{user.mention} it is not the queueing phase", color=65535))
                    return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} {ctx.guild.get_channel(row[5]).mention}", color=65535))
                return False
            return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} is not registered", color=65535))
        return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=16711680))

    # // WHEN AN USER LEAVES THE QUEUE FUNCTION
    # /////////////////////////////////////////
    async def _leave(self, ctx, user):
        if await self._data_check(ctx):
            row = SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")
            if row[5] == 0 or ctx.message.channel.id == row[5]:
                if self.data[ctx.guild.id]["state"] == "queue":
                    if user in self.data[ctx.guild.id]["queue"]:
                        self.data[ctx.guild.id]["queue"].remove(user)
                        return await ctx.channel.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id]['queue'])}/10]** {user.mention} has left the queue", color=65535))
                    return await ctx.channel.send(embed=discord.Embed(description=f"{user.mention} is not in the queue", color=65535))
                return await ctx.channel.send(embed=discord.Embed(description=f"{user.mention} it is not the queueing phase", color=65535))
            return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} {ctx.guild.get_channel(row[5]).mention}", color=65535))
        return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=16711680))

    
    # // FORCE START THE QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["fs"])
    @commands.has_permissions(manage_messages=True)
    async def forcestart(self, ctx):
        await self._start(ctx)
        return await self._embeds(ctx)

    # // PICK TEAMMATES (TEAM CAPTAIN) COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["p"])
    async def pick(self, ctx, user:discord.Member):
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
                    await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} has picked {user.mention}", color=65535))

                    if len(self.data[ctx.guild.id]["queue"]) == 1:
                        self.data[ctx.guild.id]["orange_team"].append(self.data[ctx.guild.id]["queue"][0])
                        self.data[ctx.guild.id]["queue"].remove(self.data[ctx.guild.id]["queue"][0])
                    
                    if len(self.data[ctx.guild.id]["queue"]) == 0:
                        row = SQL.select(f"SELECT * FROM settings WHERE guild_id = {ctx.guild.id}")

                        self.data[ctx.guild.id]["state"] = "final"
                        if row[2] == "true":
                            self.data[ctx.guild.id]["state"] = "maps"
                            
                    return await self._embeds(ctx)
                return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not your turn to pick", color=65535))
            return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the picking phase", color=65535))
        return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=16711680))
    
    # // PICK MAP TO PLAY (BLUE CAPTAIN) COMMAND
    # ///////////////////////////////////////////
    @commands.command()
    async def map(self, ctx, map:str):
        if await self._data_check(ctx):
            if self.data[ctx.guild.id]["state"] == "maps":
                if ctx.author == self.data[ctx.guild.id]["blue_cap"]:
                    row = SQL.select(f"SELECT * FROM maps WHERE guild_id = {ctx.guild.id}")
                    if map in str(row[1]).split(","):
                        self.data[ctx.guild.id]["map"] = map
                        self.data[ctx.guild.id]["state"] = "final"
                        return await self._embeds(ctx)
                    return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} that map is not in the map pool", color=65535))
                return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not the blue team captain", color=65535))
            return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the map picking phase", color=65535))
        return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=16711680))
    
    # // JOIN THE QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["j"])
    async def join(self, ctx):
        return await self._join(ctx, ctx.author)

    # // FORCE ADD AN USER TO THE QUEUE COMMAND
    # //////////////////////////////////////////
    @commands.command(aliases=["fj"])
    async def forcejoin(self, ctx, user:discord.Member):
        return await self._join(ctx, user)

    # // LEAVE THE QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["l"])
    async def leave(self, ctx):
        return await self._leave(ctx, ctx.author)

    # // FORCE REMOVE A PLAYER FROM THE QUEUE COMMAND
    # ////////////////////////////////////////////////
    @commands.command(aliases=["fl"])
    async def forceleave(self, ctx, user:discord.Member):
        return await self._leave(ctx, user)

    # // SHOW THE CURRENT QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        if await self._data_check(ctx):
            return await self._embeds(ctx)
        return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=16711680))
    
    # // CLEAR THE CURRENT QUEUE COMMAND
    # /////////////////////////////////////////
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx):
        if await self._data_check(ctx):
            await self._reset(ctx)
            return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} has cleared the queue", color=65535))
        return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=16711680))


    # // BUTTON CLICK LISTENER
    # /////////////////////////////////////////
    @commands.Cog.listener()
    async def on_button_click(self, res):
        if res.component.id == "join_queue":
            await self._join(res, res.author)
            players = "\n".join(str(enum.mention) for enum in self.data[res.guild.id]["queue"])
            return await res.message.edit(embed=discord.Embed(title=f'[{len(self.data[res.guild.id]["queue"])}/10] Queue', description=f'{players}', color=65535))

        if res.component.id == "leave_queue":
            await self._leave(res, res.author)
            players = "\n".join(str(enum.mention) for enum in self.data[res.guild.id]["queue"])
            return await res.message.edit(embed=discord.Embed(title=f'[{len(self.data[res.guild.id]["queue"])}/10] Queue', description=f'{players}', color=65535))


def setup(client):
    client.add_cog(Queue(client))