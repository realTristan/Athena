from .cache import Cache

class Settings:
    # // Setup default settings and cache
    @staticmethod
    async def setup(guild_id: int) -> None:
        await Cache.update("settings", guild_id=guild_id, data={
            "reg_role": 0,
            "match_categories": 0,
            "reg_channel": 0,
            "match_logs": 0,
            "mod_role": 0,
            "admin_role": 0,
            "self_rename": 1,
            "elo_roles": {}
        }, sqlcmds=[
            f"INSERT INTO settings (guild_id, is_premium, reg_role, match_categories, reg_channel, match_logs, mod_role, admin_role, self_rename) VALUES ({guild_id}, 0, 0, 0, 0, 0, 0, 0, 1)"
        ])

        # // Add guild to the lobby settings cache
        await Cache.update("lobbies", guild_id=guild_id, data={})

        # // Add the guild to the bans cache
        await Cache.update("bans", guild_id=guild_id, data={})

        # // Add the guild to the matches cache
        await Cache.update("matches", guild_id=guild_id, data={})

        # // Add the guild to the users cache
        await Cache.update("users", guild_id=guild_id, data={})

    # // Check if the settings exist
    @staticmethod
    def exists(guild_id: int) -> bool:
        return guild_id in Cache.fetch("settings")
    
    # // Get a specific setting
    @staticmethod
    def get(guild_id: int, key: str = None) -> any:
        if key is not None:
            return Cache.fetch("settings", guild_id=guild_id).get(key)
        return Cache.fetch("settings", guild_id=guild_id)

    # // Create a new elo role
    @staticmethod
    async def create_elo_role(guild_id: int, role_id: int, elo_level: int, win_elo: int, lose_elo: int) -> None:
        await Cache.update("settings", guild_id=guild_id, key="elo_roles", data={
            role_id: {
                "elo_level": elo_level, 
                "win_elo": win_elo, 
                "lose_elo": lose_elo
            }
        }, sqlcmds=[
            f"INSERT INTO elo_roles (guild_id, role_id, elo_level, win_elo, lose_elo) VALUES ({guild_id}, {role_id}, {elo_level}, {win_elo}, {lose_elo})"
        ])

    # // Check if the elo role exists
    @staticmethod
    def elo_role_exists(guild_id: int, role_id: int) -> bool:
        return role_id in Cache.fetch("settings", guild_id=guild_id)["elo_roles"]
    
    # // Delete an elo role from the lobby
    @staticmethod
    async def delete_elo_role(guild_id: int, role_id: int) -> None:
        await Cache.delete_elo_role(guild_id, role_id)

    # // Add a setting to the lobby
    @staticmethod
    async def update(guild_id: int, reg_role=None, match_categories=None, reg_channel=None, match_logs=None, mod_role=None, admin_role=None, self_rename=None) -> None:
        # // Update reg role
        if reg_role is not None:
            await Cache.update("settings", guild_id=guild_id, data={"reg_role": reg_role}, sqlcmds=[
                f"UPDATE settings SET reg_role = {reg_role} WHERE guild_id = {guild_id}"
            ])
        
        # // Update match categories
        if match_categories is not None:
            await Cache.update("settings", guild_id=guild_id, data={"match_categories": match_categories}, sqlcmds=[
                f"UPDATE settings SET match_categories = {match_categories} WHERE guild_id = {guild_id}"
            ])

        # // Update reg channel
        if reg_channel is not None:
            await Cache.update("settings", guild_id=guild_id, data={"reg_channel": reg_channel}, sqlcmds=[
                f"UPDATE settings SET reg_channel = {reg_channel} WHERE guild_id = {guild_id}"
            ])

        # // Update match logs
        if match_logs is not None:
            await Cache.update("settings", guild_id=guild_id, data={"match_logs": match_logs}, sqlcmds=[
                f"UPDATE settings SET match_logs = {match_logs} WHERE guild_id = {guild_id}"
            ])

        # // Update mod role
        if mod_role is not None:
            await Cache.update("settings", guild_id=guild_id, data={"mod_role": mod_role}, sqlcmds=[
                f"UPDATE settings SET mod_role = {mod_role} WHERE guild_id = {guild_id}"
            ])

        # // Update admin role
        if admin_role is not None:
            await Cache.update("settings", guild_id=guild_id, data={"admin_role": admin_role}, sqlcmds=[
                f"UPDATE settings SET admin_role = {admin_role} WHERE guild_id = {guild_id}"
            ])

        # // Update self rename
        if self_rename is not None:
            await Cache.update("settings", guild_id=guild_id, data={"self_rename": self_rename}, sqlcmds=[
                f"UPDATE settings SET self_rename = {self_rename} WHERE guild_id = {guild_id}"
            ])
        