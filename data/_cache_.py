from ._sql_ import *

# // The Global Cache Variable
cache: dict[str, dict] = {
    "maps": {}, "settings": {}, "users": {}, 
    "bans": {}, "elo_roles": {}, "matches": {},
    "lobby_settings": {}
}

# // The Cache Class that contains all the
# // cache functions
class Cache:
    # // Add all MySQL Data into a cached map
    @staticmethod
    async def load_data():
        await Cache.load_users()
        await Cache.load_lobby_settings()
        await Cache.load_elo_roles()
        await Cache.load_bans()
        await Cache.load_matches()
        await Cache.load_settings()
        await Cache.load_maps()

    # // Load users into the sql cache
    @staticmethod
    async def load_users():
        rows = await SqlData.select_all(f"SELECT * FROM users")
        for row in rows:
            # // If the guild does not exist in the cache
            if row[0] not in cache["users"]:
                cache["users"][row[0]] = {}

            # // Add the user to the cache
            cache["users"][row[0]][row[1]] = {
                "user_name": row[2], "elo": row[3], "wins": row[4], "loss": row[5]
                # // user_name VARCHAR(50), elo INT, wins INT, loss INT
            }

    # // Load lobby settings into the sql cache
    @staticmethod
    async def load_lobby_settings():
        rows = await SqlData.select_all(f"SELECT * FROM lobby_settings")
        for row in rows:
            # // If the guild does not exist in the cache
            if row[0] not in cache["lobby_settings"]:
                cache["lobby_settings"][row[0]] = {}

            # // Add the lobby settings to the cache
            cache["lobby_settings"][row[0]][row[1]] = {
                "lobby": row[1], "map_pick_phase": row[2], "team_pick_phase": row[3], "win_elo": row[4], "loss_elo": row[5], "party_size": row[6], "negative_elo": row[7], "queue_size": row[8]
                # // map_pick_phase INT, team_pick_phase INT, win_elo INT, loss_elo INT, party_size INT, negative_elo INT, queue_size INT
            }

    # // Load elo roles into the sql cache
    @staticmethod
    async def load_elo_roles():
        rows = await SqlData.select_all(f"SELECT * FROM elo_roles")
        for row in rows:
            # // If the guild does not exist in the cache
            if row[0] not in cache["elo_roles"]:
                cache["elo_roles"][row[0]] = {}

            # // Add the elo roles to the cache
            cache["elo_roles"][row[0]][row[1]] = {
                "role_id": row[1], "elo_level": row[2], "win_elo": row[3], "lose_elo": row[4]
                # // guild_id BIGINT, role_id BIGINT, elo_level INT, win_elo INT, lose_elo INT
            }
    
    # // Load matches into the sql cache
    @staticmethod
    async def load_matches():
        rows = await SqlData.select_all(f"SELECT * FROM matches")
        for row in rows:
            # // If the guild does not exist in the cache
            if row[0] not in cache["matches"]:
                cache["matches"][row[0]] = {}

            # // Add the match to the cache
            cache["matches"][row[0]][row[1]] = {
                "match_id": row[1], "lobby_id": row[2], "map": row[3], "team_1": row[4], "team_2": row[5], "team_1_score": row[6], "team_2_score": row[7], "winner": row[8]
                # // lobby_id BIGINT, map VARCHAR(50), team_1 VARCHAR(1000), team_2 VARCHAR(1000), team_1_score INT, team_2_score INT, winner INT
            }

    # // Load bans into the sql cache
    @staticmethod
    async def load_bans():
        rows = await SqlData.select_all(f"SELECT * FROM bans")
        for row in rows:
            # // If the guild does not exist in the cache
            if row[0] not in cache["bans"]:
                cache["bans"][row[0]] = {}

            # // Add the ban to the cache
            cache["bans"][row[0]][row[1]] = {
                "user_id": row[1], "length": row[2], "reason": row[3], "banned_by": row[4]
                # // length BIGINT, reason VARCHAR(50), banned_by VARCHAR(50)
            }
    
    # // Load settings into the sql cache
    @staticmethod
    async def load_settings():
        rows = await SqlData.select_all(f"SELECT * FROM settings")
        for row in rows:
            # // Add the setting to the cache
            cache["settings"][row[0]] = {
                "reg_role": row[1], "match_categories": row[2], "reg_channel": row[3], "match_logs": row[4], "mod_role": row[5], "admin_role": row[6], "self_rename": row[7]
                # // reg_role BIGINT, match_categories INT, reg_channel BIGINT, match_logs BIGINT, mod_role BIGINT, admin_role BIGINT, self_rename INT
            }
    
    
    # // Load maps into the sql cache
    @staticmethod
    async def load_maps():
        rows = await SqlData.select_all(f"SELECT * FROM maps")
        for row in rows:
            # // If the guild does not exist in the cache
            if row[0] not in cache["maps"]:
                cache["maps"][row[0]] = {}

            # // If the lobby does not exist in the cache
            if row[1] not in cache["maps"][row[0]]:
                cache["maps"][row[0]][row[1]] = []

            # // Add the map to the cache
            cache["maps"][row[0]][row[1]].append(row[2])
            
    # // Fetch a value from the cache
    @staticmethod
    def fetch(table: str, guild = None):
        # // Check if the guild exists in the cache table
        if guild not in cache[table]:
            cache[table][guild] = {}

        # // Return the cache table
        return cache[table][guild]
        
    
    # // Update a value in the cache
    @staticmethod
    async def update(table: str, guild: str, data: any, lobby: int = None, sqlcmds: list = []):
        # // If no lobby is provided
        if lobby is None:
            for key in data:
                cache[table][guild][key] = data[key]

        # // Update the cache for the lobby
        else:
            for key in data:
                cache[table][guild][lobby][key] = data[key]

        # // If there are provided sql cmds
        if len(sqlcmds) > 0:
            for cmd in sqlcmds:
                await SqlData.execute(cmd)

    # // Set a value from the cache
    @staticmethod
    async def set(table: str, guild: str, lobby: int = None, data: any = None, sqlcmds: list = []):
        # // If the lobby is provided
        if lobby is not None:
            cache[table][guild][lobby] = data
        
        # // Set the cache value
        else:
            cache[table][guild] = data
        
        # // If there are provided sql cmds
        if len(sqlcmds) > 0:
            for cmd in sqlcmds:
                await SqlData.execute(cmd)
                