from data import Cache, Lobby, Users
import discord, functools

class Matches:
    # // Get the number of matches in the lobby
    @staticmethod
    def count(guild_id: int) -> int:
        return len(Cache.fetch("matches", guild_id))
    
    # // Get a match
    @staticmethod
    def get(guild_id: int, match_id: int = None) -> dict:
        if match_id is not None:
            return Cache.fetch("matches", guild_id)[match_id]
        return Cache.fetch("matches", guild_id)

    # // Delete a match category
    @staticmethod
    async def delete_category(guild: discord.Guild, match_id: int) -> None:
        category = discord.utils.get(guild.categories, name=f"Match #{match_id}")
        
        # // If the category does not exist
        if not category:
            return
        
        # // Delete the channels
        for channel in category.channels:
            await channel.delete()

        # // Delete the category
        return await category.delete()

    # // Produce a match embed
    @staticmethod
    @functools.lru_cache(maxsize=128)
    def embed(guild_id: int, match_id: int) -> discord.Embed:
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
        orange_team = match_data["orange_team"].split(",", maxsplit=4)
        blue_captain = match_data["blue_cap"]
        blue_team = match_data["blue_team"].split(",", maxsplit=4)

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
    async def add(guild_id: int, lobby_id: int, match_id: int, match_data: dict) -> None:
        # // Convert the match teams to strings
        orange_team_str: str = ','.join(str(user.id) for user in match_data["orange_team"])
        blue_team_str: str = ','.join(str(user.id) for user in match_data["blue_team"])

        # // Add the match to the cache
        await Cache.update("matches", guild_id=guild_id, data={
            match_id: {
                "match_id": match_id,
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
    async def delete(guild_id: int, match_id: int) -> None:
        Cache.delete_match(guild_id, match_id)

    # // Undo a match result
    @staticmethod
    async def undo(guild: discord.Guild, lobby_id: int, winners: list, losers: list) -> None:
        # // Fetch the lobby settings
        lobby_settings: dict = Lobby.get(guild.id, lobby_id)
        negative_elo: int = lobby_settings["negative_elo"]
        win_elo: int = lobby_settings["win_elo"]
        loss_elo: int = lobby_settings["loss_elo"]

        # // Remove the loss from the losers
        for user in losers:
            # // Verify the user
            if Users.verify(guild.id, user) is None:
                continue
            
            # // Get the user info
            user_info: dict = Users.info(guild.id, user)
            user_elo: int = user_info["elo"]
            user_losses: int = user_info["losses"]
            new_elo: int = user_elo + loss_elo

            # // Update the users elo and losses
            Users.update(guild.id, user, elo = new_elo, loss = user_losses - 1)

            # // Add any elo roles that were lost
            user: discord.Member = await guild.get_member(user)
            await Users.add_elo_role(user, new_elo)

    
        # // Remove the win from the winners
        for user in winners:
            # // Verify the user
            if Users.verify(guild.id, user) is None:
                continue
                
            # // Get the user info
            user_info: dict = Users.info(guild.id, user)
            user_elo: int = user_info["elo"]
            user_wins: int = user_info["wins"]
            new_elo: int = user_elo - win_elo

            # // If negative elo is enabled, set the users new elo to 0
            if negative_elo != 1 and (user_elo - win_elo) < 0:
                new_elo = 0
            
            # // Update the users elo and wins
            Users.update(guild.id, user, elo = new_elo, win = user_wins - 1)

            # // Remove any elo roles that were added
            user: discord.Member = await guild.get_member(user)
            await Users.remove_elo_role(user, new_elo)
            
    # // Update a match
    @staticmethod
    async def update(
        guild_id: int, lobby_id: int, match_id: int, 
        orange_cap: int = None, orange_team: str = None, 
        blue_cap: int = None, blue_team: str = None, 
        status: str = None, winners: list = None
    ) -> None:
        # // Update the match status
        if status is not None:
            await Cache.update("matches", guild_id=guild_id, key=match_id, data={"status": status}, sqlcmds=[
                f"UPDATE matches SET status = '{status}' WHERE guild_id = {guild_id} AND lobby_id = {lobby_id} AND match_id = {match_id}"
            ])

        # // Update the match winners
        if winners is not None:
            await Cache.update("matches", guild_id=guild_id, key=match_id, data={"winners": winners}, sqlcmds=[
                f"UPDATE matches SET winners = '{winners}' WHERE guild_id = {guild_id} AND lobby_id = {lobby_id} AND match_id = {match_id}"
            ])

        # // Update the orange team captain
        if orange_cap is not None:
            await Cache.update("matches", guild_id=guild_id, key=match_id, data={"orange_cap": orange_cap}, sqlcmds=[
                f"UPDATE matches SET orange_cap = '{orange_cap}' WHERE guild_id = {guild_id} AND lobby_id = {lobby_id} AND match_id = {match_id}"
            ])
        
        # // Update the blue team captain
        if blue_cap is not None:
            await Cache.update("matches", guild_id=guild_id, key=match_id, data={"blue_cap": blue_cap}, sqlcmds=[
                f"UPDATE matches SET blue_cap = '{blue_cap}' WHERE guild_id = {guild_id} AND lobby_id = {lobby_id} AND match_id = {match_id}"
            ])

        # // Update the orange team
        if orange_team is not None:
            await Cache.update("matches", guild_id=guild_id, key=match_id, data={
                "orange_team": orange_team.split(",", maxsplit=4)
            }, sqlcmds=[
                f"UPDATE matches SET orange_team = '{orange_team}' WHERE guild_id = {guild_id} AND lobby_id = {lobby_id} AND match_id = {match_id}"
            ])

        # // Update the blue team
        if blue_team is not None:
            await Cache.update("matches", guild_id=guild_id, key=match_id, data={
                "blue_team": blue_team.split(",", maxsplit=4)
            }, sqlcmds=[
                f"UPDATE matches SET blue_team = '{blue_team}' WHERE guild_id = {guild_id} AND lobby_id = {lobby_id} AND match_id = {match_id}"
            ])
       