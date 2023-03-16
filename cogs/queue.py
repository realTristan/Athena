from discord_components import Button, ButtonStyle
from discord.ext import commands
from cached_queue import Queue
from cache import Lobby, Users
import discord, asyncio, re

class QueueCog(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    # // The command for team captains to pick a teammate
    @commands.command(name="pick", aliases=["p"], description='`=pick (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def pick(self, ctx: commands.Context, user: discord.Member):
        if ctx.author.bot:
            return
        
        # // Check if the lobby is valid
        if not Queue.is_valid_lobby(ctx.guild.id, ctx.channel.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby", 
                    color = 15158588
            ))
        
        # // Check if the lobby state is not pick
        if Queue.get(ctx.guild.id, ctx.channel.id, "state") != "pick":
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} it is not the picking phase", 
                    color = 15158588
            ))
        
        # // Check if the user is not the captain
        if ctx.author != Queue.get(ctx.guild.id, ctx.channel.id, "pick_logic")[0]:
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} it is not your turn to pick", 
                    color = 15158588
            ))
        
        # // Check if the user is not in the queue
        if user not in Queue.get(ctx.guild.id, ctx.channel.id, "queue"):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} that player is not in this queue", 
                    color = 15158588
            ))
        
        # // Pick the user
        await ctx.send(embed = Queue.pick(ctx.guild, ctx.channel.id, ctx.author, user))
        
        # // Send the embed
        await ctx.send(embed = Queue.embed(ctx.guild, ctx.channel.id))
        

    # Pick map to play (blue captain) command
    @commands.command(name="pickmap", description='`=pickmap (map name)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def pickmap(self, ctx: commands.Context, map: str):
        if ctx.author.bot:
            return
        
        # // Check if the lobby is valid
        if not Queue.is_valid_lobby(ctx.guild.id, ctx.channel.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby", 
                    color = 15158588
            ))
        
        # // Check if the lobby state is not maps
        if Queue.get(ctx.guild.id, ctx.channel.id, "state") != "maps":
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} it is not the map picking phase", 
                    color = 15158588
            ))
        
        # // Check if the user is the blue team captain
        if ctx.author != Queue.get(ctx.guild.id, ctx.channel.id, "blue_cap"):
            return await ctx.send(
                embed = discord.Embed(
                    description=f"{ctx.author.mention} you are not the blue team captain", 
                    color=15158588
            ))
        
        # // Get the maps
        maps: list = Lobby.get(ctx.guild.id, ctx.channel.id, "maps")

        # // Check if the map is in the map pool
        for m in maps:
            if map.lower() in m.lower():
                Queue.update_map(ctx.guild.id, ctx.channel.id, map)
                Queue.update_state(ctx.guild.id, ctx.channel.id, "final")
                return await ctx.send(embed = Queue.embed(ctx.guild, ctx.channel.id))
        
        # // If the map is not in the map pool
        await ctx.send(
            embed = discord.Embed(
            description = f"{ctx.author.mention} that map is not in the map pool", 
            color = 15158588
        ))
            
        
    # // Join the queue command
    @commands.command(name = "join", aliases = ["j"], description = '`=join`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def join(self, ctx: commands.Context):
        if not ctx.author.bot:
            await ctx.send(
                embed = await Queue.join(ctx.guild, ctx.channel.id, ctx.author)
            )

    # // Force join an user to the queue command
    @commands.command(name = "forcejoin", aliases = ["fj"], description = '`=forcejoin (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def forcejoin(self, ctx: commands.Context, user: discord.Member):
        if ctx.author.bot:
            return
        
        # // Check if the user has the mod role
        if not Users.is_mod(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
        # // Force join the user
        await ctx.send(
            embed = await Queue.join(ctx.guild, ctx.channel.id, user)
        )

    # // Leave the queue command
    @commands.command(name="leave", aliases=["l"], description='`=leave`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def leave(self, ctx: commands.Context):
        if not ctx.author.bot:
            await ctx.send(
                embed = Queue.leave(ctx.guild, ctx.channel.id, ctx.author)
            )

    # // Force remove an user from the queue command
    @commands.command(name="forceleave", aliases=["fl"], description='`=forceleave (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def forceleave(self, ctx: commands.Context, user:discord.Member):
        if ctx.author.bot:
            return
        
        # // Check if the author has the mod role
        if not Users.is_mod(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
        # // Forceleave the user
        await ctx.send(
            embed = Queue.leave(ctx.guild, ctx.channel.id, user)
        )

    # // Show the current queue command
    @commands.command(name="queue", aliases=["q"], description='`=queue`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def queue(self, ctx: commands.Context):
        if ctx.author.bot:
            return
        
        # // Check if the lobby is valid
        if not Queue.is_valid_lobby(ctx.guild.id, ctx.channel.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby", 
                    color = 15158588
            ))
        
        # // Send the embed
        await ctx.send(embed = Queue.embed(ctx.guild, ctx.channel.id))
        
    # // Clear the current queue command
    @commands.command(name="clear", description='`=clear`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def clear(self, ctx: commands.Context):
        if ctx.author.bot:
            return
        
        # // Check if the user is a mod
        if not Users.is_mod(ctx.author):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you do not have enough permissions", 
                    color = 15158588
            ))
        
        # // Check if the lobby is valid
        if not Queue.is_valid_lobby(ctx.guild.id, ctx.channel.id):
            return await ctx.send(
                embed = discord.Embed(
                description = f"{ctx.author.mention} this channel is not a lobby", 
                color = 15158588
            ))
        
        # // Clear the queue
        Queue.clear(ctx.guild.id, ctx.channel.id)
        return await ctx.send(
            embed = discord.Embed(
                description = f"{ctx.author.mention} has cleared the queue", 
                color = 3066992
            ))
        
    # // Party commands
    @commands.command(name="party", aliases=["team"], description='`=party create`**,** `=party leave)`**,** `=party show`**,** `=party kick (@user)`**,** `=party invite (@user)`')
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def party(self, ctx: commands.Context, action: str, *args):
        if ctx.author.bot:
            return
        
        # // Check if the lobby is valid
        if not Queue.is_valid_lobby(ctx.guild.id, ctx.channel.id):
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} this channel is not a lobby", 
                    color = 15158588
            ))
        
        # // Get the parties and max party size
        parties: list = Queue.get_parties(ctx.guild.id)
        max_party_size: int = Lobby.get(ctx.guild.id, ctx.channel.id, "max_party_size")

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
            user: discord.Member = ctx.guild.get_member(int(re.sub("\D","", args[0])))
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
                message: discord.Message = await user.send(
                    embed = discord.Embed(
                        description=f"{ctx.author.mention} has invited you to join their party", 
                        color=33023), 
                    components=[[
                        Button(style=ButtonStyle.green, label="Accept", custom_id='accept_party'),
                        Button(style=ButtonStyle.red, label="Decline", custom_id='decline_party')
                ]])

                # // Wait for the user to accept or decline the invite
                res: discord.Interaction = await self.client.wait_for(
                    "button_click", 
                    timeout = 10,
                    check = lambda msg: msg.author == user and msg.message.id == message.id
                )

                # // If the user accepted the party invite
                if res.component.id == "accept_party":
                    Queue.add_to_party(ctx.guild.id, ctx.author.id, user.id)
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
                Queue.disband_party(ctx.guild.id, ctx.author.id)

                # // Send the embed
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} has disbanded their party", 
                        color = 3066992
                    )
                )

            # // Remove the user from the party
            if Queue.remove_from_party(ctx.guild.id, ctx.author.id):
                return await ctx.send(
                    embed = discord.Embed(
                        description = f"{ctx.author.mention} has left the party", 
                        color = 3066992
                ))
            
            # // Send a message that the user is not in a party
            return await ctx.send(
                embed = discord.Embed(
                    description = f"{ctx.author.mention} you are not in a party", 
                    color = 15158588
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
                    member: discord.Member = Users.verify(ctx.guild, party)
                    if member is None:
                        continue

                    # // Send the party
                    return await ctx.send(
                        embed = discord.Embed(
                            title = f"[{len(parties[party])}/{max_party_size}] {member.name}'s party", 
                            description = "\n".join("<@" + str(user) + ">" for user in parties[party]),
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
                user: discord.Member = ctx.guild.get_member(int(re.sub("\D","", args[0])))

                # // Find the party the user is in
                for party in parties:
                    # // If the user is in the party, return the party
                    if user.id not in parties[party]:
                        continue

                    # // Verify the party leader
                    member: discord.Member = await self.verify_member(ctx, party)
                    if member is None:
                        continue

                    # // Send the party
                    return await ctx.send(
                        embed = discord.Embed(
                            title = f"[{len(parties[party])}/{max_party_size}] {member.name}'s party", 
                            description = "\n".join("<@" + str(user) + ">" for user in parties[user.id]), 
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
            Queue.create_party(ctx.guild.id, ctx.author.id)
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
            user: discord.Member = ctx.guild.get_member(int(re.sub("\D","", args[0])))
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
            Queue.remove_from_party(ctx.guild.id, user.id)
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
            lobby: discord.Channel = res.guild.get_channel(int(res.message.embeds[0].footer.text))

            # // Verify that the lobby exists
            if lobby is None:
                await res.channel.send(
                    embed = discord.Embed(
                        description = f"{res.author.mention} unknown lobby", color=3066992
                ))
                return await res.message.delete()
            
            # // Check if the lobby is valid
            if Queue.is_valid_lobby(res.guild.id, lobby.id):
                # // If the user is trying to join the queue
                if res.component.id == "join_queue":
                    await Queue.join(res.guild, lobby.id, res.author)

                # // If the user is trying to leave the queue
                elif res.component.id == "leave_queue":
                    await Queue.leave(res.guild, lobby.id, res.author)
                
                # // Get the players and store them in a string
                queue_players: list = Queue.get(res.guild.id, lobby.id, "queue")
                players: str = "\n".join(str(p.mention) for p in queue_players)

                # // Get the queue size
                queue_size: int = Lobby.get(res.guild.id, lobby.id, "queue_size")

                # // Create the new embed
                current_queue_size: int = len(queue_players)
                embed: discord.Embed = discord.Embed(
                    title=f'[{current_queue_size}/{queue_size}] {lobby.name}', 
                    description = players, 
                    color=33023
                )
                embed.set_footer(text=str(lobby.id))

                # // Edit the embed
                return await res.message.edit(embed=embed)
                

def setup(client: commands.Bot):
    client.add_cog(QueueCog(client))