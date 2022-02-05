from discord.ext import commands
from functools import *
import discord, datetime

class ErrorHandling(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.client_cmds = {}
        for cmd in self.client.commands:
            self.client_cmds[cmd.name] = cmd.description


    # // RUN THE COMMAND SORTER
    # //////////////////////////////
    async def _run_sorter(self, ctx, _user_command):
        sorted_cmds = await self._command_sort(_user_command)
        similar_cmds=""
        
        # // CHECK IF THERE'S ANY SIMILAR COMMANDS
        if len(sorted_cmds) <= 0:
            return await ctx.send(embed=discord.Embed(description=f"**[ERROR]** {ctx.author.mention} we could not find the command you are looking for", color=15158588))
        
        # // CREATE EMBED
        for i in range(len(sorted_cmds)):
            similar_cmds+=f"**{i+1}:** {sorted_cmds[i][0].upper()+sorted_cmds[i][1:]} {self.client_cmds[sorted_cmds[i]]}\n"

        embed=discord.Embed(title=f"Similar Commands [{_user_command}]", description=f"{similar_cmds}", color=15158588)
        embed.set_footer(text="Message \"tristan#2230\" for support")
        return await ctx.send(embed=embed)

    # CHECK HOW MANY TIMES A LETTER APPEARS IN BOTH WORDS
    # //////////////////////////////////////////////////////
    async def _letter_count(self, _user_command):
        try:
            _result = {}
            for index in range(len(self.client.commands)):
                if str(list(self.client.commands)[index]) not in _result:
                    _result[str(list(self.client.commands)[index])] = {}

                for letter in str(list(self.client.commands)[index]):
                    if letter in list(_user_command):
                        if letter not in _result[str(list(self.client.commands)[index])]:
                            _result[str(list(self.client.commands)[index])][letter] = 0
                        _result[str(list(self.client.commands)[index])][letter] += 1
        except Exception:
            return _result
        return _result

    # // CHECK LETTER POSITIONING
    # ////////////////////////////////
    async def _letter_position(self, _user_command):
        _result = await self._letter_count(_user_command)
        for command in self.client.commands:
            for index in range(len(_user_command)):
                try:
                    if _user_command[index] == str(command)[index]:
                        if _user_command[index] not in _result[str(command)]:
                            _result[str(command)][str(command)[index]] = 0
                        _result[str(command)][str(command)[index]] += 1.5
                except Exception:
                    pass
        return _result

    # // GIVE EACH COMMAND THEIR RATING
    # /////////////////////////////////////
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
    async def _command_sort(self, _user_command):
        try:
            _command_dict = await self._command_rate(_user_command)
            _sorted_command_dict = {k: v for k, v in sorted(_command_dict.items(), key=lambda item: item[1], reverse=True)}
            _result = []
            for command in _sorted_command_dict:
                if _sorted_command_dict[command] > (len(command)*0.85):
                    _result.append(command)
                    if len(_result) >= 6:
                        return _result
        except Exception:
            return _result
        return _result
    

    # ON COMMAND ERROR HANDLING
    # ///////////////////////////////
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
        
        if isinstance(error, commands.MemberNotFound):
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} player not found", color=15158588))
            
        await self._run_sorter(ctx, str(ctx.message.content.split(" ")[0]).strip("="))
        if not isinstance(error, commands.CommandNotFound):
            error_logs = self.client.get_channel(938482543227994132)
            await error_logs.send(f"**[{ctx.guild.name}]** `{datetime.datetime.utcnow()}`**:**  *{error}*")
            raise error

def setup(client):
    client.add_cog(ErrorHandling(client))