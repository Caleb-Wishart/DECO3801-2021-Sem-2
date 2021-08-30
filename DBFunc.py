##################################################################
# This file provides some basic wrapper functions to create and
# modify the DB objects
#
# report bug to Jason on messenger
#
# Created by Jason Aug 20, 2021
##################################################################
import enum

from sqlalchemy.orm import sessionmaker
from DBStructure import *

# define if you want method output messages for debugging
verbose = True


class ErrorCode(enum.Enum):
    """
    This is a enum class representing all the possible error codes when
    calling the methods below
    """
    # user id/info incorrect
    INVALID_USER = 1
    # resource id/info incorrect
    INVALID_RESOURCE = 2
    # uid not in personnel
    INCORRECT_PERSONNEL = 3
    # voter make same vote to same item twice
    SAME_VOTE_TWICE = 4
    # channel id/info incorrect
    INVALID_CHANNEL = 5
    # post id/info incorrect
    INVALID_POST = 6
    # user session expired
    USER_SESSION_EXPIRED = 7


class PersonnelModification(enum.Enum):
    """
    Defining the type of modification to be done on personnel
    """
    PERSONNEL_ADD = 0
    PERSONNEL_DELETE = 1


engine = create_engine(DBPATH)
Session = sessionmaker(engine)

epoch = datetime.datetime.utcfromtimestamp(0)


# maximum time length for session without new action -- set as 30min
USER_SESSION_EXPIRE_INTERVAL = datetime.timedelta(minutes=30)


def add_user(username, password, email, teaching_areas: dict = {},
             bio=None, avatar_link=None, profile_background_link=None):
    """
    Add a new user to table user and add teaching_areas to
    user_teaching_areas table

    :param username: username
    :param avatar_link: The link to avatar, default is null
    :param profile_background_link: The link of profile background, default is null
    :param password: The password of new user
    :param bio: The bio of new user
    :param email: The email address of that user. This field is unique for each user.
    :param teaching_areas: Mapping of teaching area - [is_public, grade (optional)] list
            e.g. [Subject.ENGLISH: [True], Subject.MATHS_C: [False, Grade.YEAR_1]
    :return The id of the new user if success.
            ErrorCode.INVALID_USER if email is occupied

    """
    email = email.lower()
    user = User(username=username, avatar_link=avatar_link, password=ascii_to_base64(password),
                email=email, created_at=datetime.datetime.now(
            tz=pytz.timezone("Australia/Brisbane")), bio=bio,
                profile_background_link=profile_background_link)

    with Session() as conn:
        if conn.query(User).filter_by(email=email).one_or_none():
            print("This email address is registered")
            return ErrorCode.INVALID_USER

        # phase 1: add a new user
        conn.add(user)
        conn.commit()
        if verbose:
            print(f"User {username} created")

        # phase 2: find id of new user -- using email,
        # then update teaching_areas table
        user = conn.query(User).filter_by(email=email).one()

        user_session = UserSession(uid=user.uid)
        conn.add(user_session)
        conn.commit()

        for area, info in teaching_areas.items():
            grade = None
            if len(info) == 2:
                is_public, grade = info[0], info[1]
            else:
                is_public = info[0]
            if isinstance(area, Subject):
                new_teach_area = UserTeachingAreas(uid=user.uid, teaching_area=area,
                                                   is_public=is_public, grade=grade)
                conn.add(new_teach_area)
        conn.commit()
        return user.uid


def get_user_by_email(email):
    """
    Retrieve the User with the unique email as the key

    :param email: The identifying email
    :return: User structure on success
             ErrorCode.INVALID_USER if no match
    """
    email = email.lower()
    with Session() as conn:
        user = conn.query(User).filter_by(email=email).one_or_none()
        if user:
            if verbose:
                print(f"email {email} is registered by user uid = {user.uid}")

            return user
        print(f"No user has email {email}")
        return ErrorCode.INVALID_USER


