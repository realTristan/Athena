from discord_components import *
from discord.ext import commands
import discord, sqlite3

db = sqlite3.connect('main.db')
cur = db.cursor()

class Settings(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def _emojis(self, ctx, option):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM settings WHERE guild_id = {ctx.guild.id});").fetchall()[0] == (0,):
            cur.execute(f"INSERT INTO settings VALUES ({ctx.guild.id}, 0, 'true', 'false', 'true')")

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

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addmap(self, ctx, map:str):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM maps WHERE guild_id = {ctx.guild.id});").fetchall()[0] == (0,):
            cur.execute(f"INSERT INTO maps VALUES ({ctx.guild.id}, '{map}')")
        else:
            for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
                if map not in str(row[1]).split(","):
                    cur.execute(f"UPDATE maps SET map_list = '{str(row[1])},{map}' WHERE guild_id = {ctx.guild.id}")
        db.commit()
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} added **{map}** to the map pool", color=65535))

    @commands.command(aliases=["removemap", "deletemap"])
    @commands.has_permissions(administrator=True)
    async def delmap(self, ctx, map:str):
        for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
            if map in str(row[1]).split(","):
                map_list = str(row[1]).split(',')
                map_list.remove(map)
                cur.execute(f"UPDATE maps SET map_list = '{','.join(str(e) for e in map_list)}' WHERE guild_id = {ctx.guild.id}")
                db.commit()
                return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} removed **{map}** from the map pool", color=65535))
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} **{map}** is not in the map pool", color=65535))

    @commands.command()
    async def maps(self, ctx):
        for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {ctx.guild.id}'):
            return await ctx.send(embed=discord.Embed(title="Maps", description=str(row[1]).replace(",", "\n"), color=65535))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def regrole(self, ctx, role:discord.Role):
        if cur.execute(f"SELECT EXISTS(SELECT 1 FROM settings WHERE guild_id = {ctx.guild.id});").fetchall()[0] == (0,):
            cur.execute(f"INSERT INTO settings VALUES ({ctx.guild.id}, {role.id})")
        else:
            cur.execute(f"UPDATE settings SET reg_role = {role.id} WHERE guild_id = {ctx.guild.id}")
        db.commit()
        return await ctx.send(embed=discord.Embed(description=f'{ctx.author.mention} set the register role to {role.mention}', color=65535))

    @commands.command(aliases=["sets"])
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        picking_phase = await self._emojis(ctx, "picking_phase")
        map_pick_phase = await self._emojis(ctx, "map_pick_phase")
        team_cap_vc = await self._emojis(ctx, "team_cap_vc")

        await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} **click below to view the settings panel**", color=65535),
            components=[
                Select(
                    placeholder="Settings",
                    options=[
                        SelectOption(emoji=f'🔵', label="Add Map", value="add_map"),
                        SelectOption(emoji=f'🔵', label="Remove Map", value="remove_map"),
                        SelectOption(emoji=f'🔵', label="Change Register Role", value="change_reg_role"),
                        SelectOption(emoji=f'{map_pick_phase[0]}', label=f"{map_pick_phase[1]} Map Picking Phase", value="map_pick_phase"),
                        SelectOption(emoji=f'{picking_phase[0]}', label=f"{picking_phase[1]} Team Picking Phase", value="picking_phase"),
                        SelectOption(emoji=f'{team_cap_vc[0]}', label=f"{team_cap_vc[1]} Team Captain Voice Channels", value="team_cap_vc")
                    ])])
        

    @commands.Cog.listener()
    async def on_select_option(self, res):
        if res.author.guild_permissions.administrator:
            for row in cur.execute(f'SELECT * FROM settings WHERE guild_id = {res.guild.id}'):
                # // MAP PICKING PHASE
                if res.values[0] == 'map_pick_phase':
                    if row[2] == "false":
                        cur.execute(f"UPDATE settings SET map_pick_phase = 'true' WHERE guild_id = {res.guild.id}"); db.commit()
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Map Picking Phase**", color=65535))

                    cur.execute(f"UPDATE settings SET map_pick_phase = 'false' WHERE guild_id = {res.guild.id}"); db.commit()
                    return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Map Picking Phase**", color=65535))


                # // TEAM CAPTAIN VOICE CHANNELS
                if res.values[0] == 'team_cap_vc':
                    if row[3] == "false":
                        cur.execute(f"UPDATE settings SET team_cap_vcs = 'true' WHERE guild_id = {res.guild.id}"); db.commit()
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Team Captain Voice Channels**", color=65535))

                    cur.execute(f"UPDATE settings SET team_cap_vcs = 'false' WHERE guild_id = {res.guild.id}"); db.commit()
                    return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Team Captain Voice Channels**", color=65535))


                # // TEAM CAPTAINS
                if res.values[0] == 'picking_phase':
                    if row[4] == "false":
                        cur.execute(f"UPDATE settings SET picking_phase = 'true' WHERE guild_id = {res.guild.id}"); db.commit()
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has enabled **Team Captains**", color=65535))

                    cur.execute(f"UPDATE settings SET picking_phase = 'false' WHERE guild_id = {res.guild.id}"); db.commit()
                    return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} has disabled **Team Captains**", color=65535))


                # // CHANGE THE REGISTER ROLE
                if res.values[0] == "change_reg_role":
                    await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} mention the role you want to use", color=65535))
                    c = await self.client.wait_for('message', check=lambda message: message.author == res.author)
                    
                    role = res.guild.get_role(int(c.content.strip("<").strip(">").strip("@").strip("&")))
                    cur.execute(f"UPDATE settings SET reg_role = {role.id} WHERE guild_id = {res.guild.id}"); db.commit()
                    return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} set the register role to {role.mention}", color=65535))


                # // ADD MAP
                if res.values[0] == "add_map":
                    await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} respond with the map name", color=65535))
                    c = await self.client.wait_for('message', check=lambda message: message.author == res.author)
                    map = c.content

                    if cur.execute(f"SELECT EXISTS(SELECT 1 FROM maps WHERE guild_id = {res.guild.id});").fetchall()[0] == (0,):
                        cur.execute(f"INSERT INTO maps VALUES ({res.guild.id}, '{map}')")
                    else:
                        for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {res.guild.id}'):
                            if map not in str(row[1]).split(","):
                                cur.execute(f"UPDATE maps SET map_list = '{str(row[1])},{map}' WHERE guild_id = {res.guild.id}")
                    db.commit()
                    return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} added **{map}** to the map pool", color=65535))

                # // REMOVE MAP
                if res.values[0] == "remove_map":
                    await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} respond with the map name", color=65535))
                    c = await self.client.wait_for('message', check=lambda message: message.author == res.author)
                    map = c.content

                    for row in cur.execute(f'SELECT * FROM maps WHERE guild_id = {res.guild.id}'):
                        if map in str(row[1]).split(","):
                            map_list = str(row[1]).split(',')
                            map_list.remove(map)
                            cur.execute(f"UPDATE maps SET map_list = '{','.join(str(e) for e in map_list)}' WHERE guild_id = {res.guild.id}")
                            db.commit()
                            return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} removed **{map}** from the map pool", color=65535))
                        return await res.channel.send(embed=discord.Embed(description=f"{res.author.mention} **{map}** is not in the map pool", color=65535))



def setup(client):
    client.add_cog(Settings(client))