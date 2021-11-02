from discord.ext import commands
import discord

class Error_Handling(commands.Cog):
    def __init__(self, client):
        self.client = client

    # // SORT COMMAND DESCRIPTIONS
    # ////////////////////////////////
    async def _sort_commands(self):
        cogs=[]; cmds={}
        for command in self.client.commands:
            cogs.append(command.cog)

        for c in list(cmds.fromkeys(cogs)):
            if c is not None:
                for i in list(cmds.fromkeys(c.get_commands())):
                    cmds[i.name] = i.description
        return cmds

    # // GET THE SIMILAR COMMANDS TO AN UNKNWON COMMAND
    # ////////////////////////////////////////////////////
    async def _similar_cmds(self, ctx):
        correct_commands = await self._sort_commands()
        similar_commands=""
        correct_usages = ""
        commands = {}

        for cmd in self.client.commands:
            for c in str(cmd):
                if c in list(ctx.message.content):
                    if str(cmd) not in commands:
                        commands[str(cmd)] = 0
                    commands[str(cmd)] += 1

        for s in range(len(commands)):
            if (commands[list(commands)[s]] * 0.95) >= (len(list(commands)[s])/2):
                similar_commands+=list(commands)[s]+"\n"
                correct_usages+=f"{list(commands)[s]}: {correct_commands[list(commands)[s]]}\n"
        
        if len(similar_commands.split("\n")) <= 1:
            return await ctx.send(embed=discord.Embed(description=f"{ctx.author.mention} we could not find the command you are looking for", color=15158588))
        return [similar_commands, correct_usages]

    # // RETURN THE ERROR EMBED
    # //////////////////////////////
    async def _error_embed(self, ctx):
        values = await self._similar_cmds(ctx)
        embed=discord.Embed(title=f"Command Error: [{ctx.message.content}]", description="**Similar Commands:**\n"+values[0]+"\n**Command Usages:**\n"+values[1], color=15158588)
        embed.set_footer(text="Message \"tristan#2230\" for support")
        return await ctx.send(embed=embed)


    # ON COMMAND ERROR HANDLING
    # ///////////////////////////////
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            return await ctx.send(embed=discord.Embed(descriptionb=f"{ctx.author.mention} you do not have enough permissions", color=15158588))
            
        await self._error_embed(ctx)
        if not isinstance(error, commands.CommandNotFound):
            raise error


def setup(client):
    client.add_cog(Error_Handling(client))