def is_user_session_expired(uid: int):
    """
    Check if a user session is expired

    :param uid: The user id to check
    :return True if the session is expired, False otherwise
    """
    with Session() as conn:
        user_session = conn.query(UserSession).filter_by(uid=uid).one_or_none()
        # NOTE: tz = pytz.timezone("Australia/Brisbane") does not work in sqlite
        current = datetime.datetime.now(tz=pytz.timezone("Australia/Brisbane"))
        # print(f"current time = {current},last_action_time = {user_session.last_action_time}")
        return current - user_session.last_action_time > USER_SESSION_EXPIRE_INTERVAL


def renew_user_session(uid: int):
    """
    Create a new session instance in Session table, if not exists;
    otherwise, update last_action_time to current datetime

    Call this when user sign in or a function requires uid and is_user_session_expired()
    is false

    :param uid: effective user id
    :return on success, None is returned.
            If uid does not exist, it returns ErrorCode.INVALID_USER
    """
    with Session() as conn:
        user = conn.query(User).filter_by(uid=uid).one_or_none()
        if not user:
            print(f"user {uid} does not exists")
            return ErrorCode.INVALID_USER

        user_session = conn.query(UserSession).filter_by(uid=uid).one_or_none()
        if not user_session:
            user_session = UserSession(uid=uid)
        else:
            user_session.last_action_time = datetime.datetime.now(
                    tz=pytz.timezone("Australia/Brisbane"))
        conn.add(user_session)
        conn.commit()
        if verbose:
            print(f"user {uid} last action time updated")


def add_tag(tag_name, tag_description=None):
    """
    Add a new tag to Database

    :param tag_name: The name of the new tag
    :param tag_description: The description of the tag (optional)
    :return the id of the new tag
    """
    tag = Tag(tag_name=tag_name, tag_description=tag_description)
    with Session() as conn:
        conn.add(tag)
        conn.commit()
        print(f"tag {tag_name} added") if verbose else None

        return conn.query(Tag).filter_by(tag_name=tag_name).one().tag_id


def get_tags():
    """
    :return: A dictionary of mapping tag_name -> tag_id
    """
    out = dict()

    with Session() as conn:
        tags = conn.query(Tag).all()

        for i in tags:
            out[i.tag_name] = i.tag_id
    return out


def add_resource(title, resource_link, difficulty: ResourceDifficulty, subject: Subject,
                 grade: Grade, creaters_id=[], is_public=True, private_personnel_id=[],
                 tags_id=[], description=None, resource_thumbnail_links=[]):
    """
    Add a resource to resource table

    :param grade: Tge grade this resource belongs to

    :param title: The name of the resource
    :param resource_link: The link to resource video
    :param difficulty: The difficulty of the resource
    :param subject: what subject this resource relates to
    :param is_public: if the resource is public
    :param private_personnel_id: if this resource is private, add all User instances
            to the private_resource_personnel. *Element to be filled in is uid
    :param tags_id: The tags associated with this resource *each element is tag_id
    :param description: The description of this resource
    :param creaters_id: The id of creaters * each element is uid
    :param resource_thumbnail_links: A list contains the link to all thumbnails of this resource
    :return The id of the new resource if success.
            ErrorCode.INCORRECT_PERSONNEL if
            private_personnel_id is not defined when is_public is False.

    """
    if not is_public and not private_personnel_id:
        print("Please specify the User allowed to access this resource")
        return ErrorCode.INCORRECT_PERSONNEL

    resource = Resource(title=title, resource_link=resource_link, grade=grade,
                        difficulty=difficulty, subject=subject, is_public=is_public,
                        description=description)

    with Session() as conn:

        # phase 1: add new resource
        conn.add(resource)
        conn.commit()

        # phase 2: find the new row, update private_resource_personnel info, tag info
        # and resource_creater table, resource_thumbnail
        resource = conn.query(Resource).filter_by(resource_link=resource_link).one()

        for i in resource_thumbnail_links:
            thumbnail = ResourceThumbnail(rid=resource.rid, thumbnail_link=i)
            conn.add(thumbnail)
        conn.commit()

        for i in creaters_id:
            creater_instance = ResourceCreater(rid=resource.rid, uid=i)
            conn.add(creater_instance)

            # creaters must have access to this resource
            if not is_public:
                private_access = PrivateResourcePersonnel(rid=resource.rid, uid=i)
                conn.add(private_access)
        conn.commit()

        if not is_public:
            for uid in private_personnel_id:
                private_access = PrivateResourcePersonnel(rid=resource.rid, uid=uid)
                conn.add(private_access)
            conn.commit()

        if tags_id:
            for i in tags_id:
                tag_record = ResourceTagRecord(rid=resource.rid, tag_id=i)
                conn.add(tag_record)
                conn.commit()
        if verbose:
            print(f"Resource {title} added")
        return resource.rid


