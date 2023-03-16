from cache import Lobby, Users, Matches, Settings, Users, Bans
from discord_components import *
import discord, random

# // Store the queue data in a cache map
queue: dict = {}

# // Queue Class
class Queue:
    # // Reset the queue
    @staticmethod
    def clear(guild_id: int, lobby_id: int):
        # // Add the guild if it doesn't exist
        if guild_id not in queue:
            queue[guild_id] = {}

        # // Reset the queue
        queue[guild_id][lobby_id] = {
            "queue": [], 
            "blue_cap": None, 
            "blue_team": [], 
            "orange_cap": None, 
            "orange_team": [], 
            "pick_logic": [], 
            "map": "None",
            "state": "queue"
        }

    # // Reset the parties
    @staticmethod
    def reset_parties(guild_id: int):
        # // Add the guild if it doesn't exist
        if guild_id not in queue:
            queue[guild_id] = {}

        # // Reset the parties
        queue[guild_id]["parties"] = {}

    # // Get a value from the queue cache
    @staticmethod
    def get(guild_id: int, lobby_id: int, key: str) -> any:
        return queue[guild_id][lobby_id][key]
    
    # // Get the lobby data
    @staticmethod
    def get_lobby(guild_id: int, lobby_id: int) -> any:
        return queue[guild_id][lobby_id]
    
    # // Delete the lobby
    @staticmethod
    def delete_lobby(guild_id: int, lobby_id: int) -> None:
        del queue[guild_id][lobby_id]

    # // Get a party from the cache
    @staticmethod
    def get_parties(guild_id: int, party: int = None) -> any:
        if party is None:
            return queue[guild_id]["parties"]
        return queue[guild_id]["parties"][party]
    
    # // Check if channel is a valid queue lobby
    @staticmethod
    def is_valid_lobby(guild_id: int, lobby_id: int) -> bool:
        if guild_id not in queue:
            queue[guild_id] = {}
        
        # // Check if the lobby exists
        if not Lobby.exists(guild_id, lobby_id):
            return False
        
        # // Check if the lobby is in the cache
        if lobby_id not in queue[guild_id]:
            Queue.clear(guild_id, lobby_id)
            Queue.reset_parties(guild_id)
        return True
    
    # // Update the map
    @staticmethod
    def update_map(guild_id: int, lobby_id: int, map: str) -> None:
        queue[guild_id][lobby_id]["map"] = str(map[0]).upper() + str(map[1:]).lower()

    # // Update the state
    @staticmethod
    def update_state(guild_id: int, lobby_id: int, state: str) -> None:
        queue[guild_id][lobby_id]["state"] = state

    # // Add an user to a party
    @staticmethod
    def add_to_party(guild_id: int, party_leader: int, user_id: int) -> None:
        queue[guild_id]["parties"][party_leader].append(user_id)

    # // Create a party
    @staticmethod
    def create_party(guild_id: int, party_leader: int) -> None:
        queue[guild_id]["parties"][party_leader] = []

    # // Disband a party
    @staticmethod
    def disband_party(guild_id: int, party_leader: int) -> None:
        del queue[guild_id]["parties"][party_leader]
    
    # // Remove a user from a party
    @staticmethod
    def remove_from_party(guild_id: int, user_id: int) -> bool:
        for party in queue[guild_id]["parties"]:
            if user_id in queue[guild_id]["parties"][party]:
                queue[guild_id]["parties"][party].remove(user_id)
                return True
        return False

    
    # // Pick and user function
    @staticmethod
    def pick(guild: discord.Guild, lobby_id: int, captain: discord.Member, user: discord.Member) -> discord.Embed:
        # // Pop the first item from the pick logic
        queue[guild.id][lobby_id]["pick_logic"].pop(0)

        # // If the user is the blue team captain
        if queue[guild.id][lobby_id]["blue_cap"] == captain:
            queue[guild.id][lobby_id]["blue_team"].append(user)
            queue[guild.id][lobby_id]["queue"].remove(user)

        # // If the user is the orange team captain
        elif queue[guild.id][lobby_id]["orange_cap"] == captain:
            queue[guild.id][lobby_id]["orange_team"].append(user)
            queue[guild.id][lobby_id]["queue"].remove(user)

        # // Check if the queue has one player left
        if len(queue[guild.id][lobby_id]["queue"]) == 1:
            # // Add the last player to the team
            queue[guild.id][lobby_id]["orange_team"].append(queue[guild.id][lobby_id]["queue"][0])
            queue[guild.id][lobby_id]["queue"].remove(queue[guild.id][lobby_id]["queue"][0])

            # // Get whether the map pick phase is enabled
            map_pick_phase: int = Lobby.get(guild.id, lobby_id, "map_pick_phase")

            # // If the map pick phase is enabled
            if map_pick_phase == 1:
                queue[guild.id][lobby_id]["state"] = "maps"

            # // If the map pick phase is disabled
            else:
                # // Get the maps
                maps: list = Lobby.get(guild.id, lobby_id, "maps")

                # // If there are maps
                if len(maps) > 0:
                    # // Pick a random map
                    queue[guild.id][lobby_id]["map"] = random.choice(maps)

                # // Set the state to final
                queue[guild.id][lobby_id]["state"] = "final"

        # // Send who the captain picked
        return discord.Embed(
            description = f"{captain.mention} has picked {user.mention}", 
            color = 33023
        )
            
    # // When the queue reaches max capacity function
    @staticmethod
    async def start(guild: discord.Guild, lobby_id: int) -> discord.Embed:
        # // Get the lobby settings
        lobby: dict = Lobby.get(guild.id, lobby_id)

        # // Set the blue team captain
        blue_cap: discord.Member = random.choice(queue[guild.id][lobby_id]["queue"])
        queue[guild.id][lobby_id]["blue_cap"] = blue_cap
        queue[guild.id][lobby_id]["queue"].remove(blue_cap)
        
        # // Set the orange team captain
        orange_cap: discord.Member = random.choice(queue[guild.id][lobby_id]["queue"])
        queue[guild.id][lobby_id]["orange_cap"] = orange_cap
        queue[guild.id][lobby_id]["queue"].remove(orange_cap)

        # // If the pick phase is enabled
        if lobby["team_pick_phase"] == 1:
            queue[guild.id][lobby_id]["state"] = "pick"

            # // Get the pick logic
            await Queue.generate_pick_logic(guild.id, lobby_id)

            # // Send the embed
            return Queue.embed(guild.id, lobby_id)
        
        # // If pick phase is diabled, create random teams
        for _ in range(len(queue[guild.id][lobby_id]["queue"]) // 2):
            # // Get a random user from the queue
            user: discord.Member = random.choice(queue[guild.id][lobby_id]["queue"])

            # // Add the user to the orange team
            queue[guild.id][lobby_id]['orange_team'].append(user)
            queue[guild.id][lobby_id]["queue"].remove(user)
        
        # // Add the remaining users to the blue team
        for _ in range(len(queue[guild.id][lobby_id]["queue"])):
            queue[guild.id][lobby_id]['blue_team'].append(user)
            queue[guild.id][lobby_id]["queue"].remove(user)
        
        # // If the map pick phase is enabled
        if lobby["map_pick_phase"] == 1:
            # // Set the state to map picking phase
            queue[guild.id][lobby_id]["state"] = "maps"

            # // Send the embed
            return Queue.embed(guild, lobby_id)

        # // Get the maps
        maps: list = lobby.get("maps")
        queue[guild.id][lobby_id]["map"] = "None"
        
        # // If there are maps
        if len(maps) > 0:
            queue[guild.id][lobby_id]["map"] = random.choice(maps)

        # // Set the state to final
        queue[guild.id][lobby_id]["state"] = "final"

        # // Store the embed
        embed: discord.Embed = Queue.embed(guild, lobby_id)

        # // Get the count of matches
        amount_of_matches: int = Matches.count(guild.id) + 1

        # // Match functions
        await Queue.new_match(guild.id, lobby_id)
        await Queue.log_match(guild, embed)
        await Queue.create_match_category(guild, amount_of_matches, lobby_id)
        Queue.clear(guild.id, lobby_id)

        # // Send the embed
        return embed
    
    # // When an user joins the queue functioncheck_party
    @staticmethod
    async def join(guild: discord.Guild, lobby_id: int, user: discord.Member) -> discord.Embed:
        # // If the lobby is invalid
        if not Queue.is_valid_lobby(guild.id, lobby_id):
            return discord.Embed(
                description = f"{user.mention} this channel is not a lobby", 
                color = 15158588
            )
        
        # // If the lobby state is not queue
        if queue[guild.id][lobby_id]["state"] != "queue":
            return discord.Embed(
                description = f"{user.mention} it is not the queueing phase", 
                color = 15158588
            )
        
        # // If the user isn't registered
        if not Users.exists(guild.id, user.id):
            return discord.Embed(
                description = f"{user.mention} is not registered",
                color = 15158588
            )
        
        # // Check if the user is a party leader
        if not await Queue.check_party(guild, user, lobby_id):
            return discord.Embed(
                description = f"{user.mention} you are not a party leader / party too full", 
                color = 15158588
            )
        
        # // Check if the user is already queued
        for lobby in queue[guild.id]:
            if user in queue[guild.id][lobby]["queue"]:
                # // Get the channel
                channel: discord.Channel = guild.get_channel(lobby)

                # // If the channel is not found, then remove the lobby
                if channel is None:
                    del queue[guild.id][lobby]

                # // Return the embed
                return discord.Embed(
                    description = f"{user.mention} is already queued in {channel.mention}", 
                    color = 15158588
                )

        # // Check if the user is banned
        if Bans.is_banned(guild.id, user.id):
            return await Bans.embed(guild.id, user)

        # // Get the queue sizes
        queue_size: int = Lobby.get(guild.id, lobby_id, "queue_size")
        current_queue_size: int = len(queue[guild.id][lobby_id]["queue"])

        # // Add the user to the queue
        queue[guild.id][lobby_id]["queue"].append(user)

        # // If the queue is full, then start the game
        if current_queue_size == queue_size:
            await Queue.start(guild, lobby_id)
        
        # // Send the queue embed
        return discord.Embed(
            description = f"**[{current_queue_size + 1}/{queue_size}]** {user.mention} has joined the queue", 
            color = 33023
        )
    
    # // Add other party members to the queue
    @staticmethod
    async def check_party(guild: discord.Guild, user: discord.Member, lobby_id: int) -> bool:
        # // If the user isn't a party leader
        if user.id not in queue[guild.id]["parties"]:
            return True
        
        # // Check if the user is in a party
        for party in queue[guild.id]["parties"]:
            if user.id in queue[guild.id]["parties"][party] and party != user.id:
                return False
        
        # // Get the queue size
        max_queue_size: int = Lobby.get(guild.id, lobby_id, "queue_size")
        lobby_queue_size: int = len(queue[guild.id][lobby_id]["queue"])
        party_size: int = len(queue[guild.id]["parties"][user.id])

        # // Check if the party can join the queue
        if party_size + lobby_queue_size > max_queue_size:
            return False
            
        # // Add the party to the queue
        for party_member in queue[guild.id]["parties"][user.id][1:]:
            party_member: discord.Member = await Users.verify(guild, party_member.id)

            # // If the party member is in the guild and registered
            if party_member is not None:
                await Queue.join(guild, party_member, lobby_id)

        # // Return true
        return True
    
    # // When an user leaves the queue function
    @staticmethod
    def leave(guild: discord.Guild, lobby_id: int, user: discord.Member) -> discord.Embed:
        # // If the lobby is invalid
        if not Queue.is_valid_lobby(guild.id, lobby_id):
            return discord.Embed(
                description = f"{user.mention} this channel is not a lobby", 
                color = 15158588
            )
        
        # // If the lobby state is not queue
        if queue[guild.id][lobby_id]["state"] != "queue":
            return discord.Embed(
                description = f"{user.mention} it is not the queueing phase", 
                color = 15158588
            )
        
        # // If the user is not in the queue
        if user not in queue[guild.id][lobby_id]["queue"]:
            return discord.Embed(
                description = f"{user.mention} is not in the queue", 
                color = 15158588
            )
        
        # // Get the queue sizes
        queue_size: int = Lobby.get(guild.id, lobby_id, "queue_size")
        current_queue_size: int = len(queue[guild.id][lobby_id]['queue'])

        # // Remove the user from the queue
        queue[guild.id][lobby_id]["queue"].remove(user)

        # // Send the queue embed
        return discord.Embed(
            description = f"**[{current_queue_size - 1}/{queue_size}]** {user.mention} has left the queue", 
            color = 33023
        )
    
    # // Routing function to create a new match
    @staticmethod
    async def new_match(guild_id: int, lobby_id: int) -> None:
        # // Get the orange team and their user ids
        orange_team: list = queue[guild_id][lobby_id].get("orange_team")
        orange_team = [user.id for user in orange_team]

        # // Get the blue team and their user ids
        blue_team: list = queue[guild_id][lobby_id].get("blue_team")
        blue_team = [user.id for user in blue_team]

        # // Get the team captains
        orange_cap: discord.Member = queue[guild_id][lobby_id].get("orange_cap")
        blue_cap: discord.Member = queue[guild_id][lobby_id].get("blue_cap")

        # // Get the count of matches
        amount_of_matches: int = Matches.count(guild_id) + 1

        # // Add the match to the database
        await Matches.add(guild_id, lobby_id, amount_of_matches, {
            "orange_team": orange_team,
            "blue_team": blue_team,
            "orange_cap": orange_cap.id,
            "blue_cap": blue_cap.id
        })

    # // Create the match category function
    @staticmethod
    async def create_match_category(guild: discord.Guild, match_id: int, lobby_id: int) -> None:
        match_categories: int = Settings.get(guild.id, "match_categories")

        # // If the match categories are disabled
        if match_categories == 0:
            return
        
        # // If the match category already exists
        if discord.utils.get(guild.categories, name=f'Match #{match_id}'):
            return
        
        # // Creating category and setting permissions
        category: discord.Category = await guild.create_category(f'Match #{match_id}')
        await category.set_permissions(guild.default_role, connect = False, send_messages = False)

        # // Creating channels inside category
        await guild.create_text_channel(f"match-{match_id}", category = category)
        await guild.create_voice_channel(f'🔹 Team ' + queue[guild.id][lobby_id]["blue_cap"].name, category = category)
        await guild.create_voice_channel(f"🔸 Team " + queue[guild.id][lobby_id]['orange_cap'].name, category = category)

        # // Blue team
        blue_team: list = queue[guild.id][lobby_id].get("blue_team")
        blue_team.append(queue[guild.id][lobby_id]["blue_cap"])

        # // Orange team
        orange_team: list = queue[guild.id][lobby_id].get("orange_team")
        orange_team.append(queue[guild.id][lobby_id]["orange_cap"])

        # // Edit the permissions for each player in the teams
        for user in orange_team:
            await category.set_permissions(user, connect = True, send_messages = True)

        for user in blue_team:
            await category.set_permissions(user, connect = True, send_messages = True)
    
    # // Create team pick logic function
    @staticmethod
    async def generate_pick_logic(guild_id: int, lobby_id: int) -> None:
        # // Get the queue size
        queue_size: int = len(queue[guild_id][lobby_id]["queue"])

        # // Get the team captains
        blue_captain: discord.Member = queue[guild_id][lobby_id]["blue_cap"]
        orange_captain: discord.Member = queue[guild_id][lobby_id]["orange_cap"]

        # // Iterate over the queue size
        for _ in range(queue_size // 2):
            # // Add the captains to the pick logic
            queue[guild_id][lobby_id]["pick_logic"].append(blue_captain)
            queue[guild_id][lobby_id]["pick_logic"].append(orange_captain)

        # // If the queue size is odd
        if queue_size % 2 != 0:
            # // Add the blue captain to the pick logic
            queue[guild_id][lobby_id]["pick_logic"].append(blue_captain)


    # // Send match logs to the given match logs channel
    @staticmethod
    async def log_match(guild: discord.Guild, embed: discord.Embed) -> None:
        match_logs: int = Settings.get(guild.id, "match_logs")

        # // If the match logs are disabled
        if match_logs == 0:
            return
        
        # // If the match logs are enabled
        channel: discord.Channel = guild.get_channel(match_logs)

        # // If the channel is not found, set the match logs to 0
        if channel is None:
            return await Settings.update(guild.id, match_logs=0)
        
        # // Else, send the embed to the channel
        await channel.send(
            embed = embed,
            components = [[
                Button(style=ButtonStyle.blue, label="Blue", custom_id='blue_report'),
                Button(style=ButtonStyle.blue, label="Orange", custom_id='orange_report'),
                Button(style=ButtonStyle.red, label="Cancel", custom_id='match_cancel')
            ]])
    

    # // Embed generator function (for queue)
    @staticmethod
    def embed(guild: discord.Guild, lobby_id: int) -> discord.Embed:
        # // Get the lobby data
        queue_state: str = queue[guild.id][lobby_id]["state"]

        # // Queue phase embed
        if queue_state == "queue":
            return Queue.state_queue_embed(guild, lobby_id)

        # // Team picking phase embed
        elif queue_state == "pick":
            return Queue.state_pick_embed(guild, lobby_id)

        # // Map picking phase embed
        elif queue_state == "maps":
            return Queue.state_maps_embed(guild, lobby_id)

        # // Final match up embed
        elif queue_state == "final":
            return Queue.state_final_embed(guild, lobby_id)

    # // Embed generator function (for queue)
    @staticmethod
    def state_queue_embed(guild: discord.Guild, lobby_id: int) -> discord.Embed:
        # // Get the lobby data
        queue_data: dict = queue[guild.id][lobby_id]

        # // Get the name of the lobby
        lobby_name: str = guild.get_channel(lobby_id).name

        # // Get the queue sizes
        current_queue_size: int = len(queue_data["queue"])
        max_queue_size: int = Lobby.get(guild.id, lobby_id, "queue_size")

        # // Get the queue
        description: str = "None"
        if current_queue_size > 0:
            description = "\n".join([user.mention for user in queue_data["queue"]])

        # // Return the embed
        return discord.Embed(
            title = f"Queue ┃ {lobby_name} ┃ {current_queue_size}/{max_queue_size}",
            description = description,
            color = 33023
        )

    # // Embed generator function (for team picking)
    @staticmethod
    def state_pick_embed(guild: discord.Guild, lobby_id: int) -> None:
        # // Get the lobby data
        queue_data: dict = queue[guild.id][lobby_id]

        # // Get the count of matches
        amount_of_matches: int = Matches.count(guild.id) + 1

        # // Create the embed
        embed: discord.Embed = discord.Embed(
            title = f"Match #{amount_of_matches}", 
            color = 33023
        )

        # // Captains
        embed.add_field(name = "Orange Captain", value = queue_data["orange_cap"].mention)
        embed.add_field(name = "\u200b", value = "\u200b")
        embed.add_field(name = "Blue Captain", value = queue_data["blue_cap"].mention)

        # // Teams
        embed.add_field(name = "Orange Team", value = "None")
        embed.add_field(name = "\u200b", value = "\u200b")
        embed.add_field(name = "Blue Team", value = "None")

        # // Available players
        embed.add_field(
            name = "Available Players", 
            value = "\n".join([user.mention for user in queue_data["queue"]])
        )

        # // Return the embed
        return embed

    # // Embed generator function (for map picking)
    @staticmethod
    def state_maps_embed(guild: discord.Guild, lobby_id: int) -> None:
        # // Get the lobby data
        queue_data: dict = queue[guild.id][lobby_id]

        # // Get the count of matches
        amount_of_matches: int = Matches.count(guild.id) + 1

        # // Get the maps
        maps: list = Lobby.get(guild.id, lobby_id, "maps")

        # // Get the blue team captain
        blue_cap: discord.Member = queue_data["blue_cap"]

        # // Create the embed
        embed: discord.Embed = discord.Embed(
            title = f"Match #{amount_of_matches}", 
            description=f"{blue_cap.mention} please pick a map",
            color = 33023
        )

        # // Captains
        embed.add_field(name = "Orange Captain", value = queue_data["orange_cap"].mention)
        embed.add_field(name = "\u200b", value = "\u200b")
        embed.add_field(name = "Blue Captain", value = queue_data["blue_cap"].mention)

        # // Teams
        embed.add_field(name = "Orange Team", value = '\n'.join(str(e.mention) for e in queue_data["orange_team"]))
        embed.add_field(name = "\u200b", value = "\u200b")
        embed.add_field(name = "Blue Team", value = '\n'.join(str(e.mention) for e in queue_data["blue_team"]))

        # // Available maps
        embed.add_field(name = "Available Maps", value = '\n'.join(str(m) for m in maps))

        # // Send the embed
        return embed
        

    # // Embed generator function (for final match up)
    @staticmethod
    def state_final_embed(guild: discord.Guild, lobby_id: int) -> None:
        # // Get the lobby data
        queue_data: dict = queue[guild.id][lobby_id]

        # // Get the count of matches
        amount_of_matches: int = Matches.count(guild.id) + 1

        # // Create the embed
        embed: discord.Embed = discord.Embed(
            title = f"Match #{amount_of_matches}", 
            description = f"**Map:** {queue_data['map']}", 
            color = 33023
        )

        # // Captains
        embed.add_field(name = "Orange Captain", value = queue_data["orange_cap"].mention)
        embed.add_field(name = "\u200b", value = "\u200b")
        embed.add_field(name = "Blue Captain", value = queue_data["blue_cap"].mention)

        # // Teams
        embed.add_field(name = "Orange Team", value = '\n'.join(str(e.mention) for e in queue_data["orange_team"]))
        embed.add_field(name = "\u200b", value = "\u200b")
        embed.add_field(name = "Blue Team", value = '\n'.join(str(e.mention) for e in queue_data["blue_team"]))

        # // Set the footer to the lobby id
        embed.set_footer(text = str(lobby_id))

        # // Send the embed
        return embed