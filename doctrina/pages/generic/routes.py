from flask import abort, redirect, render_template, request, url_for
from flask_login import current_user

from doctrina.database.database import get_user_teaching_areas
from doctrina.database.models import User

from . import bp

current_user: User


@bp.route("/")
def index():
    """The index root directory of this website
    Redirects to the home page
    """
    return redirect(url_for("home"))


@bp.route("/home")
def home():
    """The home page of the website
    Shows recommendations based on the user profile or if not authenticated the
    most upvote

    Also the end point of the search function where the search is a get method
    """
    areas = get_user_teaching_areas(current_user.uid)
    areas = areas if areas is not None else []
    messages = [
        "Richard Fritz responded to your channel comment",
        "Scott Wilson responded to your resource comment",
        "Amanda Moore responded to your channel comment",
        "Amanda Moore liked your resource",
        "Richard Fritz commented on your resource",
        "Richard Fritz commented to your resource",
    ]
    return render_template("home.html", title="Home", teaching_areas=areas, messages=messages)


@bp.route("/about")
def about():
    """A brief page descibing what the website is about"""
    # FAQs can contain html code to run on page
    faqs = [
        [
            "What is Doctrina?",
            "Doctrina is a website made for teachers to share in class activities, resources and more with each other. "
            "It is designed so that you - the teacher - finds it easier to do the thing you love most: teach! We help "
            "you find worksheets, tutorials and questions for your students so you can spoend more time teaching them, "
            "rather then putting time into creating said worksheets, tutorials and questions.",
        ],
        [
            "What can I use Doctrina for?",
            "You can share resources you found useful in your class, find a resource from another teacher to use in "
            "class, read insights and helpful notes for teaching a certain subject, and more! Doctrina also includes an "
            "online forum that allows you to talk to other teachers like you.",
        ],
        [
            "How do I make an account?",
            "Just click the login button in the top right and click create an account. We only require basic information "
            "about you and for legal reasons, official documentation stating you are a teacher (this is to make sure "
            "that none of your students get access to the site and taking advantage of your resources that you may be "
            "using with them)",
        ],
        [
            "How do I find a resource?",
            "We have an advanced searching algorithm that makes use of 'tags' to sort and search data. Each channel and "
            "resource are associated with tags given by the creator which can help narrow down your search to only "
            "results you want to see.",
        ],
        [
            "How do I create a resource?",
            "Go to our resources page and click the create button. A resource can be given a title, description, "
            "a file can be uploaded if you choose to, and obviously tags to help define what areas, subjects and year "
            "levels your resource falls into.",
        ],
        [
            "How can I talk to other teachers?",
            "Our channels page contains multiple forums discussing various subjects, resources and teaching aspects. "
            "Each channel contains threads to discuss specifics about the overarching subject. Each thread can be "
            "replied to by teachers who want ot discuss and talk to others. You can create your own channels and threads "
            "by clicking create either in the main channels page or inside a channel if you would like to start a "
            "thread.",
        ],
        [
            "How is a resources' popularity decided?",
            "Each teacher can upvote or downvote a resource if they like or dislike it respectively. Resources with more "
            "upvotes are more popular and resources with more downvotes are less popular. In order to balance out "
            "upvotes and downvotes on a resource, we use an algorithm to decide how popular it is. Resources are sorted "
            "by popularity after you search.",
        ],
        [
            "What do I do if I see a resource that breaks TOS?",
            "On each resource page there is a report button located next to the author name. If you believe the "
            "resource is breaking our Terms of Service, click the button to notify our moderators to investigate it, and "
            "if it has broken TOS, it will be swiftly removed from our site.",
        ],
    ]
    return render_template("about.html", title="About Us", name="About Us", faqs=faqs, num=len(faqs))


@bp.route("/debug")
def debug():
    """A debugging page
    not to be used in production
    """
    error = request.args.get("error") if "error" in request.args else None
    if error is not None:
        abort(int(error))

    return render_template("debug.html", title="DEBUG", variable=f"{1}")