def is_resource_public(rid: int):
    """
    Check if a resource is public

    :param rid: The resource id
    :return: True if the resource is public, False otherwise.
             ErrorCode.INVALID_RESOURCE is resource id is invalid
    """
    with Session() as conn:
        resource = conn.query(Resource).filter_by(rid=rid).one_or_none()

        if not resource:
            # resource not exist
            return ErrorCode.INVALID_RESOURCE
        return resource.is_public


def modify_resource_personnel(rid, uid, modification: PersonnelModification):
    """
    Add/delete a person from a resource personnel

    :param rid: The resource to be modified
    :param uid: The user to add/delete
    :param modification: Add or delete
    :return void on success.
            ErrorCode.INVALID_USER/-RESOURCE if uid/rid is incorrect or resource is public
            ErrorCode.INCORRECT_PERSONNEL if mode is delete and personnel info not exist
            ErrorCode.USER_SESSION_EXPIRED when user session is expired
    """
    user, resource = get_user_and_resource_instance(uid=uid, rid=rid)
    if not user:
        print("uid is invalid")
        return ErrorCode.INVALID_USER
    elif not resource or resource.is_public:
        print("rid is invalid or resource is public")
        return ErrorCode.INVALID_RESOURCE

    # check user session and renew
    if is_user_session_expired(uid):
        print("User session expired")
        return ErrorCode.USER_SESSION_EXPIRED
    renew_user_session(uid)

    with Session() as conn:
        if modification == PersonnelModification.PERSONNEL_DELETE:
            # delete
            personnel = conn.query(PrivateResourcePersonnel).filter_by(uid=uid, rid=rid). \
                one_or_none()
            if not personnel:
                print("Delete failed: User not in personnel")
                return ErrorCode.INCORRECT_PERSONNEL
            conn.delete(personnel)
            msg = "deleted"
        else:
            # add
            personnel = PrivateResourcePersonnel(uid=uid, rid=rid)
            conn.add(personnel)
            msg = "added"
        conn.commit()
        print(f"user {uid} is {msg} from/to personnel of resource {rid}")


def user_has_access_to_resource(uid, rid):
    """
    Check if a user has access to a private resource

    :param rid: The resource to be checked
    :param uid: The user to be checked
    :return True/False on success.
            ErrorCode.INVALID_USER/-RESOURCE if uid/rid is incorrect or resource is public
            ErrorCode.USER_SESSION_EXPIRED if user session is expired
    """
    user, resource = get_user_and_resource_instance(uid=uid, rid=rid)
    if not user:
        print("uid is invalid")
        return ErrorCode.INVALID_USER
    elif not resource or resource.is_public:
        print("rid is invalid or resource is public")
        return ErrorCode.INVALID_RESOURCE

    # check user session and renew
    if is_user_session_expired(uid):
        print("User session expired")
        return ErrorCode.USER_SESSION_EXPIRED
    renew_user_session(uid)

    with Session() as conn:
        return conn.query(PrivateResourcePersonnel).filter_by(uid=uid, rid=rid). \
                   one_or_none() is not None


