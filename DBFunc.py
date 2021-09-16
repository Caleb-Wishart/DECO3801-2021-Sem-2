##################################################################
# This file provides some basic wrapper functions to create and
# modify the DB objects
#
# report bug to Jason on messenger
#
# Created by Jason Aug 20, 2021
##################################################################
import traceback
import warnings

import sqlalchemy.exc
from sqlalchemy import or_
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

# use this in branch
# from .DBStructure import *
# use this in main
from DBStructure import *

# define if you want method output messages for debugging
VERBOSE = True

# this controls how DB response in case of sql commit error:
# if DEBUG_MODE is on, when error in commit happens, simply raise error and exit program
# on the contrary, when DB is not in this mode, any operations within the transaction
# that causes commit error will be roll-backed. Error message will be shown as
# a warning on screen
DEBUG_MODE = True

# link to default user profile background
DEFAULT_PROFILE_BACKGROUND_LINK = "static/profile_background/default_background.jpg"
# link to default user avatar
DEFAULT_USER_AVATAR_LINK = "static/avatar/ashley_gibbon.png"


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
    # commit failure
    COMMIT_ERROR = 8
    # email exists in DB
    EMAIL_USED = 9


class Modification(enum.Enum):
    """
    Defining the type of modification to be done
    """
    MODIFY_ADD = 0
    MODIFY_DELETE = 1


engine = create_engine(DBPATH)
Session = sessionmaker(engine)

# starting timestamp of UTC
EPOCH = datetime.datetime.utcfromtimestamp(0)


# maximum time length for session without new action -- set as 30min
# USER_SESSION_EXPIRE_INTERVAL = datetime.timedelta(weeks=10)


def try_to_commit(trans):
    """
    Call commit for a transaction (i.e. conn)

    :param trans: The transaction to be committed
    :return: True if the transaction is committed.
            In case of commit error, if DEBUG_MODE is False, then let error raised
            and program terminates itself. Otherwise, show error message as a
            warning and rollback this transaction
    """
    if DEBUG_MODE:
        trans.commit()
        return True

    try:
        trans.commit()
        return True
    except sqlalchemy.exc.SQLAlchemyError:
        # errors while commit, show as warning
        warnings.warn(traceback.format_exc())
        trans.rollback()
        warnings.warn("Transaction is roll-backed")
    return False


def add_user(username, password, email, teaching_areas: dict = None,
             bio=None, avatar_link=DEFAULT_USER_AVATAR_LINK,
             profile_background_link=DEFAULT_PROFILE_BACKGROUND_LINK):
    """
    Add a new user to table user and add teaching_areas to
    user_teaching_areas table

    :param username: username
    :param avatar_link: The link to avatar, default is null
    :param profile_background_link: The link of profile background, default is null
    :param password: The original password of new user
    :param bio: The bio of new user
    :param email: The email address of that user. This field is unique for each user.
    :param teaching_areas: Mapping of teaching area - [is_public, grade (optional)] list
            e.g. [Subject.ENGLISH: [True], Subject.MATHS_C: [False, Grade.YEAR_1]
    :return The id of the new user if success.
            ErrorCode.EMAIL_USED if email is occupied
            ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
    """
    email = email.lower()
    user = User(username=username, avatar_link=avatar_link,
                hash_password=generate_password_hash(password, "sha256"),
                email=email, bio=bio,
                created_at=datetime.datetime.now(tz=pytz.timezone("Australia/Brisbane")),
                profile_background_link=profile_background_link)

    with Session() as conn:
        if conn.query(User).filter_by(email=email).one_or_none():
            warnings.warn("This email address is registered")
            return ErrorCode.EMAIL_USED

        # phase 1: add a new user
        conn.add(user)
        if not try_to_commit(conn):
            warnings.warn(f"failed to commit user creation {username}")
            return ErrorCode.COMMIT_ERROR

        # phase 2: find id of new user -- using email,
        # then update teaching_areas table
        user = conn.query(User).filter_by(email=email).one()

        # user_session = UserSession(uid=user.uid)
        # conn.add(user_session)
        # conn.commit()

        if teaching_areas:
            modify_user_teaching_areas(uid=user.uid, conn=conn, teaching_areas=teaching_areas,
                                       modification=Modification.MODIFY_ADD)
        if not try_to_commit(conn):
            warnings.warn(f"failed to commit user creation {username}")
            conn.delete(user)
            # rollback obsolete user object
            conn.commit()
            return ErrorCode.COMMIT_ERROR
        if VERBOSE:
            print(f"User {username} created")
        return user.uid


def modify_user_teaching_areas(uid, conn, modification: Modification,
                               teaching_areas: dict = None):
    """
    Modify a sequence of teaching areas to user instance

    :param uid: The id of user
    :param conn: The Session() initiated
    :param modification: Add or Delete
    :param teaching_areas: Mapping of teaching area - [is_public, grade (optional)] list
            e.g. [Subject.ENGLISH: [True], Subject.MATHS_C: [False, Grade.YEAR_1]
    """
    for area, info in teaching_areas.items():
        grade = None
        if len(info) == 2:
            is_public, grade = info[0], info[1]
        else:
            is_public = info[0]
        if isinstance(area, Subject):
            if modification == Modification.MODIFY_ADD:
                # insert new user teaching areas
                new_teach_area = UserTeachingAreas(uid=uid, teaching_area=area,
                                                   is_public=is_public, grade=grade)
                conn.add(new_teach_area)
            else:
                # delete user teaching areas
                teaching_area = conn.query(UserTeachingAreas). \
                    filter_by(uid=uid, teaching_area=area,
                              is_public=is_public, grade=grade).one_or_none()
                if teaching_area:
                    conn.delete(teaching_area)


