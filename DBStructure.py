##################################################################
# This file is used to define all the DataBase Structures used in
# our project.
#
# Created by Jason Aug 20, 2021
##################################################################
import datetime
import base64
import enum

from sqlalchemy import Column, ForeignKey, Integer, String,\
    Text, DateTime, Numeric, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import pytz


# length of a standard string, use TEXT if longer than that
STANDARD_STRING_LENGTH = 50

DBUSERNAME = "postgres"
DBPASSWORD = "admin"
DBDATABASE = DBUSERNAME
DBPATH = f"postgresql://{DBUSERNAME}:{DBPASSWORD}@localhost/{DBDATABASE}"


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

    Credits:  https://brisbanesde.eq.edu.au/SupportAndResources/
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

    # user account created time
    created_at = Column(DateTime, default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")))

    # user password
    password = Column(Text, nullable=False)

    # user honor rating
    user_rating = Column(Numeric, default=0)

    # user email
    email = Column(String, nullable=False)

    # user bio
    bio = Column(Text, default=None, nullable=True)

    def __str__(self):
        return f"uid = {self.uid}, username = {self.username}, created at {self.created_at},\n" \
               f"base64 password = {self.password}, honor rating = {self.user_rating}, " \
                f"email = {self.email},\nbio = {self.bio}"


def ascii_to_base64(password: str):
    """
    A function to turn explicit password string to base64 encoding string

    :param password: The password string to be encoded
    :return:The base64 encoded password string
    """
    return base64.b64encode(password.encode()).decode()


def base64_to_ascii(encoded_password: str):
    """
    Turn base64 encoded string back to human readable format

    :param encoded_password: The base64 encoded string
    :return: Human readable password string
    """
    return base64.b64decode(encoded_password.encode()).decode()


class UserTeachingAreas(Base):
    """
    The table specifying users' teaching areas
    """
    __tablename__ = "user_teaching_areas"

    # user id > User.uid
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    # teaching area
    teaching_area = Column("teaching_area", Enum(Subject), primary_key=True)

    # whether this teaching_area tag is made public
    is_public = Column(Boolean, default=True, nullable=False)

    user = relationship("User", foreign_keys=[uid])


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
    created_at = Column(DateTime, default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")))

    # difficulty of the resource
    difficulty = Column("difficulty", Enum(ResourceDifficulty), nullable=False)

    # up/down-vote count
    upvote_count = Column(Integer, default=0, nullable=False)
    downvote_count = Column(Integer, default=0, nullable=False)

    # if the resource is public
    is_public = Column(Boolean, default=True, nullable=False)

    def __str__(self):
        return f"resource id = {self.rid}, title = {self.title}, resource " \
               f"link = {self.resource_link}, created at {self.created_at}, " \
               f"difficulty = {self.difficulty.name},\n#upvote = {self.upvote_count}, " \
               f"#downvote = {self.downvote_count}, is resource public = {self.is_public}"


class VoteInfo(Base):
    """
    A table of vote status for user who voted on a resource
    """
    __tablename__ = "vote_info"

    # user id
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    # resource id
    rid = Column(Integer, ForeignKey("resource.rid"), primary_key=True)

    # if this vote is upvote
    is_upvote = Column(Boolean, nullable=False)

    user = relationship("User", foreign_keys=[uid])
    resource = relationship("Resource", foreign_keys=[rid])


class ResourceCreater(Base):
    """
    A table representing the creaters of a resource
    """
    __tablename__ = "resource_creater"

    # resource id
    rid = Column(Integer, ForeignKey("resource.rid"), primary_key=True)

    # creater id
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    resource = relationship("Resource", foreign_keys=[rid])
    creater = relationship("User", foreign_keys=[uid])

    def __str__(self):
        return f"creater id = {self.uid}, resource id = {self.rid}"


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
    created_at = Column(DateTime, default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")))

    # resource to be commented
    rid = Column(Integer, ForeignKey("resource.rid"))

    # comment text
    comment = Column(Text, nullable=False)

    user = relationship("User", foreign_keys=[uid])
    resource = relationship("Resource", foreign_keys=[rid])


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
    created_at = Column(DateTime, default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")), primary_key=True)

    # replier id
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    resource_comment = relationship("ResourceComment", foreign_keys=[resource_comment_id])
    replier = relationship("User", foreign_keys=[uid])


class PrivateResourcePersonnel(Base):
    """
    The representation of a personnel that stores users that are allowed to
    watch particular resources
    """
    # todo: define trigger to avoid public resource be added to this table
    __tablename__ = "private_resource_personnel"

    # resource id
    rid = Column(Integer, ForeignKey("resource.rid"), primary_key=True)

    # user who allowed to view this resource
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    resource = relationship("Resource", foreign_keys=[rid])
    allowed_user = relationship("User", foreign_keys=[uid])


class Tag(Base):
    """
    The table representing a set of tags available in the system
    """
    __tablename__ = "tag"

    # tag id
    tag_id = Column(Integer, primary_key=True, autoincrement=True)

    # name of the tag
    tag_name = Column(String(STANDARD_STRING_LENGTH), nullable=False)

    # description of tag
    tag_description = Column(Text, default=None)


class ResourceTagRecord(Base):
    """
    Recording all tags associated to each resource
    """
    __tablename__ = "resource_tag_record"

    # tag
    tag_id = Column(Integer, ForeignKey("tag.tag_id"), primary_key=True)

    # resource
    rid = Column(Integer, ForeignKey("resource.rid"), primary_key=True)

    tag = relationship("Tag", foreign_keys=[tag_id])
    resource = relationship("Resource", foreign_keys=[rid])


class ForumQuestion(Base):
    """
    A table used to record private (forum) question
    """
    __tablename__ = "forum_question"

    # question id
    qid = Column(Integer, primary_key=True, autoincrement=True)

    # title of the question
    title = Column(String(STANDARD_STRING_LENGTH), nullable=False)

    # question creater id
    uid = Column(Integer, ForeignKey("user.uid"))

    # description of question
    content = Column(Text, nullable=False)

    questioner = relationship("User", foreign_keys=[uid])


class ForumPersonnel(Base):
    """
    A table defining the people that allowed to see contents of a question & thread
    """
    __tablename__ = "forum_personnel"

    # question id
    qid = Column(Integer, ForeignKey("forum_question.qid"), primary_key=True)

    # user allowed to view that question and following replies
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    question = relationship("ForumQuestion", foreign_keys=[qid])
    allowed_user = relationship("User", foreign_keys=[uid])


class ForumThread(Base):
    """
    A thread under a question
    """
    __tablename__ = "forum_thread"

    # thread id
    tid = Column(Integer, primary_key=True, autoincrement=True)

    # the question this thread links to
    qid = Column(Integer, ForeignKey("forum_question.qid"))

    # thread initial reply
    init_text = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")))


class ForumThreadReply(Base):
    """
    A table recording replies to a thread
    """
    __tablename__ = "forum_thread_reply"

    # thread to be replied
    tid = Column(Integer, ForeignKey("forum_thread.tid"), primary_key=True)

    # datetime when created
    created_at = Column(DateTime, default=datetime.datetime.now(
        tz=pytz.timezone("Australia/Brisbane")), primary_key=True)

    # replier id
    uid = Column(Integer, ForeignKey("user.uid"), primary_key=True)

    # reply content
    text = Column(Text, nullable=False)

    # up/down-vote count
    upvote_count = Column(Integer, default=0, nullable=False)
    downvote_count = Column(Integer, default=0, nullable=False)

    thread = relationship("ForumThread", foreign_keys=[tid])
    replier = relationship("User", foreign_keys=[uid])


engine = create_engine(DBPATH)
Base.metadata.create_all(engine)