def find_resources(title_type="like", title=None,
                   created_type="after", created=epoch,
                   difficulty=None, subject=None,
                   vote_type="more", votes=None,
                   grade=None, email=None
                   ):
    """Find a resource using the specific keys.

        If any param does not fall into the valid values the default will be
        used in its place.

        If no parameters are passed the method should return all Resources.

        :param title_type   : SQL search restriction for the title.
            Valid values are ["like","exact"]
            Defaults to "like".
        :param title        : title to search for
            Defaults to "".
        :param created_type : SQL search restriction for the creation date.
            Valid values are ["after","before"]
            Defaults to "after".
        :param created      : date to search for as a datetime object.
            Defaults to epoch.
        :param difficulty   : The difficult rating of the resource.
            Valid values are ResourceDifficulty enum values.
            Defaults to None.
        :param subject      : The subject of the resource.
            Valid values are Subject enum values.
            Defaults to None.
        :param vote_type    : SQL search restriction for the votes.
            Valid values are ["more","less"]. Refers to specified amount
            Defaults to "more".
        :param votes        : The number of upvotes a resource has.
            Defaults to None.
        :param grade        : The grade of the resource
            Valid values are the Grade enum values
            Defaults to None.
        :param email         : The logged in users email
            Defaults to None.
    """
    # Args Checking
    if title_type not in ["like", "exact"]:
        title_type = "like"
    if created_type not in ["after", "before"]:
        created_type = "after"
    if vote_type not in ["more", "less"]:
        vote_type = "more"

    with Session() as conn:
        # get User if exists
        user = conn.query(User).filter_by(email=email).one_or_none()

        resources = conn.query(Resource)

        if title is not None and isinstance(title, str):
            if title_type == "like":
                resources = resources.filter(Resource.title.ilike(f'%{title}%'))
            else:
                resources = resources.filter_by(title=title)

        if created != epoch and isinstance(created, datetime.datetime):
            if created_type == "after":
                resources = resources.filter(Resource.created_at > created)
            else:
                resources = resources.filter(Resource.created_at < created)

        if difficulty is not None and isinstance(difficulty, ResourceDifficulty):
            resources = resources.filter_by(difficulty=difficulty)

        if subject is not None and isinstance(subject, Subject):
            resources = resources.filter_by(subject=subject)

        if grade is not None and isinstance(grade, Grade):
            resources = resources.filter_by(grade=grade)

        if votes is not None and isinstance(votes, int):
            if vote_type == "more":
                resources = resources.filter(Resource.upvote_count > votes)
            else:
                resources = resources.filter(Resource.upvote_count < votes)

        if user is None:
            resources = resources.filter_by(is_public=True)
            result = resources.all()
        else:
            result = filter(lambda res: user_has_access_to_resource(user.uid, res.rid), resources.all())

    return result


def vote_resource(uid, rid, upvote=True):
    """
    Give upvote/downvote to a resource:
    1. update up/down-vote count of the nominated resource; and
    2. add/modify vote_info table

    :param uid: The voter's user id
    :param rid: The resource to vote
    :param upvote: is this is a upvote
    :return void on Success.
            ErrorCode.INVALID_RESOURCE/_USER if rid/uid is invalid.
            ErrorCode.SAME_VOTE_TWICE if current user gave same vote to this
            resource before.
            ErrorCode.USER_SESSION_EXPIRED if current session is expired
    """
    msg = "created"

    res = check_user_and_resource_validity_and_renew_user_session(uid=uid, rid=rid)
    if isinstance(res, ErrorCode):
        return res

    user, resource = res

    with Session() as conn:
        # try to find if there is an entry in vote_info
        vote_info = conn.query(ResourceVoteInfo).filter_by(uid=uid, rid=rid).one_or_none()

        if vote_info:
            if vote_info.is_upvote != upvote:
                # user voted, now change vote
                vote_info.is_upvote = upvote

                # update resource vote count
                if upvote:
                    resource.downvote_count -= 1
                    resource.upvote_count += 1
                else:
                    resource.downvote_count += 1
                    resource.upvote_count -= 1
                msg = "updated"
            else:
                if verbose:
                    print("user cannot vote the same item twice")
                return ErrorCode.SAME_VOTE_TWICE
        else:
            # new vote
            vote_info = ResourceVoteInfo(rid=rid, uid=uid, is_upvote=upvote)

            if upvote:
                resource.upvote_count += 1
            else:
                resource.downvote_count += 1

        conn.add(vote_info)
        conn.add(resource)
        conn.commit()
        if verbose:
            print(f"Vote info {msg} for resource {rid}, user {uid} upvoted = {upvote}")


