from _sql_ import SqlData
import asyncio

cache = {
    "maps": {}, "settings": {}, "users": {}, 
    "bans": {}, "elo_roles": {}, "matches": {},
    "lobby_settings": {}
}

class Cache:
    # Add all MySQL Data into a cached map
    @staticmethod
    async def map_data():
        adv_tables = ["users", "bans", "lobby_settings", "elo_roles", "matches"]
        [await Cache.load_advanced(table) for table in adv_tables]
        await Cache.load_settings()
        await Cache.load_maps()
        
    # Load advanced tables into the sql cache
    @staticmethod
    async def load_advanced(table: str):
        rows = await SqlData.select_all(f"SELECT * FROM {table}")
        for row in rows:
            if row[0] not in cache[table]:
                cache[table][row[0]] = {}
            cache[table][row[0]][row[1]] = row[2:]
    
    
    # Load settings into the sql cache
    @staticmethod
    async def load_settings():
        rows = await SqlData.select_all(f"SELECT * FROM settings")
        for row in rows:
            cache["settings"][row[0]] = row[1:]
    
    
    # Load maps into the sql cache
    @staticmethod
    async def load_maps():
        rows = await SqlData.select_all(f"SELECT * FROM maps")
        for row in rows:
            if row[0] not in cache["maps"]:
                cache["maps"][row[0]] = {}
            if row[1] not in cache["maps"][row[0]]:
                cache["maps"][row[0]][row[1]] = []
            cache["maps"][row[0]][row[1]].append(row[2])
            
    # Fetch a value from the cache
    @staticmethod
    def fetch(table: str, column=None, opt: str=None):
        if column is not None:
            if opt is not None:
                return cache[table][column][opt]
            return cache[table][column]
            
        if opt is None:
            return cache[table]
        return cache[table][opt]
    
    # Check if a value exists in the cache
    @staticmethod
    def exists(table: str, column: str, opt: str=None):
        if opt is None:
            return column in cache[table]
        return opt in cache[table][column]
    
    # Update a value in the cache
    @staticmethod
    async def update(table: str, column: str, data: any, opt: str=None, sqlcmd: str=None):
        if sqlcmd is not None:
            await SqlData.execute(sqlcmd)
        if opt is None:
            cache[table][column] = data; return
        cache[table][column][opt] = data; return
        
    
    # Delete a value in the cache
    @staticmethod
    async def delete(table: str, column: str, opt: str=None, sqlcmd: str=None):
        if sqlcmd is not None:
            await SqlData.execute(sqlcmd)
        if opt is None:
            return cache[table].pop(column)
        return cache[table][column].pop(opt)
        


if __name__ == "__main__":
    asyncio.run(Cache.map_data())

    _data:list = Cache.fetch(
        table="maps", # table
        column=883006609280864257, # guild id
        opt=883006609280864251 # lobby id
    )
    _data.remove("kafe")
    _data.append("oregon")

    asyncio.run(Cache.update(
        table="maps", # table
        column=883006609280864257, # guild id
        opt=883006609280864251, # lobby id
        data=_data, # updated data
        sqlcmd="" # sql command to edit database
    ))

    asyncio.run(Cache.delete(
        table="maps",
        column=883006609280864257, 
        opt=883006609280864251,
        sqlcmd=""
    ))

    print(cache)