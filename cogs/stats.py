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
import matplotlib

# sqlalchemy boilerplate
Base = declarative_base()
engine = create_engine('sqlite:///serverlogs.db')


# Messages within a channel
class Messagedb(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey("channel.id"), primary_key=True)
    guild_id = Column(Integer, ForeignKey("serverlist.id"))
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
    messages = relationship("Messagedb", lazy="dynamic", backref="server")


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


# Store attachments of a message - not used because it really doesn't matter
class Attachmentdb(Base):
    __tablename__ = "attachment"
    message_id = Column(Integer, ForeignKey("message.id"))
    id = Column(Integer, primary_key=True)
    url = Column(String)
    filename = Column(String)


# Store reactions of a message
class Reactiondb(Base):
    __tablename__ = "reaction"
    reaction_index = Column('index', Integer, index=True, primary_key=True)
    message_id = Column(Integer, ForeignKey("message.id"))
    emoji_name = Column(String, unique=False)
    emoji_id = Column(String)
    count = Column(Integer)
    is_custom_emoji = Column(Boolean)


Base.metadata.create_all(engine)


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.Session = sessionmaker(bind=engine)
        # Samsara, then personal testing server
        self.log_servers = [309168904310095886, 277294377548775425]

    # Add new messages to database as they arrive
    @commands.Cog.listener()
    async def on_message(self, message):
        # Disable logging for servers I'm not actively logging because there's no need for logging there
        if message.guild.id not in self.log_servers:
            return
        session = self.Session()
        await validate_serverdb(session, message.guild)
        channeldb = get_channeldb(session, message.guild, message.channel)
        await create_message(session, channeldb, message)
        session.commit()
        session.close()

    # The primary logging command
    @commands.is_owner()
    @commands.command()
    async def log_server(self, ctx):
        session = self.Session()
        await validate_serverdb(session, ctx.guild)
        logged_channels = "Logged channels:\n"
        for channel in ctx.guild.text_channels:
            print(f"Logging {channel.name}.")
            # Get the channel whose ID matches the message... if it exists
            channeldb = get_channeldb(session, ctx.guild, channel)
            # Overly broad try except, go!
            try:
                new_msg_counter = 0
                skip_msg_counter = 0
                async for msg in channel.history(limit=None, oldest_first=True):
                    # Get the message whose ID matches the message... if it exists
                    msg_db = channeldb.messages.filter_by(id=msg.id).first()
                    # Check if there is no message whose ID matches the iterated message
                    if msg_db is None:
                        # Keep track of how many new messages are created
                        new_msg_counter += 1
                        # Create the message
                        await create_message(session, channeldb, msg)
                    else:
                        skip_msg_counter += 1
                        continue
                session.commit()
                if len(logged_channels) > 1800:
                    await ctx.send(logged_channels)
                    logged_channels = ""
                logged_channels += f"Logged {new_msg_counter} messages (Skipped {skip_msg_counter}) from <#{channel.id}>.\n"
            except Exception as e:
                if len(logged_channels) > 1800:
                    await ctx.send(logged_channels)
                    logged_channels = ""
                logged_channels += f"Skipping <#{channel.id}> for {e}.\n"
        session.commit()
        session.close()
        await ctx.send(logged_channels+"Logging completed.\n")

    @commands.is_owner()
    @commands.command()
    async def show(self, ctx, count: int):
        session = self.Session()
        query = session.query(ServerListdb).filter_by(id=ctx.guild.id).first().channels.filter_by(id=ctx.channel.id)\
                .first().messages.all()
        composite_msg = f"The first {count} messages are:\n"
        for dbmessage in query:
            composite_msg += f"{dbmessage.content}\n"
            count -= 1
            if count == 0:
                break
        await ctx.send(composite_msg)
        session.close()

    @commands.is_owner()
    @commands.command()
    async def show_channels(self, ctx):
        session = self.Session()
        query = session.query(ServerListdb).filter_by(id=ctx.guild.id).first()
        if query is None:
            await ctx.send("There are no logged channels.")
        else:
            query = query.channels.all()
            composite_msg = f"The logged channels of the server are:\n"
            for channel in query:
                composite_msg += f"{channel.name}\n"
            await ctx.send(composite_msg)

    @commands.is_owner()
    @commands.command()
    async def howmany(self, ctx, member: discord.Member):
        session = self.Session()
        await ctx.send(f"{member.display_name} ({member.name}) has sent "
                       f"{len(get_member_messages(session, ctx, member.id))} messages in {ctx.guild.name}.")
        session.close()


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
            delete_db(Base)
            await ctx.send(f"Database is now deleted.")
        else:
            await ctx.send("Could not confirm, exiting command.")
    @commands.is_owner()
    @commands.group(name="graph")
    async def graph(self, ctx):
        print("This shouldn't be printing.")
        pass

    @commands.is_owner()
    @graph.command()
    async def total_msg(self, ctx):
        print("Generating graph of total messages over time.")
        session = self.session()
        await validate_serverdb(session, ctx.guild)
        channels = session.query(ServerListdb).filter_by(id=ctx.guild.id).first().channels
        total_messages = []
        dates = []
        # for channel, date in zip(channels, dates):
            # for message in channel:


# Gets the messages from a user on the guild the ctx is from
def get_member_messages(session, ctx, member_id):
    message_query = session.query(Memberdb).filter_by(id=member_id).first().messages
    message_list = []
    for message in message_query:
        if message.channel.serverlist.id == ctx.guild.id:
            message_list.append(message)
    return message_list


# Gets the channeldb object from a channel object
def get_channeldb(session, guild, channel):
    serverdb = session.query(ServerListdb).filter_by(id=guild.id).first()
    channeldb = serverdb.channels.filter_by(id=channel.id).first()
    if channeldb is None:
        print(f"Creating entry for channel {channel.name}.")
        channeldb = Channeldb(id=channel.id, name=channel.name, creation_date=channel.created_at)
        serverdb.channels.append(channeldb)
        session.commit()
    return channeldb


# Create server if it doesn't exist
async def validate_serverdb(session, guild):
    serverdb = session.query(ServerListdb).filter_by(id=guild.id).first()
    if serverdb is None:
        serverdb = ServerListdb(id=guild.id, member_count=guild.member_count,
                                creation_date=guild.created_at)
        session.add(serverdb)
        session.commit()
        print(f"Creating entry for server {guild.name}.")


async def create_message(session, channeldb, msg):
    # Creates a new member category if necessary
    # Queries for author ID
    authorquery = session.query(Memberdb).filter_by(id=msg.author.id).first()
    # If the member is not found, create it
    if authorquery is None:
        author = Memberdb(id=msg.author.id, creation_date=msg.author.created_at)
        # There's two types of users, because of course there is
        if type(msg.author) is discord.User:
            setattr(author, "join_date", None)
        else:
            setattr(author, "join_date", msg.author.joined_at)
        session.add(author)
        session.commit()

    msg_db = Messagedb(id=msg.id, content=msg.content, bot=False, has_embed=False, is_pinned=False,
                       date=msg.created_at, edited=msg.edited_at)
    authorquery = session.query(Memberdb).filter_by(id=msg.author.id).first()
    msg_db.author.append(authorquery)
    # Set the bot value
    if msg.author.bot:
        setattr(msg_db, "bot", True)
    # Sets if it has an embed
    if msg.embeds is not None:
        setattr(msg_db, "has_embeds", True)
    # Sets if it is pinned
    if msg.pinned:
        setattr(msg_db, "pinned", True)
    # Logs reactions
    for reaction in msg.reactions:
        # Handles the string case of emojis
        if type(reaction.emoji) is str:
            reactiondb = Reactiondb(emoji_name=reaction.emoji, emoji_id=None, count=reaction.count)
        # Handles partial emojis
        elif type(reaction.emoji) is discord.partial_emoji.PartialEmoji:
            reactiondb = Reactiondb(emoji_name=reaction.emoji.name, emoji_id=reaction.emoji.id,
                                    count=reaction.count)
            if reaction.emoji.is_custom_emoji():
                setattr(reactiondb, "is_custom_emoji", True)
        # Handles the only good emojis
        else:
            reactiondb = Reactiondb(emoji_name=reaction.emoji.name, emoji_id=reaction.emoji.id,
                                    count=reaction.count)
        msg_db.reactions.append(reactiondb)
    channeldb.messages.append(msg_db)
    session.commit()


# Deletes the database
def delete_db(Base):
    os.remove("serverlogs.db")
    Base.metadata.create_all(engine)


def setup(bot):
    bot.add_cog(Stats(bot))