def get_user_and_resource_instance(uid, rid):
    """
    Try to get instances User and Resource using provided uid and rid

    Can use this to check if the (uid, rid) is valid

    :param uid: The user id
    :param rid: The resource id
    :return The tuple of form User, Resource
    """
    with Session() as conn:
        resource = conn.query(Resource).filter_by(rid=rid).one_or_none()
        user = conn.query(User).filter_by(uid=uid).one_or_none()

    return user, resource


def user_viewed_resource(uid, rid):
    """
    Call this function to add a record to resource view table

    :param uid: The user id who viewed the resource
    :param rid: The id of resource viewed
    :return void on Success.
            ErrorCode.INVALID_RESOURCE/_USER if rid/uid is invalid.
            ErrorCode.USER_SESSION_EXPIRED if user session is expired
    """
    res = check_user_and_resource_validity_and_renew_user_session(uid=uid, rid=rid)
    if isinstance(res, ErrorCode):
        return res

    user, resource = res

    with Session() as conn:
        resource_view = ResourceView(rid=rid, uid=uid)
        conn.add(resource_view)
        conn.commit()
    print(f"user {uid} viewed resource {rid}") if verbose else None


def check_user_and_resource_validity_and_renew_user_session(uid, rid):
    """
    Check uid and rid's validity and renew the user session for current user

    :param uid: The user id to check
    :param rid: The resource id to check
    :return If valid, user, resource instances are returned and user session is updated.
            ErrorCode.INVALID_RESOURCE/_USER if rid/uid is invalid.
            ErrorCode.USER_SESSION_EXPIRED is current session is expired
    """
    user, resource = get_user_and_resource_instance(uid, rid)
    if not resource:
        print("rid is invalid")
        return ErrorCode.INVALID_RESOURCE
    elif not user:
        print("uid is invalid")
        return ErrorCode.INVALID_USER

    # check user session and renew
    if is_user_session_expired(uid):
        print("User session expired")
        return ErrorCode.USER_SESSION_EXPIRED
    renew_user_session(uid)

    return user, resource


def comment_to_resource(uid, rid, comment):
    """
    Add a comment to a resource

    :param uid: The commenter user id
    :param rid: The id of resource to be commented
    :param comment: The comment to that resource
    :return The id of the new resource comment on success.
            ErrorCode.INVALID_RESOURCE/_USER if rid/uid is invalid.
            ErrorCode.USER_SESSION_EXPIRED is current session is expired
    """
    res = check_user_and_resource_validity_and_renew_user_session(uid=uid, rid=rid)
    if isinstance(res, ErrorCode):
        return res

    created_at = datetime.datetime.now(tz=pytz.timezone("Australia/Brisbane"))
    with Session() as conn:
        resource_comment = ResourceComment(uid=uid, rid=rid, comment=comment, created_at=created_at)
        conn.add(resource_comment)
        conn.commit()
    if verbose:
        print(f"user {uid} commented resource {rid}")
    return conn.query(ResourceComment). \
        filter_by(uid=uid, rid=rid, created_at=created_at).one().resource_comment_id


def reply_to_resource_comment(uid, resource_comment_id, reply):
    """
    Add a reply to a resource comment

    :param uid: The resource comment replier user id
    :param resource_comment_id: The id resource
    :param reply: The reply text
    :return void on Success.
            ErrorCode.INVALID_RESOURCE/_USER if rid/uid is invalid.
            ErrorCode.USER_SESSION_EXPIRED is user session is expired
    """
    with Session() as conn:
        user = conn.query(User).filter_by(uid=uid).one_or_none()
        resource_comment = conn.query(ResourceComment). \
            filter_by(resource_comment_id=resource_comment_id).one_or_none()
        if not resource_comment:
            print("resource comment id is invalid")
            return ErrorCode.INVALID_RESOURCE
        elif not user:
            print("uid is invalid")
            return ErrorCode.INVALID_USER

        # check user session and renew
        if is_user_session_expired(uid):
            print("User session expired")
            return ErrorCode.USER_SESSION_EXPIRED
        renew_user_session(uid)

        reply_to_comment = ResourceCommentReply(resource_comment_id=resource_comment_id,
                                                reply=reply, uid=uid)
        conn.add(reply_to_comment)
        conn.commit()

        if verbose:
            print(f"user {uid} replied to resource comment {resource_comment_id}")


