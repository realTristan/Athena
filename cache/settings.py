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
    
    # // Get whether self rename is enabled
    @staticmethod
    def self_rename_enabled(guild_id: int) -> bool:
        return Cache.fetch("settings", guild_id=guild_id).get("self_rename") == 1
    
    # // Get the match categories
    @staticmethod
    def match_categories_enabled(guild_id: int) -> bool:
        return Cache.fetch("settings", guild_id=guild_id).get("match_categories") == 1
    
    # // Get the register role
    @staticmethod
    def get_reg_role(guild_id: int) -> int or None:
        reg_role: int = Cache.fetch("settings", guild_id=guild_id).get("reg_role")
        return reg_role if reg_role != 0 else None
    
    # // Get the register channel
    @staticmethod
    def get_reg_channel(guild_id: int) -> int or None:
        reg_channel: int = Cache.fetch("settings", guild_id=guild_id).get("reg_channel")
        return reg_channel if reg_channel != 0 else None
    
    # // Get the match logs channel
    @staticmethod
    def get_match_logs_channel(guild_id: int) -> int or None:
        match_logs: int = Cache.fetch("settings", guild_id=guild_id).get("match_logs")
        return match_logs if match_logs != 0 else None
    
    # // Get the mod role
    @staticmethod
    def get_mod_role(guild_id: int) -> int or None:
        mod_role: int = Cache.fetch("settings", guild_id=guild_id).get("mod_role")
        return mod_role if mod_role != 0 else None
    
    # // Get the admin role
    @staticmethod
    def get_admin_role(guild_id: int) -> int or None:
        admin_role: int = Cache.fetch("settings", guild_id=guild_id).get("admin_role")
        return admin_role if admin_role != 0 else None
    
    # // Get the elo roles
    @staticmethod
    def get_elo_roles(guild_id: int) -> dict:
        return Cache.fetch("settings", guild_id=guild_id).get("elo_roles", {})
    
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
        