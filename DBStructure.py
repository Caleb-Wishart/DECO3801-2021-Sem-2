############################################################################
# This file is used to define all the DataBase Structures used in
# our project.
#
# *******************************Note*****************************
# Under current config, the deletion of a row will be cascaded
# to ALL tables that are dependent (i.e. table which uses this table's attribute
# as foreign key) to this table. This is
# specified by adding *backref* config for each relationship
# function call. However, this constraint is enforced using sqlalchemy
# function instead of adding constraint to DB, so if you modify the DB in psql
# cli directly, any update will NO LONGER be cascaded to attributes in other
# tables that referencing it.
# To see the effect, check DBTester.py - "try delete a user instance with dependency"
# section.
#
#
# Created by Jason Aug 20, 2021
#############################################################################
import datetime
import enum

from sqlalchemy import Column, ForeignKey, Integer, String, \
    Text, DateTime, Numeric, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine
import pytz


# length of a standard string, use TEXT if longer than that
STANDARD_STRING_LENGTH = 300

# OPTIONS for DB testing:

# Option 1: access psql DB and create schema using you own account in your own DB
DBUSERNAME = "postgres"  # change this field to your first name (all lowercase), "call me by your name"

DBPASSWORD = "admin"
DBDATABASE = "project"  # DBUSERNAME
DBPATH = f"postgresql://{DBUSERNAME}:{DBPASSWORD}@localhost/{DBDATABASE}"


# Option 2: Feel lazy to sign in to cli? No worries, you can play these using sqlite
# on your local device
# uncomment DBPATH below to overwrite the above PATH config
# DBPATH = "sqlite:///Doctrina.db"


class ResourceDifficulty(enum.Enum):
    """
    The enum used to denoted the difficulty of a resource
    """
    EASY = 0
    MODERATE = 1
    HARD = 2
    SPECIALIST = 3


class Subject(enum.Enum):
    """
    The set of available subject tags

    Credit:  https://brisbanesde.eq.edu.au/SupportAndResources/

    FormsAndDocuments/Documents/Subject%20Guides/Lists%20and%20Handbooks/
    subject-guide-y11-12-hb-web.pdf
    """
    ENGLISH = 0
    MATHS_A = 1
    MATHS_B = 2
    MATHS_C = 3
    BIOLOGY = 4
    GEOGRAPHY = 5
    CHEMISTRY = 6
    PHYSICS = 7
    ACCOUNTING = 8
    ECONOMICS = 9
    ANCIENT_HISTORY = 10
    LEGAL_STUDIES = 11
    BUSINESS_STUDIES = 12
    SOCIAL_STUDIES = 13
    DANCE = 14
    DRAMA = 15
    IT = 16
    MUSIC = 17
    DESIGN = 18
    PE = 19
    CHINESE = 20
    SPANISH = 21
    GERMAN = 22
    JAPANESE = 23
    OTHER = 24


class Grade(enum.Enum):
    """
    The grades used to classify resources
    """
    KINDERGARTEN = 0
    YEAR_1 = 1
    YEAR_2 = 2
    YEAR_3 = 3
    YEAR_4 = 4
    YEAR_5 = 5
    YEAR_6 = 6
    YEAR_7 = 7
    YEAR_8 = 8
    YEAR_9 = 9
    YEAR_10 = 10
    YEAR_11 = 11
    YEAR_12 = 12
    TERTIARY = 13


class ChannelVisibility(enum.Enum):
    """
    The visibility of channel
    """
    INVITE_ONLY = 0
    FULLY_PRIVATE = 1
    PUBLIC = 2


def enum_to_website_output(item: enum.Enum) -> str:
    """
    Convert an enum value to human friendly format: to lowercase, capitalize first
    letter of each word and get rid of underscore, if any

    e.g. Subject.MATHS_A -> "Maths A:

    :param item: The enum item to convert
    :return The human friendly string value of the enum item
    """
    name = item.name
    if len(name) == 2:
        # Subject.IT/PE, no need to convert to lowercase
        return name
    return name.lower().replace('_', ' ', 1).title()


def website_input_to_enum(readable_string: str, enum_class: enum.Enum):
    """
    Convert a human readable enum value to an appropriate enum variable.
    i.e. applicable to Subject, Grade and ChannelVisibility only

    :param readable_string: The enum string value human can understand
    :param enum_class: The class of this enum value to return
    :return if corresponding enum variable in the nominated enum_class is found,
            it returns it. Otherwise
    """
    value = readable_string.upper().replace(' ', '_', 1)
    try:
        return enum_class[value]
    except KeyError:
        # no such enum variable
        print(f"value {readable_string} not found in enum class {enum_class}")
        return None