def modify_user(uid: int, username=None, password=None, email=None,
                teaching_areas_to_add: dict = None,
                teaching_areas_to_delete: dict = None,
                profile_background_link: str = "NULL",
                bio: str = "NULL", avatar_link: str = "NULL"):
    """
    Modify the information of a user instance

    :param uid: The id of user to be modified
    :param username: The new username
    :param password: The new password (not hashed)
    :param email: The new email address
    :param teaching_areas_to_add: Mapping of teaching area
                                - [is_public, grade (optional)] list
                                The new teaching areas to be added
                                e.g. [Subject.ENGLISH: [True],
                                 Subject.MATHS_C: [False, Grade.YEAR_1]
    :param teaching_areas_to_delete: Mapping of teaching area
                                - [is_public, grade (optional)] list
                                The new teaching areas to be deleted
                                e.g. [Subject.ENGLISH: [True],
                                 Subject.MATHS_C: [False, Grade.YEAR_1]
    :param profile_background_link: The new link to profile_background image.
                                    By default, "NULL" does not change profile link;
                                    None turns the profile background back to default one
    :param bio: The new bio. By default, "NULL" does not change the bio.
                None clears the original bio
    :param avatar_link: The new link to avatar. By default, "NULL" does not change
                        link to avatar. None turns the avatar link to default one
    :return void on success
            ErrorCode.INVALID_USER if cid is invalid
            ErrorCode.EMAIL_USED if new email is already registered
            ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
    """
    with Session() as conn:
        user = conn.query(User).filter_by(uid=uid).one_or_none()
        if not user:
            warnings.warn("Invalid uid")
            return ErrorCode.INVALID_USER

        if email:
            if isinstance(User, get_user(email)):
                warnings.warn("email is already registered")
                return ErrorCode.EMAIL_USED
            user.email = email
        if username:
            user.username = username
        if password:
            user.hash_password = generate_password_hash(password, "sha256")
        if profile_background_link != "NULL":
            if not profile_background_link:
                user.profile_background_link = DEFAULT_PROFILE_BACKGROUND_LINK
            else:
                user.profile_background_link = profile_background_link
        if bio != "NULL":
            if not bio:
                user.bio = None
            else:
                user.bio = bio
        if avatar_link != "NULL":
            if not avatar_link:
                user.avatar_link = DEFAULT_USER_AVATAR_LINK
            else:
                user.avatar_link = avatar_link

        conn.add(user)

        if teaching_areas_to_add:
            modify_user_teaching_areas(uid=uid, conn=conn, teaching_areas=teaching_areas_to_add,
                                       modification=Modification.MODIFY_ADD)
        if teaching_areas_to_delete:
            modify_user_teaching_areas(uid=uid, conn=conn, teaching_areas=teaching_areas_to_delete,
                                       modification=Modification.MODIFY_DELETE)

        if not try_to_commit(conn):
            warnings.warn("Error committing")
            return ErrorCode.COMMIT_ERROR


def remove_resource(rid: int):
    """
    Remove a resource entity. This also removes all the records relevant to
    this resource entity in ResourceTagRecord, ResourceThumbnail,
    ResourceVoteInfo, ResourceCreater, ResourcePersonnel, ResourceComment,
    ResourceCommentReply tables

    :param rid: The id of resource to be removed
    """
    with Session() as conn:
        resource = conn.query(Resource).filter_by(rid=rid).one_or_none()
        if resource:
            conn.delete(resource)
            conn.commit()


def get_user(email):
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
            if VERBOSE:
                warnings.warn(f"email {email} is registered by user uid = {user.uid}")

            return user
        warnings.warn(f"No user has email {email}")
        return ErrorCode.INVALID_USER


# def is_user_session_expired(uid: int):
#     """
#     Check if a user session is expired
#
#     :param uid: The user id to check
#     :return True if the session is expired, False otherwise
#     """
#     with Session() as conn:
#         user_session = conn.query(UserSession).filter_by(uid=uid).one_or_none()
#         # NOTE: tz = pytz.timezone("Australia/Brisbane") does not work in sqlite
#         current = datetime.datetime.now(tz=pytz.timezone("Australia/Brisbane"))
#         # print(f"current time = {current},last_action_time = {user_session.last_action_time}")
#         return current - user_session.last_action_time > USER_SESSION_EXPIRE_INTERVAL


# def renew_user_session(uid: int):
#     """
#     Create a new session instance in Session table, if not exists;
#     otherwise, update last_action_time to current datetime
#
#     Call this when user sign in or a function requires uid and is_user_session_expired()
#     is false
#
#     :param uid: effective user id
#     :return on success, None is returned.
#             If uid does not exist, it returns ErrorCode.INVALID_USER
#     """
#     with Session() as conn:
#         user = conn.query(User).filter_by(uid=uid).one_or_none()
#         if not user:
#             print(f"user {uid} does not exists")
#             return ErrorCode.INVALID_USER
#
#         user_session = conn.query(UserSession).filter_by(uid=uid).one_or_none()
#         if not user_session:
#             user_session = UserSession(uid=uid)
#         else:
#             user_session.last_action_time = datetime.datetime.now(
#                 tz=pytz.timezone("Australia/Brisbane"))
#         conn.add(user_session)
#         conn.commit()
#         if verbose:
#             print(f"user {uid} last action time updated")


