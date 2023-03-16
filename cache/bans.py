from .cache import Cache
import time, datetime, discord, functools

class Bans:
    # // Add a ban to the lobby
    @staticmethod
    async def ban(guild_id: int, user_id: int, length: int, reason: str, banned_by: int) -> None:
        await Cache.update("bans", guild_id=guild_id, key=user_id, data={
            "length": length, 
            "reason": reason, 
            "banned_by": banned_by
        }, sqlcmds=[
            f"INSERT INTO bans (guild_id, user_id, length, reason, banned_by) VALUES ({guild_id}, {user_id}, {length}, '{reason}', {banned_by})"
        ])

    # // Delete a ban from the lobby
    @staticmethod
    async def unban(guild_id: int, user_id: int) -> None:
        await Cache.delete_ban(guild_id, user_id)

    # // Get the ban of an user
    @staticmethod
    def get(guild_id: int, user_id: int = None) -> any:
        if user_id is not None:
            return Cache.fetch("bans", guild_id).get(user_id, None)
        return Cache.fetch("bans", guild_id).get(user_id, None)
    
    # // Check if a user is banned
    @staticmethod
    def is_banned(guild_id: int, user_id: int) -> bool:
        return user_id in Cache.fetch("bans", guild_id)
    
    # // Create a ban embed
    @staticmethod
    async def embed(guild_id: int, user: discord.Member) -> discord.Embed:
        if not Bans.is_banned(guild_id, user.id):
            return discord.Embed(
                title = f"{user.name} is not banned", 
                description = "This user is not banned", 
                color = 15158588
            )
        
        # // Get the users ban info
        ban_data: dict = Bans.get(guild_id, user.id)

        # // If the ban has expired, then unban the user
        if ban_data["length"] - time.time() <= 0:
            await Bans.unban(guild_id, user.id)

        # // If the ban is still active, then...
        ban_length: datetime.timedelta = datetime.timedelta(seconds = int(ban_data["length"] - time.time()))

        # // Return the embed
        return discord.Embed(
            title = f"{user.name} is banned", 
            description = f"**Length:** {ban_length}\n**Reason:** {ban_data['reason']}\n**Banned by:** {ban_data['banned_by']}", 
            color = 15158588
        )
