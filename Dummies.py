###############################################################################
# This script is used to import dummy resources/users/channel comments to our website
#
# created by Jason Aug 26, 2021
###############################################################################
import random

from DBFunc import *
from random import choice, sample, randint
from faker import Faker
import pagan

engine = create_engine(DBPATH)

Session = sessionmaker(engine)

# instance to create random personal info
random_person = Faker()
random.seed(1)

# get a list of random sentences from Harvard sentences
random_texts = []
with open("./static/files_for_testing/harvard-sentences.txt", "r") as fp:
    for i in fp.readlines():
        if not i.startswith("#"):
            sentence = i.rstrip("\n")
            random_texts.append(sentence)


def get_random_voters(accessors):
    return sample(accessors, k=random.randint(0, min(len(accessors), 3)))


def add_pseudo_comment_to_resource(rid: int, accessors_id: list):
    """
    For an rid given, add a comment followed by a reply to it to this resource from
    a list of accessors
    """
    commenter = choice(accessors_id)
    accessors_id.pop(accessors_id.index(commenter))

    comment_id = comment_to_resource(uid=commenter, rid=rid, comment=choice(random_texts))
    if comment_id == ErrorCode.INVALID_USER:
        print(commenter, rid, "comment")
        exit(2)

    repliers = sample(accessors_id, min(2, len(accessors_id)))
    for replier in repliers:
        if reply_to_resource_comment(uid=replier, resource_comment_id=comment_id,
                                     reply=choice(random_texts)) == ErrorCode.INVALID_USER:
            print(replier, rid, "comment reply")
            exit(3)

    print(f"comment and comment reply to resource {rid} added")


def add_pseudo_channel_post_and_replies(cid: int, accessors_id: list):
    """
    For a cid given, make a channel post and a post comment. Random votes
    on this post and comment by users in accessors_id
    """
    poster_uid = choice(accessors_id)
    # warnings.warn(f"channel {cid} with personnel {accessors_id}, selected poster {poster_uid}")
    channel_post = post_on_channel(uid=poster_uid, title=choice(random_texts),
                                   cid=cid, text=" ".join(sample(random_texts,
                                                                 k=random.randint(1, 10))))
    for voter in get_random_voters(accessors_id):
        vote_channel_post(uid=voter, upvote=bool(random.getrandbits(1)), post_id=channel_post)

    repliers = sample(accessors_id, min(2, len(accessors_id)))
    for replier in repliers:
        post_reply = comment_on_channel_post(uid=replier,
                                             post_id=channel_post,
                                             text=" ".join(sample(random_texts,
                                                                  k=random.randint(1, 10))))
        for voter in get_random_voters(accessors_id):
            vote_channel_post_comment(uid=voter, post_comment_id=post_reply,
                                      upvote=bool(random.getrandbits(1)))


subject_list = [e for e in Subject if e != Subject.NULL]
grade_list = [e for e in Grade if e != Grade.NULL]


def get_random_teaching_areas() -> dict:
    """
    Return random number (1, 10) of teaching areas in a dict, all teaching areas are public
    """

    areas = {}
    for count in range(random.randint(1, 10)):
        show_grade = bool(random.getrandbits(1))
        key = [True]
        if show_grade:
            key.append(random.choice(grade_list))
        areas[random.choice(subject_list)] = key
    return areas


# test user 1
teaching_areas = {Subject.MATHS_A: [True], Subject.CHEMISTRY: [True], Subject.ENGLISH: [True]}
uid0 = add_user(username="Ashley Gibbons", password="123456", email="a.gibbsons@uq.edu.au",
                avatar_link="avatar/ashley_gibbons.png",
                bio="Hi! My name is Ashley and I love children! "
                    "Especially teaching them! I have worked at Somerset College for"
                    " 4 years and honestly I wanna leave. But I am stuck while I pay for"
                    " the bills while fucking Harold spends all our money on the Pokies"
                    "Yall will see contents I uploaded not just restrict to Math, but"
                    "a little bit of this and a little bit of that. Don't ask why. I need that money!",
                teaching_areas=teaching_areas)
