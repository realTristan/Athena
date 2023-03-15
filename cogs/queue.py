import discord, random, asyncio, re
from discord_components import *
from discord.ext import commands
from functools import *
from data import *

class QueueCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    # // Clean a players name to look more professional
    def clean_name(self, name: str):
        return str(name[0]).upper() + str(name[1:]).lower()


    # // When the queue reaches max capacity function
    async def _start(self, ctx:commands.Context, lobby: int):
        # // Get the lobby settings
        lobby = Lobby.get(ctx.guild.id, lobby)

        # // Create team captains (blue)
        blue_cap = random.choice(self.data[ctx.guild.id][lobby]["queue"])
        self.data[ctx.guild.id][lobby]["blue_cap"] = blue_cap
        self.data[ctx.guild.id][lobby]["queue"].remove(blue_cap)
        
        # // Create team captains (orange)
        orange_cap = random.choice(self.data[ctx.guild.id][lobby]["queue"])
        self.data[ctx.guild.id][lobby]["orange_cap"] = orange_cap
        self.data[ctx.guild.id][lobby]["queue"].remove(orange_cap)

        # // If the pick phase is enabled
        if lobby["team_pick_phase"] == 1:
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
        if lobby["map_pick_phase"] == 1:
            self.data[ctx.guild.id][lobby]["state"] = "maps"

        # // Else, pick a random map
        else:
            # // Get the maps
            maps = Lobby.get(ctx.guild.id, lobby, "maps")
            self.data[ctx.guild.id][lobby]["map"] = "None"
            
            # // If there are maps
            if len(maps) > 0:
                self.data[ctx.guild.id][lobby]["map"] = random.choice(maps)

            # // Set the state to final
            self.data[ctx.guild.id][lobby]["state"] = "final"

        # // Send the embed
        return await self._embeds(ctx, lobby)

    # // When an user joins the queue function
    async def _join(self, ctx:commands.Context, user, lobby):
        # // If the lobby is invalid
        if not await self.is_valid_lobby(ctx, lobby):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby", 
                    color = 15158588
            ))
        
        # // If the lobby state is not queue
        if self.data[ctx.guild.id][lobby]["state"] != "queue":
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{user.mention} it is not the queueing phase", 
                    color = 15158588
            ))
        
        # // If the user isn't registered
        if not User.exists(ctx.guild.id, user.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{user.mention} is not registered",
                    color = 15158588
            ))
        
        # // Check if the user is a party leader
        if not await self.check_party(ctx, user, lobby):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you are not a party leader / party too full", 
                    color = 15158588
            ))
        
        # // Check if the user is already queued
        for l in self.data[ctx.guild.id]:
            if user in self.data[ctx.guild.id][l]["queue"]:
                # // Get the channel
                channel = ctx.guild.get_channel(int(l))
                if channel is not None:
                    return await ctx.send(embed = discord.Embed(
                        description = f"{user.mention} is already queued in {channel.mention}", 
                        color = 15158588
                    ))
                
                # // If the channel is not found, then remove the lobby
                del self.data[ctx.guild.id][l]

        # // Check if the user is banned
        if Bans.is_banned(ctx.guild.id, user.id):
            await Bans.embed(ctx.guild.id, user)

        # // Get the queue sizes
        queue_size = Lobby.get(ctx.guild.id, lobby, "queue_size")
        current_queue_size: int = len(self.data[ctx.guild.id][lobby]['queue'])

        # // Add the user to the queue
        self.data[ctx.guild.id][lobby]["queue"].append(user)

        # // If the queue is full, then start the game
        if current_queue_size == queue_size:
            return await self._start(ctx, lobby)
        
        # // Send the queue embed
        return await ctx.send(
            embed = discord.Embed(
                description = f"**[{current_queue_size + 1}/{queue_size}]** {user.mention} has joined the queue", 
                color = 33023
        ))
        
    
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
        if self.data[ctx.guild.id][lobby]["state"] != "queue":
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{user.mention} it is not the queueing phase", 
                    color = 15158588
            ))
        
        # // If the user is not in the queue
        if user not in self.data[ctx.guild.id][lobby]["queue"]:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{user.mention} is not in the queue", 
                    color = 15158588
            ))
        
        # // Get the queue sizes
        queue_size: int = Lobby.get(ctx.guild.id, lobby, "queue_size")
        current_queue_size: int = len(self.data[ctx.guild.id][lobby]['queue'])

        # // Remove the user from the queue
        self.data[ctx.guild.id][lobby]["queue"].remove(user)

        # // Send the queue embed
        return await ctx.send(
            embed = discord.Embed(
                description = f"**[{current_queue_size - 1}/{queue_size}]** {user.mention} has left the queue", 
                color = 33023
        ))
        

    # // The command for team captains to pick a teammate
    @commands.command(name="pick", aliases=["p"], description='`=pick (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def pick(self, ctx:commands.Context, user:discord.Member):
        if ctx.author.bot:
            return
        
        # // Check if the lobby is valid
        if not await self.is_valid_lobby(ctx, ctx.channel.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby", 
                    color = 15158588
            ))
        
        # // Check if the lobby state is not pick
        if self.data[ctx.guild.id][ctx.channel.id]["state"] != "pick":
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} it is not the picking phase", 
                    color = 15158588
            ))
        
        # // Check if the user is not the captain
        if not ctx.author == self.data[ctx.guild.id][ctx.channel.id]["pick_logic"][0]:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} it is not your turn to pick", 
                    color = 15158588
            ))
        
        # // Check if the user is not in the queue
        if user not in self.data[ctx.guild.id][ctx.channel.id]["queue"]:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} that player is not in this queue", 
                    color = 15158588
            ))
        
        # // Continue with picking
        self.data[ctx.guild.id][ctx.channel.id]["pick_logic"].pop(0)
        if self.data[ctx.guild.id][ctx.channel.id]["blue_cap"] == ctx.author:
            self.data[ctx.guild.id][ctx.channel.id]["blue_team"].append(user)
            self.data[ctx.guild.id][ctx.channel.id]["queue"].remove(user)
        else:
            self.data[ctx.guild.id][ctx.channel.id]["orange_team"].append(user)
            self.data[ctx.guild.id][ctx.channel.id]["queue"].remove(user)

        # // Send who the captain picked
        await ctx.send(
            embed = discord.Embed(
                description = f"{ctx.author.mention} has picked {user.mention}", 
                color = 33023
            ))

        # // Check if the queue has one player left
        if len(self.data[ctx.guild.id][ctx.channel.id]["queue"]) == 1:
            # // Add the last player to the team
            self.data[ctx.guild.id][ctx.channel.id]["orange_team"].append(self.data[ctx.guild.id][ctx.channel.id]["queue"][0])
            self.data[ctx.guild.id][ctx.channel.id]["queue"].remove(self.data[ctx.guild.id][ctx.channel.id]["queue"][0])

            # // Get whether the map pick phase is enabled
            map_pick_phase = Lobby.get(ctx.guild.id, ctx.channel.id, "map_pick_phase")

            # // If the map pick phase is enabled
            if map_pick_phase == 1:
                self.data[ctx.guild.id][ctx.channel.id]["state"] = "maps"

            # // If the map pick phase is disabled
            else:
                # // Get the maps
                maps = Lobby.get(ctx.guild.id, ctx.channel.id, "maps")

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
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby", 
                    color = 15158588
            ))
        
        # // Check if the lobby state is not maps
        if self.data[ctx.guild.id][ctx.channel.id]["state"] != "maps":
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} it is not the map picking phase", 
                    color = 15158588
            ))
        
        # // Check if the user is the blue team captain
        if ctx.author != self.data[ctx.guild.id][ctx.channel.id]["blue_cap"]:
            return await ctx.send(
                embed = discord.Embed(
                    description=f"{ctx.author.mention} you are not the blue team captain", 
                    color=15158588
            ))
        
        # // Get the maps
        maps = Lobby.get(ctx.guild.id, ctx.channel.id, "maps")

        # // Check if the map is in the map pool
        for m in maps:
            if map.lower() in m.lower():
                self.data[ctx.guild.id][ctx.channel.id]["map"] = self.clean_name(map)
                self.data[ctx.guild.id][ctx.channel.id]["state"] = "final"
                return await self._embeds(ctx, ctx.channel.id)
        
        # // If the map is not in the map pool
        return await ctx.send(
            embed = discord.Embed(
            description = f"{ctx.author.mention} that map is not in the map pool", 
            color = 15158588
        ))
            
        
    # // Join the queue command
    @commands.command(name = "join", aliases = ["j"], description = '`=join`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def join(self, ctx:commands.Context):
        if not ctx.author.bot:
            return await self._join(ctx, ctx.author, ctx.channel.id)

    # // Force join an user to the queue command
    @commands.command(name = "forcejoin", aliases = ["fj"], description = '`=forcejoin (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def forcejoin(self, ctx:commands.Context, user: discord.Member):
        if ctx.author.bot:
            return
        
        # // Check if the user has the mod role
        if not User.is_mod(ctx.guild, ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
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
        if not User.is_mod(ctx.guild, ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
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
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby", 
                    color = 15158588
            ))
        
        # // Send the embed
        await self._embeds(ctx, ctx.channel.id)
            
    
    # // Clear the current queue command
    @commands.command(name="clear", description='`=clear`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def clear(self, ctx:commands.Context):
        if ctx.author.bot:
            return
        
        # // Check if the user is a mod
        if not User.is_mod(ctx.guild, ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
        # // Check if the lobby is valid
        if not await self.is_valid_lobby(ctx, ctx.channel.id):
            return await ctx.send(
                embed = discord.Embed(
                description = f"{ctx.author.mention} this channel is not a lobby", 
                color = 15158588
            ))
        
        # // Clear the queue
        self._reset(ctx, ctx.channel.id)
        return await ctx.send(
            embed = discord.Embed(
                description = f"{ctx.author.mention} has cleared the queue", 
                color = 3066992
            ))
        
    # // Party commands
    @commands.command(name="party", aliases=["team"], description='`=party create`**,** `=party leave)`**,** `=party show`**,** `=party kick (@user)`**,** `=party invite (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def party(self, ctx:commands.Context, action:str, *args):
        if ctx.author.bot:
            return
        
        # // Check if the lobby is valid
        if not await self.is_valid_lobby(ctx, ctx.channel.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby", 
                    color = 15158588
            ))
        
        # // Get the parties and max party size for the current lobby
        parties = self.data[ctx.guild.id][ctx.channel.id]["parties"]
        max_party_size = Lobby.get(ctx.guild.id, ctx.channel.id, "max_party_size")

        # // Invite a player to your party
        if action in ["invite", "inv"]:
            if ctx.author.id not in parties:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} you are not a party leader", 
                        color = 15158588
                ))
            
            # // Verify that the party is not full
            if len(parties[ctx.author.id]) + 1 > max_party_size:
                return await ctx.send(
                    embed = discord.Embed(
                    description = f"**[{len(parties[ctx.author.id])}/{max_party_size}]** {ctx.author.mention} your party is full", 
                    color = 15158588
                ))
            
            # // Check if the user is valid
            user = ctx.guild.get_member(int(re.sub("\D","", args[0])))
            if user is None:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} unknown player", 
                        color = 15158588
                ))
            
            # // Check if the invited user is already in a party
            for party in parties:
                if user.id not in parties[party]:
                    continue

                # // Send a message that the user is already in a party
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} this player is already in a party", 
                        color = 15158588
                ))
            
            # // Invite the user
            try:
                # // Send the success message
                await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} a party invite has been sent to {user.mention}", 
                        color = 3066992
                ))

                # // Send the party invite
                message = await user.send(
                    embed = discord.Embed(
                        description=f"{ctx.author.mention} has invited you to join their party", 
                        color=33023), 
                    components=[[
                        Button(style=ButtonStyle.green, label="Accept", custom_id='accept_party'),
                        Button(style=ButtonStyle.red, label="Decline", custom_id='decline_party')
                ]])

                # // Wait for the user to accept or decline the invite
                res = await self.client.wait_for("button_click", check=lambda m: m.author == user and m.message.id == message.id, timeout=10)

                # // If the user accepted the party invite
                if res.component.id == "accept_party":
                    parties[ctx.author.id].append(user.id)
                    await res.send(
                        embed = discord.Embed(
                            description = f"{res.author.mention} you have accepted {ctx.author.mention}'s party invite", 
                            color = 3066992
                    ))
                    return await ctx.send(
                        embed = discord.Embed(
                            description = f"**[{len(parties[ctx.author.id])}/{max_party_size}]** {user.mention} has accepted {ctx.author.mention}'s party invite", 
                            color = 3066992
                    ))
                
                # // If the user declined the party invite
                await res.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} you have declined {ctx.author.mention}'s party invite", 
                        color = 15158588
                ))
                return await ctx.send(
                    embed = discord.Embed(
                    description = f"{user.mention} has declined {ctx.author.mention}'s party invite", 
                    color = 15158588
                ))
            
            # // If the user did not respond in time
            except asyncio.TimeoutError:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{user.mention} did not answer {ctx.author.mention}'s invite in time", 
                        color = 15158588
                ))

        # Leave/Disband party
        if action in ["leave"]:
            # // Disband party
            if ctx.author.id in parties:
                del parties[ctx.author.id]

                # // Send the embed
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} has disbanded their party", 
                        color = 3066992
                    )
                )

            # // Iterate over the parties
            for party in parties:
                if ctx.author.id not in parties[party]:
                    continue

                # // Remove the user from the party
                parties[party].remove(ctx.author.id)

                # // Send the embed
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"**[{len(parties[party])}/{max_party_size}]** {ctx.author.mention} has left the party", 
                        color = 3066992
                ))
            
            # // Send a message that the user is not in a party
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you are not in a party", color=15158588
            ))

        # // Show party
        if action in ["show"]:
            # // Show the authors party
            if not args:
                # // Find the party the user is in
                for party in parties:
                    if ctx.author.id not in parties[party]:
                        continue

                    # // Verify the party leader
                    member = await self.verify_member(ctx, party)
                    if member is None:
                        continue

                    # // Send the party
                    return await ctx.send(
                        embed = discord.Embed(
                            title = f"[{len(parties[party])}/{max_party_size}] {member.name}'s party", 
                            description = "\n".join("<@" + str(e) + ">" for e in parties[party]),
                            color = 33023
                    ))
                
                # // Send a message that the user is not in a party
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} you are not in a party", 
                        color = 15158588
                ))
            
            # // Show another players party
            if "@" in args[0]:
                # // Get the user from the mention
                user = ctx.guild.get_member(int(re.sub("\D","", args[0])))

                # // Find the party the user is in
                for party in parties:
                    # // If the user is in the party, return the party
                    if user.id not in parties[party]:
                        continue

                    # // Verify the party leader
                    member = await self.verify_member(ctx, party)
                    if member is None:
                        continue

                    # // Send the party
                    return await ctx.send(
                        embed = discord.Embed(
                            title = f"[{len(parties[party])}/{max_party_size}] {member.name}'s party", 
                            description = "\n".join("<@" + str(e) + ">" for e in parties[user.id]), 
                            color = 33023
                    ))
                
                # // Send a message that the user is not in a party
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{user.mention} is not in a party", 
                        color = 15158588
                ))

        # // Create a new party
        if action in ["create"]:
            # // If the user is already a party leader, return
            if ctx.author.id in parties:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} you are already in a party",
                        color = 15158588
                ))
            
            # // Check if the user is already in a party
            for party in parties:
                if ctx.author.id in parties[party]:
                    return await ctx.send(
                        embed = discord.Embed(
                            description = f"{ctx.author.mention} you are already in a party", 
                            color = 15158588
                    ))
            
            # // Add the user to the parties list
            parties[ctx.author.id] = [ctx.author.id]
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} has created a party", 
                    color = 3066992
            ))
            

        # // Kick an user from the party
        if action in ["kick", "remove"]:
            # // Check if the author is a party leader
            if ctx.author.id not in parties:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} you are not a party leader", 
                        color = 15158588
                ))
            
            # // Get the user to kick and verify that they are not null
            user = ctx.guild.get_member(int(re.sub("\D","", args[0])))
            if user is None:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} unknown player", 
                        color = 15158588
                ))
            
            # // If the user is not in the party
            if user.id not in parties[ctx.author.id]:
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} that player is not in your party", 
                        color = 15158588
                ))
            
            # // Kick the user from the party
            parties[ctx.author.id].remove(user.id)
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} has kicked {user.mention} from the party", 
                    color = 3066992
            ))

    # // Listen to the queue embed buttons
    @commands.Cog.listener()
    async def on_button_click(self, res: discord.Interaction):
        if res.author.bot:
            return
        
        # // If the user is trying to join or leave a queue
        if res.component.id in ["join_queue", "leave_queue"]:
            lobby = res.guild.get_channel(int(res.message.embeds[0].footer.text))

            # // Verify that the lobby exists
            if lobby is None:
                await res.channel.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} unknown lobby", color=3066992
                ))
                return await res.message.delete()
            
            # // Check if the lobby is valid
            if await self.is_valid_lobby(res, lobby.id):
                # // If the user is trying to join the queue
                if res.component.id == "join_queue":
                    await self._join(res, res.author, lobby.id)

                # // If the user is trying to leave the queue
                else:
                    await self._leave(res, res.author, lobby.id)
                
                # // Get the players and store them in a string
                players = "\n".join(str(e.mention) for e in self.data[res.guild.id][lobby.id]["queue"])

                # // Get the queue size
                queue_size = Lobby.get(res.guild.id, lobby.id, "queue_size")

                # // Create the new embed
                current_queue_size: int = len(self.data[res.guild.id][lobby.id]["queue"])
                embed = discord.Embed(
                    title=f'[{current_queue_size}/{queue_size}] {lobby.name}', 
                    description = players, 
                    color=33023
                )
                embed.set_footer(text=str(lobby.id))

                # // Edit the embed
                return await res.message.edit(embed=embed)
                

def setup(client: commands.Bot):
    client.add_cog(QueueCog(client))