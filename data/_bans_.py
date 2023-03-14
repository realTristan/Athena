from ._cache_ import Cache

class Bans:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id

    # // Add a ban to the lobby
    async def ban(self, user_id: int, length: int, reason: str, banned_by: str):
        # // Update the cache and the database
        await Cache.update("bans", guild=self.guild_id, data={
            user_id: {
                "length": length, 
                "reason": reason, 
                "banned_by": banned_by
            }
        }, sqlcmds=[
            f"INSERT INTO bans (guild_id, user_id, length, reason, banned_by) VALUES ({self.guild_id}, {user_id}, {length}, '{reason}', '{banned_by}')"
            # // guild_id BIGINT, user_id BIGINT, length BIGINT, reason VARCHAR(50), banned_by VARCHAR(50)
        ])

    # // Delete a ban from the lobby
    async def unban(self, user_id: str):
        # // Fetch the current bans
        bans = Cache.fetch("bans", self.guild_id)

        # // Delete the ban
        del bans[user_id]

        # // Update the cache and the database
        await Cache.update("bans", guild=self.guild_id, data=bans, sqlcmds=[
            f"DELETE FROM bans WHERE guild_id = {self.guild_id} AND lobby_id = {self.lobby_id} AND user_id = {user_id}"
        ])

    # // Get the bans
    def get(self, user_id: int):
        return Cache.fetch("bans", self.guild_id)[user_id]
    
    # // Check if a user is banned
    def is_banned(self, user_id: int):
        return user_id in Cache.fetch("bans", self.guild_id)
