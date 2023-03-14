from ._cache_ import Cache

class Lobby:
    def __init__(self, guild: int, lobby_id: int):
        self.guild = guild
        self.lobby_id = lobby_id

    # // Get all the lobbies in the guild
    @staticmethod
    def get_all(guild: int):
        return Cache.fetch("lobbies", guild)
    
    # // Check if a lobby exists for the guild
    @staticmethod
    def exists(guild: int, lobby_id: int):
        return lobby_id in Cache.fetch("lobbies", guild)

    @staticmethod
    async def create(guild: int, lobby_id: int):
        await Cache.update("lobbies", guild=guild, data={
            lobby_id: {
                "map_pick_phase": 0,
                "team_pick_phase": 1,
                "win_elo": 5,
                "loss_elo": 2,
                "party_size": 1,
                "negative_elo": 1,
                "queue_size": 10
            }
        }, sqlcmds=[
            f"INSERT INTO lobbies (guild_id, lobby_id, map_pick_phase, team_pick_phase, win_elo, loss_elo, party_size, negative_elo, queue_size) VALUES ({guild}, {lobby_id}, 0, 1, 5, 2, 1, 1, 10)"
        ])
        await Cache.update("elo_roles", guild=guild, data={}, sqlcmds=[])


    # // Delete an elo role from the lobby
    async def delete_elo_role(self, role_id: int):
        Cache.delete_elo_role(self.guild, role_id)

    # // Delete a map from the lobby
    async def delete_map(self, map: str):
        Cache.delete_map(self.guild, self.lobby_id, map)

    # // Add a map to the lobby
    async def add_map(self, map: str):
        Cache.add_map(self.guild, self.lobby_id, map)
    
    # // Delete the lobby
    async def delete(self):
        Cache.delete_lobby(self.guild, self.lobby_id)

    # // Get the lobby maps
    def get_maps(self):
        return Cache.fetch("lobbies", self.guild)[self.lobby_id]["maps"]
    
    # // Get the lobby or data from the lobby
    def get(self, key: str = None):
        if key is not None:
            return Cache.fetch("lobbies", self.guild)[self.lobby_id][key]
        return Cache.fetch("lobbies", self.guild)[self.lobby_id]

    # // Update lobby settings
    async def update(self, map_pick_phase=None, team_pick_phase=None, win_elo=None, loss_elo=None, party_size=None, negative_elo=None, queue_size=None):
        # // Update map pick phase
        if map_pick_phase is not None:
            await Cache.update("lobbies", lobby=self.lobby_id, data={"map_pick_phase": map_pick_phase}, sqlcmds=[
                f"UPDATE lobbies SET map_pick_phase = {map_pick_phase} WHERE lobby_id = {self.lobby_id}"
            ])

        # // Update team pick phase
        if team_pick_phase is not None:
            await Cache.update("lobbies", lobby=self.lobby_id, data={"team_pick_phase": team_pick_phase}, sqlcmds=[
                f"UPDATE lobbies SET team_pick_phase = {team_pick_phase} WHERE lobby_id = {self.lobby_id}"
            ])
        
        # // Update win elo
        if win_elo is not None:
            await Cache.update("lobbies", lobby=self.lobby_id, data={"win_elo": win_elo}, sqlcmds=[
                f"UPDATE lobbies SET win_elo = {win_elo} WHERE lobby_id = {self.lobby_id}"
            ])

        # // Update loss elo
        if loss_elo is not None:
            await Cache.update("lobbies", lobby=self.lobby_id, data={"loss_elo": loss_elo}, sqlcmds=[
                f"UPDATE lobbies SET loss_elo = {loss_elo} WHERE lobby_id = {self.lobby_id}"
            ])

        # // Update party size
        if party_size is not None:
            await Cache.update("lobbies", lobby=self.lobby_id, data={"party_size": party_size}, sqlcmds=[
                f"UPDATE lobbies SET party_size = {party_size} WHERE lobby_id = {self.lobby_id}"
            ])

        # // Update negative elo
        if negative_elo is not None:
            await Cache.update("lobbies", lobby=self.lobby_id, data={"negative_elo": negative_elo}, sqlcmds=[
                f"UPDATE lobbies SET negative_elo = {negative_elo} WHERE lobby_id = {self.lobby_id}"
            ])

        # // Update queue size
        if queue_size is not None:
            await Cache.update("lobbies", lobby=self.lobby_id, data={"queue_size": queue_size}, sqlcmds=[
                f"UPDATE lobbies SET queue_size = {queue_size} WHERE lobby_id = {self.lobby_id}"
            ])


        