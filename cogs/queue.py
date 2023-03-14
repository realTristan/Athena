import discord, random, time, asyncio, re
from discord_components import *
from discord.ext import commands
from discord.utils import get
import datetime as datetime
from functools import *
from data import *

class Queue(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.data = {}

    # Reset guilds variables function
    def _reset(self, ctx: commands.Context, lobby):
        self.data[ctx.guild.id][lobby] = {
            "queue": [], 
            "blue_cap": "", 
            "blue_team": [], 
            "orange_cap": "", 
            "orange_team": [], 
            "pick_logic": [], 
            "map": "None", 
            "parties": {}, 
            "state": "queue"
        }

    # // Clean a players name to look more professional
    def _clean_name(self, name):
        return str(name[0]).upper() + str(name[1:]).lower()
    
    # // Check if a member is still in the server
    async def _check_member(self, ctx: commands.Context, member_id: int):
        # // Get the member
        member = ctx.guild.get_member(member_id)

        # // If the member is still in the server, return the member
        if member is not None:
            return member
        
        # // If the member is not in the server, check if they are in the database
        if User(ctx.guild.id, member_id).exists():
            # // If so, delete the user
            await User(ctx.guild.id, member_id).delete()

        # // Return the member
        return member
    
    
    # // Check if channel is a valid queue lobby
    async def is_valid_lobby(self, ctx:commands.Context, lobby: int):
        if ctx.guild.id not in self.data:
            self.data[ctx.guild.id] = {}
        
        if Lobby.exists(ctx.guild.id, lobby):
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
        mod_role = Settings(ctx.guild.id).get("mod_role")
        return ctx.guild.get_role(mod_role) in ctx.author.roles
    
    
    # // Check admin role or admin permissions
    # //////////////////////////////////////////
    async def check_admin_role(self, ctx: commands.Context):
        # // Get the admin role from settings
        admin_role = Settings(ctx.guild.id).get("admin_role")
        
        # // Check admin permissions
        if admin_role == 0 or ctx.author.guild_permissions.administrator:
            return ctx.author.guild_permissions.administrator
        return ctx.guild.get_role(admin_role) in ctx.author.roles


    # // Add other party members to the queue
    async def _check_party(self, ctx:commands.Context, user, lobby):
        for party in self.data[ctx.guild.id][lobby]["parties"]:
            if user.id in self.data[ctx.guild.id][lobby]["parties"][party] and party != user.id:
                return False
        
        if user.id in self.data[ctx.guild.id][lobby]["parties"]:
            queue_size: int = Lobby(ctx.guild.id, lobby).get("queue_size")
            # // Check if the party can join the queue
            if len(self.data[ctx.guild.id][lobby]["parties"][user.id]) + len(self.data[ctx.guild.id][lobby]["queue"]) <= queue_size:
                # // Add the party to the queue
                for player in self.data[ctx.guild.id][lobby]["parties"][user.id][1:]:
                    member = await self._check_member(ctx, player)
                    if member is not None:
                        await self._join(ctx, member, lobby)
                return True
            return False
        return True
    
    
    # // Send match logs to the given match logs channel
    async def _match_log(self, ctx:commands.Context, embed:discord.Embed):
        match_logs = Settings(ctx.guild.id).get("match_logs")

        # // If the match logs are disabled
        if match_logs == 0:
            return
        
        # // If the match logs are enabled
        channel = ctx.guild.get_channel(match_logs)

        # // If the channel is not found, set the match logs to 0
        if channel is None:
            return await Settings(ctx.guild.id).update(match_logs=0)
        
        # // Else, send the embed to the channel
        return await channel.send(
            embed = embed,
            components = [[
                Button(style=ButtonStyle.blue, label="Blue", custom_id='blue_report'),
                Button(style=ButtonStyle.blue, label="Orange", custom_id='orange_report'),
                Button(style=ButtonStyle.red, label="Cancel", custom_id='match_cancel')
            ]])
                

    # // Create the match category function
    async def _match_category(self, ctx:commands.Context, match_id, lobby):
        match_categories = Settings(ctx.guild.id).get("match_categories")

        # // If the match categories are disabled
        if match_categories == 0:
            return
        
        # // Else, create the match category
        if not get(ctx.guild.categories, name=f'Match #{match_id}'):
            # // Creating category and setting permissions
            category = await ctx.guild.create_category(f'Match #{match_id}')
            await category.set_permissions(ctx.guild.default_role, connect=False, send_messages=False)

            # // Creating channels inside category
            await ctx.guild.create_text_channel(f"match-{match_id}", category=category)
            await ctx.guild.create_voice_channel(f'🔹 Team ' + self.data[ctx.guild.id][lobby]["blue_cap"].name, category=category)
            await ctx.guild.create_voice_channel(f"🔸 Team " + self.data[ctx.guild.id][lobby]['orange_cap'].name, category=category)

            # // Create the teams
            blue_team = self.data[ctx.guild.id][lobby]["blue_team"]
            blue_team.append(self.data[ctx.guild.id][lobby]["blue_cap"])
            orange_team = self.data[ctx.guild.id][lobby]["orange_team"]
            orange_team.append(self.data[ctx.guild.id][lobby]["orange_cap"])
            self._reset(ctx, lobby)

            # // Edit the permissions for each player in the teams
            for user in orange_team:
                await category.set_permissions(user, connect=True, send_messages=True)

            for _user in blue_team:
                await category.set_permissions(_user, connect=True, send_messages=True)


    # // Match logging function
    async def _match(self, ctx:commands.Context, lobby: int):
        # // Get the teams
        orange_team = ','.join(str(e.id) for e in self.data[ctx.guild.id][lobby]['orange_team'])
        blue_team = ','.join(str(e.id) for e in self.data[ctx.guild.id][lobby]['blue_team'])

        # // Get the team captains
        orange_cap = self.data[ctx.guild.id][lobby]['orange_cap']
        blue_cap = self.data[ctx.guild.id][lobby]['blue_cap']

        # // Get the count of matches
        amount_of_matches = Matches.count(ctx.guild.id, lobby) + 1

        # // Add the match to the database
        await Matches.add(ctx.guild.id, amount_of_matches, orange_cap, orange_team, blue_cap, blue_team, "ongoing", "none")


    # // Create team pick logic function
    async def _pick_logic(self, ctx:commands.Context, lobby):
        for _ in range(round(len(self.data[ctx.guild.id][lobby]["queue"]) / 2)):
            self.data[ctx.guild.id][lobby]["pick_logic"].append(self.data[ctx.guild.id][lobby]["blue_cap"])
            self.data[ctx.guild.id][lobby]["pick_logic"].append(self.data[ctx.guild.id][lobby]["orange_cap"])

        if len(self.data[ctx.guild.id][lobby]["queue"]) > len(self.data[ctx.guild.id][lobby]["pick_logic"]):
            self.data[ctx.guild.id][lobby]["pick_logic"].append(self.data[ctx.guild.id][lobby]["orange_cap"])


    # // Embed generator function (for queue)
    async def _embeds(self, ctx:commands.Context, lobby: int):
        # // Get the lobby data
        lobby_data = self.data[ctx.guild.id][lobby]

        # // Queue phase embed
        if lobby_data["state"] == "queue":
            current_queue = "None"

            # // Get the current queue and store it in a string
            if len(lobby_data["queue"]) != 0:
                current_queue = '\n'.join(str(e.mention) for e in lobby_data["queue"])

            # // Get the lobby settings
            current_queue_size = len(lobby_data['queue'])
            queue_size = Lobby(ctx.guild.id, lobby).get("queue_size")

            # // Send the embed
            return await ctx.send(
                embed = discord.Embed(
                    title = f"[{current_queue_size}/{queue_size}] {ctx.channel.name}", 
                    description = current_queue, 
                    color = 33023
                )
            )

        # // Team picking phase embed
        if lobby_data["state"] == "pick":
            # // Get the orange team
            orange_team = "None"
            if len(lobby_data["orange_team"]) != 0:
                orange_team = '\n'.join(str(e.mention) for e in lobby_data["orange_team"])

            # // Get the blue team
            blue_team = "None"
            if len(lobby_data["blue_team"]) != 0:
                blue_team = '\n'.join(str(e.mention) for e in lobby_data["blue_team"])

            # // Create the embed
            embed = discord.Embed(title="Team Picking Phase", color=33023)

            # // Captains
            embed.add_field(name = "Orange Captain", value = lobby_data["orange_cap"].mention)
            embed.add_field(name = "\u200b", value = "\u200b")
            embed.add_field(name = "Blue Captain", value = lobby_data["blue_cap"].mention)

            # // Teams
            embed.add_field(name = "Orange Team", value = orange_team)
            embed.add_field(name = "\u200b", value = "\u200b")
            embed.add_field(name = "Blue Team", value = blue_team)

            # // Available players
            embed.add_field(name="Available Players", value = "\n".join(str(e.mention) for e in lobby_data["queue"]))
            
            # // Send the embed
            await ctx.send(embed=embed)
            return await ctx.send(f"**{lobby_data['pick_logic'][0].mention} it is your turn to pick (=pick [@user])**")

        # // Map picking phase embed
        if lobby_data["state"] == "maps":
            # // Get the maps
            maps = Lobby(ctx.guild.id, lobby).get_maps()

            # // Create the embed
            embed = discord.Embed(title="Map Picking Phase", color=33023)

            # // Captains
            embed.add_field(name = "Orange Captain", value = lobby_data["orange_cap"].mention)
            embed.add_field(name = "\u200b", value = "\u200b")
            embed.add_field(name = "Blue Captain", value = lobby_data["blue_cap"].mention)

            # // Teams
            embed.add_field(name = "Orange Team", value = '\n'.join(str(p.mention) for p in lobby_data["orange_team"]))
            embed.add_field(name = "\u200b", value = "\u200b")
            embed.add_field(name = "Blue Team", value = '\n'.join(str(p.mention) for p in lobby_data["blue_team"]))

            # // Available maps
            embed.add_field(name="Available Maps", value="\n".join(m for m in maps))

            # // Send the embed
            await ctx.send(embed=embed)
            return await ctx.send(f"**{lobby_data['blue_cap'].mention} select a map to play (=pickmap [map])**")

        # // Final match up embed
        if lobby_data["state"] == "final":
            # // Get the count of matches
            amount_of_matches = Matches.count(ctx.guild.id, lobby) + 1

            # // Create the embed
            embed = discord.Embed(title = f"Match #{amount_of_matches}", description = f"**Map:** {lobby_data['map']}", color = 33023)

            # // Captains
            embed.add_field(name = "Orange Captain", value = lobby_data["orange_cap"].mention)
            embed.add_field(name = "\u200b", value = "\u200b")
            embed.add_field(name = "Blue Captain", value = lobby_data["blue_cap"].mention)

            # // Teams
            embed.add_field(name = "Orange Team", value = '\n'.join(str(e.mention) for e in lobby_data["orange_team"]))
            embed.add_field(name = "\u200b", value = "\u200b")
            embed.add_field(name = "Blue Team", value = '\n'.join(str(e.mention) for e in lobby_data["blue_team"]))

            # // Set the footer to the lobby id
            embed.set_footer(text = str(lobby))

            # // Send the embed
            await ctx.send(embed = embed)

            # // Match functions
            await self._match(ctx, lobby)
            await self._match_log(ctx, embed)
            await self._match_category(ctx, amount_of_matches, lobby)
            self._reset(ctx, lobby)


    # // When the queue reaches max capacity function
    async def _start(self, ctx:commands.Context, lobby: int):
        # // Get the lobby settings
        lobby_settings = Lobby(ctx.guild.id, lobby).get()

        # // Create team captains (blue)
        blue_cap = random.choice(self.data[ctx.guild.id][lobby]["queue"])
        self.data[ctx.guild.id][lobby]["blue_cap"] = blue_cap
        self.data[ctx.guild.id][lobby]["queue"].remove(blue_cap)
        
        # // Create team captains (orange)
        orange_cap = random.choice(self.data[ctx.guild.id][lobby]["queue"])
        self.data[ctx.guild.id][lobby]["orange_cap"] = orange_cap
        self.data[ctx.guild.id][lobby]["queue"].remove(orange_cap)

        # // If the pick phase is enabled
        if lobby_settings["team_pick_phase"] == 1:
            self.data[ctx.guild.id][lobby]["state"] = "pick"

            # // Get the pick logic
            await self._pick_logic(ctx, lobby)

            # // Send the embed
            return await self._embeds(ctx, lobby)
        
        # // If pick phase is diabled, create random teams
        for _ in range(len(self.data[ctx.guild.id][lobby]["queue"]) // 2):
            # // Get a random user from the queue
            user = random.choice(self.data[ctx.guild.id][lobby]["queue"])

            # // Add the user to the orange team
            self.data[ctx.guild.id][lobby]['orange_team'].append(user)
            self.data[ctx.guild.id][lobby]["queue"].remove(user)
        
        # // Add the remaining users to the blue team
        for _ in range(len(self.data[ctx.guild.id][lobby]["queue"])):
            self.data[ctx.guild.id][lobby]['blue_team'].append(user)
            self.data[ctx.guild.id][lobby]["queue"].remove(user)
        

        # // If the map pick phase is enabled
        if lobby_settings["map_pick_phase"] == 1:
            self.data[ctx.guild.id][lobby]["state"] = "maps"

        # // Else, pick a random map
        else:
            # // Get the maps
            maps = Lobby(ctx.guild.id, lobby).get_maps()
            self.data[ctx.guild.id][lobby]["map"] = "None"
            
            # // If there are maps
            if len(maps) > 0:
                self.data[ctx.guild.id][lobby]["map"] = random.choice(maps)

            # // Set the state to final
            self.data[ctx.guild.id][lobby]["state"] = "final"

        # // Send the embed
        return await self._embeds(ctx, lobby)


    # // Check if user is banned function
    async def _ban_check(self, ctx:commands.Context, user):
        if Bans(ctx.guild.id).is_banned(user.id):
            # // Get the users ban info
            ban_data = Bans(ctx.guild.id).get(user.id)

            # // If the ban is still active
            if ban_data[0] - time.time() > 0:
                # // Get the ban length
                ban_length = datetime.timedelta(seconds=int(ban_data[0] - time.time()))

                # // Send the embed
                await ctx.channel.send(
                    embed = discord.Embed(
                        title = f"{self._clean_name(user.name)} is banned", 
                        description = f"**Length:** {ban_length}\n**Reason:** {ban_data[1]}\n**Banned by:** {ban_data[2]}", 
                        color = 15158588
                    )
                )

                # // Return false
                return False
            
            # // If the ban has expired, then unban the user
            await Bans(ctx.guild.id).unban(user.id)

        # // Return true
        return True


    # When an user joins the queue function
    async def _join(self, ctx:commands.Context, user, lobby):
        # // If the lobby is invalid
        if not await self.is_valid_lobby(ctx, lobby):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
        
        # // If the lobby state is not queue
        if not self.data[ctx.guild.id][lobby]["state"] == "queue":
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} it is not the queueing phase", color=15158588))
        
        # // If the user isn't registered
        if not User(ctx.guild.id).exists(user.id):
            return await ctx.send(embed=discord.Embed(description=f"{user.mention} is not registered", color=15158588))
        
        # // Check if the user is a party leader
        if not await self._check_party(ctx, user, lobby):
            return await ctx.send(embed=discord.Embed(description = f"{ctx.author.mention} you are not a party leader / party too full", color = 15158588))
        
        # // Check if the user is already queued
        for l in self.data[ctx.guild.id]:
            if user in self.data[ctx.guild.id][l]["queue"]:
                # // Get the channel
                channel = ctx.guild.get_channel(int(l))
                if channel is not None:
                    return await ctx.send(embed = discord.Embed(description = f"{user.mention} is already queued in {channel.mention}", color = 15158588))
                
                # // If the channel is not found, then remove the lobby
                del self.data[ctx.guild.id][l]

        # // Check if the user is banned
        if await self._ban_check(ctx, user):
            # // Get the queue size
            queue_size = Lobby(ctx.guild.id, lobby).get("queue_size")

            # // Add the user to the queue
            self.data[ctx.guild.id][lobby]["queue"].append(user)

            # // If the queue is full
            if len(self.data[ctx.guild.id][lobby]["queue"]) == queue_size:
                # // Start the game
                return await self._start(ctx, lobby)
            
            # // Send the queue embed
            return await ctx.send(embed=discord.Embed(description=f"**[{len(self.data[ctx.guild.id][lobby]['queue'])}/{queue_size}]** {user.mention} has joined the queue", color=33023))
        
    
    # // When an user leaves the queue function
    async def _leave(self, ctx:commands.Context, user, lobby):
        # // If the lobby is invalid
        if not await self.is_valid_lobby(ctx, lobby):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby", color = 15158588
                )
            )
        
        # // If the lobby state is not queue
        if not self.data[ctx.guild.id][lobby]["state"] == "queue":
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{user.mention} it is not the queueing phase", 
                    color = 15158588
                )
            )
        
        # // If the user is not in the queue
        if user not in self.data[ctx.guild.id][lobby]["queue"]:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{user.mention} is not in the queue", 
                    color = 15158588
                )
            )
        
        # // Get the queue size
        queue_size = Lobby(ctx.guild.id, lobby).get("queue_size")

        # // Remove the user from the queue
        self.data[ctx.guild.id][lobby]["queue"].remove(user)

        # // Send the queue embed
        return await ctx.send(
            embed = discord.Embed(
                description = f"**[{len(self.data[ctx.guild.id][lobby]['queue'])}/{queue_size}]** {user.mention} has left the queue", 
                color = 33023
            )
        )
        

    # // The command for team captains to pick a teammate
    @commands.command(name="pick", aliases=["p"], description='`=pick (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def pick(self, ctx:commands.Context, user:discord.Member):
        if ctx.author.bot:
            return
        
        # // Check if the lobby is valid
        if not await self.is_valid_lobby(ctx, ctx.channel.id):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
        
        # // Check if the lobby state is not pick
        if not self.data[ctx.guild.id][ctx.channel.id]["state"] == "pick":
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the picking phase", color=15158588))
        
        # // Check if the user is not the captain
        if not ctx.author == self.data[ctx.guild.id][ctx.channel.id]["pick_logic"][0]:
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not your turn to pick", color=15158588))
        
        # // Check if the user is not in the queue
        if user not in self.data[ctx.guild.id][ctx.channel.id]["queue"]:
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} that player is not in this queue", color=15158588))
        
        # // Continue with picking
        self.data[ctx.guild.id][ctx.channel.id]["pick_logic"].pop(0)
        if self.data[ctx.guild.id][ctx.channel.id]["blue_cap"] == ctx.author:
            self.data[ctx.guild.id][ctx.channel.id]["blue_team"].append(user)
            self.data[ctx.guild.id][ctx.channel.id]["queue"].remove(user)
        else:
            self.data[ctx.guild.id][ctx.channel.id]["orange_team"].append(user)
            self.data[ctx.guild.id][ctx.channel.id]["queue"].remove(user)
        await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has picked {user.mention}", color=33023))

        # // Check if the queue has one player left
        if len(self.data[ctx.guild.id][ctx.channel.id]["queue"]) == 1:
            # // Add the last player to the team
            self.data[ctx.guild.id][ctx.channel.id]["orange_team"].append(self.data[ctx.guild.id][ctx.channel.id]["queue"][0])
            self.data[ctx.guild.id][ctx.channel.id]["queue"].remove(self.data[ctx.guild.id][ctx.channel.id]["queue"][0])

            # // Get whether the map pick phase is enabled
            map_pick_phase = Lobby(ctx.guild.id, ctx.channel.id).get("map_pick_phase")

            # // If the map pick phase is enabled
            if map_pick_phase == 1:
                self.data[ctx.guild.id][ctx.channel.id]["state"] = "maps"

            # // If the map pick phase is disabled
            else:
                # // Get the maps
                maps = Lobby(ctx.guild.id, ctx.channel.id).get_maps()

                # // If there are maps
                if len(maps) > 0:
                    # // Pick a random map
                    self.data[ctx.guild.id][ctx.channel.id]["map"] = random.choice(maps)

                # // Set the state to final
                self.data[ctx.guild.id][ctx.channel.id]["state"] = "final"
        
        # // Send the embed
        return await self._embeds(ctx, ctx.channel.id)
        
        
            
            
    # Pick map to play (blue captain) command
    @commands.command(name="pickmap", description='`=pickmap (map name)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def pickmap(self, ctx:commands.Context, map:str):
        if ctx.author.bot:
            return
        
        # // Check if the lobby is valid
        if not await self.is_valid_lobby(ctx, ctx.channel.id):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
        
        # // Check if the lobby state is not maps
        if self.data[ctx.guild.id][ctx.channel.id]["state"] != "maps":
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} it is not the map picking phase", color=15158588))
        
        # // Check if the user is the blue team captain
        if ctx.author != self.data[ctx.guild.id][ctx.channel.id]["blue_cap"]:
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you are not the blue team captain", color=15158588))
        
        # // Get the maps
        maps = Lobby(ctx.guild.id, ctx.channel.id).get_maps()

        # // Check if the map is in the map pool
        for m in maps:
            if map.lower() in m.lower():
                self.data[ctx.guild.id][ctx.channel.id]["map"] = self._clean_name(map)
                self.data[ctx.guild.id][ctx.channel.id]["state"] = "final"
                return await self._embeds(ctx, ctx.channel.id)
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} that map is not in the map pool", color=15158588))
            
        
    # // Join the queue command
    @commands.command(name="join", aliases=["j"], description='`=join`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def join(self, ctx:commands.Context):
        if not ctx.author.bot:
            return await self._join(ctx, ctx.author, ctx.channel.id)

    # // Force join an user to the queue command
    @commands.command(name="forcejoin", aliases=["fj"], description='`=forcejoin (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def forcejoin(self, ctx:commands.Context, user:discord.Member):
        if ctx.author.bot:
            return
        
        # // Check if the user has the mod role
        if not await self.check_mod_role(ctx):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
        # // Force join the user
        return await self._join(ctx, user, ctx.channel.id)

    # // Leave the queue command
    @commands.command(name="leave", aliases=["l"], description='`=leave`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def leave(self, ctx:commands.Context):
        if not ctx.author.bot:
            return await self._leave(ctx, ctx.author, ctx.channel.id)

    # // Force remove an user from the queue command
    @commands.command(name="forceleave", aliases=["fl"], description='`=forceleave (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def forceleave(self, ctx:commands.Context, user:discord.Member):
        if ctx.author.bot:
            return
        
        # // Check if the author has the mod role
        if not await self.check_mod_role(ctx):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
        # // Forceleave the user
        return await self._leave(ctx, user, ctx.channel.id)

    # // Show the current queue command
    @commands.command(name="queue", aliases=["q"], description='`=queue`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def queue(self, ctx:commands.Context):
        if ctx.author.bot:
            return
        
        # // Check if the lobby is valid
        if not await self.is_valid_lobby(ctx, ctx.channel.id):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
        
        # // Send the embed
        await self._embeds(ctx, ctx.channel.id)
            
    
    # // Clear the current queue command
    @commands.command(name="clear", description='`=clear`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def clear(self, ctx:commands.Context):
        if ctx.author.bot:
            return
        
        # // Check if the user is a mod
        if not await self.check_mod_role(ctx):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
        # // Check if the lobby is valid
        if not await self.is_valid_lobby(ctx, ctx.channel.id):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
        
        # // Clear the queue
        self._reset(ctx, ctx.channel.id)
        return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} has cleared the queue", color=3066992))
        
    # // Party commands
    @commands.command(name="party", aliases=["team"], description='`=party create`**,** `=party leave)`**,** `=party show`**,** `=party kick (@user)`**,** `=party invite (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def party(self, ctx:commands.Context, action:str, *args):
        if ctx.author.bot:
            return
        
        # // Check if the lobby is valid
        if not await self.is_valid_lobby(ctx, ctx.channel.id):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} this channel is not a lobby", color=15158588))
        
        parties = self.data[ctx.guild.id][ctx.channel.id]["parties"]
        max_party_size = Lobby(ctx.guild.id, ctx.channel.id).get("max_party_size")

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

    # // Listen to the queue embed buttons
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
                    queue_size = Lobby(res.guild.id, lobby.id).get("queue_size")
                    embed = discord.Embed(title=f'[{len(self.data[res.guild.id][lobby.id]["queue"])}/{queue_size}] {lobby.name}', description=players, color=33023)
                    embed.set_footer(text=str(lobby.id))
                    return await res.message.edit(embed=embed)
                

def setup(client: commands.Bot):
    client.add_cog(Queue(client))