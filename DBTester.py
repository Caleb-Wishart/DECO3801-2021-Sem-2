###############################################################################
# This is a script used to test and demonstrate
# the usage of some methods in DBFunc
#
# ***********************************************************************
# Some hints for interacting with postgres
# log in to psql:
# 1. type "psql firstname firstname" (no uppercase) in cli
# 2. prompt for password, enter "admin"
# 3. You are in.
#
#
# view records in a table:
# In psql cli: type "SELECT * FROM table_name;"
#
# delete all tables created in your own DB:
# see instructions on https://makandracards.com/makandra/62111-how-to-drop-all-tables-in-postgresql
#
# more basic commands for psql cli:
# check out https://gist.github.com/Kartones/dd3ff5ec5ea238d4c546
# ************************************************************************
#
# created by Jason Aug 20, 2021
##############################################################################

# import these two modules to do everything with DB, despite demo here we
# only calls function from DBFunc
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

    # observe entry of with uid = 1 in vote_info table is also gone
    for i in conn.query(VoteInfo).all():
        print(f"voter id = {i.uid}, resource id = {i.rid}")

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