def create_channel(name, visibility: ChannelVisibility, admin_uid, subject: Subject = None,
                   grade: Grade = None, description=None, tags_id=[],
                   personnel_id=[]):
    """
    Create a channel

    :param name: The name of the channel
    :param visibility: The visibility of this channel to public
    :param admin_uid: Admin's user id
    :param subject: The subject this channel belongs to
    :param grade: The grade this channel belongs to
    :param description: The description of this channel
    :param tags_id: The id of tags of this channel
    :param personnel_id: If visibility is not Public, then this personnel
                         is used to define users with access to this channel
    :return the id of the new channel on success.
            ErrorCode.INVALID_USER if admin_uid does not exist.
            ErrorCode.USER_SESSION_EXPIRED if current session is expired
    """
    with Session() as conn:
        admin = conn.query(User).filter_by(uid=admin_uid).one_or_none()
        if not admin:
            print("Admin id is invalid")
            return ErrorCode.INVALID_USER

        # check user session and renew
        if is_user_session_expired(admin_uid):
            print("User session expired")
            return ErrorCode.USER_SESSION_EXPIRED
        renew_user_session(admin_uid)

        # phase 1: create instance
        channel = Channel(name=name, visibility=visibility, admin_uid=admin_uid,
                          subject=subject, grade=grade, description=description)
        conn.add(channel)
        conn.commit()

        # phase 2: use name (unique) to retrieve instance for next step operation
        channel = conn.query(Channel).filter_by(name=name).one()
        for i in tags_id:
            channel_tag_record = ChannelTagRecord(tag_id=i, cid=channel.cid)
            conn.add(channel_tag_record)
        conn.commit()

        if visibility != ChannelVisibility.PUBLIC:
            # add admin to personnel
            personnel = ChannelPersonnel(cid=channel.cid, uid=admin_uid)
            conn.add(personnel)
            for i in personnel_id:
                personnel = ChannelPersonnel(cid=channel.cid, uid=i)
                conn.add(personnel)
            conn.commit()

        if verbose:
            print(f"Channel {name} created")
        return channel.cid


def modify_channel_personnel(uid, cid, modification: PersonnelModification):
    """
    Add/ delete a user from/to a private personnel

    :param cid: The channel to be modified
    :param uid: The user to add/delete
    :param modification: Add or delete
    :return void on success.
            ErrorCode.INVALID_USER/-CHANNEL if uid/rid is incorrect or channel is public
            ErrorCode.INCORRECT_PERSONNEL if mode is delete and personnel info not exist
    """
    with Session() as conn:
        user = conn.query(User).filter_by(uid=uid).one_or_none()
        if not user:
            print("uid invalid")
            return ErrorCode.INVALID_USER
        channel = conn.query(Channel).filter_by(cid=cid).one_or_none()
        if not channel or channel.visibility == ChannelVisibility.PUBLIC:
            print("cid invalid")
            return ErrorCode.INVALID_CHANNEL

        if modification == PersonnelModification.PERSONNEL_DELETE:
            # delete
            personnel = conn.query(ChannelPersonnel).filter_by(uid=uid, cid=cid). \
                one_or_none()
            if not personnel:
                print("personnel does not exists")
                return ErrorCode.INCORRECT_PERSONNEL
            conn.delete(personnel)
            msg = "deleted"
        else:
            # add
            personnel = ChannelPersonnel(cid=cid, uid=uid)
            conn.add(personnel)
            msg = "created"
        conn.commit()
        if verbose:
            print(f"user {uid} is {msg} from/to personnel of channel {cid}")


