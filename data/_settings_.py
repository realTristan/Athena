from ._cache_ import Cache

class Settings:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id

    # // Setup default settings and cache
    async def setup(self):
        await Cache.update("settings", guild=self.guild_id, data={
            "reg_role": 0,
            "match_categories": 0,
            "reg_channel": 0,
            "match_logs": 0,
            "mod_role": 0,
            "admin_role": 0,
            "self_rename": 1
        }, sqlcmds=[
            f"INSERT INTO settings (guild_id, reg_role, match_categories, reg_channel, match_logs, mod_role, admin_role, self_rename) VALUES ({self.guild_id}, 0, 0, 0, 0, 0, 0, 1)"
            # // guild_id BIGINT, reg_role BIGINT, match_categories BIGINT, reg_channel BIGINT, match_logs BIGINT, mod_role BIGINT, admin_role BIGINT, self_rename BIGINT
        ])

        # // Add guild to the elo roles cache
        await Cache.update("elo_roles", guild=self.guild_id, data={})
        
        # // Add guild to the lobby settings cache
        await Cache.update("lobby_settings", guild=self.guild_id, data={})

        # // Add the guild to the bans cache
        await Cache.update("bans", guild=self.guild_id, data={})

        # // Add the guild to the maps cache
        await Cache.update("maps", guild=self.guild_id, data={})

        # // Add the guild to the matches cache
        await Cache.update("matches", guild=self.guild_id, data={})

        # // Add the guild to the users cache
        await Cache.update("users", guild=self.guild_id, data={})

    # // Check if the settings exist
    async def exists(self):
        return self.guild_id in Cache.fetch("settings")

    # // Add a setting to the lobby
    async def update(self, reg_role=None, match_categories=None, reg_channel=None, match_logs=None, mod_role=None, admin_role=None, self_rename=None):
        # // Update reg role
        if reg_role is not None:
            await Cache.update("settings", guild=self.guild_id, data={"reg_role": reg_role}, sqlcmds=[
                f"UPDATE settings SET reg_role = {reg_role} WHERE guild_id = {self.guild_id}"
            ])
        
        # // Update match categories
        if match_categories is not None:
            await Cache.update("settings", guild=self.guild_id, data={"match_categories": match_categories}, sqlcmds=[
                f"UPDATE settings SET match_categories = {match_categories} WHERE guild_id = {self.guild_id}"
            ])

        # // Update reg channel
        if reg_channel is not None:
            await Cache.update("settings", guild=self.guild_id, data={"reg_channel": reg_channel}, sqlcmds=[
                f"UPDATE settings SET reg_channel = {reg_channel} WHERE guild_id = {self.guild_id}"
            ])

        # // Update match logs
        if match_logs is not None:
            await Cache.update("settings", guild=self.guild_id, data={"match_logs": match_logs}, sqlcmds=[
                f"UPDATE settings SET match_logs = {match_logs} WHERE guild_id = {self.guild_id}"
            ])

        # // Update mod role
        if mod_role is not None:
            await Cache.update("settings", guild=self.guild_id, data={"mod_role": mod_role}, sqlcmds=[
                f"UPDATE settings SET mod_role = {mod_role} WHERE guild_id = {self.guild_id}"
            ])

        # // Update admin role
        if admin_role is not None:
            await Cache.update("settings", guild=self.guild_id, data={"admin_role": admin_role}, sqlcmds=[
                f"UPDATE settings SET admin_role = {admin_role} WHERE guild_id = {self.guild_id}"
            ])

        # // Update self rename
        if self_rename is not None:
            await Cache.update("settings", guild=self.guild_id, data={"self_rename": self_rename}, sqlcmds=[
                f"UPDATE settings SET self_rename = {self_rename} WHERE guild_id = {self.guild_id}"
            ])

    # // Get a specific setting
    def get(self, key: str = None):
        if key is not None:
            return Cache.fetch("settings", guild=self.guild_id)[key]
        return Cache.fetch("settings", guild=self.guild_id)
        