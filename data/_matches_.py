from ._cache_ import Cache

class Matches:
    def __init__(self, guild: int, lobby_id: int):
        self.guild = guild
        self.lobby_id = lobby_id

    # // Get the number of matches in the lobby
    def count(self):
        return len(Cache.fetch("matches", self.guild)[self.lobby_id])

    # // Add a match to the lobby
    async def add(self, match_id: int, map: str, orange_cap: str, orange_team: str, blue_cap: str, blue_team: str, status: str, winners: str):
        await Cache.update("matches", guild=self.guild, lobby=self.lobby_id, data={
            match_id: {
                "lobby_id": self.lobby_id, 
                "map": map, 
                "orange_cap": orange_cap, 
                "orange_team": orange_team, 
                "blue_cap": blue_cap, 
                "blue_team": blue_team, 
                "status": status, 
                "winners": winners
            }
        }, sqlcmds=[
            f"INSERT INTO matches (guild_id, match_id, lobby_id, map, orange_cap, orange_team, blue_cap, blue_team, status, winners) VALUES ({self.guild}, {match_id}, {self.lobby_id}, '{map}', '{orange_cap}', '{orange_team}', '{blue_cap}', '{blue_team}', '{status}', '{winners}')"
        ])

    # // Delete a match from the lobby
    async def delete(self, match_id: str):
        Cache.delete_match(self.guild, self.lobby_id, match_id)

    # // Get the matches
    def get(self, match_id: int = None):
        if match_id is not None:
            return Cache.fetch("matches", self.guild)[self.lobby_id][match_id]
        return Cache.fetch("matches", self.guild)[self.lobby_id]
    