def user_has_access_to_channel(uid, cid):
    """
    Check if user has access to a channel

    :param uid: The id of user to check
    :param cid: The id of channel to check
    :return True/False on success.
            ErrorCode.INVALID_USER/-CHANNEL if uid/rid is incorrect or resource is public
            ErrorCode.USER_SESSION_EXPIRED is current session is invalid
    """
    with Session() as conn:
        user = conn.query(User).filter_by(uid=uid).one_or_none()
        if not user:
            print("uid invalid")
            return ErrorCode.INVALID_USER

        # check user session and renew
        if is_user_session_expired(uid):
            print("User session expired")
            return ErrorCode.USER_SESSION_EXPIRED
        renew_user_session(uid)

        channel = conn.query(Channel).filter_by(cid=cid).one_or_none()
        if not channel or channel.visibility == ChannelVisibility.PUBLIC:
            print("cid invalid")
            return ErrorCode.INVALID_CHANNEL

        personnel = conn.query(ChannelPersonnel).filter_by(uid=uid, cid=cid). \
            one_or_none()
        return personnel is not None


def post_on_channel(uid, title, text, channel_name=None, cid=None):
    """
    Make a new post on a channel

    **Must specify a channel name or cid. cid has precedence over channel_name

    :param uid: The user who makes the post
    :param channel_name: The name of the channel to post
    :param cid: The id of the channel to post
    :param title: The title of the post
    :param text: The text of the post
    :return the post id on success.
            ErrorCode.INVALID_CHANNEL if channel_name or cid is invalid
            ErrorCode.INVALID_USER if uid is invalid
            ErrorCode.INCORRECT_PERSONNEL if user has permission to visit
            ErrorCode.USER_SESSION_EXPIRED if user session is expired
    """
    if not channel_name and not cid:
        print("Please supply channel name or cid")
        return ErrorCode.INVALID_CHANNEL

    with Session() as conn:
        if not conn.query(User).filter_by(uid=uid).one_or_none():
            print("invalid uid")
            return ErrorCode.INVALID_USER

        # check user session and renew
        if is_user_session_expired(uid):
            print("User session expired")
            return ErrorCode.USER_SESSION_EXPIRED
        renew_user_session(uid)

        if cid:
            channel = conn.query(Channel).filter_by(cid=cid).one_or_none()
        else:
            channel = conn.query(Channel).filter_by(name=channel_name).one_or_none()

        if not channel:
            print("Invalid channel name")
            return ErrorCode.INVALID_CHANNEL

        if channel.visibility != ChannelVisibility.PUBLIC:
            # not public, check if user is in the personnel
            personnel = conn.query(ChannelPersonnel). \
                filter_by(cid=channel.cid, uid=uid).one_or_none()
            if not personnel:
                print(f"User {uid} is not in channel {channel.name}")
                return ErrorCode.INCORRECT_PERSONNEL

        channel_post = ChannelPost(cid=channel.cid, title=title, init_text=text)
        conn.add(channel_post)
        conn.commit()

        channel_post = conn.query(ChannelPost).filter_by(cid=channel.cid, title=title).one()
        if verbose:
            print(f"post {title} by user {uid} is added to {channel_name}")
        return channel_post.post_id


def comment_to_channel_post(uid, post_id, text):
    """
    Create a comment to a post in the channel

    :param uid: Commenter's id
    :param post_id: The id of post to be commented
    :param text: The comment
    :return The id of new post comment
    :return The post_id on success.
            ErrorCode.INVALID_USER if uid is invalid
            ErrorCode.INVALID_POST if post_id is invalid
            ErrorCode.USER_SESSSION_EXPIRED if current session is expired
    """
    with Session() as conn:
        if not conn.query(User).filter_by(uid=uid).one_or_none():
            print("uid is invalid")
            return ErrorCode.INVALID_USER
        elif not conn.query(ChannelPost).filter_by(post_id=post_id).one_or_none():
            print("post_id is invalid")
            return ErrorCode.INVALID_POST

        # check user session and renew
        if is_user_session_expired(uid):
            print("User session expired")
            return ErrorCode.USER_SESSION_EXPIRED
        renew_user_session(uid)

        created_at = datetime.datetime.now(tz=pytz.timezone("Australia/Brisbane"))
        post_comment = PostComment(post_id=post_id, uid=uid, created_at=created_at,
                                   text=text)
        conn.add(post_comment)
        conn.commit()

        post_comment = conn.query(PostComment).filter_by(post_id=post_id, uid=uid,
                                                         created_at=created_at).one()
        if verbose:
            print(f"Comment to post {post_id} by user {uid} in created")
        return post_comment.post_comment_id


