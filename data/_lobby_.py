from ._cache_ import Cache

class Lobby:
    # // Get all the lobbies in the guild
    @staticmethod
    def get_all(guild_id: int) -> dict:
        return Cache.fetch("lobbies", guild_id)
    
    # // Check if a lobby exists for the guild
    @staticmethod
    def exists(guild_id: int, lobby_id: int) -> bool:
        return lobby_id in Cache.fetch("lobbies", guild_id)

    # // Create a new lobby
    @staticmethod
    async def create(guild_id: int, lobby_id: int) -> None:
        await Cache.update("lobbies", guild_id=guild_id, data={
            lobby_id: {
                "map_pick_phase": 0,
                "team_pick_phase": 1,
                "win_elo": 5,
                "loss_elo": 2,
                "party_size": 1,
                "negative_elo": 1,
                "queue_size": 10,
                "maps": []
            }
        }, sqlcmds=[
            f"INSERT INTO lobbies (guild_id, lobby_id, map_pick_phase, team_pick_phase, win_elo, loss_elo, party_size, negative_elo, queue_size) VALUES ({guild}, {lobby_id}, 0, 1, 5, 2, 1, 1, 10)"
        ])

    # // Delete an elo role from the lobby
    @staticmethod
    async def delete_elo_role(guild_id: int, role_id: int) -> None:
        Cache.delete_elo_role(guild_id, role_id)

    # // Delete a map from the lobby
    @staticmethod
    async def delete_map(guild_id: int, lobby_id: int, map: str) -> None:
        Cache.delete_map(guild_id, lobby_id, map)

    # // Add a map to the lobby
    @staticmethod
    async def add_map(guild_id: int, lobby_id: int, map: str) -> None:
        Cache.add_map(guild_id, lobby_id, map)
    
    # // Delete the lobby
    @staticmethod
    async def delete(guild_id: int, lobby_id: int) -> None:
        Cache.delete_lobby(guild_id, lobby_id)

    # // Get the lobby or data from the lobby
    @staticmethod
    def get(guild_id: int, lobby_id: int, key: str = None) -> any:
        if key is not None:
            return Cache.fetch("lobbies", guild_id)[lobby_id][key]
        return Cache.fetch("lobbies", guild_id)[lobby_id]

    # // Update lobby settings
    @staticmethod
    async def update(guild_id: int, lobby_id: int, map_pick_phase=None, team_pick_phase=None, win_elo=None, loss_elo=None, party_size=None, negative_elo=None, queue_size=None) -> None:
        # // Update map pick phase
        if map_pick_phase is not None:
            await Cache.update("lobbies", guild_id=guild_id, key=lobby_id, data={"map_pick_phase": map_pick_phase}, sqlcmds=[
                f"UPDATE lobbies SET map_pick_phase = {map_pick_phase} WHERE lobby_id = {lobby_id} AND guild_id = {guild_id}"
            ])

        # // Update team pick phase
        if team_pick_phase is not None:
            await Cache.update("lobbies", guild_id=guild_id, key=lobby_id, data={"team_pick_phase": team_pick_phase}, sqlcmds=[
                f"UPDATE lobbies SET team_pick_phase = {team_pick_phase} WHERE lobby_id = {lobby_id} AND guild_id = {guild_id}"
            ])
        
        # // Update win elo
        if win_elo is not None:
            await Cache.update("lobbies", guild_id=guild_id, key=lobby_id, data={"win_elo": win_elo}, sqlcmds=[
                f"UPDATE lobbies SET win_elo = {win_elo} WHERE lobby_id = {lobby_id} AND guild_id = {guild_id}"
            ])

        # // Update loss elo
        if loss_elo is not None:
            await Cache.update("lobbies", guild_id=guild_id, key=lobby_id, data={"loss_elo": loss_elo}, sqlcmds=[
                f"UPDATE lobbies SET loss_elo = {loss_elo} WHERE lobby_id = {lobby_id} AND guild_id = {guild_id}"
            ])

        # // Update party size
        if party_size is not None:
            await Cache.update("lobbies", guild_id=guild_id, key=lobby_id, data={"party_size": party_size}, sqlcmds=[
                f"UPDATE lobbies SET party_size = {party_size} WHERE lobby_id = {lobby_id} AND guild_id = {guild_id}"
            ])

        # // Update negative elo
        if negative_elo is not None:
            await Cache.update("lobbies", guild_id=guild_id, key=lobby_id, data={"negative_elo": negative_elo}, sqlcmds=[
                f"UPDATE lobbies SET negative_elo = {negative_elo} WHERE lobby_id = {lobby_id} AND guild_id = {guild_id}"
            ])

        # // Update queue size
        if queue_size is not None:
            await Cache.update("lobbies", guild_id=guild_id, key=lobby_id, data={"queue_size": queue_size}, sqlcmds=[
                f"UPDATE lobbies SET queue_size = {queue_size} WHERE lobby_id = {lobby_id} AND guild_id = {guild_id}"
            ])
