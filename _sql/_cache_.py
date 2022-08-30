from ._sql_ import SqlData
import sys

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
    async def map_data():
        adv_tables = ["users", "bans", "lobby_settings", "elo_roles", "matches"]
        [await Cache.load_advanced(table) for table in adv_tables]
        await Cache.load_settings()
        await Cache.load_maps()
        
    # // Load advanced tables into the sql cache
    @staticmethod
    async def load_advanced(table: str):
        rows = await SqlData.select_all(f"SELECT * FROM {table}")
        for row in rows:
            if row[0] not in cache[table]:
                cache[table][row[0]] = {}
            cache[table][row[0]][row[1]] = row[2:]
    
    
    # // Load settings into the sql cache
    @staticmethod
    async def load_settings():
        rows = await SqlData.select_all(f"SELECT * FROM settings")
        for row in rows:
            cache["settings"][row[0]] = row[1:]
    
    
    # // Load maps into the sql cache
    @staticmethod
    async def load_maps():
        rows = await SqlData.select_all(f"SELECT * FROM maps")
        for row in rows:
            if row[0] not in cache["maps"]:
                cache["maps"][row[0]] = {}
            if row[1] not in cache["maps"][row[0]]:
                cache["maps"][row[0]][row[1]] = []
            cache["maps"][row[0]][row[1]].append(row[2])
            
    # // Fetch a value from the cache
    @staticmethod
    def fetch(table: str, guild=None, key: str=None):
        
        # // If not guild param is provided
        if guild is not None:
            if key is not None:
                return cache[table][guild][key]
            return cache[table][guild]
        
        # If no key param is provided
        if key is None:
            return cache[table]
        return cache[table][key]
    
    # Check if a value exists in the cache
    @staticmethod
    def exists(table: str, guild: str, key: str=None):
        # // If no key is provided
        if key is None:
            return guild in cache[table]
        
        #  If guild doesn't exist in the cache table
        if guild not in cache[table]:
            cache[table][guild] = {}
        return key in cache[table][guild]
    
    # Update a value in the cache
    @staticmethod
    async def update(table: str, guild: str, data: any, key: str=None, sqlcmds: list=None):
        
        # // If there are provided sql cmds
        if len(sqlcmds) > 0:
            for cmd in sqlcmds:
                await SqlData.execute(cmd)
                
        # If no key is provided
        if key is None:
            cache[table][guild] = data; print(sys.getsizeof(cache)); return
        cache[table][guild][key] = data; print(sys.getsizeof(cache)); return
        
        
    # Delete a value in the cache
    @staticmethod
    async def delete(table: str, guild: str, key: str=None, sqlcmds: list=None):
        
        # If there are provided sql cmds
        if len(sqlcmds) > 0:
            for cmd in sqlcmds:
                await SqlData.execute(cmd)
                
        # If no key is provided
        if key is None:
            return cache[table].pop(guild)
        
        # Else remove the key from the cache[table][guild] map
        return cache[table][guild].pop(key)

