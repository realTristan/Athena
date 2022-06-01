from _sql import *
import asyncio

class Cache:
    def __init__(self):
        self.cache = {"maps": {}, "settings": {}}
        asyncio.run(function(self._on_start()))


    async def _on_start(self):
        for table in [
            "settings",
            "lobbies",
            "bans",
            "maps"
        ]:
            rows = await SqlData.select_all(f"SELECT * FROM {table}")
            for row in rows:
                if not row in self.cache:
                    self.cache[row] = {}
                for column in row:
                    self.cache[row][column] = {}
