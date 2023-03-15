import threading, discord, functools
from discord_components import *
from data import Lobby, User, Matches, Settings

# // Store the queue data in a cache map
queue: dict = {}

# // Queue Lock
queue_lock: threading.Lock = threading.Lock()

# // TODO
# // - Convert the join() function
# // - Convert the leave() function
# // - Convert the pick() function
# // - Convert the start() function

# // Queue Class
class Queue:
    @staticmethod
    def reset(guild_id: int, lobby_id: int):
        with queue_lock.acquire():
            queue[guild_id][lobby_id] = {
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
    
    # // Get the lobby data
    @staticmethod
    @functools.lru_cache(maxsize=128)
    def get_lobby(guild_id: int, lobby_id: int) -> any:
        return queue[guild_id][lobby_id]
    
    # // Get the lobby maps
    @staticmethod
    @functools.lru_cache(maxsize=128)
    def get_lobby_maps(guild_id: int, lobby_id: int) -> list:
        return queue[guild_id][lobby_id]["maps"]
    
    # // Check if channel is a valid queue lobby
    @staticmethod
    @functools.lru_cache(maxsize=128)
    async def is_valid_lobby(guild_id: int, lobby: int) -> bool:
        with queue_lock.acquire():
            if guild_id not in queue:
                queue[guild_id] = {}
        
        # // Check if the lobby exists
        if not Lobby.exists(guild_id, lobby):
            return False
        
        # // Check if the lobby is in the cache
        if lobby not in queue[guild_id]:
            Queue.reset(guild_id, lobby)
        return True
    
    # // Add other party members to the queue
    @staticmethod
    @functools.lru_cache(maxsize=128)
    async def check_party(guild: discord.Guild, user: discord.Member, lobby: int) -> bool:
        # // If the user isn't a party leader
        if user.id not in queue[guild.id][lobby]["parties"]:
            return True
        
        # // Check if the user is in a party
        for party in queue[guild.id][lobby]["parties"]:
            if user.id in queue[guild.id][lobby]["parties"][party] and party != user.id:
                return False
        
        # // Get the queue size
        max_queue_size: int = Lobby.get(guild.id, lobby, "queue_size")
        lobby_queue_size: int = len(queue[guild.id][lobby]["queue"])
        party_size: int = len(queue[guild.id][lobby]["parties"][user.id])

        # // Check if the party can join the queue
        if party_size + lobby_queue_size > max_queue_size:
            return False
            
        # // Add the party to the queue
        for party_member in queue[guild.id][lobby]["parties"][user.id][1:]:
            party_member: discord.Member = await User.verify(guild, party_member)

            # // If the party member is in the guild and registered
            if party_member is not None:
                await self._join(ctx, party_member, lobby)

        # // Return true
        return True
    
    # // Get a value from the queue cache
    @staticmethod
    @functools.lru_cache(maxsize=128)
    def get(guild_id: int, lobby: int, key: str) -> any:
        return queue[guild_id][lobby][key]
    
    # // Routing function to create a new match
    @staticmethod
    @functools.lru_cache(maxsize=128)
    async def new_match(guild_id: int, lobby: int) -> None:
        # // Get the orange team and their user ids
        orange_team: list = queue[guild_id][lobby].get("orange_team")
        orange_team = [user.id for user in orange_team]

        # // Get the blue team and their user ids
        blue_team: list = queue[guild_id][lobby].get("blue_team")
        blue_team = [user.id for user in blue_team]

        # // Get the team captains
        orange_cap: discord.Member = queue[guild_id][lobby].get("orange_cap")
        blue_cap: discord.Member = queue[guild_id][lobby].get("blue_cap")

        # // Get the count of matches
        amount_of_matches: int = Matches.count(guild_id, lobby) + 1

        # // Add the match to the database
        await Matches.add(guild_id, lobby, amount_of_matches, {
            "orange_team": orange_team,
            "blue_team": blue_team,
            "orange_cap": orange_cap.id,
            "blue_cap": blue_cap.id
        })

    # // Create the match category function
    @staticmethod
    async def create_match_category(guild: discord.Guild, match_id: int, lobby: int) -> None:
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
        await guild.create_voice_channel(f'🔹 Team ' + queue[guild.id][lobby]["blue_cap"].name, category = category)
        await guild.create_voice_channel(f"🔸 Team " + queue[guild.id][lobby]['orange_cap'].name, category = category)

        # // Blue team
        blue_team: list = queue[guild.id][lobby].get("blue_team")
        blue_team.append(queue[guild.id][lobby]["blue_cap"])

        # // Orange team
        orange_team: list = queue[guild.id][lobby].get("orange_team")
        orange_team.append(queue[guild.id][lobby]["orange_cap"])

        # // Edit the permissions for each player in the teams
        for user in orange_team:
            await category.set_permissions(user, connect = True, send_messages = True)

        for user in blue_team:
            await category.set_permissions(user, connect = True, send_messages = True)

    # // Create team pick logic function
    @staticmethod
    @functools.lru_cache(maxsize=128)
    async def pick_logic(guild_id: int, lobby: int) -> None:
        with queue_lock.acquire():
            # // Get the queue size
            queue_size: int = len(queue[guild_id][lobby]["queue"])

            # // Get the team captains
            blue_captain: discord.Member = queue[guild_id][lobby]["blue_cap"]
            orange_captain: discord.Member = queue[guild_id][lobby]["orange_cap"]

            # // Iterate over the queue size
            for _ in range(queue_size // 2):
                # // Add the captains to the pick logic
                queue[guild_id][lobby]["pick_logic"].append(blue_captain)
                queue[guild_id][lobby]["pick_logic"].append(orange_captain)

            # // If the queue size is odd
            if queue_size % 2 != 0:
                # // Add the blue captain to the pick logic
                queue[guild_id][lobby]["pick_logic"].append(blue_captain)


    # // Send match logs to the given match logs channel
    @staticmethod
    @functools.lru_cache(maxsize=128)
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
    @functools.lru_cache(maxsize=128)
    async def embed(guild: discord.Guild, lobby: int) -> discord.Embed:
        # // Get the lobby data
        queue_state: str = queue[guild.id][lobby]["state"]

        # // Queue phase embed
        if queue_state == "queue":
            Queue.state_queue_embed(guild, lobby)

        # // Team picking phase embed
        if queue_state == "pick":
            Queue.state_pick_embed(guild, lobby)

        # // Map picking phase embed
        if queue_state == "maps":
            Queue.state_maps_embed(guild, lobby)

        # // Final match up embed
        if queue_state == "final":
            Queue.state_final_embed(guild, lobby)

    # // Embed generator function (for queue)
    @staticmethod
    @functools.lru_cache(maxsize=128)
    async def state_queue_embed(guild: discord.Guild, lobby: int) -> discord.Embed:
        # // Get the lobby data
        queue_data: dict = queue[guild.id][lobby]

        # // Get the count of matches
        amount_of_matches: int = Matches.count(guild.id, lobby) + 1

        # // Create the embed
        embed: discord.Embed = discord.Embed(
            title = f"Match #{amount_of_matches}", description = f"**Map:** {queue_data['map']}", 
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

        # // Queue
        embed.add_field(name = "Queue", value = "\n".join([user.mention for user in queue_data["queue"]]))

        # // Return the embed
        return embed

    # // Embed generator function (for team picking)
    @staticmethod
    @functools.lru_cache(maxsize=128)
    async def state_pick_embed(guild: discord.Guild, lobby: int) -> None:
        # // Get the lobby data
        queue_data: dict = queue[guild.id][lobby]

        # // Get the count of matches
        amount_of_matches: int = Matches.count(guild.id, lobby) + 1

        # // Create the embed
        embed: discord.Embed = discord.Embed(
            title = f"Match #{amount_of_matches}", description = f"**Map:** {queue_data['map']}", 
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

        # // Return the embed
        return embed

    # // Embed generator function (for map picking)
    @staticmethod
    @functools.lru_cache(maxsize=128)
    async def state_maps_embed(guild: discord.Guild, lobby: int) -> None:
        # // Get the lobby data
        queue_data: dict = queue[guild.id][lobby]

        # // Get the count of matches
        amount_of_matches: int = Matches.count(guild.id, lobby) + 1

        # // Create the embed
        embed: discord.Embed = discord.Embed(
            title = f"Match #{amount_of_matches}", description = f"**Map:** {queue_data['map']}", 
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

        # // Send the embed
        return embed
        

    # // Embed generator function (for final match up)
    @staticmethod
    @functools.lru_cache(maxsize=128)
    async def state_final_embed(guild: discord.Guild, lobby: int) -> None:
        # // Get the lobby data
        queue_data: dict = queue[guild.id][lobby]

        # // Get the count of matches
        amount_of_matches: int = Matches.count(guild.id, lobby) + 1

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
        embed.set_footer(text = str(lobby))

        # // Match functions
        await Queue.new_match(guild.id, lobby)
        await Queue.log_match(guild, embed)
        await Queue.create_match_category(guild, amount_of_matches, lobby)
        Queue.reset(guild.id, lobby)

        # // Send the embed
        return embed