from ._cache_ import Cache

class Lobby:
    def __init__(self, guild: int, lobby_id: int):
        self.guild = guild
        self.lobby_id = lobby_id

    # // Get all the lobbies in the guild
    @staticmethod
    def get_all(guild: int):
        return Cache.fetch("lobby_settings", guild)
    
    # // Check if a lobby exists for the guild
    @staticmethod
    def exists(guild: int, lobby_id: int):
        return lobby_id in Cache.fetch("lobby_settings", guild)

    @staticmethod
    async def create(guild: int, lobby_id: int):
        await Cache.update("lobby_settings", guild=guild, data={
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
            f"INSERT INTO lobby_settings (guild_id, lobby_id, map_pick_phase, team_pick_phase, win_elo, loss_elo, party_size, negative_elo, queue_size) VALUES ({guild}, {lobby_id}, 0, 1, 5, 2, 1, 1, 10)"
        ])
        await Cache.update("elo_roles", guild=guild, data={}, sqlcmds=[
            f"INSERT INTO elo_roles (guild_id, lobby_id) VALUES ({guild}, {lobby_id})"
        ])

    # // Delete an elo role from the lobby
    async def delete_elo_role(self, role_id: int):
        # // Fetch the elo roles
        elo_roles = Cache.fetch("elo_roles", self.guild)
        del elo_roles[role_id]

        # // Update the cache and the database
        await Cache.set("elo_roles", guild=self.guild, data=elo_roles, sqlcmds=[
            f"DELETE FROM elo_roles WHERE guild_id = {self.guild} AND role_id = {role_id}"
        ])

    # // Add an elo role to the lobby
    async def add_elo_role(self, role_id: int, elo_level: int, win_elo: int, lose_elo: int):
        # // Fetch the elo roles
        elo_roles = Cache.fetch("elo_roles", self.guild)
        elo_roles[role_id] = {"elo_level": elo_level, "win_elo": win_elo, "lose_elo": lose_elo}

        # // Update the cache and the database
        await Cache.update("elo_roles", guild=self.guild, data=elo_roles, sqlcmds=[
            # // role_id BIGINT, elo_level INT, win_elo INT, lose_elo INT
            f"INSERT INTO elo_roles (guild_id, role_id, elo_level, win_elo, lose_elo) VALUES ({self.guild}, {role_id}, {elo_level}, {win_elo}, {lose_elo})"
        ])

    # // Get the elo roles
    def get_elo_roles(self):
        return Cache.fetch("elo_roles", self.guild)

    # // Delete a map from the lobby
    async def delete_map(self, map: str):
        # // Fetch the current maps
        maps = Cache.fetch("maps", self.guild)[self.lobby_id]
        maps.remove(map)

        # // Update the cache and the database
        await Cache.set("maps", guild=self.guild, data=maps, sqlcmds=[
            f"DELETE FROM maps WHERE guild_id = {self.guild} AND lobby_id = {self.lobby_id} AND map = '{map}'"
        ])

    # // Add a map to the lobby
    async def add_map(self, map: str):
        # // Fetch the current maps
        maps = Cache.fetch("maps", self.guild)[self.lobby_id]
        maps.append(map)

        # // Update the cache and the database
        await Cache.set("maps", guild=self.guild, lobby=self.lobby_id, data=maps, sqlcmds=[
            f"INSERT INTO maps (guild_id, lobby_id, map) VALUES ({self.guild}, {self.lobby_id}, '{map}')"
        ])

    # // Get the maps
    def get_maps(self):
        return Cache.fetch("maps", self.guild)[self.lobby_id]
    
    # // Get a specific lobby
    def get(self, key: str = None):
        if key is not None:
            return Cache.fetch("lobby_settings", self.guild)[self.lobby_id][key]
        return Cache.fetch("lobby_settings", self.guild)[self.lobby_id]
    
    # // Delete the lobby
    async def delete(self):
        # // Fetch the current lobby settings
        lobbies = Cache.fetch("lobby_settings", self.guild)

        # // Delete the lobby from the lobby settings
        del lobbies[self.lobby_id]
        
        # // Update the lobby settings
        await Cache.set("lobby_settings", guild=self.guild, data=lobbies, sqlcmds=[
            f"DELETE FROM lobby_settings WHERE lobby_id = {self.lobby_id}"
        ])

        # // Fetch the current maps
        lobby_maps = Cache.fetch("maps", self.guild)

        # // Delete the lobby from the maps
        del lobby_maps[self.lobby_id]

        # // Update the maps
        await Cache.set("maps", guild=self.guild, data=lobby_maps, sqlcmds=[
            f"DELETE FROM maps WHERE lobby_id = {self.lobby_id}"
        ])


    # // Update lobby settings
    async def update(self, map_pick_phase=None, team_pick_phase=None, win_elo=None, loss_elo=None, party_size=None, negative_elo=None, queue_size=None):
        # // Update map pick phase
        if map_pick_phase is not None:
            await Cache.update("lobby_settings", lobby=self.lobby_id, data={"map_pick_phase": map_pick_phase}, sqlcmds=[
                f"UPDATE lobby_settings SET map_pick_phase = {map_pick_phase} WHERE lobby_id = {self.lobby_id}"
            ])

        # // Update team pick phase
        if team_pick_phase is not None:
            await Cache.update("lobby_settings", lobby=self.lobby_id, data={"team_pick_phase": team_pick_phase}, sqlcmds=[
                f"UPDATE lobby_settings SET team_pick_phase = {team_pick_phase} WHERE lobby_id = {self.lobby_id}"
            ])
        
        # // Update win elo
        if win_elo is not None:
            await Cache.update("lobby_settings", lobby=self.lobby_id, data={"win_elo": win_elo}, sqlcmds=[
                f"UPDATE lobby_settings SET win_elo = {win_elo} WHERE lobby_id = {self.lobby_id}"
            ])

        # // Update loss elo
        if loss_elo is not None:
            await Cache.update("lobby_settings", lobby=self.lobby_id, data={"loss_elo": loss_elo}, sqlcmds=[
                f"UPDATE lobby_settings SET loss_elo = {loss_elo} WHERE lobby_id = {self.lobby_id}"
            ])

        # // Update party size
        if party_size is not None:
            await Cache.update("lobby_settings", lobby=self.lobby_id, data={"party_size": party_size}, sqlcmds=[
                f"UPDATE lobby_settings SET party_size = {party_size} WHERE lobby_id = {self.lobby_id}"
            ])

        # // Update negative elo
        if negative_elo is not None:
            await Cache.update("lobby_settings", lobby=self.lobby_id, data={"negative_elo": negative_elo}, sqlcmds=[
                f"UPDATE lobby_settings SET negative_elo = {negative_elo} WHERE lobby_id = {self.lobby_id}"
            ])

        # // Update queue size
        if queue_size is not None:
            await Cache.update("lobby_settings", lobby=self.lobby_id, data={"queue_size": queue_size}, sqlcmds=[
                f"UPDATE lobby_settings SET queue_size = {queue_size} WHERE lobby_id = {self.lobby_id}"
            ])