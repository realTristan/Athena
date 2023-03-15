from ._cache_ import Cache

class Bans:
    # // Add a ban to the lobby
    @staticmethod
    async def ban(guild_id: int, user_id: int, length: int, reason: str, banned_by: str):
        # // Update the cache and the database
        await Cache.update("bans", guild=guild_id, data={
            user_id: {
                "length": length, 
                "reason": reason, 
                "banned_by": banned_by
            }
        }, sqlcmds=[
            f"INSERT INTO bans (guild_id, user_id, length, reason, banned_by) VALUES ({guild_id}, {user_id}, {length}, '{reason}', '{banned_by}')"
        ])

    # // Delete a ban from the lobby
    @staticmethod
    async def unban(guild_id: int, user_id: str):
        Cache.delete_ban(guild_id, user_id)

    # // Get the ban of an user
    @staticmethod
    def get(guild_id: int, user_id: int = None):
        if user_id is not None:
            return Cache.fetch("bans", guild_id)[user_id]
        return Cache.fetch("bans", guild_id)[user_id]
    
    # // Check if a user is banned
    @staticmethod
    def is_banned(guild_id: int, user_id: int):
        return user_id in Cache.fetch("bans", guild_id)