# create 9 more users
for i in range(1, 10):
    name = random_person.name()
    avatar = pagan.Avatar(name, pagan.MD5)
    file_path = "avatar"
    avatar.save("static/" + file_path, f"{i}.png")
    file_path += f"/{i}.png"
    globals()[f"uid{i}"] = add_user(username=name, password="123456",
                                    email=random_person.email(),
                                    avatar_link=file_path,
                                    teaching_areas=get_random_teaching_areas(),
                                    bio=" ".join(random.sample(random_texts,
                                                               k=random.randint(1, 10))))

# note here user_id 1 -> uid = 0 since DB is 1 indexing
users_id = [e for e in range(1, 11)]

# add tag
add_tag("CS")
add_tag("Math_Tutorial")
add_tag("Drama_activities")
add_tag("Math_practice_sheet")
add_tag("1_min_tutorial")
add_tag("brainstorming")
add_tag('distance_teaching')
add_tag("metric_math")

tags = get_tags()
print(tags)
print("\n")

# add resource
# single pdf file
src0 = add_resource(title="CS50 at Harvard - The Most Rewarding Class I Have Taken"
                          " . . . Ever!",
                    resource_link="resource/CS50_at_Harvard_The_Most_Rewarding"
                                  "_Class_I_Have_Taken_Ever.pdf",
                    difficulty=ResourceDifficulty.EASY, subject=Subject.IT,
                    tags_id=[tags["CS"], tags["brainstorming"]],
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
                    grade=Grade.TERTIARY, creaters_id=sample(users_id, k=1))