def vote_channel_post(uid, post_id, upvote=True):
    """
    A user vote a channel post

    :param uid: The id of the voter
    :param post_id: The post to be voted
    :param upvote: If this vote is a upvote
    :return void on success.
            ErrorCode.INVALID_USER if uid is invalid
            ErrorCode.INVALID_POST if post_id is invalid
            ErrorCode.SAME_VOTE_TWICE if current user gave same vote to this
            post before.
            ErrorCode.USER_SESSION_EXPIRED if current user is expired
    """
    with Session() as conn:
        user = conn.query(User).filter_by(uid=uid).one_or_none()
        post = conn.query(ChannelPost).filter_by(post_id=post_id).one_or_none()
        if not user:
            print("uid is invalid")
            return ErrorCode.INVALID_USER
        elif not post:
            print("post id is invalid")
            return ErrorCode.INVALID_POST

        # check user session and renew
        if is_user_session_expired(uid):
            print("User session expired")
            return ErrorCode.USER_SESSION_EXPIRED
        renew_user_session(uid)

        # try to find if there is an entry in vote_info
        vote = conn.query(ChannelPostVoteInfo).filter_by(uid=uid, post_id=post_id).one_or_none()
        if vote:
            if vote.is_upvote != upvote:
                # user voted, now change vote
                vote.is_upvote = upvote

                # update resource vote count
                if upvote:
                    post.downvote_count -= 1
                    post.upvote_count += 1
                else:
                    post.downvote_count += 1
                    post.upvote_count -= 1
            else:
                if verbose:
                    print("user cannot vote the same item twice")
                return ErrorCode.SAME_VOTE_TWICE
        else:
            # new vote
            vote = ChannelPostVoteInfo(uid=uid, post_id=post_id, is_upvote=upvote)
            if upvote:
                post.upvote_count += 1
            else:
                post.downvote_count += 1

        conn.add(vote)
        conn.add(post)
        conn.commit()
        if verbose:
            print(f"User {uid} voted post {post_id}, is_upvote = {upvote}")


def vote_channel_post_comment(uid, post_comment_id, upvote=True):
    """
    Make a vote to a channel post comment

    :param uid: The voter's id
    :param post_comment_id: The id of the post comment
    :param upvote: If this is an upvote
    :return void on success.
            ErrorCode.INVALID_USER if uid is invalid
            ErrorCode.INVALID_POST if post_id is invalid
            ErrorCode.SAME_VOTE_TWICE if current user gave same vote to this
            post comment before.
            ErrorCode.USER_SESSION_EXPIRED if user session is expired
    """
    with Session() as conn:
        user = conn.query(User).filter_by(uid=uid).one_or_none()
        post_comment = conn.query(PostComment).filter_by(post_comment_id=post_comment_id). \
            one_or_none()
        if not user:
            print("uid is invalid")
            return ErrorCode.INVALID_USER
        elif not post_comment:
            print("post id is invalid")
            return ErrorCode.INVALID_POST

        # try to find if there is an entry in vote_info
        vote = conn.query(PostCommentVoteInfo).filter_by(
            uid=uid, post_comment_id=post_comment_id).one_or_none()
        if vote:
            if vote.is_upvote != upvote:
                # user voted, now change vote
                vote.is_upvote = upvote

                # update resource vote count
                if upvote:
                    post_comment.downvote_count -= 1
                    post_comment.upvote_count += 1
                else:
                    post_comment.downvote_count += 1
                    post_comment.upvote_count -= 1
            else:
                if verbose:
                    print("user cannot vote the same item twice")
                return ErrorCode.SAME_VOTE_TWICE
        else:
            # new vote
            vote = PostCommentVoteInfo(uid=uid, post_comment_id=post_comment_id,
                                       is_upvote=upvote)
            if upvote:
                post_comment.upvote_count += 1
            else:
                post_comment.downvote_count += 1

        conn.add(vote)
        conn.add(post_comment)
        conn.commit()
        if verbose:
            print(f"User {uid} voted post {post_comment_id}, is_upvote = {upvote}")