def add_tag(tag_name, tag_description=None):
    """
    Add a new tag to Database

    :param tag_name: The name of the new tag
    :param tag_description: The description of the tag (optional)
    :return On success, the id of the new tag is returned
            ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
    """
    tag = Tag(tag_name=tag_name, tag_description=tag_description)
    with Session() as conn:
        if conn.query(Tag).filter_by(tag_name=tag_name).one_or_none():
            warnings.warn("tag already exists")
            return

        conn.add(tag)
        if not try_to_commit(conn):
            warnings.warn(f"tag {tag_name} creation failed")
            return ErrorCode.COMMIT_ERROR
        print(f"tag {tag_name} added") if VERBOSE else None

        return conn.query(Tag).filter_by(tag_name=tag_name).one().tag_id


def get_tags() -> dict:
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
                 grade: Grade, creaters_id: list = None, is_public=True,
                 private_personnel_id: list = None, tags_id: list = None,
                 description=None, resource_thumbnail_links: list = None):
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
            ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
    """
    if resource_thumbnail_links is None:
        resource_thumbnail_links = []
    if tags_id is None:
        tags_id = []
    if private_personnel_id is None:
        private_personnel_id = []
    if creaters_id is None:
        creaters_id = []

    if not is_public and not private_personnel_id:
        warnings.warn("Please specify the User allowed to access this resource")
        return ErrorCode.INCORRECT_PERSONNEL

    resource = Resource(title=title, resource_link=resource_link, grade=grade,
                        difficulty=difficulty, subject=subject, is_public=is_public,
                        description=description)

    with Session() as conn:

        # phase 1: add new resource
        conn.add(resource)
        if not try_to_commit(conn):
            warnings.warn(f"resource {title} creation failed")
            return ErrorCode.COMMIT_ERROR

        # phase 2: find the new row, update private_resource_personnel info, tag info
        # and resource_creater table, resource_thumbnail
        resource = conn.query(Resource).filter_by(resource_link=resource_link).one()

        # get rid of duplicate
        creaters_id = list(set(creaters_id))
        if resource_thumbnail_links:
            resource_thumbnail_links = list(set(resource_thumbnail_links))
        if private_personnel_id:
            private_personnel_id = list(set(private_personnel_id))
        if tags_id:
            tags_id = list(set(tags_id))

        for i in resource_thumbnail_links:
            thumbnail = ResourceThumbnail(rid=resource.rid, thumbnail_link=i)
            conn.add(thumbnail)

        for i in creaters_id:
            creater_instance = ResourceCreater(rid=resource.rid, uid=i)
            conn.add(creater_instance)

            # creaters must have access to this resource
            if not is_public and i not in private_personnel_id:
                private_access = PrivateResourcePersonnel(rid=resource.rid, uid=i)
                conn.add(private_access)

        if not is_public:
            for uid in private_personnel_id:
                private_access = PrivateResourcePersonnel(rid=resource.rid, uid=uid)
                conn.add(private_access)

        if tags_id:
            for i in tags_id:
                tag_record = ResourceTagRecord(rid=resource.rid, tag_id=i)
                conn.add(tag_record)
        if not try_to_commit(conn):
            warnings.warn(f"resource {title} creation failed")
            # roll back process
            conn.delete(resource)
            conn.commit()
            return ErrorCode.COMMIT_ERROR
        if VERBOSE:
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


def modify_resource_personnel(rid, uid, modification: Modification):
    """
    Add/delete a person from a resource personnel

    :param rid: The resource to be modified
    :param uid: The user to add/delete
    :param modification: Add or delete
    :return void on success.
            ErrorCode.INVALID_USER/-RESOURCE if uid/rid is incorrect
            ErrorCode.INCORRECT_PERSONNEL if mode is delete and personnel info not exist
            ErrorCode.USER_SESSION_EXPIRED when user session is expired
    """
    user, resource = get_user_and_resource_instance(uid=uid, rid=rid)
    if not user:
        warnings.warn("uid is invalid")
        return ErrorCode.INVALID_USER
    elif not resource:
        warnings.warn("rid is invalid")
        return ErrorCode.INVALID_RESOURCE

    # check user session and renew
    # if is_user_session_expired(uid):
    #     print("User session expired")
    #     return ErrorCode.USER_SESSION_EXPIRED
    # renew_user_session(uid)

    with Session() as conn:
        if modification == Modification.MODIFY_DELETE:
            # delete
            personnel = conn.query(PrivateResourcePersonnel).filter_by(uid=uid, rid=rid). \
                one_or_none()
            if not personnel:
                warnings.warn("Delete failed: User not in personnel")
                return ErrorCode.INCORRECT_PERSONNEL
            conn.delete(personnel)
            msg = "deleted"
        else:
            # add
            personnel = PrivateResourcePersonnel(uid=uid, rid=rid)
            conn.add(personnel)
            msg = "added"
        if not try_to_commit(conn):
            warnings.warn(f"User {uid} cannot be added to personnel of resource {rid}")
            return ErrorCode.COMMIT_ERROR
        print(f"user {uid} is {msg} from/to personnel of resource {rid}")


def modify_resource(rid: int, title=None, resource_link=None,
                    difficulty: ResourceDifficulty = None, subject: Subject = None,
                    grade: Grade = None, creaters_id: list = None, is_public: bool = None,
                    ids_to_delete_from_personnel: list = None, description="NULL",
                    ids_to_add_to_personnel: list = None, tags_id: list = None,
                    resource_thumbnail_links: list = None):
    """
    This method is used to modify the information of a resource

    Notes:
    1. Only fill in the parameters that needed to be modified.
    2. For creaters_id, tags_id and resource_thumbnail_links lists,
    every element will be checked, if that element already exists for this resource,
    it will then be removed; if an element does not exist for this resource,
    it will then be added.

    :param rid: The id of resource to be modified
    :param title: The new title
    :param resource_link: The new resource link
    :param difficulty: The new difficulty tag
    :param subject: The new subject tag
    :param grade: The new grade tag
    :param creaters_id: Creater ids to be removed/added
    :param is_public: whether the resource is made public or not
    :param ids_to_delete_from_personnel: The private personnel ids to be removed
    :param ids_to_add_to_personnel: The private personnel ids to be added
    :param tags_id: The tag ids to be removed/added
    :param description: The new description of the resource. By default, "NULL" does
                        not change description contents; None clears original description
    :param resource_thumbnail_links: The links of thumbnails to be removed/added
    :return on success, void is returned.
            ErrorCode.INVALID_RESOURCE is rid is invalid
            ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
    """
    with Session() as conn:
        resource = conn.query(Resource).filter_by(rid=rid).one_or_none()
        if not resource:
            warnings.warn("Invalid rid")
            return ErrorCode.INVALID_RESOURCE
        if title:
            resource.title = title
        if resource_link:
            resource.resource_link = resource_link
        if difficulty:
            resource.difficulty = difficulty
        if subject:
            resource.subject = subject
        if grade:
            resource.grade = grade
        if description and description != "NULL":
            resource.description = description
        elif not description:
            resource.description = None

        if creaters_id:
            creaters = conn.query(ResourceCreater).filter(
                ResourceCreater.uid.in_(creaters_id),
                ResourceCreater.rid == rid).all()
            deleted_creaters = set()
            for i in creaters:
                conn.delete(i)
                deleted_creaters.add(i.uid)
            new_creaters = list(set(creaters_id).difference(deleted_creaters))
            if new_creaters:
                for i in new_creaters:
                    creater = ResourceCreater(rid=rid, uid=i)
                    conn.add(creater)

        if tags_id:
            tags = conn.query(ResourceTagRecord).filter(
                ResourceTagRecord.rid == rid,
                ResourceTagRecord.tag_id.in_(tags_id))
            deleted_tags = set()
            for i in tags:
                conn.delete(i)
                deleted_tags.add(i.tag_id)
            new_tags = list(set(tags_id).difference(deleted_tags))
            if new_tags:
                for i in new_tags:
                    tag = ResourceTagRecord(rid=rid, tag_id=i)
                    conn.add(tag)

        if resource_thumbnail_links:
            thumbnails = conn.query(ResourceThumbnail).filter(
                ResourceThumbnail.rid == rid,
                ResourceThumbnail.thumbnail_link.in_(resource_thumbnail_links))
            deleted_thumbnails = set()
            for i in thumbnails:
                deleted_thumbnails.add(i.thumbnail_link)
                conn.delete(i)
            new_thumbnails = list(set(
                resource_thumbnail_links).difference(deleted_thumbnails))
            if new_thumbnails:
                for i in new_thumbnails:
                    thumbnail = ResourceThumbnail(rid=rid, thumbnail_link=i)
                    conn.add(thumbnail)

        # commit before making changes to resource access permission
        conn.add(resource)

        # test: here fake unique constraint violation
        # test = conn.query(Resource).filter_by(rid=2).first()
        # test.title = "Temp title"
        # conn.add(test)

        if not try_to_commit(conn):
            warnings.warn("Error committing")
            return ErrorCode.COMMIT_ERROR

        if is_public is not None or \
                ids_to_add_to_personnel or ids_to_delete_from_personnel:
            if not resource.is_public:
                if is_public is not None and is_public:
                    # originally private, now public
                    resource.is_public = True
                    for i in conn.query(PrivateResourcePersonnel). \
                            filter_by(rid=rid).all():
                        conn.delete(i)
                elif is_public is None:
                    # modify the personnel for a private resource
                    if ids_to_add_to_personnel:
                        # only add new records to personnel
                        for i in ids_to_add_to_personnel:
                            modify_resource_personnel(
                                rid=rid, uid=i,
                                modification=Modification.MODIFY_ADD)
                    if ids_to_delete_from_personnel:
                        # only delete records from personnel
                        for i in ids_to_delete_from_personnel:
                            modify_resource_personnel(
                                rid=rid, uid=i,
                                modification=Modification.MODIFY_DELETE)
            else:
                # resource is originally public
                if not is_public:
                    # now change to private and add users allow to view the resource
                    # to personnel
                    resource.is_public = False
                    # creaters must have access to private resource
                    creaters = conn.query(ResourceCreater).filter_by(rid=rid).all()
                    if not ids_to_add_to_personnel:
                        ids_to_add_to_personnel = []
                    ids_to_add_to_personnel = set(ids_to_add_to_personnel)
                    for i in creaters:
                        ids_to_add_to_personnel.add(i.uid)
                    for i in ids_to_add_to_personnel:
                        modify_resource_personnel(
                            rid=rid, uid=i, modification=Modification.MODIFY_ADD)
        conn.add(resource)
        if not try_to_commit(conn):
            warnings.warn("Error committing")
            return ErrorCode.COMMIT_ERROR


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
        warnings.warn("uid is invalid")
        return ErrorCode.INVALID_USER
    elif not resource or resource.is_public:
        warnings.warn("rid is invalid or resource is public")
        return ErrorCode.INVALID_RESOURCE

    # check user session and renew
    # if is_user_session_expired(uid):
    #     print("User session expired")
    #     return ErrorCode.USER_SESSION_EXPIRED
    # renew_user_session(uid)

    with Session() as conn:
        return conn.query(PrivateResourcePersonnel).filter_by(uid=uid, rid=rid). \
                   one_or_none() is not None


def find_resources(title_type="like", title=None,
                   created_type="after", created=EPOCH,
                   difficulty=None, subject=None,
                   vote_type="more", votes=None,
                   grade=None, email=None, sort_by="natural"
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
        :param sort_by         : The sort by parameter
            Valid values are ["natural","newest","upvotes"].
            Defaults to "natural".
    """
    # Args Checking
    if title_type not in ["like", "exact"]:
        title_type = "like"
    if created_type not in ["after", "before"]:
        created_type = "after"
    if vote_type not in ["more", "less"]:
        vote_type = "more"
    if sort_by not in ["Natural", "newest", "upvotes"]:
        sort_by = "natural"

    with Session() as conn:
        # get User if exists
        user = conn.query(User).filter_by(email=email).one_or_none()

        resources = conn.query(Resource)

        if title is not None and isinstance(title, str):
            if title_type == "like":
                resources = resources.filter(Resource.title.ilike(f'%{title}%'))
            else:
                resources = resources.filter_by(title=title)

        if created != EPOCH and isinstance(created, datetime.datetime):
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

        if sort_by != "natural":
            if sort_by == "newest":
                resources = resources.order_by(Resource.created_at)
            elif sort_by == "upvotes":
                resources = resources.order_by(Resource.upvote_count)

        if user is None:
            resources = resources.filter_by(is_public=True)
            result = resources.all()
        else:
            result = filter(lambda res: user_has_access_to_resource(user.uid, res.rid), resources.all())

    return result


