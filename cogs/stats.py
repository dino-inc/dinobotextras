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
class Messagedb(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True)
    content = Column(String)
    bot = Column(Boolean)
    has_embed = Column(Boolean)
    is_pinned = Column(Boolean)
    date = Column(DateTime(timezone=True))
    edited = Column(DateTime(timezone=True))
    reactions = relationship("Reactiondb", backref="message")
    attachments = relationship("Attachmentdb", backref="message")
    author = relationship("Memberdb", secondary="member_message")


# Channel within a server
class Channeldb(Base):
    __tablename__ = "channel"
    topic = Column(String)
    id = Column(Integer, primary_key=True)
    creation_date = Column(DateTime(timezone=True))
    messages = relationship("Messagedb", backref = "channel")


# Servers with the bot
class ServerListdb(Base):
    __tablename__ = "serverlist"
    id = Column(Integer, primary_key=True)
    member_count = Column(Integer)
    creation_date = Column(Integer)
    channels = relationship("Channeldb", backref = "serverlist")


# Members with messages
class Memberdb(Base):
    __tablename__ = "member"
    id = Column(Integer, primary_key=True)
    join_date = Column(DateTime(timezone=True))
    creation_date = Column(DateTime(timezone=True))
    messages = relationship("Messagedb", secondary="member_message")


# Junction between members and messages
class Member_Message(Base):
    __tablename__ = "member_message"
    member_id = Column(Integer, ForeignKey('member.id'), primary_key=True)
    message_id = Column(Integer, ForeignKey('message.id'), primary_key=True)


# Store attachments of a message
class Attachmentdb(Base):
    __tablename__ = "attachment"
    id = Column(Integer, primary_key=True)
    url = Column(String)
    filename = Column(String)


# Store reactions of a message
class Reactiondb(Base):
    __tablename__ = "reaction"
    emoji_name = Column(String)
    emoji_id = Column(String)
    count = Column(Integer)
    is_custom_emoji = Column(Boolean)


Base.metadata.create_all(engine)


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.Session = sessionmaker(bind=engine)

    @commands.is_owner()
    @commands.command()
    async def log_message_test(self, ctx):
        session = self.Session()

        # Grab most recent channel message
        for msg in ctx.channel.history(limit=1):
            for reaction in msg.reactions:
                reactiondb = Reactiondb()
                session.add(reactiondb)
            msg_db = Messagedb(id=msg.id, content=msg.content, bot=False, has_embed=False, is_pinned=False,
                               date=msg.created_at, edited=msg.edited_at)



def setup(bot):
    bot.add_cog(Stats(bot))