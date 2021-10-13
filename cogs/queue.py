import discord, sqlite3, random, time
from discord.ext import commands
from discord.utils import get
import datetime as datetime

class Queue(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data = {}


    # MAIN FUNCTIONS
    # ////////////////////////
    async def _reset(self, ctx):
        self.data[ctx.guild.id] = {"queue": [], "blue_cap": "", "blue_team": [], "orange_cap": "", "orange_team": [], "pick_logic": [], "map": "", "state": "queue"}
        
    async def _data_check(self, ctx):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM settings WHERE guild_id = {ctx.guild.id});").fetchall()[0] == (0,):
                cur.execute(f"INSERT INTO settings VALUES ({ctx.guild.id}, 0, 'true', 'false', 'true', 0, 0)")
                db.commit()

            if ctx.guild.id not in self.data:
                await self._reset(ctx)
            return True

    async def _embeds(self, ctx):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            
            # // QUEUE PHASE EMBED
            if self.data[ctx.guild.id]["state"] == "queue":
                current_queue = "None"
                if len(self.data[ctx.guild.id]["queue"]) != 0:
                    current_queue = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["queue"])
                return await ctx.send(embed=discord.Embed(title=f"[{len(self.data[ctx.guild.id]['queue'])}/10] Queue", description=current_queue, color=65535))

            # // TEAM PICKING PHASE EMBED
            if self.data[ctx.guild.id]["state"] == "pick":
                orange_team="None"
                blue_team="None"
                if len(self.data[ctx.guild.id]["orange_team"]) == 0:
                    orange_team = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["orange_team"])

                if len(self.data[ctx.guild.id]["blue_team"]) == 0:
                    blue_team = '\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["blue_team"])

                embed=discord.Embed(title="Team Picking Phase", color=65535)
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
                for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
                    embed=discord.Embed(title="Map Picking Phase", color=65535)
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
                match_count=0
                for _ in cur.execute(f'SELECT * FROM matches WHERE guild_id = {ctx.guild.id}'):
                    match_count+=1

                embed=discord.Embed(title=f"Match #{match_count}", description=f"**Map:** {self.data[ctx.guild.id]['map']}", color=65535)
                embed.add_field(name="Orange Captain", value=self.data[ctx.guild.id]["orange_cap"].mention)
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="Blue Captain", value=self.data[ctx.guild.id]["blue_cap"].mention)
                embed.add_field(name="Orange Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["orange_team"]))
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="Blue Team", value='\n'.join(str(e.mention) for e in self.data[ctx.guild.id]["blue_team"]))

                await self._match(ctx)
                await self._team_vc(ctx)
                await self._reset(ctx)
                return await ctx.send(embed=embed)

    # // CREATE TEAM VOICE CHANNELS FUNCTION
    async def _team_vc(self, ctx):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            for row in cur.execute(f'SELECT * FROM settings WHERE guild_id = {ctx.guild.id}'):
                if row[3] == "true":
                    category = get(ctx.guild.categories, name='ten mans')
                    if not category:
                        category = await ctx.guild.create_category('ten mans')

                    blue_vc = await ctx.guild.create_voice_channel(f'🔹 Team {self.data[ctx.guild.id]["blue_cap"].name}', category=category)
                    await blue_vc.set_permissions(ctx.guild.default_role, connect=False)
                    for user in self.data[ctx.guild.id]["blue_team"]:
                        await blue_vc.set_permissions(user, connect=True)

                    orange_vc = await ctx.guild.create_voice_channel(f"🔸 Team {self.data[ctx.guild.id]['orange_cap'].name}", category=category)
                    await orange_vc.set_permissions(ctx.guild.default_role, connect=False)
                    for user in self.data[ctx.guild.id]["orange_team"]:
                        await orange_vc.set_permissions(user, connect=True)

    # // MATCH LOGGING FUNCTION
    async def _match(self, ctx):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            orange_team = ','.join(str(e.id) for e in self.data[ctx.guild.id]['orange_team'])
            blue_team = ','.join(str(e.id) for e in self.data[ctx.guild.id]['blue_team'])
            match_count=0

            for _ in cur.execute(f'SELECT * FROM matches WHERE guild_id = {ctx.guild.id}'):
                match_count+=1
            cur.execute(f"""INSERT INTO matches VALUES ({ctx.guild.id}, {match_count}, '{self.data[ctx.guild.id]['map']}', '{self.data[ctx.guild.id]['orange_cap'].id}', '{orange_team}', '{self.data[ctx.guild.id]['blue_cap'].id}', '{blue_team}', 'ongoing', 'none')""")
            db.commit()

    # // STARTING FUNCTION FOR AFTER QUEUE REACHES 10 PEOPLE
    async def _start(self, ctx):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            for row in cur.execute(f'SELECT * FROM settings WHERE guild_id = {ctx.guild.id}'):
                if row[4] == "true":
                    # // PICK PHASE ENABLED
                    # // CREATING TEAM CAPTAINS AND LOGIC
                    self.data[ctx.guild.id]["state"] = "pick"
                    self.data[ctx.guild.id]["blue_cap"] = random.choice(self.data[ctx.guild.id]["queue"]); self.data[ctx.guild.id]["queue"].remove(self.data[ctx.guild.id]["blue_cap"])
                    self.data[ctx.guild.id]["orange_cap"] = random.choice(self.data[ctx.guild.id]["queue"]); self.data[ctx.guild.id]["queue"].remove(self.data[ctx.guild.id]["orange_cap"])
                    self.data[ctx.guild.id]["pick_logic"] = [
                        self.data[ctx.guild.id]["blue_cap"], self.data[ctx.guild.id]["orange_cap"], self.data[ctx.guild.id]["orange_cap"], self.data[ctx.guild.id]["blue_cap"],
                        self.data[ctx.guild.id]["blue_cap"], self.data[ctx.guild.id]["orange_cap"], self.data[ctx.guild.id]["blue_cap"], self.data[ctx.guild.id]["orange_cap"]]
                else: 
                    # // PICK PHASE DISABLED
                    # // CREATING TEAM CAPTAINS
                    self.data[ctx.guild.id]["blue_cap"] = random.choice(self.data[ctx.guild.id]["queue"]); self.data[ctx.guild.id]["queue"].remove(self.data[ctx.guild.id]["blue_cap"])
                    self.data[ctx.guild.id]["orange_cap"] = random.choice(self.data[ctx.guild.id]["queue"]); self.data[ctx.guild.id]["queue"].remove(self.data[ctx.guild.id]["orange_cap"])

                    # // CREATING THE RANDOM TEAMS
                    for _ in range(round(len(self.data[ctx.guild.id]["queue"] / 2))):
                        _user = random.choice(self.data[ctx.guild.id]["queue"])
                        self.data[ctx.guild.id]['orange_team'].append(_user); self.data[ctx.guild.id]["queue"].remove(_user)
                    
                    for _ in range(round(len(self.data[ctx.guild.id]["queue"]))):
                        _user = random.choice(self.data[ctx.guild.id]["queue"])
                        self.data[ctx.guild.id]['blue_team'].append(_user); self.data[ctx.guild.id]["queue"].remove(_user)
                    
                    # // CHECKING IF MAP PHASE IS DISABLED/ENABLED
                    if row[2] == "true":
                        self.data[ctx.guild.id]["state"] = "maps"
                    else:
                        for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
                            self.data[ctx.guild.id]["map"] = random.choice(str(row[1]).split(","))
                        self.data[ctx.guild.id]["state"] = "final"

    # // CHECK IF THE USER IS BANNED FUNCTION
    async def _ban_check(self, ctx, user):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                for row in cur.execute(f'SELECT * FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id}'):
                    if row[2] - time.time() > 0:
                        await ctx.send(embed=discord.Embed(title=f"{user.name} is banned", description=f"**Length:** {datetime.timedelta(seconds=int(row[2] - time.time()))}\n**Reason:** {row[3]}\n**Banned by:** {row[4]}", color=65535))
                        return False
                cur.execute(f"DELETE FROM bans WHERE guild_id = {ctx.guild.id} AND user_id = {user.id};")
                db.commit()
            return True
    
    # // ON JOIN FUNCTION
    async def _join(self, ctx, user):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if await self._data_check(ctx):
                if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id});").fetchall()[0] == (1,):
                    for row in cur.execute(f'SELECT * FROM settings WHERE guild_id = {ctx.guild.id}'):
                        if await self._ban_check(ctx, user):
                            if row[5] == 0 or ctx.message.channel.id == row[5]:
                                if self.data[ctx.guild.id]["state"] == "queue":
                                    if not user in self.data[ctx.guild.id]["queue"]:
                                        self.data[ctx.guild.id]["queue"].append(user)
                                        if len(self.data[ctx.guild.id]["queue"]) == 10:
                                            await self._start(ctx)
                                            return await self._embeds(ctx)
                                        return await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id]['queue'])}/10]** {user.mention} has joined the queue", color=65535))
                                    return await ctx.send(embed=discord.Embed(description=f"{user.mention} is already in the queue", color=65535))
                                return await ctx.send(embed=discord.Embed(description=f"{user.mention} it is not the queueing phase", color=65535))
                            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} join the queue in {ctx.guild.get_channel(row[5]).mention}", color=65535))
                        return False
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} is not registered", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=16711680))

    # // ON LEAVE FUNCTION
    async def _leave(self, ctx, user):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if await self._data_check(ctx):
                for row in cur.execute(f'SELECT * FROM settings WHERE guild_id = {ctx.guild.id}'):
                    if row[5] == 0 or ctx.message.channel.id == row[5]:
                        if self.data[ctx.guild.id]["state"] == "queue":
                            if user in self.data[ctx.guild.id]["queue"]:
                                self.data[ctx.guild.id]["queue"].remove(user)
                                return await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id]['queue'])}/10]** {user.mention} has left the queue", color=65535))
                            return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not in the queue", color=65535))
                        return await ctx.send(embed=discord.Embed(description=f"{user.mention} it is not the queueing phase", color=65535))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} leave the queue in {ctx.guild.get_channel(row[5]).mention}", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=16711680))

    
    # MAIN COMMANDS
    # ////////////////////////
    @commands.command(aliases=["fs"])
    @commands.has_permissions(manage_messages=True)
    async def forcestart(self, ctx):
        await self._start(ctx)
        return await self._embeds(ctx)


    @commands.command(aliases=["p"])
    async def pick(self, ctx, user:discord.Member):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
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
                        await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has picked {user.mention}", color=65535))
                        
                        if len(self.data[ctx.guild.id]["queue"]) == 0:
                            for row in cur.execute(f'SELECT * FROM settings WHERE guild_id = {ctx.guild.id}'):
                                if row[2] == "true":
                                    self.data[ctx.guild.id]["state"] = "maps"
                                else:
                                    self.data[ctx.guild.id]["state"] = "final"
                        return await self._embeds(ctx)
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not your turn to pick", color=65535))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the picking phase", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=16711680))
            
    @commands.command()
    async def map(self, ctx, map:str):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if await self._data_check(ctx):
                if self.data[ctx.guild.id]["state"] == "maps":
                    if ctx.author == self.data[ctx.guild.id]["blue_cap"]:
                        for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
                            if map in str(row[1]).split(","):
                                self.data[ctx.guild.id]["map"] = map
                                self.data[ctx.guild.id]["state"] = "final"
                                return await self._embeds(ctx)
                        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} that map is not in the map pool", color=65535))
                    return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not the blue team captain", color=65535))
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the map picking phase", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=16711680))
        
    @commands.command(aliases=["j"])
    async def join(self, ctx):
        return await self._join(ctx, ctx.author)

    @commands.command(aliases=["fj"])
    async def forcejoin(self, ctx, user:discord.Member):
        return await self._join(ctx, user)

    @commands.command(aliases=["l"])
    async def leave(self, ctx):
        return await self._leave(ctx, ctx.author)

    @commands.command(aliases=["fl"])
    async def forceleave(self, ctx, user:discord.Member):
        return await self._leave(ctx, user)

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        if await self._data_check(ctx):
            return await self._embeds(ctx)
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=16711680))
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx):
        if await self._data_check(ctx):
            await self._reset(ctx)
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has cleared the queue", color=65535))
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} an internal error has occured!", color=16711680))


def setup(client):
    client.add_cog(Queue(client))