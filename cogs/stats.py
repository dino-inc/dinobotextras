import discord
from discord.ext import commands
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy import exc
import asyncio
import random

class Message(Base):
    __tablename__ = 'channellog'

    def __repr(self):
        return f""


class Stats(commands.Cog):
    def __init__(self, bot):
        example = 1
        
    @commands.command()
    async def logStuff(self, ctx, channel : discord.TextChannel):



def setup(bot):
    bot.add_cog(Stats(bot))