"""
Embed link:
<iframe width="560" height="315" src="https://www.youtube.com/embed/kztICk78ZcE"
 title="YouTube video player" frameborder="0" allow="accelerometer;
  autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
   allowfullscreen></iframe>
"""
src1 = add_resource(title="Grade 2 Math 1.1, Understanding Addition",
                    resource_link="https://www.youtube.com/embed/kztICk78ZcE",
                    difficulty=ResourceDifficulty.MODERATE,
                    grade=Grade.YEAR_2,
                    creaters_id=sample(users_id, k=1),
                    tags_id=[tags["Math_Tutorial"], tags["1_min_tutorial"]],
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
src2 = add_resource(title="3rd Grade Math 8.6, Relate Fractions and Whole Numbers",
                    resource_link="https://www.youtube.com/embed/efnA7byI8sg",
                    difficulty=ResourceDifficulty.SPECIALIST,
                    grade=Grade.YEAR_3,
                    creaters_id=sample(users_id, k=1),
                    tags_id=[tags["Math_Tutorial"]],
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
src3 = add_resource(title="Drama Lesson Activities, Grade 4-6: Creative Play",
                    resource_link="https://www.youtube.com/embed/u8VEuS-32JM",
                    difficulty=ResourceDifficulty.EASY,
                    creaters_id=sample(users_id, k=1),
                    tags_id=[tags["Drama_activities"]], grade=Grade.YEAR_6,
                    subject=Subject.DRAMA,
                    description="A variety of creative drama games are explored. These games"
                                " teach basic skills such as problem solving, communication,"
                                " trust, quick thinking,"
                                "confidence, cooperation and more. These games ensure that"
                                " learners feel challenged, "
                                "but never threatened")

# compressed file of multiple pdfs
src4 = add_resource(title="Grade 12 QLD Math C U10 worksheet",
                    resource_link="resource/MQC-12.zip",
                    difficulty=ResourceDifficulty.SPECIALIST,
                    creaters_id=sample(users_id, k=1),
                    tags_id=[tags["Math_practice_sheet"]],
                    grade=Grade.YEAR_12, subject=Subject.MATHS_C,
                    description="Some worksheets directly copied from MCQ website.")

"""
Embed link:
<iframe width="560" height="315" src="https://www.youtube.com/embed/1IbkUY9vZcU"
 title="YouTube video player" frameborder="0" allow="accelerometer; autoplay;
 clipboard-write; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen></iframe>
"""
src5 = add_resource(title="4th Grade Math Input-Output Tables",
                    resource_link="https://www.youtube.com/embed/1IbkUY9vZcU",
                    difficulty=ResourceDifficulty.EASY,
                    creaters_id=sample(users_id, k=1),
                    tags_id=[tags["Math_Tutorial"]],
                    grade=Grade.YEAR_4, subject=Subject.MATHS_A,
                    description="Learn how to find unknown quantities in the "
                                "position or value of numbers as they relate to rule"
                                " or numerical expressions. Two examples are given"
                                " in the video.")

# add comments and comment replies to each src above (all public)
for i in range(0, 6):
    rid = globals()[f"src{i}"]
    add_pseudo_comment_to_resource(rid=rid, accessors_id=users_id)

# next 5 resources are private, all resources are locally stored
resource_titles = ["Learn Chinese for Beginners Beginner Chinese"
                   " Lesson 1 Self-Introduction in Chinese Mandarin 1.1",
                   "GRADE 12 TRIGONOMETRY WORKSHEET",
                   "ANALYTICAL GEOMETRY - The basics (a compilation)",
                   "Grade 12 Calculus An Introduction to Calculus and Overview"
                   " of Key Concepts NSC DBE Maths NTE",
                   "Factoring Quadratic - Expressions (B)"]
resource_links = ["Learn_Chinese_for_Beginners_Beginner_Chinese_Lesson_1_Self-"
                  "Introduction_in_Chinese_Mandarin_1.1.mp4",
                  "GRADE_12_TRIGONOMETRY_WORKSHEET.zip",
                  "ANALYTICAL_GEOMETRY_-_The_basics_(a_compilation).mp4",
                  "Grade_12_Calculus_An_Introduction_to_Calculus_and_Overview_"
                  "of_Key_Concepts_NSC_DBE_Maths_NTE.mp4",
                  "Algebra.Factorization.Factoring_Quadratic_Expressions_-_(B).US.pdf"]
resource_links = ["resource/" + e for e in resource_links]
grades = [Grade.TERTIARY, Grade.YEAR_12, Grade.YEAR_12, Grade.YEAR_12, Grade.YEAR_12]
subjects = [Subject.CHINESE, Subject.MATHS_C, Subject.MATHS_C, Subject.MATHS_C,
            Subject.MATHS_C]
resource_difficulty = [ResourceDifficulty.EASY, ResourceDifficulty.SPECIALIST,
                       ResourceDifficulty.SPECIALIST, ResourceDifficulty.SPECIALIST,
                       ResourceDifficulty.SPECIALIST]
descriptions = ["Learn Chinese w/ ChineseFor.Us Beginner Chinese Lesson 1: Self-introduction"
                " in Mandarin Chinese | Beginner Course with 40 Beginner Chinese Lessons,"
                " 52 Video, 40 Quizzes, 400+ Questions. \n★Is this my level? Take quiz➥"
                "https://goo.gl/1jhrKS \n★Full Course➥https://ChineseFor.Us/Basic",
                "Trigonometry is used to calculate angles and lengths of different shapes and sizes.\n"
                "It is generally used in construction, sound engineering etc. This worksheet looks at using sketches "
                "in trigonometry, as well identities and graphs.\nThe worksheet also works"
                " through general and specific solutions and ends with a 3D-trigonometry question.",
                "This is a video on the basics of Analytical Geometry. This covers the distance formula;"
                " determining the midpoint of a line segment; gradient as well as the angle of inclination.",
                "Grade 12"
                "\nMathematics | Calculus  | NTE"
                "\n\nHello everyone and welcome back to NTE🙆"
                "\nIn today's video, we are looking at looking a brief history and"
                " application of calculus.  This is the introduction video"
                " to the new calculus playlist that will look at:"
                "\n\n●Introduction to Limits ( An intuitive understanding )"
                "\n●Differentiation by first principle"
                "\n●Differentiation using basic differentiation rules"
                "\n●The second derivative"
                "\n●Sketching of cubic functions"
                "\n●Optimization problems"
                "\n●The Calculus of motion",
                "Factor the following quadratic expressions."]

resource_tags = [[tags["1_min_tutorial"], tags['distance_teaching']],
                 [tags["Math_practice_sheet"], tags["brainstorming"]],
                 [tags["Math_Tutorial"]],
                 [tags["Math_Tutorial"], tags["metric_math"]],
                 [tags["Math_practice_sheet"]]]

OFFSET = 6
for i in range(6, 11):
    name = random_person.name()
    avatar = pagan.Avatar(name, pagan.MD5)
    file_path = "thumbnail"
    file_name = resource_titles[i - OFFSET].replace(' ', '_') + ".png"
    avatar.save("static/" + file_path, file_name)
    file_path += f"/{file_name}"
    creaters = sample(users_id, k=1)
    compliment = list(set(users_id) - set(creaters))
    # creater must included in personnel
    personnel = creaters + sample(compliment, k=random.randint(0, min(3, len(compliment))))
    # print(personnel)
    personnel = list(set(personnel))
    globals()[f"src{i}"] = add_resource(title=resource_titles[i - OFFSET],
                                        resource_link=resource_links[i - OFFSET],
                                        difficulty=resource_difficulty[i - OFFSET],
                                        tags_id=resource_tags[i - OFFSET],
                                        grade=grades[i - OFFSET],
                                        subject=subjects[i - OFFSET],
                                        description=descriptions[i - OFFSET],
                                        creaters_id=creaters,
                                        is_public=False,
                                        private_personnel_id=personnel,
                                        resource_thumbnail_links=[file_path])
    for j in range(random.randint(0, len(personnel))):
        # add resource comments
        add_pseudo_comment_to_resource(rid=globals()[f"src{i}"], accessors_id=personnel)
    # vote resource
    voters = get_random_voters(accessors=personnel)
    for uid in voters:
        vote_resource(uid=uid, rid=globals()[f"src{i}"],
                      upvote=bool(random.getrandbits(1)))

# create 5 channels
channel_names = sample(random_texts, k=5)
visibility = 2 * [ChannelVisibility.PUBLIC] + [ChannelVisibility.INVITE_ONLY] + \
             2 * [ChannelVisibility.FULLY_PRIVATE]
# deliberately set admins of 2 public channels to be user 0 (uid = 1)
admins = 2 * [1] + sample(users_id, k=3)
channel_subjects, channel_grades, channel_descriptions = [], [], []
for i in range(0, 5):
    has_subject, has_grade = bool(random.getrandbits(1)), bool(random.getrandbits(1))
    channel_subjects.append(choice(subject_list) if has_subject else None)
    channel_grades.append(choice(grade_list) if has_grade else None)
    description = " ".join(random.sample(random_texts, k=random.randint(1, 3)))
    channel_descriptions.append(description)
for i in range(0, 5):
    if visibility[i] != ChannelVisibility.PUBLIC:
        personnel = sample(users_id, k=random.randint(1, len(users_id)))

        # add user 1 to channel 2 deliberately
        if i == 2:
            personnel.append(1)

        # get rid of duplicate admin_id, if selected by random
        personnel = list(set(personnel))
    else:
        personnel = None
    globals()[f"cid{i}"] = create_channel(name=channel_names[i],
                                          visibility=visibility[i],
                                          admin_uid=admins[i],
                                          subject=channel_subjects[i],
                                          grade=channel_grades[i],
                                          description=channel_descriptions[i],
                                          tags_id=sample(list(tags.values()), k=random.randint(1, len(tags))),
                                          personnel_id=personnel)
    # print(f"personnel for cid = {globals()[f'cid{i}']} is {personnel}")

    max_cont = len(personnel) if visibility[i] != ChannelVisibility.PUBLIC else len(users_id)
    for j in range(random.randint(0, max_cont)):
        add_pseudo_channel_post_and_replies(cid=globals()[f"cid{i}"],
                                            accessors_id=personnel
                                            if personnel is not None else users_id)
