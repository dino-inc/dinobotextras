import discord
from discord.ext import commands
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy import exc
import asyncio
import os

# sqlalchemy boilerplate
Base = declarative_base()
engine = create_engine('sqlite:///serverlogs.db')


# Messages within a channel
class Messagedb(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey("channel.id"), primary_key=True)
    content = Column(String)
    bot = Column(Boolean)
    has_embed = Column(Boolean)
    is_pinned = Column(Boolean)
    date = Column(DateTime(timezone=True))
    edited = Column(DateTime(timezone=True))
    reactions = relationship("Reactiondb", lazy="dynamic", backref="message")
    attachments = relationship("Attachmentdb", lazy="dynamic", backref="message")
    author = relationship("Memberdb", lazy="dynamic", secondary="member_message")


# Channel within a server
class Channeldb(Base):
    __tablename__ = "channel"
    topic = Column(String)
    name = Column(String)
    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey("serverlist.id"))
    creation_date = Column(DateTime(timezone=True))
    messages = relationship("Messagedb", lazy="dynamic", backref="channel")


# Servers with the bot
class ServerListdb(Base):
    __tablename__ = "serverlist"
    id = Column(Integer, primary_key=True)
    member_count = Column(Integer)
    creation_date = Column(DateTime(timezone=True))
    channels = relationship("Channeldb", lazy="dynamic", backref="serverlist")


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
    member_id = Column(Integer, ForeignKey("member.id"), primary_key=True)
    message_id = Column(Integer, ForeignKey("message.id"), primary_key=True)


# Store attachments of a message
class Attachmentdb(Base):
    __tablename__ = "attachment"
    message_id = Column(Integer, ForeignKey("message.id"), primary_key=True)
    id = Column(Integer)
    url = Column(String)
    filename = Column(String)


# Store reactions of a message
class Reactiondb(Base):
    __tablename__ = "reaction"
    message_id = Column(Integer, ForeignKey("message.id"), primary_key=True)
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
    async def log(self, ctx):
        session = self.Session()

        # Grab most recent channel message
        serverdb = ServerListdb(id=ctx.guild.id, member_count=ctx.guild.member_count,
                                creation_date=ctx.guild.created_at)
        channeldb = Channeldb(id=ctx.channel.id, name=ctx.channel.name, creation_date=ctx.channel.created_at)
        serverdb.channels.append(channeldb)
        async for msg in ctx.channel.history(limit=5, oldest_first=True):
            msg_db = Messagedb(id=msg.id, content=msg.content, bot=False, has_embed=False, is_pinned=False,
                               date=msg.created_at, edited=msg.edited_at)

            for reaction in msg.reactions:
                reactiondb = Reactiondb(reaction.emoji.name)
                msg_db.reactions.append(reactiondb)
            for attachment in msg.attachments:
                attachmentdb = Attachmentdb(id=attachment.id, url=attachment.url)
                msg_db.attachments.append(attachmentdb)
            channeldb.messages.append(msg_db)
        session.add(serverdb)
        session.commit()
        await ctx.send("Tested database creation.")

    @commands.is_owner()
    @commands.command()
    async def show(self, ctx):
        session = self.Session()
        query = session.query(ServerListdb).filter_by(id=ctx.guild.id).first().channels.filter_by(id=ctx.channel.id)\
                .first().messages.all()
        composite_msg = "The first five messages are:\n"
        for dbmessage in query:
            composite_msg += f"{dbmessage.content}\n"
        await ctx.send(composite_msg)

    @commands.is_owner()
    @commands.command()
    async def cleardb(self, ctx):
        def verify_user(message):
            if message.author == ctx.message.author and message.channel == ctx.message.channel:
                return True
            else:
                return False
        await ctx.send("Are you sure you want to delete the database? Type \"DELETE\" to delete.")
        choice = ""
        try:
            choice = await self.bot.wait_for('message', check=verify_user, timeout=30)
        except asyncio.TimeoutError:
            await ctx.send(f"No input found, exiting command.")
            session.close()
            return
        if choice.content == "DELETE":
            os.remove("serverlogs.db")
            await ctx.send(f"Database is now deleted.")
        else:
            await ctx.send("Could not confirm, exiting command.")


def setup(bot):
    bot.add_cog(Stats(bot))