def find_channels(title_type="like", channel_name=None,
                  subject: Subject = None, visibility: ChannelVisibility = None,
                  grade: Grade = None, caller_uid=None, admin_uid=None, tag_ids: list = None):
    """
    find_channels method mainly follows the style of find_resources() and is capable
    of finding channels that match all the conditions specified in parameter values

    If caller_uid is supplied, it returns channels this caller has access to.

    If admin_uid is supplied, it returns channel this admin controls

    * if both caller_uid and admin_uid are supplied, the return results will be
    channels viewable by caller_uid

    When no parameters are passed to the method, it returns all channels with
    ChannelVisibility == PUBLIC
    :param title_type: SQL search restriction for the title.
            Valid values are ["like","exact"]
    :param channel_name: The name of the channel to look up
    :param subject: The subject the channel is related to.
    :param visibility: The visibility of the channel
    :param grade: The grade the channel is related to
    :param caller_uid: The user who call find channels function
    :param admin_uid: The admin id of channel
    :param tag_ids: The list of tag ids the channel is related to
    :return List of Channel objects
    """
    # Args Checking
    if tag_ids is None:
        tag_ids = []

    if title_type not in ["like", "exact"]:
        title_type = "like"

    with Session() as conn:
        # list of channel id projects
        channel_id_obj = []
        if tag_ids:
            channel_id_obj = conn.query(ChannelTagRecord).filter(
                ChannelTagRecord.tag_id.in_(tag_ids)).all()
        if channel_id_obj:
            # find channels that match the tags, if any
            cids = set()
            for i in channel_id_obj:
                cids.add(i.cid)
            cids = tuple(cids)
            channels = conn.query(Channel).filter(Channel.cid.in_(cids))
        else:
            # no tag_id supplied, get all the channels
            channels = conn.query(Channel)

        if subject:
            channels = channels.filter_by(subject=subject)
        if grade:
            channels = channels.filter_by(grade=grade)
        if visibility:
            channels = channels.filter_by(visibility=visibility)

        if channel_name:
            if title_type == "like":
                channels = channels.filter(Channel.name.ilike(f'%{channel_name}%'))
            else:
                # exact match
                channels = channels.filter_by(name=channel_name)

        if caller_uid:
            # find all private channels this caller has access to
            personnel = conn.query(ChannelPersonnel).filter_by(uid=caller_uid)
            accessible = set()
            for i in personnel:
                accessible.add(i.cid)
            accessible = tuple(accessible)

            # return channels that this user can access: either public or
            # private but accessible
            channels = channels.filter(or_(Channel.visibility == ChannelVisibility.PUBLIC,
                                           Channel.cid.in_(accessible)))
        elif admin_uid:
            channels = channels.filter_by(admin_uid=admin_uid)

        return channels.all()


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
            ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
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
                if VERBOSE:
                    warnings.warn("user cannot vote the same item twice")
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
        if not try_to_commit(conn):
            warnings.warn(f"user {uid} vote resource {rid} failed")
            return ErrorCode.COMMIT_ERROR
        if VERBOSE:
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
            ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
    """
    res = check_user_and_resource_validity_and_renew_user_session(uid=uid, rid=rid)
    if isinstance(res, ErrorCode):
        return res

    with Session() as conn:
        resource_view = ResourceView(rid=rid, uid=uid)
        conn.add(resource_view)
        if not try_to_commit(conn):
            warnings.warn(f"User {uid} view resource {rid} record cannot be committed")
            return ErrorCode.COMMIT_ERROR
    print(f"user {uid} viewed resource {rid}") if VERBOSE else None


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
        warnings.warn("rid is invalid")
        return ErrorCode.INVALID_RESOURCE
    elif not user:
        warnings.warn("uid is invalid")
        return ErrorCode.INVALID_USER

    # check user session and renew
    # if is_user_session_expired(uid):
    #     print("User session expired")
    #     return ErrorCode.USER_SESSION_EXPIRED
    # renew_user_session(uid)

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
            ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
    """
    res = check_user_and_resource_validity_and_renew_user_session(uid=uid, rid=rid)
    if isinstance(res, ErrorCode):
        return res

    created_at = datetime.datetime.now(tz=pytz.timezone("Australia/Brisbane"))
    with Session() as conn:
        resource_comment = ResourceComment(uid=uid, rid=rid, comment=comment, created_at=created_at)
        conn.add(resource_comment)
        if not try_to_commit(conn):
            warnings.warn(f"User {uid} comment resource {rid} failed")
            return ErrorCode.COMMIT_ERROR
    if VERBOSE:
        print(f"user {uid} commented resource {rid}")
    return conn.query(ResourceComment). \
        filter_by(uid=uid, rid=rid, created_at=created_at).one().resource_comment_id


