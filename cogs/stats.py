import discord
from discord.ext import commands
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship, backref
from sqlalchemy import exc
import asyncio

# sqlalchemy boilerplate
Base = declarative_base()
engine = create_engine('sqlite:///serverlogs.db')

# Messages within a channel
class Message(Base):
    __tablename__="message"
    id = Column(Integer, primary_key=True)
    content = Column(String)
    bot = Column(Boolean)
    has_embed = Column(Boolean)
    is_pinned = Column(Boolean)
    date = Column(DateTime(timezone=True))
    edited = Column(DateTime(timezone=True))
    reactions = relationship("Reaction", backref="message")
    attachments = relationship("Attachment", backref="message")
    author = relationship("Member", secondary="member_message")

# Channel within a server
class Channel(Base):
    __tablename__ = "channel"
    topic = Column(String)
    creation_date = Column(DateTime(timezone=True))
    messages = relationship("Message", backref = "channel")

# Servers with the bot
class ServerList(Base):
    __tablename__="serverlist"
    id = Column(Integer)
    member_count = Column(Integer)
    creation_date = Column(Integer)
    channels = relationship("Channel", backref = "serverlist")

# Members with messages
class Member(Base):
    __tablename__="member"
    id = Column(Integer, primary_key=True)
    join_date = Column(DateTime(timezone=True))
    creation_date = Column(DateTime(timezone=True))
    messages = relationship("Message", secondary="member_message")

# Junction between members and messages
class Member_Message(Base):
    __tablename__="member_message"
    member_id = Column(Integer, ForeignKey('member.id'), primary_key = True)
    message_id = Column(Integer, ForeignKey('message.id'), primary_key = True)

#Store attachments of a message
class Attachment(Base):
    __tablename__="attachment"
    id = Column(Integer, primary_key=True)
    url = Column(String)
    filename = Column(String)

#Store reactions of a message
class Reaction(Base):
    __tablename__="reaction"
    emoji_name = Column(String)
    emoji_id = Column(String)
    count = Column(Integer)
    is_custom_emoji = Column(Boolean)

Base.metadata.create_all(engine)

class Stats(commands.Cog):
    def __init__(self, bot):
        example = 1
        
    @commands.command()
    async def logStuff(self, ctx, channel : discord.TextChannel):



def setup(bot):
    bot.add_cog(Stats(bot))