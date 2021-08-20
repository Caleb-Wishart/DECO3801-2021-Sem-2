from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from DBStructure import *
from DBFunc import *

engine = create_engine(DBPATH)

# test user
add_user("test1", "123456", "cumfast@gmail.com", {Subject.CHINESE: True, Subject.BIOLOGY: False})
add_user("test2", "999999", "bigdaddy@onlyfans.com", {Subject.BIOLOGY: True, Subject.ENGLISH: True})
with Session(engine) as conn:
    print("User info:")
    for i in conn.query(User).all():
        print(i)

# add tag
add_tag("try me daddy", "Can I get a hoya?")
add_tag("NSFW")
with Session(engine) as conn:
    print("Tag info:")
    for i in conn.query(Tag).all():
        print(i)
tags = get_tags()
print(tags)


# add resource
add_resource("How to do edging", "127.0.0.1:8080", ResourceDifficulty.SPECIALIST,
             Subject.BIOLOGY, tags=[tags["NSFW"]])
add_resource("Can't find another good title", "acm.org", ResourceDifficulty.EASY,
             Subject.IT, False, private_personnel=[2],
             tags=[tags["NSFW"], tags["try me daddy"]])
with Session(engine) as conn:
    print("Resource info:")
    for i in conn.query(Resource).all():
        print(i)

    print("Resource Tag Record:")
    for i in conn.query(ResourceTagRecord).all():
        print(i)

    print("Private personnel:")
    for i in conn.query(PrivateResourcePersonnel).all():
        print(i)


# vote resource
vote_resource(1, 1, True)
vote_resource(1, 1, False)
vote_resource(2, 2, True)
with Session(engine) as conn:
    for i in conn.query(VoteInfo).all():
        print(f"voter id = {i.uid}, resource id = {i.rid}")

    for i in conn.query(Resource).all():
        print(i)


# try delete a user instance with dependency
with Session(engine) as conn:
    user = conn.query(User).filter_by(uid=1).one()
    conn.delete(user)
    conn.commit()

    for i in conn.query(User).all():
        print(i)

    for i in conn.query(VoteInfo).all():
        print(f"voter id = {i.uid}, resource id = {i.rid}")
# test_user1 = User(username="test1", password="123456", email="cumfast@gmail.com")
#
# test_user2 = User(username="test2", password="123456", email="bigdaddy@gmail.com")

# test_resource = Resource(title="How to do edging", resource_link="127.0.0.1:8080",
#                          difficulty=ResourceDifficulty.EASY)

# foreign key
# test_resource_creater = ResourceCreater(rid=1, uid=1)


# insertion test
# with Session(engine) as conn:
#     conn.add(test_user1)
#     conn.add(test_resource)
#     conn.add(test_resource_creater)
#     conn.commit()

# view table test

#
#     for i in conn.query(Resource).all():
#         print(i)
#
#     for i in conn.query(ResourceCreater).all():
#         print(i)
