###############################################################################
# This script is used to import dummy resources to our website
#
# created by Jason Aug 26, 2021
###############################################################################
from DBStructure import *
from DBFunc import *
from random import choice

engine = create_engine(DBPATH)

Session = sessionmaker(engine)

# get a list of random sentences from Harvard sentences
random_comments = []
with open("./static/files_for_testing/harvard-sentences.txt", "r") as fp:
    for i in fp.readlines():
        if not i.startswith("#"):
            sentence = i.rstrip("\n")
            random_comments.append(sentence)


def add_pseudo_comment_to_resource(rid: int, uid: int):
    """
    For an rid give, add a comment followed by a reply to it to this resource
    """
    comment_id = comment_to_resource(uid=uid, rid=rid, comment=choice(random_comments))

    reply_to_resource_comment(uid=uid, resource_comment_id=comment_id,
                              reply=choice(random_comments))

    print(f"comment and comment reply to resource {rid} added")


# test user 1
teaching_areas = {Subject.MATHS_A: [True], Subject.CHEMISTRY: [True], Subject.ENGLISH: [True]}
uid1 = add_user(username="Ashley Gibbons", password="123456", email="a.gibbsons@uq.edu.au",
                avatar_link="static/avatar/ashley_gibbons.png",
                bio="Hi! My name is Ashley and I love children! "
                    "Especially teaching them! I have worked at Somerset College for"
                    " 4 years and honestly I wanna leave. But I am stuck while I pay for"
                    " the bills while fucking Harold spends all our money on the Pokies"
                    "Yall will see contents I uploaded not just restrict to Math, but"
                    "a little bit of this and a little bit of that. Don't ask why. I need that money!",
                teaching_areas=teaching_areas)

# add tag
add_tag("CS")
add_tag("Math Tutorial")
add_tag("Drama activities")
add_tag("Math practice sheet")

tags = get_tags()
print(tags)
print("\n")

# add resource
# single pdf file
src1 = add_resource(title="CS50 at Harvard - The Most Rewarding Class I Have Taken"
                          " . . . Ever!",
                    resource_link="static/resource/CS50_at_Harvard_The_Most_Rewarding"
                                  "_Class_I_Have_Taken_Ever.pdf",
                    difficulty=ResourceDifficulty.EASY, subject=Subject.IT,
                    tags_id=[tags["CS"]],
                    description="A trail of colorful balloons leads from Oxford "
                                "Street to the Northwest"
                                "Labs building. As I head downstairs, I exchange"
                                " greetings with our dean. Someone "
                                "hands me"
                                " a tub of popcorn, a squishy ball, and a scavenger"
                                " hunt list. The "
                                "room is pulsing to a techno beat, and as I scan"
                                " the room I can see many of my "
                                "faculty and staff colleagues, "
                                "including our university "
                                "president, who is having an animated discussion with an "
                                "undergraduate. "
                                " Is this a party? A film festival? No. This is CS50.",
                    grade=Grade.TERTIARY, creaters_id=[uid1])

"""
Embed link:
<iframe width="560" height="315" src="https://www.youtube.com/embed/kztICk78ZcE"
 title="YouTube video player" frameborder="0" allow="accelerometer;
  autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
   allowfullscreen></iframe>
"""
src2 = add_resource(title="Grade 2 Math 1.1, Understanding Addition",
                    resource_link="https://www.youtube.com/embed/kztICk78ZcE",
                    difficulty=ResourceDifficulty.MODERATE,
                    grade=Grade.YEAR_2, creaters_id=[uid1], tags_id=[tags["Math Tutorial"]],
                    subject=Subject.MATHS_A,
                    description="How to do basic addition and the parts of"
                                " an addition sentence. Using counters to add. Page"
                                " 1 in the textbook.")


"""
Embed link:
<iframe width="560" height="315" src="https://www.youtube.com/embed/efnA7byI8sg"
 title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; 
 clipboard-write; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen></iframe>
"""
src3 = add_resource(title="3rd Grade Math 8.6, Relate Fractions and Whole Numbers",
                    resource_link="https://www.youtube.com/embed/efnA7byI8sg",
                    difficulty=ResourceDifficulty.SPECIALIST,
                    grade=Grade.YEAR_3, creaters_id=[uid1], tags_id=[tags["Math Tutorial"]],
                    subject=Subject.MATHS_B,
                    description="A fraction can represent an amount less than one"
                                " whole, one whole, or more than one whole. When a "
                                "fraction is less than 1, the numerator is less than"
                                " the denominator. When a fraction is equal to 1,"
                                " the numerator and denominator are the same number."
                                " When a fraction is greater ")


"""
Embed link:
<iframe width="560" height="315" src="https://www.youtube.com/embed/u8VEuS-32JM"
 title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write;
  encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
"""
src4 = add_resource(title="Drama Lesson Activities, Grade 4-6: Creative Play",
                    resource_link="https://www.youtube.com/embed/u8VEuS-32JM",
                    difficulty=ResourceDifficulty.EASY,
                    creaters_id=[uid1], tags_id=[tags["Drama activities"]], grade=Grade.YEAR_6,
                    subject=Subject.DRAMA,
                    description="A variety of creative drama games are explored. These games"
                                " teach basic skills such as problem solving, communication,"
                                " trust, quick thinking,"
                                "confidence, cooperation and more. These games ensure that"
                                " learners feel challenged, "
                                "but never threatened")


# compressed file of multiple pdfs
src5 = add_resource(title="Grade 12 QLD Math C U10 worksheet",
                    resource_link="static/resource/MQC-12.zip",
                    difficulty=ResourceDifficulty.SPECIALIST,
                    creaters_id=[uid1], tags_id=[tags["Math practice sheet"]],
                    grade=Grade.YEAR_12, subject=Subject.MATHS_C,
                    description="Some worksheets directly copied from MCQ website.")


"""
Embed link:
<iframe width="560" height="315" src="https://www.youtube.com/embed/1IbkUY9vZcU"
 title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; 
 clipboard-write; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen></iframe>
"""
src6 = add_resource(title="4th Grade Math Input-Output Tables",
                    resource_link="https://www.youtube.com/embed/1IbkUY9vZcU",
                    difficulty=ResourceDifficulty.EASY,
                    creaters_id=[uid1], tags_id=[tags["Math Tutorial"]],
                    grade=Grade.YEAR_4, subject=Subject.MATHS_A,
                    description="Learn how to find unknown quantities in the "
                                "position or value of numbers as they relate to rule"
                                " or numerical expressions. Two examples are given"
                                " in the video.")

# add comments and comment replies to each src above
for i in range(1, 7):
    rid = globals()[f"src{i}"]
    add_pseudo_comment_to_resource(rid=rid, uid=uid1)

    resource_comments = get_resource_comments(rid=rid)
    resource_comment_replies = get_resource_comment_replies(resource_comments)
    print(f"rid = {rid}, number of resource comment = {len(resource_comments)},"
          f"number of resource comment replies to that comment = "
          f"{len(resource_comment_replies)}")


with Session() as conn:
    for i in conn.query(Resource).all():
        print(i)
    print("\n")

    for i in conn.query(ResourceTagRecord).all():
        print(i)
    print("\n")

    for i in conn.query(PrivateResourcePersonnel).all():
        print(i)
    print("\n")

    for i in conn.query(ResourceCreater).all():
        print(i)
    print("\n")

    for i in conn.query(ResourceComment).all():
        print(i)
    print("\n")

    for i in conn.query(ResourceCommentReply).all():
        print(i)

