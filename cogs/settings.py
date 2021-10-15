from discord_components import *
from discord.ext import commands
import discord, sqlite3

class Settings(commands.Cog):
    def __init__(self, client):
        self.client = client

    # // RETURN CORRESPONDING EMOJI TO SETTING
    # /////////////////////////////////////////
    async def _emojis(self, ctx, option):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM settings WHERE guild_id = {ctx.guild.id});").fetchall()[0] == (0,):
                cur.execute(f"INSERT INTO settings VALUES ({ctx.guild.id}, 0, 'true', 'false', 'true', 0, 0, 5, 2, 0)")
                db.commit()

            for row in cur.execute(f'SELECT * FROM settings WHERE guild_id = {ctx.guild.id}'):
                # // MAP PICKING PHASE
                if option == "map_pick_phase":
                    if row[2] == "true":
                        return ["🟢", "Disable"]
                    return ["🔴", "Enable"]

                # // TEAM CAPTAIN VOICE CHANNELS
                if option == "team_cap_vc":
                    if row[3] == "true":
                        return ["🟢", "Disable"]
                    return ["🔴", "Enable"]

                # // TEAM CAPTAINS
                if option == "picking_phase":
                    if row[4] == "true":
                        return ["🟢", "Disable"]
                    return ["🔴", "Enable"]

                # // MATCH LOGGING
                if option == "match_logging":
                    if row[9] != 0:
                        return ["🟢", "Disable"]
                    return ["🔴", "Enable"]


    # // ADD MAP TO THE DATABASE
    # /////////////////////////////////////////
    async def _add_map(self, ctx, map):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM maps WHERE guild_id = {ctx.guild.id});").fetchall()[0] == (0,):
                cur.execute(f"INSERT INTO maps VALUES ({ctx.guild.id}, '{map}')")
                db.commit()
            else:
                for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
                    if map not in str(row[1]).split(","):
                        cur.execute(f"UPDATE maps SET map_list = '{str(row[1])},{map}' WHERE guild_id = {ctx.guild.id}")
                        db.commit()
            return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} added **{map}** to the map pool", color=65535), delete_after=2)

    # // REMOVE MAP FROM THE DATABASE
    # /////////////////////////////////////////
    async def _del_map(self, ctx, map):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM maps WHERE guild_id = {ctx.guild.id});").fetchall()[0] == (1,):
                for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
                    if map in str(row[1]).split(","):
                        map_list = str(row[1]).split(',')
                        map_list.remove(map)
                        cur.execute(f"UPDATE maps SET map_list = '{','.join(str(e) for e in map_list)}' WHERE guild_id = {ctx.guild.id}")
                        db.commit()
                        return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} removed **{map}** from the map pool", color=65535), delete_after=2)
                    return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} **{map}** is not in the map pool", color=65535), delete_after=2)
            return await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} the map pool is empty", color=65535), delete_after=2)


    # // ADD MAP COMMAND
    # /////////////////////////////////////////
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addmap(self, ctx, map:str):
        await self._add_map(ctx, map)

    # // DELETE MAP COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["removemap", "deletemap"])
    @commands.has_permissions(administrator=True)
    async def delmap(self, ctx, map:str):
        await self._del_map(ctx, map)

    # // SHOW LIST OF MAPS COMMAND
    # /////////////////////////////////////////
    @commands.command()
    async def maps(self, ctx):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
                return await ctx.channel.send(embed=discord.Embed(title="Maps", description=str(row[1]).replace(",", "\n"), color=65535))

    # // SET THE REGISTER ROLE COMMAND
    # /////////////////////////////////////////
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def regrole(self, ctx, role:discord.Role):
        with sqlite3.connect('main.db', timeout=60) as db:
            cur = db.cursor()
            if cur.execute(f"SELECT EXISTS(SELECT 1 FROM settings WHERE guild_id = {ctx.guild.id});").fetchall()[0] == (0,):
                cur.execute(f"INSERT INTO settings VALUES ({ctx.guild.id}, 0, 'true', 'false', 'true', 0, 0, 5, 2, 0)")
                db.commit()
            else:
                cur.execute(f"UPDATE settings SET reg_role = {role.id} WHERE guild_id = {ctx.guild.id}")
                db.commit()
            return await ctx.channel.send(embed=discord.Embed(description=f'{ctx.author.mention} set the register role to {role.mention}', color=65535), delete_after=2)

    # // SHOW SETTINGS MENU COMMAND
    # /////////////////////////////////////////
    @commands.command(aliases=["sets"])
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        await ctx.message.delete()
        picking_phase = await self._emojis(ctx, "picking_phase")
        map_pick_phase = await self._emojis(ctx, "map_pick_phase")
        team_cap_vc = await self._emojis(ctx, "team_cap_vc")
        match_logging = await self._emojis(ctx, "match_logging")

        await ctx.channel.send(embed=discord.Embed(description=f"{ctx.author.mention} ┃ **Ten Man's Settings Menu**", color=65535),
            components=[
                Select(
                    placeholder="View Settings",
                    options=[
                        SelectOption(emoji=f'🔵', label="Add Map", value="add_map"),
                        SelectOption(emoji=f'🔵', label="Remove Map", value="remove_map"),
                        SelectOption(emoji=f'🔵', label="Change Elo Per Win", value="change_win_elo"),
                        SelectOption(emoji=f'🔵', label="Change Elo Per Loss", value="change_loss_elo"),
                        SelectOption(emoji=f'🔵', label="Create Queue Embed", value="queue_embed"),
                        SelectOption(emoji=f'🔵', label="Change Register Role", value="change_reg_role"),
                        SelectOption(emoji=f'🔵', label="Change Queue Channel", value="change_queue_channel"),
                        SelectOption(emoji=f'🔵', label="Change Register Channel", value="change_reg_channel"),
                        SelectOption(emoji=f'{match_logging[0]}', label=f"{match_logging[1]} Match Logging", value="match_logging"),
                        SelectOption(emoji=f'{map_pick_phase[0]}', label=f"{map_pick_phase[1]} Map Picking Phase", value="map_pick_phase"),
                        SelectOption(emoji=f'{picking_phase[0]}', label=f"{picking_phase[1]} Team Picking Phase", value="picking_phase"),
                        SelectOption(emoji=f'{team_cap_vc[0]}', label=f"{team_cap_vc[1]} Team Captain Voice Channels", value="team_cap_vc")
                    ])])

    # // SELECT MENU LISTENER
    # /////////////////////////////////////////
    @commands.Cog.listener()
    async def on_select_option(self, res):
        # // MAP PICKING PHASE
        if res.values[0] == 'map_pick_phase':
            if res.author.guild_permissions.administrator:
                with sqlite3.connect('main.db', timeout=60) as db:
                    cur = db.cursor()
                    for row in cur.execute(f'SELECT * FROM settings WHERE guild_id = {res.guild.id}'):
                        if row[2] == "false":
                            cur.execute(f"UPDATE settings SET map_pick_phase = 'true' WHERE guild_id = {res.guild.id}"); db.commit()
                            return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Map Picking Phase**", color=65535), delete_after=2)

                        cur.execute(f"UPDATE settings SET map_pick_phase = 'false' WHERE guild_id = {res.guild.id}"); db.commit()
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Map Picking Phase**", color=65535), delete_after=2)

        # // TEAM CAPTAIN VOICE CHANNELS
        if res.values[0] == 'team_cap_vc':
            if res.author.guild_permissions.administrator:
                with sqlite3.connect('main.db', timeout=60) as db:
                    cur = db.cursor()
                    for row in cur.execute(f'SELECT * FROM settings WHERE guild_id = {res.guild.id}'):
                        if row[3] == "false":
                            cur.execute(f"UPDATE settings SET team_cap_vcs = 'true' WHERE guild_id = {res.guild.id}"); db.commit()
                            return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Team Captain Voice Channels**", color=65535), delete_after=2)

                        cur.execute(f"UPDATE settings SET team_cap_vcs = 'false' WHERE guild_id = {res.guild.id}"); db.commit()
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Team Captain Voice Channels**", color=65535), delete_after=2)

        # // TEAM CAPTAINS
        if res.values[0] == 'picking_phase':
            if res.author.guild_permissions.administrator:
                with sqlite3.connect('main.db', timeout=60) as db:
                    cur = db.cursor()
                    for row in cur.execute(f'SELECT * FROM settings WHERE guild_id = {res.guild.id}'):
                        if row[4] == "false":
                            cur.execute(f"UPDATE settings SET picking_phase = 'true' WHERE guild_id = {res.guild.id}"); db.commit()
                            return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Team Captains**", color=65535), delete_after=2)

                        cur.execute(f"UPDATE settings SET picking_phase = 'false' WHERE guild_id = {res.guild.id}"); db.commit()
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Team Captains**", color=65535), delete_after=2)

        # // CHANGE THE REGISTER ROLE
        if res.values[0] == "change_reg_role":
            if res.author.guild_permissions.administrator:
                with sqlite3.connect('main.db', timeout=60) as db:
                    cur = db.cursor()
                    await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} mention the role you want to use", color=65535))
                    c = await self.client.wait_for('message', check=lambda message: message.author == res.author)
                    if "<@" in str(c.content):
                        role = res.guild.get_role(int(str(c.content).strip("<").strip(">").strip("@").strip("&")))
                        cur.execute(f"UPDATE settings SET reg_role = {role.id} WHERE guild_id = {res.guild.id}"); db.commit()
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} set the register role to {role.mention}", color=65535), delete_after=2)
                    return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} role not found", color=65535))

        # // ADD MAP
        if res.values[0] == "add_map":
            if res.author.guild_permissions.administrator:
                await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} respond with the map name", color=65535))
                c = await self.client.wait_for('message', check=lambda message: message.author == res.author)
                await self._add_map(res, c.content)

        # // REMOVE MAP
        if res.values[0] == "remove_map":
            if res.author.guild_permissions.administrator:
                await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} respond with the map name", color=65535))
                c = await self.client.wait_for('message', check=lambda message: message.author == res.author)
                await self._del_map(res, c.content)

        # // CHANGE THE QUEUE CHANNEL
        if res.values[0] == "change_queue_channel":
            if res.author.guild_permissions.administrator:
                with sqlite3.connect('main.db', timeout=60) as db:
                    cur = db.cursor()
                    await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} mention the channel you want to use", color=65535))
                    c = await self.client.wait_for('message', check=lambda message: message.author == res.author)
                    
                    if "<#" not in str(c.content):
                        cur.execute(f"UPDATE settings SET queue_channel = 0 WHERE guild_id = {res.guild.id}"); db.commit()
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} set the queue channel to **None**", color=65535), delete_after=2)
                    channel = res.guild.get_channel(int(str(c.content).strip("<").strip(">").strip("#")))
                    cur.execute(f"UPDATE settings SET queue_channel = {channel.id} WHERE guild_id = {res.guild.id}"); db.commit()
                    return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} set the queue channel to {channel.mention}", color=65535), delete_after=2)

        # // CHANGE THE REGISTER CHANNEL
        if res.values[0] == "change_reg_channel":
            if res.author.guild_permissions.administrator:
                with sqlite3.connect('main.db', timeout=60) as db:
                    cur = db.cursor()
                    await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} mention the channel you want to use", color=65535))
                    c = await self.client.wait_for('message', check=lambda message: message.author == res.author)

                    if "<#" not in str(c.content):
                        cur.execute(f"UPDATE settings SET reg_channel = 0 WHERE guild_id = {res.guild.id}"); db.commit()
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} set the register channel to **None**", color=65535), delete_after=2)
                    channel = res.guild.get_channel(int(str(c.content).strip("<").strip(">").strip("#")))
                    cur.execute(f"UPDATE settings SET reg_channel = {channel.id} WHERE guild_id = {res.guild.id}"); db.commit()
                    return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} set the register channel to {channel.mention}", color=65535), delete_after=2)
        
        # // CHANGE THE ELO PER WIN
        if res.values[0] == "change_win_elo":
            if res.author.guild_permissions.administrator:
                with sqlite3.connect('main.db', timeout=60) as db:
                    cur = db.cursor()
                    await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} respond with the amount of elo you want to gain", color=65535))
                    c = await self.client.wait_for('message', check=lambda message: message.author == res.author)

                    cur.execute(f"UPDATE settings SET win_elo = {int(c.content)} WHERE guild_id = {res.guild.id}"); db.commit()
                    return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has set the win elo to **{c.content}**", color=65535), delete_after=2)
            
        # // CHANGE THE ELO PER LOSS
        if res.values[0] == "change_loss_elo":
            if res.author.guild_permissions.administrator:
                with sqlite3.connect('main.db', timeout=60) as db:
                    cur = db.cursor()
                    await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} respond with the amount of elo you want to lose", color=65535))
                    c = await self.client.wait_for('message', check=lambda message: message.author == res.author)

                    cur.execute(f"UPDATE settings SET loss_elo = {int(c.content)} WHERE guild_id = {res.guild.id}"); db.commit()
                    return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has set the loss elo to **{c.content}**", color=65535), delete_after=2)

        # // MATCH LOGGING
        if res.values[0] == "match_logging":
            if res.author.guild_permissions.administrator:
                with sqlite3.connect('main.db', timeout=60) as db:
                    cur = db.cursor()
                    await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} mention the channel you want to use", color=65535))
                    c = await self.client.wait_for('message', check=lambda message: message.author == res.author)

                    channel = res.guild.get_channel(int(str(c.content).strip("<").strip(">").strip("#")))
                    cur.execute(f"UPDATE settings SET match_logs = {channel.id} WHERE guild_id = {res.guild.id}"); db.commit()
                    return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has set the match log channel to **{channel.mention}**", color=65535), delete_after=2)

        # // QUEUE EMBED
        if res.values[0] == "queue_embed":
            if res.author.guild_permissions.administrator:
                await res.channel.send(embed=discord.Embed(title=f'[0/10] Queue', description='None', color=65535), 
                components=[[
                    Button(style=ButtonStyle.green, label='Join', custom_id='join_queue'),
                    Button(style=ButtonStyle.red, label="Leave", custom_id='leave_queue')]])

def setup(client):
    client.add_cog(Settings(client))