def remove_resource_comment(resource_comment_id: int):
    """
    Remove a resource comment, if resource_comment_id is valid

    :param resource_comment_id: The id of the resource comment to be removed
    """
    with Session() as conn:
        comment = conn.query(ResourceComment).\
                filter_by(resource_comment_id=resource_comment_id).one_or_none()
        if comment:
            conn.delete(comment)
            try_to_commit(conn)


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
            warnings.warn("resource comment id is invalid")
            return ErrorCode.INVALID_RESOURCE
        elif not user:
            warnings.warn("uid is invalid")
            return ErrorCode.INVALID_USER

        # check user session and renew
        # if is_user_session_expired(uid):
        #     print("User session expired")
        #     return ErrorCode.USER_SESSION_EXPIRED
        # renew_user_session(uid)

        reply_to_comment = ResourceCommentReply(resource_comment_id=resource_comment_id,
                                                reply=reply, uid=uid)
        conn.add(reply_to_comment)
        if not try_to_commit(conn):
            warnings.warn(f"user {uid} failed to reply to resource comment {resource_comment_id}")

        if VERBOSE:
            print(f"user {uid} replied to resource comment {resource_comment_id}")


def remove_resource_comment_reply(resource_comment_id: int, created_at):
    """
    Remove a resource comment reply. If any matches for
     (resource_comment_id, created_at)

     * Since resource comment reply does not have a unique identifier,
     this operation may be non-deterministic
    """
    with Session() as conn:
        resource_comment_reply = conn.query(ResourceCommentReply).\
                filter_by(resource_comment_id=resource_comment_id,
                          created_at=created_at).one_or_none()
        if resource_comment_reply:
            conn.delete(resource_comment_reply)
            try_to_commit(conn)


