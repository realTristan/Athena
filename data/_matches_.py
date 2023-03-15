from data import Cache, Lobby, User
import discord

class Matches:
    # // Get the number of matches in the lobby
    @staticmethod
    def count(guild_id: int, lobby_id: int):
        return len(Cache.fetch("matches", guild_id)[lobby_id])
    
    # // Get a match
    @staticmethod
    def get(guild_id: int, lobby_id: int, match_id: int = None):
        if match_id is not None:
            return Cache.fetch("matches", guild_id)[lobby_id][match_id]
        return Cache.fetch("matches", guild_id)[lobby_id]
    

    # // Delete a match category
    @staticmethod
    async def delete_category(guild: discord.Guild, match_id: int):
        category = discord.utils.get(guild.categories, name=f"Match #{match_id}")
        
        # // If the category does not exist
        if not category:
            return
        
        # // Delete the channels
        for channel in category.channels:
            await channel.delete()

        # // Delete the category
        return await category.delete()
    
    
    # // Search through all lobbies to find a match
    @staticmethod
    def find(guild_id: int, match_id: int):
        # // Get the matches
        matches = Cache.fetch("matches", guild_id)

        # // Search through the matches
        for lobby_id in matches:
            if match_id in matches[lobby_id]:
                return matches[lobby_id]
        
        # // Return None if the match was not found
        return None
    

    # // Show the match
    @staticmethod
    def show(guild_id: int, match_id: int):
        # // Fetch the match data
        match_data: dict = Matches.find(guild_id, match_id)

        # // Check to make sure the match is valid
        if match_data is None:
            return discord.Embed(
                description = f"We were unable to find **Match #{match_id}**", 
                color = 15158588
            )

        # // Get the match winners and clean up the team name
        match_winners = match_data["winners"][0].upper() + match_data["winners"][1:]
        match_status = match_data["status"]
        match_map = match_data["map"]

        # // Team variables
        orange_captain = match_data["orange_cap"]
        orange_team = match_data["orange_team"].split(",")
        blue_captain = match_data["blue_cap"]
        blue_team = match_data["blue_team"].split(",")

        # // Create the embed
        embed = discord.Embed(
            title = f"Match #{match_id} ┃ {match_status}", 
            description = f"**Map:** {match_map}\n**Winners:** {match_winners}", 
            color = 33023
        )

        # // Captains
        embed.add_field(name = "Orange Captain", value = f"<@{orange_captain}>")
        embed.add_field(name = "\u200b", value = "\u200b")
        embed.add_field(name = "Blue Captain", value = f"<@{blue_captain}>")

        # // Teams
        embed.add_field(name = "Orange Team", value = '\n'.join(f"<@{e}>" for e in orange_team))
        embed.add_field(name = "\u200b", value = "\u200b")
        embed.add_field(name = "Blue Team", value = '\n'.join(f"<@{e}>" for e in blue_team))
        
        # // Return the embed
        return embed
        
    # // Add a match to the lobby
    @staticmethod
    async def add(guild_id: int, lobby_id: int, match_id: int, match_data: dict):
        # // Convert the match teams to strings
        orange_team_str: str = ','.join(str(user.id) for user in match_data["orange_team"])
        blue_team_str: str = ','.join(str(user.id) for user in match_data["blue_team"])

        # // Add the match to the cache
        await Cache.update("matches", guild=guild_id, lobby=lobby_id, data={
            match_id: {
                "lobby_id": lobby_id, 
                "map": match_data["map"], 
                "orange_cap": match_data["orange_cap"], 
                "orange_team": match_data["orange_team"],
                "blue_cap": match_data["blue_cap"],
                "blue_team": match_data["blue_team"], 
                "status": match_data["status"],
                "winners": match_data["winners"]
            }
        }, sqlcmds=[
            f"""
            INSERT INTO matches (guild_id, match_id, lobby_id, map, orange_cap, orange_team, blue_cap, blue_team, status, winners) 
            VALUES (
                {guild_id}, {match_id}, {lobby_id}, '{match_data["map"]}', '{match_data["orange_cap"]}', '{orange_team_str}', 
                '{match_data["blue_cap"]}', '{blue_team_str}', '{match_data["status"]}', '{match_data["winners"]}'
            )"""
        ])

    # // Delete a match from the lobby
    @staticmethod
    async def delete(guild_id: int, lobby_id: int, match_id: str):
        Cache.delete_match(guild_id, lobby_id, match_id)

    # // Undo a match result
    @staticmethod
    async def undo(guild: discord.Guild, lobby_id: int, winners: list, losers: list):
        # // Fetch the lobby settings
        lobby_settings: dict = Lobby(guild.id, lobby_id).get()
        negative_elo: bool = lobby_settings["negative_elo"] == 1
        win_elo: int = lobby_settings["win_elo"]
        loss_elo: int = lobby_settings["loss_elo"]


        # // Remove the loss from the losers
        for user in losers:
            # // Verify the user
            if User(guild.id, user).verify() is None:
                continue
            
            # // Get the user info
            user_info: dict = User(guild.id, user).info()
            user_elo: int = user_info["elo"]
            user_losses: int = user_info["losses"]
            new_elo: int = user_elo + loss_elo

            # // Update the users elo and losses
            User(guild.id, user).update_elo(elo = new_elo, loss = user_losses - 1)

            # // Add any elo roles that were lost
            user: discord.Member = await guild.get_member(user)
            await User.add_elo_roles(guild, user, new_elo)

    
        # // Remove the win from the winners
        for user in winners:
            # // Verify the user
            if User(guild.id, user).verify() is None:
                continue
                
            # // Get the user info
            user_info: dict = User(guild.id, user).info()
            user_elo: int = user_info["elo"]
            user_wins: int = user_info["wins"]
            new_elo: int = user_elo - win_elo

            # // If negative elo is enabled, set the users new elo to 0
            if not negative_elo and (user_elo - win_elo) < 0:
                new_elo = 0
            
            # // Update the users elo and wins
            User(guild.id, user).update_elo(elo = new_elo, win = user_wins - 1)

            # // Remove any elo roles that were added
            user: discord.Member = await guild.get_member(user)
            await User.remove_elo_roles(guild, user, new_elo)
            
    # // Update a match
    @staticmethod
    async def update(guild_id: int, lobby_id: int, match_id: int, status: str = None, winners: list = None):
        # // Get the current match data
        match_data: dict = Matches.get(guild_id, lobby_id)[match_id]

        # // Update the match status
        if status is not None:
            match_data["status"] = status
            Cache.update("matches", guild=guild_id, lobby=lobby_id, data={match_id: match_data}, sqlcmds=[
                f"UPDATE matches SET status = '{status}' WHERE guild_id = {guild_id} AND lobby_id = {lobby_id} AND match_id = {match_id}"
            ])

        # // Update the match winners
        if winners is not None:
            match_data["winners"] = winners
            Cache.update("matches", guild=guild_id, lobby=lobby_id, data={match_id: match_data}, sqlcmds=[
                f"UPDATE matches SET winners = '{winners}' WHERE guild_id = {guild_id} AND lobby_id = {lobby_id} AND match_id = {match_id}"
            ])
       