##################################################################
# This file provides some basic wrapper functions to create and
# modify the DB objects
# todo: add functions for forum and comment related tables
#
# report bug to Jason on messager
#
# Created by Jason Aug 20, 2021
##################################################################
from typing import List
from sqlalchemy.orm import Session
from DBStructure import *


engine = create_engine(DBPATH)


epoch = datetime.datetime.utcfromtimestamp(0)

def add_user(username, password, email, teaching_areas: dict = {},
             verbose=True, bio=None, avatar_link=None) -> None:
    """
    Add a new user to table user and add teaching_areas to
    user_teaching_areas table

    :param username: username
    :param avatar_link: The link to avatar, default is null
    :param password: The password of new user
    :param bio: The bio of new user
    :param email: The email address of that user. This field is unique for each user.
    :param verbose: Show creation message
    :param teaching_areas: Mapping of teaching area - is_public
            e.g. [Subject.ENGLISH: True, Subject.MATHS_C: False]
    """
    email = email.lower()
    user = User(username=username, avatar_link=avatar_link, password=ascii_to_base64(password),
                email=email, created_at=datetime.datetime.now(
                tz=pytz.timezone("Australia/Brisbane")), bio=bio)

    with Session(engine) as conn:
        if conn.query(User).filter_by(email=email).one_or_none():
            print("This email address is registered")
            return

        # phase 1: add a new user
        conn.add(user)
        conn.commit()
        if verbose:
            print(f"User {username} created")

        # phase 2: find id of new user -- using email,
        # then update teaching_areas table
        user = conn.query(User).filter_by(email=email).one()
        for area, is_public in teaching_areas.items():
            if isinstance(area, Subject):
                new_teach_area = UserTeachingAreas(uid=user.uid, teaching_area=area,
                                                   is_public=is_public)
                conn.add(new_teach_area)
        conn.commit()


def get_user(email) -> User:
    """
    Retrieve the User with the unique email as the key

    :param email: The identifiying email
    :return: User structure or None
    """
    email = email.lower()
    with Session(engine) as conn:
        user = conn.query(User).filter_by(email=email).one_or_none()
        return user


def add_tag(tag_name, tag_description=None, verbose=True):
    """
    Add a new tag to Database

    :param tag_name: The name of the new tag
    :param tag_description: The description of the tag (optional)
    :param verbose: Show creation message
    """
    tag = Tag(tag_name=tag_name, tag_description=tag_description)
    with Session(engine) as conn:
        conn.add(tag)
        conn.commit()
        print(f"tag {tag_name} added") if verbose else None


def get_tags():
    """
    :return: A dictionary of mapping tag_name -> tag_id
    """
    out = dict()

    with Session(engine) as conn:
        tags = conn.query(Tag).all()

        for i in tags:
            out[i.tag_name] = i.tag_id
    return out


def add_resource(title, resource_link, difficulty, subject, is_public=True,
                 private_personnel=[], tags=[], verbose=True):
    """
    Add a resource to resource table

    :param title: The name of the resource
    :param resource_link: The link to resource video
    :param difficulty: The difficulty of the resource
    :param subject: what subject this resource relates to
    :param is_public: if the resource is public
    :param private_personnel: if this resource is private, add all User instances
            to the private_resource_personnel. Element to be filled in is uid
    :param tags: The tags associated with this resource -- each element is tag_id
    :param verbose: Show creation message
    """
    if not is_public and not private_personnel:
        print("Please specify the User allowed to access this resource")
        return

    resource = Resource(title=title, resource_link=resource_link,
                        difficulty=difficulty, subject=subject, is_public=is_public)
    with Session(engine) as conn:
        # phase 1: add new resource
        conn.add(resource)
        conn.commit()

        # phase 2: find the new row, update private_resource_personnel info and tag info
        resource = conn.query(Resource).filter_by(
            resource_link=resource_link).one()
        if not is_public:
            for uid in private_personnel:
                private_access = PrivateResourcePersonnel(
                    rid=resource.rid, uid=uid)
                conn.add(private_access)
            conn.commit()

        if tags:
            for i in tags:
                tag_record = ResourceTagRecord(rid=resource.rid, tag_id=i)
                conn.add(tag_record)
                conn.commit()
        if verbose:
            print(f"Resource {title} added")

def find_resources(title_type="like",title="",
    created_type="after",created=epoch,
    difficulty=None, subject=None,
    vote_type="more",votes=None
    ):
    """Find a resource using the specific keys.

        If a param_type parameter is specified then the corresponding param must
        be specified.

        If any param does not fall into the valid values the default will be
        used in its place.

        If no parameters are passed the method should return all Resources.

        :param title_type   : SQL search restriction for the title.
            Valid values are ["like","exact"]
            Defaults to "like".
        :param title        : title to search for
            Defaults to "".
        :param created_type : SQL search restriction for the creation date.
            Valid values are ["after","before","on"]
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
    """
    with Session(engine) as conn:
        resource = conn.query(Resource)



def vote_resource(uid, rid, upvote=True, verbose=True):
    """
    Give upvote/downvote to a resource:
    1. update up/down-vote count of the nominated resource; and
    2. add/modify vote_info table

    :param uid: The voter's user id
    :param rid: The resource to vote
    :param upvote: is this is a upvote
    :param verbose: show process message
    """
    msg = "created"

    with Session(engine) as conn:
        resource = conn.query(Resource).filter_by(rid=rid).one()

        # try to find if there is an entry in vote_info
        vote_info = conn.query(VoteInfo).filter_by(
            uid=uid, rid=rid).one_or_none()
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
                return
        else:
            # new vote
            vote_info = VoteInfo(rid=rid, uid=uid, is_upvote=upvote)
            if upvote:
                resource.upvote_count += 1
            else:
                resource.downvote_count += 1

        conn.add(vote_info)
        conn.add(resource)
        conn.commit()
        print(f"Vote info {msg}") if verbose else None