def get_resource_comments(rid: int) -> list:
    """
    Load and returns a list of resource comments for a resource

    :param rid: The resource id
    :return a list of all comment instances to this resource, if any
    """
    with Session() as conn:
        return conn.query(ResourceComment).filter_by(rid=rid).all()


def get_resource_comment_replies(resource_comment_instance_list: list) -> dict:
    """
    Get a dict of resource comment replies of the form
    resource_comment instance -> [resource_comment_reply objects with that resource_comment_id]

    :param resource_comment_instance_list: The list of resource_comment instances,
            obtained typically from get_resource_comments()
    return a dictionary of the form
            resource_comment instance -> [resource_comment_reply objects with that resource_comment_id]
    """
    out = {}
    with Session() as conn:
        for i in resource_comment_instance_list:
            replies = conn.query(ResourceCommentReply).filter_by(
                resource_comment_id=i.resource_comment_id).all()
            if replies:
                out[i] = replies
        return out


def create_channel(name, visibility: ChannelVisibility, admin_uid, subject: Subject = None,
                   grade: Grade = None, description=None, tags_id: list = None,
                   personnel_id: list = None):
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
            ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
    """
    if personnel_id is None:
        personnel_id = []
    if tags_id is None:
        tags_id = []

    with Session() as conn:
        admin = conn.query(User).filter_by(uid=admin_uid).one_or_none()
        if not admin:
            warnings.warn("Admin id is invalid")
            return ErrorCode.INVALID_USER

        # check user session and renew
        # if is_user_session_expired(admin_uid):
        #     print("User session expired")
        #     return ErrorCode.USER_SESSION_EXPIRED
        # renew_user_session(admin_uid)

        # phase 1: create instance
        channel = Channel(name=name, visibility=visibility, admin_uid=admin_uid,
                          subject=subject, grade=grade, description=description)
        conn.add(channel)
        if not try_to_commit(conn):
            warnings.warn(f"channel {name} cannot be created")
            return ErrorCode.COMMIT_ERROR

        # phase 2: use name (unique) to retrieve instance for next step operation
        channel = conn.query(Channel).filter_by(name=name).one()
        # get rid of duplicate
        if tags_id:
            tags_id = list(set(tags_id))
        if personnel_id:
            personnel_id = list(set(personnel_id))

        for i in tags_id:
            channel_tag_record = ChannelTagRecord(tag_id=i, cid=channel.cid)
            conn.add(channel_tag_record)

        if visibility != ChannelVisibility.PUBLIC:
            if admin_uid not in personnel_id:
                # add admin to personnel if not in personnel id yet
                personnel = ChannelPersonnel(cid=channel.cid, uid=admin_uid)
                conn.add(personnel)
            for i in personnel_id:
                personnel = ChannelPersonnel(cid=channel.cid, uid=i)
                conn.add(personnel)

        if not try_to_commit(conn):
            warnings.warn(f"channel {name} cannot be created")
            # delete obsolete channel object
            conn.delete(channel)
            conn.commit()
            return ErrorCode.COMMIT_ERROR

        if VERBOSE:
            print(f"Channel {name} created")
        return channel.cid


def get_user_and_channel_instance(uid, cid):
    """
    Try to get instances User and Channel using provided uid and rid

    Can use this to check if the (uid, cid) is valid

    :param uid: The user id
    :param cid: The channel id
    :return On success, the tuple of form User, Channel is returned
            ErrorCode.INVALID_USER/-CHANNEL if uid/rid is incorrect
    """
    with Session() as conn:
        user = conn.query(User).filter_by(uid=uid).one_or_none()
        channel = conn.query(Channel).filter_by(cid=cid).one_or_none()
        if not user:
            warnings.warn("uid invalid")
            return ErrorCode.INVALID_USER
        if not channel:
            warnings.warn("cid invalid")
            return ErrorCode.INVALID_CHANNEL
    return user, channel


def modify_channel_personnel(uid, cid, modification: Modification):
    """
    Add/ delete a user from/to a private personnel

    :param cid: The channel to be modified
    :param uid: The user to add/delete
    :param modification: Add or delete
    :return void on success.
            ErrorCode.INVALID_USER/-CHANNEL if uid/rid is incorrect
            ErrorCode.INCORRECT_PERSONNEL if mode is delete and personnel info not exist
            ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
    """
    res = get_user_and_channel_instance(uid=uid, cid=cid)
    if isinstance(res, ErrorCode):
        return res
    # if channel.visibility == ChannelVisibility.PUBLIC:
    #     warnings.warn("Channel is public")
    #     return ErrorCode.INVALID_CHANNEL

    with Session() as conn:
        if modification == Modification.MODIFY_DELETE:
            # delete
            personnel = conn.query(ChannelPersonnel).filter_by(uid=uid, cid=cid). \
                one_or_none()
            if not personnel:
                warnings.warn("personnel does not exists")
                return ErrorCode.INCORRECT_PERSONNEL
            conn.delete(personnel)
            msg = "deleted"
        else:
            # add
            personnel = ChannelPersonnel(cid=cid, uid=uid)
            conn.add(personnel)
            msg = "created"

        if not try_to_commit(conn):
            warnings.warn(f"user {uid} is failed to be {msg} from/to personnel of channel {cid}")
            return ErrorCode.COMMIT_ERROR
        if VERBOSE:
            print(f"user {uid} is {msg} from/to personnel of channel {cid}")


def modify_channel(cid: int, name=None, visibility: ChannelVisibility = None,
                   admin_uid=None, subject: Subject = Subject.NULL,
                   grade: Grade = Grade.NULL, description="NULL", tags_id: list = None,
                   ids_to_delete_from_personnel: list = None,
                   ids_to_add_to_personnel: list = None):
    """
        This method is used to modify the information of a channel

        Notes:
        1. Only fill in the parameters that needed to be modified.
        2. For tags_id lists, every element will be checked, if that element
        already exists for this resource, it will then be removed; if an element
        does not exist for this resource, it will then be added.

        :param cid: The id of channel to be modified
        :param name: The new name of the channel
        :param visibility: The new visibility of the channel
        :param subject: The new subject tag. By default, Subject.NULL does not change
                        the subject tag; None clears original subject tag
        :param grade: The new grade tag. By default, Grade.NULL does not change
                        the grade tag; None clears original grade tag
        :param admin_uid: The new admin of this channel
        :param ids_to_delete_from_personnel: The private personnel ids to be removed
        :param ids_to_add_to_personnel: The private personnel ids to be added
        :param tags_id: The tag ids to be removed/added
        :param description: The new description of the channel. By default, "NULL" does
                            not change description contents; None clears original description
        :return on success, void is returned.
                ErrorCode.INVALID_CHANNEL if cid is invalid
                ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
        """
    with Session() as conn:
        channel = conn.query(Channel).filter_by(cid=cid).one_or_none()
        if not channel:
            warnings.warn("Invalid cid")
            return ErrorCode.INVALID_CHANNEL
        if name:
            channel.name = name
        if admin_uid:
            channel.admin_uid = admin_uid
        if subject != Subject.NULL:
            channel.subject = subject
        if grade != Grade.NULL:
            channel.grade = grade
        if description != "NULL":
            channel.description = description
        if tags_id:
            old_tags = conn.query(ChannelTagRecord).filter_by(cid=cid).all()
            deleted_tags = set()
            tags_id = set(tags_id)
            for i in old_tags:
                if i.tag_id in tags_id:
                    conn.delete(i)
                    deleted_tags.add(i.tag_id)
            new_tags = tags_id.difference(deleted_tags)
            for i in new_tags:
                tag = ChannelTagRecord(cid=cid, tags_id=i)
                conn.add(tag)

        if visibility:
            if visibility == ChannelVisibility.PUBLIC and \
                    channel.visibility != ChannelVisibility.PUBLIC:
                # originally private, now public
                channel.visibility = visibility
                conn.query(ChannelPersonnel).filter_by(cid=cid).delete()
            elif visibility != ChannelVisibility.PUBLIC and \
                    channel.visibility == ChannelVisibility.PUBLIC:
                # originally public, now private
                # admin must be in the channel personnel
                modify_channel_personnel(uid=admin_uid, cid=cid,
                                         modification=Modification.MODIFY_ADD)
        # commit before proceed to personnel modification
        conn.add(channel)
        if not try_to_commit(conn):
            warnings.warn("Error committing")
            return ErrorCode.COMMIT_ERROR

        # now deal with ids add/delete to/from personnel
        channel = conn.query(Channel).filter_by(cid=cid).one_or_none()
        if channel.visibility != ChannelVisibility.PUBLIC:
            if ids_to_add_to_personnel:
                for i in ids_to_add_to_personnel:
                    personnel = ChannelPersonnel(cid=cid, uid=i)
                    conn.add(personnel)
            if ids_to_delete_from_personnel:
                for i in ids_to_delete_from_personnel:
                    personnel = conn.query(ChannelPersonnel).\
                        filter_by(cid=cid, uid=i).one_or_none()
                    if personnel:
                        conn.delete(personnel)
        if not try_to_commit(conn):
            warnings.warn("Error committing")
            return ErrorCode.COMMIT_ERROR


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
        res = get_user_and_channel_instance(uid=uid, cid=cid)
        if isinstance(res, ErrorCode):
            return res
        channel = res[1]
        if channel.visibility == ChannelVisibility.PUBLIC:
            warnings.warn("Channel is public")
            return ErrorCode.INVALID_CHANNEL

        # check user session and renew
        # if is_user_session_expired(uid):
        #     print("User session expired")
        #     return ErrorCode.USER_SESSION_EXPIRED
        # renew_user_session(uid)

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
            ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
    """
    if not channel_name and not cid:
        warnings.warn("Please supply channel name or cid")
        return ErrorCode.INVALID_CHANNEL

    with Session() as conn:
        if not conn.query(User).filter_by(uid=uid).one_or_none():
            warnings.warn("invalid uid")
            return ErrorCode.INVALID_USER

        # check user session and renew
        # if is_user_session_expired(uid):
        #     print("User session expired")
        #     return ErrorCode.USER_SESSION_EXPIRED
        # renew_user_session(uid)

        if cid:
            channel = conn.query(Channel).filter_by(cid=cid).one_or_none()
        else:
            channel = conn.query(Channel).filter_by(name=channel_name).one_or_none()

        if not channel:
            warnings.warn("Invalid channel name")
            return ErrorCode.INVALID_CHANNEL

        if channel.visibility != ChannelVisibility.PUBLIC:
            # not public, check if user is in the personnel
            personnel = conn.query(ChannelPersonnel). \
                filter_by(cid=channel.cid, uid=uid).one_or_none()
            if not personnel:
                warnings.warn(f"User {uid} is not in channel {channel.name}")
                return ErrorCode.INCORRECT_PERSONNEL

        channel_post = ChannelPost(cid=channel.cid, title=title, init_text=text)
        conn.add(channel_post)
        if not try_to_commit(conn):
            warnings.warn(f"post {title} by user {uid} failed to be added to {channel.name}")
            return ErrorCode.COMMIT_ERROR

        channel_post = conn.query(ChannelPost).filter_by(cid=channel.cid, title=title).one()
        if VERBOSE:
            print(f"post {title} by user {uid} is added to {channel.name}")
        return channel_post.post_id


