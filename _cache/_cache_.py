from _sql import *
import asyncio


class Cache:
    def __init__(self):
        self.cache = {"maps": {}, "settings": {}}
        asyncio.run(function(self._on_start_maps()))
        asyncio.run(function(self._on_start_settings()))

    # // CACHE MAPS INTO THE 'self.cache' DICTIONARY
    async def _on_start_maps(self):
        rows = await SQL_CLASS().select_all(f"SELECT * FROM maps")
        for row in rows:
            if not row[0] in self.cache["maps"]:
                self.cache["maps"][row[0]] = []
                maps = self.cache["maps"][row[0]]
                maps.append(row[1])

                for m in maps:
                    maps.append(str(m[0].lower() + m[1:]))

    # // CACHE SETTINGS INTO THE 'self.cache' DICTIONARY
    async def _on_start_settings(self):
        rows = await SQL_CLASS().select_all(f"SELECT * FROM settings")
        for row in rows:
            if not row[0] in self.cache["settings"]:
                self.cache["settings"][row[0]] = {
                    "queue_channel": row[5],
                    "reg_channel": row[6],
                    "reg_role": row[1],
                    "match_categories": row[3],
                    "map_pick_phase": row[2],
                    "team_pick_phase": row[4],
                    "win_elo": row[7],
                    "loss_elo": row[8],
                    "match_logs": row[9],
                    "id": row[10],
                }

    # // RETURN CACHE DICTIONARY
    async def _cache(self):
        return self.cache
