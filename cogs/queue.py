from discord.ext.commands import has_permissions
import discord, sqlite3, random, time
from discord.ext import commands
import datetime as datetime

db = sqlite3.connect('main.db')
cur = db.cursor()

class Queue(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.data = {}

    async def check_data(self, guild):
        if guild.id not in self.data:
            self.data[guild.id] = {"queue": [], "blue_cap": "", "blue_team": [], "orange_cap": "", "orange_team": [], "pick_logic": [], "map": "", "state": "queue"}
        return True

    async def embed_gen(self, guild):
        if self.data[guild.id]["state"] == "queue":
            if len(self.data[guild.id]["queue"]) == 0:
                current_queue = "None"
            else:
                current_queue = '\n'.join(str(e.mention) for e in self.data[guild.id]["queue"])
            return discord.Embed(title=f"[{len(self.data[guild.id]['queue'])}/10] Queue", description=current_queue, color=65535)

        if self.data[guild.id]["state"] == "pick":
            if len(self.data[guild.id]["orange_team"]) == 0:
                o_team = "None"
            else:
                o_team = '\n'.join(str(e.mention) for e in self.data[guild.id]["orange_team"])

            if len(self.data[guild.id]["blue_team"]) == 0:
                b_team = "None"
            else:
                b_team = '\n'.join(str(e.mention) for e in self.data[guild.id]["blue_team"])

            embed=discord.Embed(title="Picking Phase", color=65535)
            embed.add_field(name="Orange Captain", value=self.data[guild.id]["orange_cap"].mention)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=self.data[guild.id]["blue_cap"].mention)
            embed.add_field(name="Orange Team", value=o_team)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value=b_team)
            embed.add_field(name="Available Players", value="\n".join(str(e.mention) for e in self.data[guild.id]["queue"]))
            return embed

        if self.data[guild.id]["state"] == "maps":
            for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {guild.id}'):
                embed=discord.Embed(title="Map Phase", color=65535)
                embed.add_field(name="Orange Captain", value=self.data[guild.id]["orange_cap"].mention)
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="Blue Captain", value=self.data[guild.id]["blue_cap"].mention)
                embed.add_field(name="Orange Team", value='\n'.join(str(e.mention) for e in self.data[guild.id]["orange_team"]))
                embed.add_field(name="\u200b", value="\u200b")
                embed.add_field(name="Blue Team", value='\n'.join(str(e.mention) for e in self.data[guild.id]["blue_team"]))
                embed.add_field(name="Available Maps", value=str(row[1]).replace(",", "\n"))
                return embed

        if self.data[guild.id]["state"] == "final":
            embed=discord.Embed(title="Final Match Up", description=f"**Map:** {self.data[guild.id]['map']}", color=65535)
            embed.add_field(name="Orange Captain", value=self.data[guild.id]["orange_cap"].mention)
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Captain", value=self.data[guild.id]["blue_cap"].mention)
            embed.add_field(name="Orange Team", value='\n'.join(str(e.mention) for e in self.data[guild.id]["orange_team"]))
            embed.add_field(name="\u200b", value="\u200b")
            embed.add_field(name="Blue Team", value='\n'.join(str(e.mention) for e in self.data[guild.id]["blue_team"]))

            await self.add_match(guild)
            await self.reset(guild)
            return embed

    async def add_match(self, guild):
        orange_team = ','.join(str(e.id) for e in self.data[guild.id]['orange_team'])
        blue_team = ','.join(str(e.id) for e in self.data[guild.id]['blue_team'])
        match_count=0

        for _ in cur.execute(f'SELECT * FROM matches WHERE guild_id = {guild.id}'):
            match_count+=1
        cur.execute(f"""INSERT INTO matches VALUES ({guild.id}, {match_count}, '{self.data[guild.id]['map']}', '{self.data[guild.id]['orange_cap'].id}', '{orange_team}', '{self.data[guild.id]['blue_cap'].id}', '{blue_team}', 'ongoing')""")
        db.commit()

    async def on_join(self, guild, user):
        if await self.check_data(guild):
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
                for row in cur.execute(f'SELECT * FROM bans WHERE guild_id = {guild.id} AND user_id = {user.id}'):
                    if row[2] - time.time() > 0:
                        return discord.Embed(title=f"{user.name} is banned", description=f"**Length:** {datetime.timedelta(seconds=int(row[2] - time.time()))}\n**Reason:** {row[3]}\n**Banned by:** {row[4]}", color=65535)
                    else:
                        cur.execute(f"DELETE FROM bans WHERE guild_id = {guild.id} AND user_id = {user.id};")
            #if not user in self.data[guild.id]["queue"]:
            self.data[guild.id]["queue"].append(user)
            if len(self.data[guild.id]["queue"]) == 10:
                self.data[guild.id]["state"] = "pick"
                self.data[guild.id]["blue_cap"] = random.choice(self.data[guild.id]["queue"]); self.data[guild.id]["queue"].remove(self.data[guild.id]["blue_cap"])
                self.data[guild.id]["orange_cap"] = random.choice(self.data[guild.id]["queue"]); self.data[guild.id]["queue"].remove(self.data[guild.id]["orange_cap"])
                self.data[guild.id]["pick_logic"] = [
                    self.data[guild.id]["blue_cap"], self.data[guild.id]["orange_cap"], self.data[guild.id]["orange_cap"], self.data[guild.id]["blue_cap"],
                    self.data[guild.id]["blue_cap"], self.data[guild.id]["orange_cap"], self.data[guild.id]["blue_cap"], self.data[guild.id]["orange_cap"]]
                return await self.embed_gen(guild)
            return discord.Embed(description=f"**[{len(self.data[guild.id]['queue'])}/10]** {user.mention} has joined the queue", color=65535)
    
    async def on_leave(self, guild, user):
        if await self.check_data(guild):
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM bans WHERE guild_id = {guild.id} AND user_id = {user.id});").fetchall()[0] == (0,):
                if user in self.data[guild.id]["queue"]:
                    self.data[guild.id]["queue"].remove(user)
                    return discord.Embed(description=f"**[{len(self.data[guild.id]['queue'])}/10]** {user.mention} has left the queue", color=65535)

    async def reset(self, guild):
        self.data[guild.id] = {"queue": [], "blue_cap": "", "blue_team": [], "orange_cap": "", "orange_team": [], "pick_logic": [], "map": "", "state": "queue"}

    @commands.command(aliases=["p"])
    async def pick(self, ctx, user:discord.Member):
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
                    self.data[ctx.guild.id]["state"] = "maps"
                    await ctx.send(embed=await self.embed_gen(ctx.guild))
                    await ctx.send(f"**{self.data[ctx.guild.id]['blue_cap'].mention} select a map to play**")
                    return
                await ctx.send(embed=await self.embed_gen(ctx.guild))
                await ctx.send(f"**{self.data[ctx.guild.id]['pick_logic'][0].mention} it is your turn to pick**")
    
    @commands.command()
    async def map(self, ctx, map:str):
        if ctx.author == self.data[ctx.guild.id]["blue_cap"] and self.data[ctx.guild.id]["state"] == "maps":
            for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
                if map in str(row[1]).split(","):
                    self.data[ctx.guild.id]["map"] = map
                    self.data[ctx.guild.id]["state"] = "final"
                    await ctx.send(embed=await self.embed_gen(ctx.guild))
            
    @commands.command(aliases=["j"])
    async def join(self, ctx):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {ctx.author.id});").fetchall()[0] == (1,):
            await ctx.send(embed=await self.on_join(ctx.guild, ctx.author))

    @commands.command(aliases=["fj"])
    async def forcejoin(self, ctx, user:discord.Member):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM users WHERE guild_id = {ctx.guild.id} AND user_id = {user.id});").fetchall()[0] == (1,):
            await ctx.send(embed=await self.on_join(ctx.guild, user))

    @commands.command(aliases=["l"])
    async def leave(self, ctx):
        await ctx.send(embed=await self.on_leave(ctx.guild, ctx.author))

    @commands.command(aliases=["fl"])
    async def forceleave(self, ctx, user:discord.Member):
        await ctx.send(embed=await self.on_leave(ctx.guild, user))

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        if await self.check_data(ctx.guild):
            await ctx.send(embed=await self.embed_gen(ctx.guild))
    
    @commands.command()
    @has_permissions(manage_messages=True)
    async def clear(self, ctx):
        if await self.check_data(ctx.guild):
            await self.reset(ctx.guild)
            await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has cleared the queue", color=65535))


def setup(client):
    client.add_cog(Queue(client))