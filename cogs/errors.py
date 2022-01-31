from discord.ext import commands
from functools import *
import discord

class Error_Handling(commands.Cog):
    def __init__(self, client):
        self.client = client


    # // RUN THE COMMAND SORTER
    # //////////////////////////////
    @cache
    async def _run_sorter(self, ctx, _user_command):
        _sorted_commands = await self._command_sort(_user_command)
        correct_usages=""
        similar_commands=""
        
        # // CHECK IF THERE'S ANY SIMILAR COMMANDS
        if len(_sorted_commands) <= 1:
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} we could not find the command you are looking for", color=15158588))

        # // SORT COMMANDS INTO A LIST
        for command in self.client.commands:
            if str(command) in _sorted_commands:
                similar_commands+=f"{str(command)}\n"
                correct_usages+=f"{str(command)}: {command.description}\n"

        embed=embed=discord.Embed(title=f"Command Error: [={_user_command}]", description=f"**Similar Commands:**\n{similar_commands}\n**Command Usages:**\n{correct_usages}", color=15158588)
        embed.set_footer(text="Message \"tristan#2230\" for support")
        return await ctx.send(embed=embed)

    # CHECK HOW MANY TIMES A LETTER APPEARS IN BOTH WORDS
    # //////////////////////////////////////////////////////
    @cache
    async def _letter_count(self, _user_command):
        try:
            _letter_dict = {}
            for index in range(len(self.client.commands)):
                if str(list(self.client.commands)[index]) not in _letter_dict:
                    _letter_dict[str(list(self.client.commands)[index])] = {}

                for letter in str(list(self.client.commands)[index]):
                    if letter in list(_user_command):
                        if letter not in _letter_dict[str(list(self.client.commands)[index])]:
                            _letter_dict[str(list(self.client.commands)[index])][letter] = 0
                        _letter_dict[str(list(self.client.commands)[index])][letter] += 1
        except Exception:
            return _letter_dict
        return _letter_dict

    # // CHECK LETTER POSITIONING
    # ////////////////////////////////
    @cache
    async def _letter_position(self, _user_command):
        _letter_dict = await self._letter_count(_user_command)
        for command in self.client.commands:
            for index in range(len(_user_command)):
                try:
                    if _user_command[index] == str(command)[index]:
                        if _user_command[index] not in _letter_dict[str(command)]:
                            _letter_dict[str(command)][str(command)[index]] = 0
                        _letter_dict[str(command)][str(command)[index]] += 1.5
                except Exception:
                    pass
        return _letter_dict

    # // GIVE EACH COMMAND THEIR RATING
    # /////////////////////////////////////
    @cache
    async def _command_rate(self, _user_command):
        try:
            _letter_dict = await self._letter_position(_user_command)
            _result = {}
            for command in _letter_dict:
                if not command in _result:
                    _result[command] = 0

                for letter in _letter_dict[command]:
                    _result[command] += _letter_dict[command][letter]
        except Exception:
            return _result
        return _result

    # SORT THE COMMANDS
    # /////////////////////
    @cache
    async def _command_sort(self, _user_command):
        try:
            _command_dict = await self._command_rate(_user_command)
            _sorted_command_dict = {k: v for k, v in sorted(_command_dict.items(), key=lambda item: item[1], reverse=True)}
            _result = []

            for command in _sorted_command_dict:
                if _sorted_command_dict[command] > (len(command)*0.85):
                    _result.append(command)
        except Exception:
            return _result
        return _result
    

    # ON COMMAND ERROR HANDLING
    # ///////////////////////////////
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
            
        await self._run_sorter(ctx, str(ctx.message.content.split(" ")[0]).strip("="))
        if not isinstance(error, commands.CommandNotFound):
            raise error

def setup(client):
    client.add_cog(Error_Handling(client))