def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return [value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")]


Base = declarative_base()


class User(Base):
    """
    The table representing users of the platform
    """
    __tablename__ = "user"

    # user id (autoincrement, PK)
    uid = Column(Integer, primary_key=True, autoincrement=True)

    # username
    username = Column(String(STANDARD_STRING_LENGTH), nullable=False)

    # link to avatar image
    avatar_link = Column(String(STANDARD_STRING_LENGTH), nullable=True, default=None)

    # profile background link
    profile_background_link = Column(String(STANDARD_STRING_LENGTH), nullable=True, default=None)

    # user account created time
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")), nullable=False)

    # user hash_password -- sha256 encoded
    hash_password = Column(Text, nullable=False)

    # user honor rating
    user_rating = Column(Numeric, default=0)

    # user email -- This is unique
    email = Column(String, nullable=False, unique=True)

    # user bio
    bio = Column(Text, default=None, nullable=True)

    # user authentication
    authenticated = Column(Boolean, nullable=False, default=False)

    def __str__(self):
        return f"User table:\n" \
               f"uid = {self.uid}, username = {self.username}, created at {self.created_at},\n" \
               f"sha256 password = {self.hash_password}," \
               f"honor rating = {self.user_rating}, email = {self.email}," \
               f"avatar link = {self.avatar_link}\nbio = {self.bio}"

    @property
    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email

    @property
    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    @property
    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False


class UserSession(Base):
    """
    A concept of a user login session
    """
    __tablename__ = "user_session"

    # user id
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    # last action request time
    last_action_time = Column(DateTime(timezone=True), default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")), nullable=False)

    user = relationship("User", foreign_keys=[uid],
                        backref=backref("user_session", cascade="all, delete"))


class UserTeachingAreas(Base):
    """
    The table specifying users' teaching areas
    """
    __tablename__ = "user_teaching_areas"

    # user id
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    # teaching area
    teaching_area = Column("teaching_area", Enum(Subject), primary_key=True)

    # teaching grade - optional for users
    grade = Column("teaching_grade", Enum(Grade), nullable=True, default=None)

    # whether this teaching_area tag is made public
    is_public = Column(Boolean, default=True, nullable=False)

    user = relationship("User", foreign_keys=[uid],
                        backref=backref("user_teaching_areas", cascade="all, delete"))

    def __str__(self):
        text = f"UserTeachingAreas table:\n" \
               f"uid = {self.uid}, teaching area = {self.teaching_area}," \
               f"is_public = {self.is_public}"
        if self.grade:
            return text + f", grade = {self.grade.name}"
        else:
            return text


class Resource(Base):
    """
    The class representing an instance of a resource (video) on the platform
    """
    __tablename__ = "resource"

    # resource id
    rid = Column(Integer, primary_key=True, autoincrement=True)

    # title of the resource
    title = Column(String(STANDARD_STRING_LENGTH), nullable=False)

    # link to video
    resource_link = Column(String(STANDARD_STRING_LENGTH), nullable=False)

    # date and time of creation
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")), nullable=False)

    # difficulty of the resource
    difficulty = Column("difficulty", Enum(ResourceDifficulty), nullable=False)

    # subject of the resource
    subject = Column("subject", Enum(Subject), nullable=False)

    # grade of the resource
    grade = Column("grade", Enum(Grade), nullable=False)

    # up/down-vote count
    upvote_count = Column(Integer, default=0, nullable=False, autoincrement=False)
    downvote_count = Column(Integer, default=0, nullable=False, autoincrement=False)

    # if the resource is public
    is_public = Column(Boolean, default=True, nullable=False)

    # description of a resource
    description = Column(Text, default=None)

    def __str__(self):
        return f"Resource table:\n" \
               f"rid = {self.rid}, title = {self.title}, resource " \
               f"link = {self.resource_link},\ncreated at {self.created_at},\n" \
               f"grade = {self.grade.name}, " \
               f"difficulty = {self.difficulty.name}, #upvote = {self.upvote_count}, " \
               f"#downvote = {self.downvote_count}, is_public = {self.is_public}\n" \
               f"description = {self.description}"

    @property
    def serialize(self):
        """Return object data in serialisable format """
        return {
            "rid": self.rid,
            "title": self.title,
            "resource_link": self.resource_link,
            "created_at": dump_datetime(self.created_at),
            "grade": self.grade.name,
            "difficulty": self.difficulty.name,
            "upvote_count": self.upvote_count,
            "downvote_count": self.downvote_count,
            "is_public": self.is_public,
            "description": self.description
        }


class ResourceView(Base):
    """
    A table recording resources viewed by users
    """
    __tablename__ = "resource_view"

    # resource id
    rid = Column(Integer, ForeignKey("resource.rid"), primary_key=True)

    # user id
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    # timestamp
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")), nullable=False)

    user = relationship("User", foreign_keys=[uid],
                        backref=backref("resource_view", cascade="all,delete"))
    resource = relationship("Resource", foreign_keys=[rid],
                            backref=backref("resource_view", cascade="all,delete"))

    def __str__(self):
        return f"ResourceView table:\n" \
               f"rid = {self.rid}, uid = {self.uid},\n" \
               f"created at = {self.created_at}"


class ResourceThumbnail(Base):
    """
    A table which stores all the thumbnails of resources, which are displayed
    in resource preview
    """
    __tablename__ = "resource_thumbnail"

    # resource id
    rid = Column(Integer, ForeignKey("resource.rid"), primary_key=True)

    # link to thumbnail
    thumbnail_link = Column(Text, nullable=False, primary_key=True)

    resource = relationship("Resource", foreign_keys=[rid],
                            backref=backref("resource_thumbnail", cascade="all,delete"))

    def __str__(self):
        return f"ResourceThumbnail table:\n" \
               f"rid = {self.rid}, thumbnail link = {self.thumbnail_link}"


class ResourceVoteInfo(Base):
    """
    A table of vote status for user who voted on a resource
    """
    __tablename__ = "resource_vote_info"

    # user id
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    # resource id
    rid = Column(Integer, ForeignKey("resource.rid"), primary_key=True)

    # if this vote is upvote
    is_upvote = Column(Boolean, nullable=False)

    user = relationship("User", foreign_keys=[uid],
                        backref=backref("resource_vote_info", cascade="all,delete"))
    resource = relationship("Resource", foreign_keys=[rid],
                            backref=backref("resource_vote_info", cascade="all,delete"))

    def __str__(self):
        return f"ResourceVoteInfo table:\n" \
               f"Voter id = {self.uid}, rid = {self.rid}, " \
               f"is_upvote = {self.is_upvote}"


class ResourceCreater(Base):
    """
    A table representing the creaters of a resource
    """
    __tablename__ = "resource_creater"

    # resource id
    rid = Column(Integer, ForeignKey("resource.rid"), primary_key=True)

    # creater id
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    resource = relationship("Resource", foreign_keys=[rid],
                            backref=backref("resource_creater", cascade="all, delete"))
    creater = relationship("User", foreign_keys=[uid],
                           backref=backref("resource_creater", cascade="all, delete"))

    def __str__(self):
        return f"ResourceCreater table:\n" \
               f"creater id = {self.uid}, rid = {self.rid}"


class ResourceComment(Base):
    """
    A table representing the comments of resources
    """
    __tablename__ = "resource_comment"

    # resource_comment id
    resource_comment_id = Column(Integer, primary_key=True, autoincrement=True)

    # commenter id
    uid = Column(Integer, ForeignKey("user.uid"))

    # comment created time
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")), nullable=False)

    # resource to be commented
    rid = Column(Integer, ForeignKey("resource.rid"))

    # comment text
    comment = Column(Text, nullable=False)

    user = relationship("User", foreign_keys=[uid],
                        backref=backref("resource_comment", cascade="all, delete"))
    resource = relationship("Resource", foreign_keys=[rid],
                            backref=backref("resource_comment", cascade="all, delete"))

    def __str__(self):
        return f"ResourceComment table:\n" \
               f"resource comment id = {self.resource_comment_id}, uid = {self.uid}, " \
               f"rid = {self.rid},\ncreated at = {self.created_at}\n" \
               f"comment = {self.comment}"


class ResourceCommentReply(Base):
    """
    A table representing replies to resources' comments
    """
    __tablename__ = "resource_comment_reply"

    # id of comment to be replied
    resource_comment_id = Column(Integer,
                                 ForeignKey("resource_comment.resource_comment_id"),
                                 primary_key=True)

    # reply text
    reply = Column(Text, nullable=False)

    # reply time
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")), primary_key=True)

    # replier id
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    resource_comment = relationship("ResourceComment", foreign_keys=[resource_comment_id],
                                    backref=backref("resource_comment_reply",
                                                    cascade="all, delete"))
    replier = relationship("User", foreign_keys=[uid],
                           backref=backref("resource_comment_reply",
                                           cascade="all, delete"))

    def __str__(self):
        return f"ResourceCommentReply table:\n" \
               f"resource_comment_id = {self.resource_comment_id}, " \
               f"replier id = {self.uid}, created_at = {self.created_at}\n" \
               f"reply = {self.reply}"


class PrivateResourcePersonnel(Base):
    """
    The representation of a personnel that stores users that are allowed to
    watch particular resources
    """

    __tablename__ = "private_resource_personnel"

    # resource id
    rid = Column(Integer, ForeignKey("resource.rid"), primary_key=True)

    # user who allowed to view this resource
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    resource = relationship("Resource", foreign_keys=[rid],
                            backref=backref("private_resource_personnel", cascade="all, delete"))
    allowed_user = relationship("User", foreign_keys=[uid],
                                backref=backref("private_resource_personnel", cascade="all, delete"))

    def __str__(self):
        return f"PrivateResourcePersonnel table:\n" \
               f"allowed uid = {self.uid}, rid = {self.rid}"


class Tag(Base):
    """
    The table representing a set of tags available in the system
    """
    __tablename__ = "tag"

    # tag id
    tag_id = Column(Integer, primary_key=True, autoincrement=True)

    # name of the tag
    tag_name = Column(String(STANDARD_STRING_LENGTH), nullable=False, unique=True)

    # description of tag
    tag_description = Column(Text, default=None)

    def __str__(self):
        return f"Tag table:\n" \
               f"tag_id = {self.tag_id}, " \
               f"tag name = {self.tag_name}, tag id = {self.tag_id}"


class ResourceTagRecord(Base):
    """
    Recording all tags associated to each resource
    """
    __tablename__ = "resource_tag_record"

    # tag
    tag_id = Column(Integer, ForeignKey("tag.tag_id"), primary_key=True)

    # resource
    rid = Column(Integer, ForeignKey("resource.rid"), primary_key=True)

    tag = relationship("Tag", foreign_keys=[tag_id],
                       backref=backref("resource_tag_record", cascade="all, delete"))
    resource = relationship("Resource", foreign_keys=[rid],
                            backref=backref("resource_tag_record", cascade="all, delete"))

    def __str__(self):
        return f"ResourceTagRecord table:\n" \
               f"tag id = {self.tag_id}, rid = {self.rid}"


class Channel(Base):
    """
    A table used to record channels of the chat functionality
    """
    __tablename__ = "channel"

    # channel id
    cid = Column(Integer, primary_key=True, autoincrement=True)

    # subject of this channel - optional
    subject = Column("subject", Enum(Subject), nullable=True, default=None)

    # grade of this channel
    grade = Column("grade", Enum(Grade), nullable=True, default=None)

    # visibility of this channel
    visibility = Column("visibility", Enum(ChannelVisibility), nullable=False,
                        default=ChannelVisibility.PUBLIC)

    # name of the channel, enforce unique constraint
    name = Column(String(STANDARD_STRING_LENGTH), nullable=False, unique=True)

    # channel admin id
    admin_uid = Column(Integer, ForeignKey("user.uid"))

    # description of the channel
    description = Column(Text, nullable=True)

    admin = relationship("User", foreign_keys=[admin_uid],
                         backref=backref("channel", cascade="all, delete"))

    def __str__(self):
        text = f"Channel table:\n" \
               f"channel name = {self.name}, admin id = {self.admin_uid},\n" \
               f"cid = {self.cid}, " \
               f"visibility = {self.visibility.name}, "
        if self.subject:
            text += f"subject={self.subject.name}, "
        if self.grade:
            text += f"grade={self.grade.name},"
        return text + "\n" + f"description = {self.description}"


class ChannelPersonnel(Base):
    """
    A table defining the people that allowed to see contents of a channel
    """
    __tablename__ = "channel_personnel"

    # channel id
    cid = Column(Integer, ForeignKey("channel.cid"), primary_key=True)

    # user allowed to view that channel
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    channel = relationship("Channel", foreign_keys=[cid],
                           backref=backref("channel_personnel", cascade="all, delete"))
    allowed_user = relationship("User", foreign_keys=[uid],
                                backref=backref("channel_personnel", cascade="all, delete"))

    def __str__(self):
        return f"ChannelPersonnel table:\n" \
               f"cid = {self.cid}, allowed uid = {self.uid}"


class ChannelTagRecord(Base):
    """
    A table that records all tags associated with channels
    """
    __tablename__ = "channel_tag_record"

    # tag id
    tag_id = Column(Integer, ForeignKey("tag.tag_id"), primary_key=True)

    # channel id
    cid = Column(Integer, ForeignKey("channel.cid"), primary_key=True)

    tag = relationship("Tag", foreign_keys=[tag_id],
                       backref=backref("channel_tag_record", cascade="all,delete"))
    channel = relationship("Channel", foreign_keys=[cid],
                           backref=backref("channel_tag_record", cascade="all, delete"))

    def __str__(self):
        return f"ChannelTagRecord table:\n" \
               f"tag_id = {self.tag_id}, cid = {self.cid}"


class ChannelPost(Base):
    """
    Representation of a post in a channel
    """
    __tablename__ = "channel_post"

    # post id
    post_id = Column(Integer, primary_key=True, autoincrement=True)

    # creater of the post
    uid = Column(Integer, ForeignKey("user.uid"))

    # the channel this thread belongs to
    cid = Column(Integer, ForeignKey("channel.cid"))

    # the title of the post
    title = Column(String(STANDARD_STRING_LENGTH), nullable=False)

    # up/down-vote count
    upvote_count = Column(Integer, default=0, nullable=False, autoincrement=False)
    downvote_count = Column(Integer, default=0, nullable=False, autoincrement=False)

    # thread initial reply
    init_text = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")), nullable=False)

    channel = relationship("Channel", foreign_keys=[cid],
                           backref=backref("channel_post", cascade="all, delete"))

    def __str__(self):
        return f"ChannelPost table:\n" \
               f"post_id = {self.post_id}, cid = {self.cid},\n" \
               f"title = {self.title}, post creater id = {self.uid}\n" \
               f"#upvote = {self.upvote_count}, #downvote = {self.downvote_count},\n" \
               f"created at = {self.created_at}\n" \
               f"init_text = {self.init_text}"


class ChannelPostVoteInfo(Base):
    """
    Representation of a vote stat for channel post
    """
    __tablename__ = "channel_post_vote_info"

    # post to be commented
    post_id = Column(Integer, ForeignKey("channel_post.post_id"), primary_key=True)

    # voter's id
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    # vote status
    is_upvote = Column(Boolean, nullable=False)

    thread = relationship("ChannelPost", foreign_keys=[post_id],
                          backref=backref("channel_post_vote_info", cascade="all, delete"))
    voter = relationship("User", foreign_keys=[uid],
                         backref=backref("channel_post_vote_info", cascade="all, delete"))

    def __str__(self):
        return f"channel_post_vote_info table:\n" \
               f"post id = {self.post_id}, voter is = {self.uid}, is upvote = {self.is_upvote}"


class PostComment(Base):
    """
    A table recording replies to a thread
    """
    __tablename__ = "post_comment"

    # post comment id
    post_comment_id = Column(Integer, primary_key=True, autoincrement=True)

    # post to be commented
    post_id = Column(Integer, ForeignKey("channel_post.post_id"))

    # datetime when created
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")), nullable=False)

    # commenter id
    uid = Column(Integer, ForeignKey("user.uid"))

    # comment content
    text = Column(Text, nullable=False)

    # up/down-vote count
    upvote_count = Column(Integer, default=0, nullable=False, autoincrement=False)
    downvote_count = Column(Integer, default=0, nullable=False, autoincrement=False)

    thread = relationship("ChannelPost", foreign_keys=[post_id],
                          backref=backref("post_comment", cascade="all, delete"))
    commenter = relationship("User", foreign_keys=[uid],
                             backref=backref("post_comment", cascade="all, delete"))

    def __str__(self):
        return f"PostComment table:\npost comment id = {self.post_comment_id}" \
               f"post_id = {self.post_id}, commenter uid = {self.uid},\n" \
               f"created_at = {self.created_at},\n" \
               f"text = {self.text}\n," \
               f"#upvote = {self.upvote_count}, #downvote = {self.downvote_count}"


class PostCommentVoteInfo(Base):
    """
    A table recording all the voting info to a post comment
    """
    __tablename__ = "post_comment_vote_info"

    # id of post comment to vote
    post_comment_id = Column(Integer, ForeignKey("post_comment.post_comment_id"), primary_key=True)

    # voter's id
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    # vote status
    is_upvote = Column(Boolean, nullable=False)

    post_comment = relationship("PostComment", foreign_keys=[post_comment_id],
                                backref=backref("post_comment_vote_info",
                                                cascade="all, delete"))
    voter = relationship("User", foreign_keys=[uid],
                         backref=backref("post_comment_vote_info", cascade="all, delete"))

    def __str__(self):
        return f"PostCommentVoteInfo table:\npost_comment_id = {self.post_comment_id}, " \
               f"uid = {self.uid}, is_upvote = {self.is_upvote}"


engine = create_engine(DBPATH)
Base.metadata.create_all(engine)
