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
import time

engine = create_engine(DBPATH)

Session = sessionmaker(engine)

# need to change USER_SESSION_EXPIRE_INTERVAL in DBFunc to 10s
# test is_user_expired(), renew_user_session(), get_user_by_email(), user_session table
# session_test_user = add_user("test_session", "123456", "lol@mail.com")
# time.sleep(5)
# print(f"user {session_test_user} is expired after 5s = "
#       f"{is_user_session_expired(session_test_user)}")
# time.sleep(11)
# print(f"user {session_test_user} is expired after 11s = "
#       f"{is_user_session_expired(session_test_user)}")
# renew_user_session(session_test_user)
# print(f"After renewal, user {session_test_user} is expired = "
#       f"{is_user_session_expired(session_test_user)}")
# exit(1)

# test add_user(), user, user_teaching_areas tables
# teaching_areas1 = {Subject.CHINESE: [True], Subject.BIOLOGY: [False, Grade.YEAR_1]}
# add_user("test1", "123456", "cumfast@gmail.com", teaching_areas=teaching_areas1)
#
# teaching_areas2 = {Subject.BIOLOGY: [True, Grade.YEAR_12], Subject.ENGLISH: [True]}
# add_user("test2", "999999", "bigdaddy@onlyfans.com", teaching_areas=teaching_areas2)
# with Session() as conn:
#     # print("User info:")
#     for i in conn.query(User).all():
#         print(i)
#     for i in conn.query(UserTeachingAreas).all():
#         print(i)
#
#
# print("\n")
#
#
# # test add/get_tag(), tag
# add_tag("try me daddy", "Can I get a hoya?")
# add_tag("NSFW")
# with Session() as conn:
#     # print("Tag info:")
#     for i in conn.query(Tag).all():
#         print(i)
# tags = get_tags()
# print(tags)
#
#
# print("\n")
#
#
# # test add_resource(),
# # resource, private_resource_personnel, resource_tag_record, resource_creater tables
# # public resource
# creater_id1 = [1, 2]
# rid1 = add_resource("How to do edging", "127.0.0.1:8080", difficulty=ResourceDifficulty.SPECIALIST,
#                     subject=Subject.BIOLOGY, grade=Grade.YEAR_7, creaters_id=creater_id1,
#                     tags_id=[tags["NSFW"]], description="Oh well this shouldn't be grade 7 thing.")
# # private resource
# rid2 = add_resource("Can't find another good title", "acm.org", difficulty=ResourceDifficulty.EASY,
#                     subject=Subject.IT, grade=Grade.KINDERGARTEN, is_public=False,
#                     private_personnel_id=[2], tags_id=[tags["NSFW"], tags["try me daddy"]])
# with Session() as conn:
#     # print("Resource info:")
#     for i in conn.query(Resource).all():
#         print(i)
#
#     # print("Resource Tag Record:")
#     for i in conn.query(ResourceTagRecord).all():
#         print(i)
#
#     # print("Private personnel:")
#     for i in conn.query(PrivateResourcePersonnel).all():
#         print(i)
#
#     for i in conn.query(ResourceCreater).all():
#         print(i)
#
#
# print("\n")
#
#
# # test modify_resource_personnel() and user_has_access_to_resource()
# # user 1 has no access to resource 2
# print(f"user {1} can access resource {rid2} = {user_has_access_to_resource(uid=1, rid=rid2)}")
# modify_resource_personnel(rid=rid2, uid=1, modification=PersonnelModification.PERSONNEL_ADD)
# print(f"Now user {1} can access resource {rid2} = {user_has_access_to_resource(uid=1, rid=rid2)}")
# modify_resource_personnel(rid=rid2, uid=1, modification=PersonnelModification.PERSONNEL_DELETE)
#
#
# print("\n")
#
#
# # test vote_resource(), vote_info tables
# # upvote 1
# vote_resource(1, 1, True)
# # downvote 1, previous upvote canceled
# vote_resource(1, 1, False)
# # upvote 2
# vote_resource(2, 2, True)
# with Session() as conn:
#     for i in conn.query(ResourceVoteInfo).all():
#         # print(f"voter id = {i.uid}, resource id = {i.rid}")
#         print(i)
#
#     for i in conn.query(Resource).all():
#         print(i)
#
#
# print("\n")
#
#
# # test user_viewed_resource(), ResourceView table
# user_viewed_resource(uid=1, rid=2)
# user_viewed_resource(uid=2, rid=2)
# with Session() as conn:
#     for i in conn.query(ResourceView).all():
#         print(i)
#
#
# print("\n")
#
#
# # test comment_on_resource, resource_comment table
# test_comment_id = comment_to_resource(uid=2, rid=1, comment="Not cool")
# comment_to_resource(uid=1, rid=1, comment="lol")
# with Session() as conn:
#     for i in conn.query(ResourceComment).all():
#         print(i)
#
#
# print("\n")
#
#
# # test reply_to_resource_comment(), resource_comment_reply table
# reply_to_resource_comment(uid=1, resource_comment_id=test_comment_id, reply="Shut up")
# reply_to_resource_comment(uid=2, resource_comment_id=test_comment_id, reply="so what, jerk")
# with Session() as conn:
#     for i in conn.query(ResourceCommentReply).all():
#         print(i)
#
#
# print("\n")
#
#
# # test create_channel(), channel, channel_personnel tables
# # public
# cid1 = create_channel(name="OFFICIALTEAMNAME", visibility=ChannelVisibility.PUBLIC,
#                       admin_uid=1, subject=Subject.IT, grade=Grade.KINDERGARTEN,
#                       description="Ain't got no word", tags_id=[tags["NSFW"]])
#
# # private, empty personnel implies only admin is in the channel
# cid2 = create_channel(name="Dotrina Q&A", visibility=ChannelVisibility.FULLY_PRIVATE,
#                       admin_uid=1, personnel_id=[])
# with Session() as conn:
#     for i in conn.query(Channel).all():
#         print(i)
#
#
# print("\n")
#
#
# print("\n")
#
#
# # test modify_channel_personnel(), user_has_access_to_channel()
# # user 2 has no access to channel 2
# print(f"User {2} has access to channel {cid2} = {user_has_access_to_channel(uid=2, cid=cid2)}")
# modify_channel_personnel(uid=2, cid=cid2, modification=PersonnelModification.PERSONNEL_ADD)
# print(f"New user {2} has access to channel {cid2} = {user_has_access_to_channel(uid=2, cid=cid2)}")
# modify_channel_personnel(uid=2, cid=cid2, modification=PersonnelModification.PERSONNEL_DELETE)
#
#
# # test post_on_channel(), channel_post table
# # this should be successful
# post_id = post_on_channel(uid=1, title="Intro", text="This is the first post",
#                           channel_name="OFFICIALTEAMNAME")
# # this should be rejected since uid = 2 is not in the channel
# post_on_channel(uid=2, title="Test", text="Test", cid=cid2)
#
# # test vote_channel_post(), ChannelPostVoteInfo table
# vote_channel_post(uid=1, post_id=post_id, upvote=True)
# with Session() as conn:
#     for i in conn.query(ChannelPostVoteInfo).all():
#         print(i)
#
#
# print("\n")
#
#
# # test comment_to_channel_post(), post_comment table
# post_comment_id = comment_to_channel_post(uid=2, post_id=post_id, text="Ayyyyy")
# with Session() as conn:
#     for i in conn.query(PostComment).all():
#         print(i)
#
#
# print("\n")
#
#
# # test vote_channel_post_comment(), PostCommentVoteInfo table
# vote_channel_post_comment(uid=1, post_comment_id=post_comment_id, upvote=False)
# with Session() as conn:
#     for i in conn.query(PostCommentVoteInfo).all():
#         print(i)
#
#
# print("\n")
#
#
# # try delete a user instance with dependency
# with Session() as conn:
#     delete_uid = 2
#     user = conn.query(User).filter_by(uid=2).one()
#     conn.delete(user)
#     conn.commit()
#     print(f"user {delete_uid} deleted")
#
#     for i in conn.query(User).all():
#         print(i)
#
#     # observe entry of with uid = 1 in vote_info table is also gone
#     for i in conn.query(ResourceVoteInfo).all():
#         print(f"voter id = {i.uid}, resource id = {i.rid}")
#
#     for i in conn.query(ResourceCreater).all():
#         print(i)
#
#     for i in conn.query(PrivateResourcePersonnel).all():
#         print(i)


# check find_channels
print("No parameters provided")
for i in find_channels():
    print(i.cid)
print("\n")

print("grade = year 3 only, accessed by uid = 3")
for i in find_channels(grade=Grade.YEAR_3, caller_uid=3):
    print(i.cid)
print("\n")

print("grade = year 3, subject = math A, accessed by uid = 3")
for i in find_channels(grade=Grade.YEAR_3, caller_uid=3, subject=Subject.MATHS_A):
    print(i.cid)
print("\n")

print("all channels created by admin user 1")
for i in find_channels(admin_uid=1):
    print(i.cid)

print('all channels created by 1, tag_id == 8')
for i in find_channels(admin_uid=1, tag_ids=[8]):
    print(i.cid)

print("visibility == PUBLIC")
for i in find_channels(visibility=ChannelVisibility.PUBLIC):
    print(i.cid)