def remove_channel_post(post_id: int):
    """
    Remove a channel post comment, if the post_id is valid

    :param post_id: The id of channel post comment
    """
    with Session() as conn:
        post = conn.query(ChannelPost).filter_by(post_id=post_id).one_or_none()
        if post:
            conn.delete(post)
            try_to_commit(conn)


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
            ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
    """
    with Session() as conn:
        if not conn.query(User).filter_by(uid=uid).one_or_none():
            warnings.warn("uid is invalid")
            return ErrorCode.INVALID_USER
        elif not conn.query(ChannelPost).filter_by(post_id=post_id).one_or_none():
            warnings.warn("post_id is invalid")
            return ErrorCode.INVALID_POST

        # check user session and renew
        # if is_user_session_expired(uid):
        #     print("User session expired")
        #     return ErrorCode.USER_SESSION_EXPIRED
        # renew_user_session(uid)

        created_at = datetime.datetime.now(tz=pytz.timezone("Australia/Brisbane"))
        post_comment = PostComment(post_id=post_id, uid=uid, created_at=created_at,
                                   text=text)
        conn.add(post_comment)
        if not try_to_commit(conn):
            warnings.warn(f"Comment to post {post_id} by user {uid} failed")
            return ErrorCode.COMMIT_ERROR

        post_comment = conn.query(PostComment).filter_by(post_id=post_id, uid=uid,
                                                         created_at=created_at).one()
        if VERBOSE:
            print(f"Comment to post {post_id} by user {uid} is created")
        return post_comment.post_comment_id


def remove_channel_post_comment(post_comment_id: int):
    """
    Remove a channel post comment, if the post_id is valid

    :param post_comment_id: The id of channel post comment
    """
    with Session() as conn:
        channel_post_comment = conn.query(PostComment).\
                filter_by(post_comment_id=post_comment_id).one_or_none()
        if channel_post_comment:
            conn.delete(channel_post_comment)
            try_to_commit(conn)


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
            ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
    """
    with Session() as conn:
        user = conn.query(User).filter_by(uid=uid).one_or_none()
        post = conn.query(ChannelPost).filter_by(post_id=post_id).one_or_none()
        if not user:
            warnings.warn("uid is invalid")
            return ErrorCode.INVALID_USER
        elif not post:
            warnings.warn("post id is invalid")
            return ErrorCode.INVALID_POST

        # check user session and renew
        # if is_user_session_expired(uid):
        #     print("User session expired")
        #     return ErrorCode.USER_SESSION_EXPIRED
        # renew_user_session(uid)

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
                if VERBOSE:
                    warnings.warn("user cannot vote the same item twice")
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
        if not try_to_commit(conn):
            warnings.warn(f"User {uid} failed vote to post {post_id}")
            return ErrorCode.COMMIT_ERROR
        if VERBOSE:
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
            ErrorCode.COMMIT_ERROR if cannot commit (used when DEBUG_MODE is False)
    """
    with Session() as conn:
        user = conn.query(User).filter_by(uid=uid).one_or_none()
        post_comment = conn.query(PostComment).filter_by(post_comment_id=post_comment_id). \
            one_or_none()
        if not user:
            warnings.warn("uid is invalid")
            return ErrorCode.INVALID_USER
        elif not post_comment:
            warnings.warn("post id is invalid")
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
                if VERBOSE:
                    warnings.warn("user cannot vote the same item twice")
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
        if not try_to_commit(conn):
            warnings.warn(f"User {uid} failed to vote post {post_comment_id}")
            return ErrorCode.COMMIT_ERROR
        if VERBOSE:
            print(f"User {uid} voted post {post_comment_id}, is_upvote = {upvote}")
