from flask import Flask, request, render_template, redirect, url_for, abort, flash, Response, jsonify
from sqlalchemy.sql.expression import func
import os
import json
import random
import warnings
import os
import posixpath
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, AnonymousUserMixin
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException, InternalServerError
from re import search as re_search
# If in branch use the following
# from .DBFunc import *
# from .forms import LoginForm, RegisterForm, ResourceForm
# If in main use the following
from DBFunc import *
from forms import LoginForm, RegisterForm, ResourceForm

# -----{ INIT }----------------------------------------------------------------
DEBUG = True

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "You need to be logged in to view this page"
login_manager.login_message_category = "error"

# NOTE: added for flush() usage
app.secret_key = "admin"

# File upload
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
app.config['MAX_CONTENT_PATH'] = 50  # 50 chars long


# -----{ LOGIN }---------------------------------------------------------------


class Anonymous(AnonymousUserMixin):
    def __init__(self):
        self.uid = -1
        self.username = "Guest User"

    def __str__(self):
        return f"Anonymous User: uid = {self.uid}"

    def __repr__(self):
        return __str__(self)


login_manager.anonymous_user = Anonymous


@login_manager.user_loader
def load_user(user_id):
    """
        :param unicode user_id: user_id (email) user to retrieve
    """
    return get_user(user_id)


# -----{ PAGES }---------------------------------------------------------------
#
# This section contains the different landing pages for the web page
#
# -----{ PAGES.MAIN }----------------------------------------------------------
@app.route('/')
def index():
    """The index root directory of this website
    Redirects to the home page
    """
    return redirect(url_for('home'))


@app.route('/home')
def home():
    """The home page of the website
    Shows recomendations based on the user profile or if not authenticated the
    most upvoted

    Also the end point of the search function where the search is a get method
    """
    return render_template('home.html', title='Home')


# -----{ PAGES.LOGIN }---------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for a user to authenticate

    Asks for the users email and password.

    Gives feedback on fail, redirects to referring page on success
     (through GET data), if not refered then home page
    """
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        if email:
            user = get_user(email)
            if user != ErrorCode.INVALID_USER and check_password_hash(user.hash_password, form.password.data):
                user_auth(user.email, True)
                login_user(user, remember=False)
                if 'next' in request.args:
                    return redirect(request.args.get("next"))
                return redirect(url_for('home'))
        flash('That username or password was incorrect', "error")
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
@login_required
def logout():
    """Logout page
    Redircts in 3 seconds
    """
    user_auth(current_user.email, False)
    logout_user()
    flash('You have been logged out. This page will redirect in 3 seconds', "info")
    return render_template("logout.html", title='Logout')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Page for a user to register for an account

    Must provide: username, email, password (with conditions)

    Optionally provide: interests / subjects tags

    Other user fields are configured in profile()
    """
    data = {
        "username": False,
        "emailUsed": False,
        "passwordMsg": False,
        "passwordDif": False
    }
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        if email:
            user = get_user(email)
            # Ensure new account
            if user != ErrorCode.INVALID_USER:
                data['emailUsed'] = 'An account with that email already exists'
                # flash('An account with that email already exists',"error")
                return render_template('register.html', title='Register', form=form, data=data)
            # email validation
            if re_search('@', email) is None:
                data["emailUsed"] = "You must provide a valid email"
            username = form.username.data
            if not username:
                data['username'] = 'You must provide a username'
            password = form.password.data
            passwordConfirm = form.passwordConfirm.data
            # Check passwords
            if not password or not passwordConfirm:
                data['passwordMsg'] = 'You must provide a valid password'
            if password != passwordConfirm:
                data['passwordDif'] = True
            if len(password) < 8:
                data['passwordMsg'] = "Make sure your password is at lest 8 letters"
            elif re_search('[0-9]', password) is None:
                data['passwordMsg'] = "Make sure your password has a number in it"
            elif re_search('[A-Z]', password) is None:
                data['passwordMsg'] = "Make sure your password has a capital letter in it"
            else:
                # add user and log in
                res = add_user(username, password, email)
                if res != ErrorCode.COMMIT_ERROR:
                    user = get_user(email)
                    user_auth(user.email, True)
                    login_user(user, remember=False)
                    return redirect(url_for('home'))
                flash('Something went wrong, please try again', "error")
        else:
            data['emailUsed'] = 'You must provide a valid email'
    return render_template('register.html', title='Register', form=form, data=data)


# -----{ PAGES.RESOURCE }------------------------------------------------------

@app.route('/resource')
@app.route('/resource/<int:rid>')
def resource(rid=None):
    """Page for a resource

    If no resource ID is set then the home page is shown
    If a resource ID is set then that resource page is shown

    Shows information based on the resource type and content

    :param rid: The resource id

    If the currently logged in user does not have access to the resource then
    they are given a 403
    If the resource does not exist then they are given a 404
    """
    # Base resource page
    if rid is None:
        return render_template('resource.html', title='Resources')
    uid = current_user.uid
    # individual resource page
    user, res = get_user_and_resource_instance(uid=uid, rid=rid)
    # resource does not exist
    if res is None:
        abort(404, description="The requested resource does not exist")
    # user has access to resource
    if not is_resource_public(rid=rid) and (user is None or not user_has_access_to_resource(uid=uid, rid=rid)):
        abort(403,
              description=f"You ({current_user.username}) do not have permission to access the resource : {res.title}" + "\nIf you think this is incorrect contact the resource owner")

    # convert utc time to AEST
    created_at = res.created_at.astimezone(pytz.timezone("Australia/Brisbane"))

    # render the template
    kwargs = {
        "title": res.title,
        "rid": rid,
        "uid": uid,
        "res": res,
        "difficulty": enum_to_website_output(res.difficulty),
        "subject": enum_to_website_output(res.subject),
        "grade": enum_to_website_output(res.grade),
        "resource_tags": get_resource_tags(res.rid),
        "authors": get_resource_author(res.rid),
        "banner": get_resource_thumbnail(rid) if get_resource_thumbnail(rid) != ErrorCode.INVALID_RESOURCE else {
            'thumbnail_link': 'img/placeholder.png'}
    }
    return render_template("resource_item.html", **kwargs)


@app.route('/resource/new', methods=['GET', 'POST'])
@login_required
def resource_new():
    """The user creates a new resource
    """
    form = ResourceForm()
    if form.validate_on_submit():
        title = form.title.data
        resource_file = request.files[form.files.name]
        resource_link = resource_file.filename
        resource_thumbnail_file = request.files[form.thumbnail.name]
        resource_thumbnail_links = resource_thumbnail_file.filename

        difficulty = ResourceDifficulty.EASY
        try:
            subject = Subject[request.form.get('subject').replace(' ', '_').upper()]
        except KeyError:
            subject = None
        try:
            grade = Grade[request.form.get('grades').replace(' ', '_').upper()]
        except KeyError:
            grade = None
        creaters_id = [current_user.uid]
        private_personnel_id = [get_user(email).uid for email in request.form.getlist('personnel_ids') if
                                get_user(email) != ErrorCode.INVALID_USER]
        is_public = len(private_personnel_id) == 0

        tags_id = [get_tags()[t] for t in request.form if t == request.form.get(t) and t in get_tags(t)]
        description = form.description.data

        i = 0
        while os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], 'resource', secure_filename(resource_link))):
            root, ext = os.path.splitext(resource_link)
            resource_link = root + '_' + str(i) + ext
            i += 1
        i = 0
        while os.path.isfile(
                os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnail', secure_filename(resource_thumbnail_links))):
            root, ext = os.path.splitext(resource_thumbnail_links)
            resource_thumbnail_links = root + '_' + str(i) + ext
            i += 1

        resource_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'resource', secure_filename(resource_link)))
        resource_thumbnail_file.save(
            os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnail', secure_filename(resource_thumbnail_links)))

        rid = add_resource(title, os.path.join('resource', secure_filename(resource_link)), difficulty, subject, grade,
                           creaters_id, is_public,
                           private_personnel_id, tags_id,
                           description, [os.path.join('thumbnail', secure_filename(resource_thumbnail_links))])
        if isinstance(rid, ErrorCode):
            abort(400)
        flash("Resource created", 'info')
        return redirect(url_for('resource', rid=rid))
    return render_template('resource_create.html', title='New Resource', form=form)
    # todo


@app.route("/resource/<rid>/edit", methods=["GET", "POST"])
def resource_edit(rid=None):
    """
    The user edits a resource they authored.

    If current_user is not the creater of this resource, return to
    current resource page. If rid is not given, redirects to resource home page
    """
    if not rid:
        return redirect(url_for("resource"))

    rid = int(rid)
    _, resource_item = get_user_and_resource_instance(uid=-1, rid=rid)

    if not resource_item:
        flash("rid is invalid", "error")
        return redirect(url_for("resource"))

    with Session() as conn:
        creater_uid = conn.query(ResourceCreater).filter_by(rid=rid).first().uid
        if creater_uid != current_user.uid:
            # current user does not have privilege to edit this resource,
            # return to resource home page
            flash("You do have edit access to current resource", "error")
            return redirect(url_for("resource"))

    form = ResourceForm()

    if request.method == "GET":
        form.title.data = resource_item.title
        form.description.data = resource_item.description

        if resource_item.resource_link.split("/")[0] == "resource":
            # local resource, gives title
            filename = resource_item.title
        else:
            # local resource, gives resource link
            filename = resource_item.resource_link

        current_grade = enum_to_website_output(resource_item.grade)

        current_subject = enum_to_website_output(resource_item.subject)

        with Session() as conn:
            thumbnails = conn.query(ResourceThumbnail).filter_by(rid=rid).all()

            thumbnails_filename = ""
            if thumbnails:
                for i in thumbnails:
                    thumbnails_filename += i.thumbnail_link.split("/")[-1] + ", "
                if thumbnails_filename[-2:] == ", ":
                    thumbnails_filename = thumbnails_filename[:-2]

            # populate private personnel
            personnel_email = []
            if not resource_item.is_public:
                for i in conn.query(PrivateResourcePersonnel).filter_by(rid=rid).all():
                    allowed_person = conn.query(User).filter_by(uid=i.uid).first()
                    if allowed_person.uid != creater_uid:
                        personnel_email.append(allowed_person.email)

            tag_map = get_tags(mapping="id2name")
            applied_tags = []
            for tag in conn.query(ResourceTagRecord).filter_by(rid=rid).all():
                applied_tags.append(tag_map.get(tag.tag_id))

        visibility = "Public" if resource_item.is_public else "Private"

        return render_template("resource_edit.html", title=f"Edit resource #{rid}", form=form,
                               filename=filename, thumbnails_filename=thumbnails_filename,
                               subject=current_subject, grade=current_grade,
                               current_visibility=visibility, personnel_emails=personnel_email,
                               applied_tags=applied_tags, rid=rid)
    elif request.method == "POST":
        # update resource: currently do not update other tags
        title = form.title.data
        resource_thumbnail_file = request.files[form.thumbnail.name]
        subject = website_input_to_enum(request.form.get('subject'), Subject)
        grade = website_input_to_enum(request.form.get('grades'), Grade)
        description = form.description.data
        is_public = True if request.form.get("visibility_choice") == 'Public' else False

        thumbnail_path = None
        if resource_thumbnail_file and resource_thumbnail_file.filename != "":
            thumbnail_path = posixpath.join("thumbnail", secure_filename(
                resource_thumbnail_file.filename))
            resource_thumbnail_file.save(posixpath.join(
                app.config['UPLOAD_FOLDER'], thumbnail_path))
        thumbnail_path = [thumbnail_path] if thumbnail_path else []

        if not description:
            description = "NULL"

        if isinstance(modify_resource(rid=rid, title=title, subject=subject, grade=grade,
                                      is_public=is_public, description=description,
                                      resource_thumbnail_links=thumbnail_path),
                      ErrorCode):
            flash("Something went wrong, please try again.", "error")
            return redirect(url_for("resource_edit", rid=rid))

        flash("Edited successfully.", 'info')
        return redirect(url_for("resource", rid=rid))

    # invalid call, go back to resource home page
    return redirect(url_for("resource"))


# -----{ PAGES.RESOURCE.AJAX }-------------------------------------------------

@app.route('/AJAX/resourceAJAX')
def resourceAJAX():
    """The endpoint for the AJAX search for resources using a get request
    returns it in json format
    """
    title = request.args.get('title') if 'title' in request.args else None
    subject = request.args.get('subject').upper() if 'subject' in request.args else None
    year = request.args.get('year').upper() if 'year' in request.args else None
    tags = request.args.getlist('tags[]') if 'tags[]' in request.args else None
    tags = list(filter(lambda x: x != '', tags)) if tags is not None else None
    sort = request.args.get('sort') if 'sort' in request.args else "natural"
    try:
        subject = Subject[subject]
    except KeyError:
        subject = None
    try:
        year = Grade[year]
    except KeyError:
        year = None
    if title == '':
        title = None
    return jsonify([dict(i.serialize, tags=get_resource_tags(i.rid),
                         banner=get_resource_thumbnail(i.rid).serialize if get_resource_thumbnail(
                             i.rid) != ErrorCode.INVALID_RESOURCE else {'thumbnail_link': 'img/placeholder.png'}) for i
                    in find_resources(title=title, subject=subject, grade=year, tags=tags, sort_by=sort)])


@app.route('/AJAX/resourceVote')
def resourceVote():
    """The endpoint for the AJAX search for resources voting a get request
    returns it in json format
    """
    rid = request.args.get('rid') if 'rid' in request.args else None
    up = request.args.get('up') if 'up' in request.args else None
    down = request.args.get('down').upper() if 'down' in request.args else None
    if rid is None:
        abort(404)
    if up is None or down is None:
        abort(404)
    vote_res = vote_resource(uid=current_user.uid, rid=rid, upvote=up == '1')
    _, res = get_user_and_resource_instance(-1, rid)
    if res is None:
        abort(404)
    return jsonify({
        'up': res.upvote_count,
        'down': res.downvote_count
    })


@app.route('/AJAX/resourceComment')
def resourceComment():
    """The endpoint for the AJAX search for resource comments a get request
    returns it in json format
    """
    rid = request.args.get('rid') if 'rid' in request.args else None
    if rid is None:
        abort(404)
    postType = request.args.get('type') if 'type' in request.args else None
    if postType is not None:
        text = request.args.get('text') if 'text' in request.args else None
        # quit if bad data
        if text is None:
            abort(404)
        if postType == 'comment':
            res = comment_to_resource(current_user.uid, rid, text)
            if isinstance(res, ErrorCode):
                abort(404)
        elif postType == 'reply':
            cid = request.args.get('cid') if 'cid' in request.args else None
            if cid is None:
                abort(404)
            res = reply_to_resource_comment(current_user.uid, cid, text)
            if isinstance(res, ErrorCode):
                abort(404)
        else:
            abort(404)

    # individual resource page
    _, res = get_user_and_resource_instance(uid=-1, rid=rid)
    comms = get_resource_comments(res.rid)
    comments = []
    for comment in comms:
        replies = get_resource_comment_replies([comment])
        rep = []
        if comment in replies:
            for reply in replies[comment]:
                rep.append({
                    "reply": reply.serialize,
                    "author": get_user_and_resource_instance(reply.uid, -1)[0].serialize
                })

        comments.append({
            "comment": comment.serialize,
            "resource_comment_id": comment.resource_comment_id,
            "replies": rep,
            "author": get_user_and_resource_instance(comment.uid, -1)[0].serialize
        })
    return jsonify(comments[::-1])


# -----{ PAGES.PROFILE }-------------------------------------------------------

@app.route('/profile', methods=["GET"])
@login_required
def profile():
    """
    The default view of a users profile,
    this can be used to view your own profiles.
    Specified with the GET request
    """
    teaching_areas = []

    # get hold number
    user_rating_whole = int(current_user.user_rating)
    # get if a user's honor rating is greater than int.5
    user_rating_half = 0 if current_user.user_rating - user_rating_whole < .5 else 1
    # empty stars
    user_rating_unchecked = 5 - user_rating_whole - user_rating_half

    with Session() as conn:
        for area in conn.query(UserTeachingAreas). \
                filter_by(uid=current_user.uid, is_public=True).all():
            # concat both grade + subject
            text = enum_to_website_output(area.grade) + " " + \
                   enum_to_website_output(area.teaching_area)
        teaching_areas.append(text)

    return render_template('profile.html', title='Profile', user=current_user.serialize,
                           teaching_areas=teaching_areas, rating_whole=user_rating_whole,
                           rating_half=user_rating_half, rating_unchecked=user_rating_unchecked)


@app.route("/profile/studio_contents", methods=["GET"])
def load_studio_contents():
    """
    Load the entries for user edit studio. Entries here can be channel or resource
    """
    # resource/channel
    load_type = request.args.get("load_type")
    # create/access
    create_or_access = request.args.get("create_or_access")
    title = request.args.get("title")
    # ascending/descending of date
    sort_algo = request.args.get("sort_algo")
    uid = request.args.get("uid")

    if not uid:
        return
    uid = int(uid)

    # set default refinement strategy
    if load_type not in ["resource", "channel"]:
        load_type = "resource"

    if create_or_access not in ["create", "access"]:
        create_or_access = "create"

    if sort_algo not in ['ascending', "descending"]:
        sort_algo = 'ascending'
    sort_algo = sort_algo.lower()

    if title == "":
        title = None

    is_resource = True if load_type == "resource" else False
    is_create = True if create_or_access == "create" else False

    out = []
    if is_resource:
        # deal with resource
        qualified_ids = []
        with Session() as conn:
            if is_create:
                # resources created by user
                for temp in conn.query(ResourceCreater).filter_by(uid=uid).all():
                    qualified_ids.append(temp.rid)
            else:
                # resources user has access to
                for temp in conn.query(PrivateResourcePersonnel).filter_by(uid=uid).all():
                    qualified_ids.append(temp.rid)
            res = conn.query(Resource).filter(Resource.rid.in_(qualified_ids))
        if title:
            res = res.filter(Resource.name.ilike(f"%{title}%"))
        if sort_algo == "ascending":
            res = res.order_by(Resource.created_at.asc()).all()
        else:
            res = res.order_by(Resource.created_at.desc()).all()
        for item in res:
            info = item.serialize
            if not is_create:
                # fill manage link to null
                info["manage_link"] = None
            else:
                info["manage_link"] = url_for("resource_edit", rid=item.rid)

            out.append(info)
    else:
        # deal with channel
        sort_by_newest_date = True if sort_algo == "descending" else False
        if create_or_access == "create":
            # channels created by user
            res = find_channels(channel_name=title, admin_uid=uid,
                                sort_by_newest_date=sort_by_newest_date)
        else:
            # channels user has access to: private only
            res = find_channels(channel_name=title, caller_uid=uid,
                                sort_by_newest_date=sort_by_newest_date, is_public=False)

        for item in res:
            info = item.serialize

            # need to change attribute "name"  to "title"
            info["title"] = info["name"]
            del info["name"]

            # add upvote_count, downvote_count to '-'
            info["upvote_count"], info["downvote_count"] = '-', '-'

            if not is_create:
                # fill manage link to null
                info["manage_link"] = None
            else:
                info["manage_link"] = url_for("create_or_modify_channel", cid=item.cid)
            out.append(info)
    return jsonify(out)


@app.route("/profile/settings", methods=["GET", "POST"])
@login_required
def settings():
    """
    Render user settings page when receiving GET request.

    Update user settings when receiving POST request.
    """
    # todo: tag system not implemented
    if request.method == "GET":
        # send all info of the user and render template
        subjects = [enum_to_website_output(i) for i in Subject if i != Subject.NULL]
        grades = [enum_to_website_output(i) for i in Grade if i != Grade.NULL]

        return render_template("settings.html", title="User Settings",
                               user_info=current_user.serialize)
    else:
        # POST method
        username, bio, old_password, new_password = \
            request.form.get("username"), request.form.get("bio"), \
            request.form.get("old_password"), request.form.get("new_password")
        avatar, profile_background = \
            request.files.get("avatar"), request.files.get("profile_background")

        if not bio:
            bio = "NULL"

        avatar_path, profile_background_path = "NULL", "NULL"
        if avatar and avatar.filename != "":
            avatar_path = posixpath.join("avatar", secure_filename(avatar.filename))
            avatar.save(posixpath.join("static", avatar_path))

        if profile_background and profile_background.filename != "":
            profile_background_path = posixpath.join("profile_background",
                                                     secure_filename(
                                                         profile_background.filename))
            profile_background.save(posixpath.join("static", profile_background_path))

        user, _ = get_user_and_resource_instance(uid=current_user.uid, rid=-1)

        if not old_password and not check_password_hash(user.hash_password, old_password):
            # old password does not match, do not change password
            new_password = None

        if isinstance(
                modify_user(uid=current_user.uid, username=username,
                            password=new_password, bio=bio, avatar_link=avatar_path,
                            profile_background_link=profile_background_path),
                ErrorCode):
            # invalid action
            flash("Cannot modify user profile at this time, try later", "error")
            return redirect(url_for("settings"))
        # success
        flash("Profile modified successfully", "info")
        return redirect(url_for("profile"))


# -----{ PAGES.GENERIC }-------------------------------------------------------

@app.route('/about')
def about():
    """A brief page descibing what the website is about"""
    # FAQs can contain html code to run on page
    faqs = [
        ["What is Doctrina?",
         "Doctrina is a website made for teachers to share in class activities, resources and more with each other. "
         "It is designed so that you - the teacher - finds it easier to do the thing you love most: teach! We help "
         "you find worksheets, tutorials and questions for your students so you can spoend more time teaching them, "
         "rather then putting time into creating said worksheets, tutorials and questions."],
        ["What can I use Doctrina for?",
         "You can share resources you found useful in your class, find a resource from another teacher to use in "
         "class, read insights and helpful notes for teaching a certain subject, and more! Doctrina also includes an "
         "online forum that allows you to talk to other teachers like you."],
        ["How do I make an account?",
         "Just click the login button in the top right and click create an account. We only require basic information "
         "about you and for legal reasons, official documentation stating you are a teacher (this is to make sure "
         "that none of your students get access to the site and taking advantage of your resources that you may be "
         "using with them)"],
        ["How do I find a resource?",
         "We have an advanced searching algorithm that makes use of 'tags' to sort and search data. Each channel and "
         "resource are associated with tags given by the creator which can help narrow down your search to only "
         "results you want to see."],
        ["How do I create a resource?",
         "Go to our resources page and click the create button. A resource can be given a title, description, "
         "a file can be uploaded if you choose to, and obviously tags to help define what areas, subjects and year "
         "levels your resource falls into."],
        ["How can I talk to other teachers?",
         "Our channels page contains multiple forums discussing various subjects, resources and teaching aspects. "
         "Each channel contains threads to discuss specifics about the overarching subject. Each thread can be "
         "replied to by teachers who want ot discuss and talk to others. You can create your own channels and threads "
         "by clicking create either in the main channels page or inside a channel if you would like to start a "
         "thread."],
        ["How is a resources' popularity decided?",
         "Each teacher can upvote or downvote a resource if they like or dislike it respectively. Resources with more "
         "upvotes are more popular and resources with more downvotes are less popular. In order to balance out "
         "upvotes and downvotes on a resource, we use an algorithm to decide how popular it is. Resources are sorted "
         "by popularity after you search."],
    ]
    return render_template('about.html', title='About Us', name="About Us", faqs=faqs, num=len(faqs))


# -----------------------------------{ PAGES.CHANNEL } ----------------------------------------


@app.route("/channel/<cid>/edit", methods=["GET", "POST"])
@app.route('/channel/create', methods=["POST", "GET"])
@login_required
def create_or_modify_channel(cid=None):
    """
    The user creates or modifies a channel

    If GET request and no cid, render channel create page; otherwise return previous info

    If POST request, collect information needed to create/modify a channel, then redirect
    to channel page. Discard changes/ Draft will redirect back to current channel page for
    edit; or channel home page for create.

    When create/edit success, redirects to current channel page
    """
    # todo: other_tag system not implemented

    if request.method == "GET":
        # reverse visibility options so PUBLIC is always the default choice for creation
        visibility_options = [enum_to_website_output(i) for i in ChannelVisibility][::-1]
        subjects = [enum_to_website_output(i) for i in Subject if i != Subject.NULL]
        grades = [enum_to_website_output(i) for i in Grade if i != Grade.NULL]
        kwargs = {
            "other_tags": get_tags().keys(),
            "visibility_options": visibility_options,
            "subjects": subjects,
            "grades": grades
        }

        if not cid:
            kwargs["title"] = "new channel"
            # create channel
            template = "create_channel.html"
        else:
            # modify channel
            cid = int(cid)

            if not user_has_access_to_channel(cid=cid, uid=current_user.uid):
                # no permission, go back to channel home page
                flash("You do not have permission to visit this page")
                return redirect(url_for("view_channel"))

            kwargs["title"] = f"edit channel#{cid}"

            with Session() as conn:
                channel = conn.query(Channel).filter_by(cid=cid).first()
                if not channel:
                    return redirect(url_for("view_channel"))

                kwargs["channel"] = channel
                kwargs["current_subject"] = enum_to_website_output(channel.subject)
                kwargs["current_grade"] = enum_to_website_output(channel.grade)
                kwargs["current_visibility"] = enum_to_website_output(channel.visibility)

                personnel_emails = []
                if channel.visibility != ChannelVisibility.PUBLIC:
                    channel_personnel = conn.query(ChannelPersonnel).filter_by(cid=cid).all()
                    for i in channel_personnel:
                        if i.uid != channel.admin_uid:
                            # do not display admin_uid
                            personnel_emails.append(conn.query(User).filter_by(uid=i.uid).first().email)
                kwargs["personnel_emails"] = personnel_emails

                tag_records = conn.query(ChannelTagRecord).filter_by(cid=cid).all()
                tag_id_to_name = get_tags(mapping="id2name")
                tags_used = []
                for i in tag_records:
                    tags_used.append(tag_id_to_name[i.tag_id])
                kwargs["tags_used"] = tags_used

                template = "edit_channel.html"
        return render_template(template, **kwargs)

    elif request.method == "POST":
        # response to request
        name, description, personnel_emails, visibility, subject, grade, thumbnail = \
            request.form.get("channel_title"), request.form.get('channel_description'), \
            request.form.getlist("personnel_ids"), \
            request.form.get("visibility_choice"), request.form.get("subject"), \
            request.form.get("grade"), request.files.get("thumbnail")

        thumbnail_path = None
        if thumbnail.filename != "":
            thumbnail_path = posixpath.join("channel_avatar", secure_filename(thumbnail.filename))
            thumbnail.save(posixpath.join("static", thumbnail_path))

        visibility = website_input_to_enum(readable_string=visibility,
                                           enum_class=ChannelVisibility)

        subject = website_input_to_enum(readable_string=subject, enum_class=Subject)

        grade = website_input_to_enum(readable_string=grade, enum_class=Grade)

        # convert personnel emails to personnel ids
        personnel_ids = []
        for i in personnel_emails:
            user = get_user(i)
            if not isinstance(user, ErrorCode):
                personnel_ids.append(user.uid)

        if not cid:
            # create channel
            cid = create_channel(name=name, visibility=visibility,
                                 admin_uid=current_user.uid, subject=subject,
                                 grade=grade, description=description,
                                 personnel_id=personnel_ids, avatar_link=thumbnail_path)
            if isinstance(cid, ErrorCode):
                flash("Cannot create channel at the moment")
                return redirect(url_for("create_or_modify_channel"))

            # created, now goes to view channel page
            flash("Channel created")
        else:
            # edit channel
            if not subject:
                subject = Subject.NULL
            if not grade:
                grade = Grade.NULL

            modify_channel(cid=cid, name=name, visibility=visibility, admin_uid=current_user.uid,
                           subject=subject, grade=grade, description=description,
                           personnel_ids=personnel_ids, avatar_link=thumbnail_path)
            flash("Channel edited")
        return redirect(url_for("view_channel", cid=cid))


@app.route('/channel')
@app.route("/channel/<cid>", methods=["POST", "GET"])
@login_required
def view_channel(cid=None):
    """The user view a channel page

    The home channel page is displayed when cid=None
    Allows user to create a channel etc.

    The channel/cid page shows the posts in that channel
    Allows users to add posts to the channel

    If cid is not valid name redirect to home channel page
    """
    if cid:
        # view a specific channel page
        with Session() as conn:
            channel = conn.query(Channel).filter_by(cid=cid).one_or_none()
            if not channel:
                flash("Invalid cid")
                return redirect(url_for("view_channel"))

            if not user_has_access_to_channel(cid=cid, uid=current_user.uid):
                # no permission, go back to channel home page
                flash("You do not have permission to visit this page")
                return redirect(url_for("view_channel"))

            admin = conn.query(User).filter_by(uid=channel.admin_uid).first()

            visibility = "Public" if channel.visibility == ChannelVisibility.PUBLIC else "Private"

            # generate some random posts and random contributors
            top_posts = conn.query(ChannelPost).filter_by(cid=cid).order_by(func.random()).limit(5).all()

            top_contributors = set()
            random_posts = conn.query(ChannelPost).filter_by(cid=cid).order_by(func.random()).limit(5).all()
            for i in random_posts:
                top_contributors.add(conn.query(User).filter_by(uid=i.uid).first().username)
            top_contributors = list(top_contributors)
        return render_template("channel_item.html", channel=channel, admin=admin,
                               user=current_user, is_admin=current_user.uid == channel.admin_uid,
                               visibility=visibility, top_posts=top_posts,
                               top_contributors=top_contributors, title=f"Channel #{channel.cid}")

    # load channel home page
    # todo: other_tag system not implemented
    return render_template("channel.html", user=current_user, title="Channel Home")


@app.route('/search/channel')
def search_channel():
    """
    Returns json object of all qualified channels
    """
    name = request.args.get("name")
    is_public = request.args.get("is_public")
    is_public = True if (is_public == 'true' or is_public is True) else False
    sort_by_date = True if request.args.get("sort_by_date") == "newest" else False
    uid = int(request.args.get("uid"))

    out = []

    with Session() as conn:
        for i in find_channels(channel_name=name, is_public=is_public,
                               sort_by_newest_date=sort_by_date):
            if not user_has_access_to_channel(uid=uid, cid=i.cid):
                # user does not have access to channel
                continue
            info = i.serialize

            # assign tag names of this channel
            info["all_tags"] = get_all_tags_for_channel(cid=i.cid)

            posts = conn.query(ChannelPost).filter_by(cid=i.cid)

            post_count = posts.count()

            recent_post_time, poster_name = None, None
            if post_count != 0:
                # get most recent post time and poster's username
                most_recent_post = posts.order_by(ChannelPost.created_at.desc()).first()
                recent_post_time = most_recent_post.created_at
                # change to local time
                recent_post_time = dump_datetime(recent_post_time)
                poster_name = conn.query(User).filter_by(
                    uid=most_recent_post.uid).first().username

            info["most_recent_post_time"] = recent_post_time
            info["recent_poster_username"] = poster_name
            info["post_count"] = post_count
            # info["channel_tags"] = channel_tags

            out.append(info)
    if not sort_by_date:
        # trending mode: fake a trend by shuffle
        random.shuffle(out)
    return jsonify(out)


# --------------------------{ PAGES.CHANNEL_POST }---------------------------------------


@app.route("/search/channel/<cid>/post")
def search_channel_post(cid=None):
    """
    Returns json object of posts of a specific channel
    """
    title = request.args.get("title")
    sort_algo = request.args.get("sort_algo").lower()
    cid = int(cid)

    out = []
    if sort_algo == "newest":
        posts = find_channel_posts(cid=cid, title=title, sort_algo='date')
    else:
        posts = find_channel_posts(cid=cid, title=title, sort_algo="upvote")

    with Session() as conn:
        for i in posts:
            info = i.serialize

            poster = conn.query(User).filter_by(uid=i.uid).first()
            poster_avatar_link = poster.avatar_link
            poster_username = poster.username

            post_comments = get_channel_post_comments(post_id=i.post_id)
            comments_count = len(post_comments)

            recent_comment_time, recent_commenter_name = None, None
            if comments_count != 0:
                most_recent_comment = conn.query(PostComment).filter_by(post_id=i.post_id). \
                    order_by(PostComment.created_at.desc()).first()
                recent_comment_time = most_recent_comment.created_at
                # convert to local time
                recent_comment_time = \
                    recent_comment_time.astimezone(pytz.timezone("Australia/Brisbane")). \
                        strftime("%d/%m/%Y, %H:%M:%S")
                recent_commenter_name = conn.query(User). \
                    filter_by(uid=most_recent_comment.uid).first().username
            info["comment_count"] = comments_count
            info["recent_comment_time"] = recent_comment_time
            info["recent_commenter_name"] = recent_commenter_name
            info["poster_avatar_link"] = url_for("static", filename=poster_avatar_link)
            info["poster_username"] = poster_username
            out.append(info)

    if sort_algo == "trending":
        # shuffle output to fake trending
        random.shuffle(out)
    return jsonify(out)


@app.route('/channel/<cid>/post/<post_id>')
@login_required
def view_channel_post(cid=None, post_id=None):
    """
    Function to show a channel post (include info of post itself as well as
    following post comments

    First check if current user has access to this channel; if not, redirect to channel
    main page.

    If current user is the post creater, then there will be an "edit" button
    shows up on screen so they can edit the post (edit_channel_post())
    """
    if not cid or not post_id:
        return redirect(url_for("view_channel"))
    cid, post_id = int(cid), int(post_id)

    if not user_has_access_to_channel(cid=cid, uid=current_user.uid):
        # no permission, go back to channel home page
        flash("You do not have permission to visit this page")
        return redirect(url_for("view_channel"))

    with Session() as conn:
        post = conn.query(ChannelPost).filter_by(post_id=post_id).one_or_none()
        channel = conn.query(Channel).filter_by(cid=cid).one_or_none()
        if not post or not channel:
            # post or channel does not exist, go back to current channel page
            flash("Post does not exists")
            return redirect(url_for("view_channel", cid=cid))

        # info of a post, include all items of a post and author's name
        post_info = post.serialize
        # get author of this post
        author = conn.query(User).filter_by(uid=post.uid).first()
        post_info["username"] = author.username + " (Author)"
        post_info["author_avatar_link"] = author.avatar_link

    # list of all post comments info, each element is a dict including all attributes
    # of a post comment as well as the username and link to user avatar of the commenter
    post_comments_info = []
    # get list of all comments related to that post
    post_comments = get_channel_post_comments(post_id=post_id)
    for i in post_comments:
        commenter = conn.query(User).filter_by(uid=i.uid).first()
        comment_info = i.serialize
        comment_info["username"] = commenter.username + " (Author)" \
            if commenter.username == author.username else commenter.username
        comment_info["commenter_avatar_link"] = commenter.avatar_link
        post_comments_info.append(comment_info)

    # check if current user is admin of the channel or owner of this post
    has_edit_privilege = post.uid == current_user.uid or channel.admin_uid == current_user.uid

    return render_template("post.html", title=f"Channel Post #{post.post_id}",
                           post_info=post_info, comments_info=post_comments_info,
                           has_edit_privilege=has_edit_privilege, channel=channel,
                           current_user=current_user)


@app.route("/channel/<cid>/post/create", methods=["POST", "GET"])
@app.route("/channel/<cid>/post/<post_id>/edit", methods=["POST", "GET"])
@login_required
def create_or_modify_channel_post(cid=None, post_id=None):
    """
    Add a new channel post to a channel or edit a channel post

    First check if current user has access to this channel; if not, redirect to channel
    main page.
    """
    if not cid:
        # no cid, return to channel main page
        return redirect(url_for("view_channel"))

    cid = int(cid)

    if not user_has_access_to_channel(cid=cid, uid=current_user.uid):
        # no permission, go back to channel home page
        flash("You do not have permission to visit this page", 'info')
        return redirect(url_for("view_channel"))

    with Session() as conn:
        channel = conn.query(Channel).filter_by(cid=cid).first()

    if request.method == "GET":
        if not post_id:
            #  create channel post page
            return render_template("create_post.html", channel=channel.serialize, title="new channel post")
        else:
            # edit channel post page
            with Session() as conn:
                post_id = int(post_id)
                post = conn.query(ChannelPost).filter_by(post_id=post_id).one_or_none()
                if not post:
                    # post to edit does not exists
                    return redirect(url_for("view_channel"))

                return render_template("edit_post.html", channel=channel.serialize,
                                       title=f'edit channel post#{post.post_id}',
                                       post_info=post.serialize)
    else:
        # POST request
        title, text = request.form.get("title"), request.form.get("init_text")

        if not post_id:
            # creation
            post_id = post_on_channel(uid=current_user.uid, title=title, text=text,
                                      cid=channel.cid)
            if isinstance(post_id, ErrorCode):
                # problem adding new post
                flash("Cannot proceed at the moment. Try again later.")
                return redirect(url_for("create_or_modify_channel", cid=cid))

            flash("Post created", "info")
            return redirect(url_for("view_channel_post", cid=cid, post_id=post_id))
        else:
            # edit channel post
            post_id = int(post_id)
            modify_channel_post(post_id, title=title, text=text)
            flash("Channel post successfully modified", "info")
            # redirect to current channel post page
            return redirect(url_for("view_channel_post", cid=channel.cid, post_id=post_id))


# ---------------------------------{ PAGES.CHANNEL POST & CHANNEL COMMENT }----------------------------


@app.route("/AJAX/channel/post/vote")
def vote_channel_post_or_comment():
    """
    Vote a channel post or post comment
    """
    voter_id = int(request.args.get("uid"))
    post_id_or_comment_id = int(request.args.get("id"))
    is_upvote = True if request.args.get("upvote") == "true" else False
    post_or_comment = request.args.get("post_or_comment")

    if post_or_comment == "post":
        # vote a channel post
        vote_res = vote_channel_post(uid=voter_id, post_id=post_id_or_comment_id, upvote=is_upvote)
    else:
        # vote post comment
        vote_res = vote_channel_post_comment(uid=voter_id, post_comment_id=post_id_or_comment_id,
                                             upvote=is_upvote)

    if vote_res == ErrorCode.SAME_VOTE_TWICE:
        flash("Please don't vote the same thing twice")

    with Session() as conn:
        if post_or_comment == "post":
            res = conn.query(ChannelPost).filter_by(post_id=post_id_or_comment_id).first()
        else:
            res = conn.query(PostComment).filter_by(post_comment_id=post_id_or_comment_id).first()

        return jsonify({
            # "id": post_id_or_comment_id,
            "upvote_count": res.upvote_count,
            "downvote_count": res.downvote_count
        })


@app.route("/channel/<cid>/post/<post_id>/comment/create", methods=["POST"])
@login_required
def add_new_post_comment(cid=None, post_id=None):
    """
    Add a new comment to a post
    """
    cid, post_id = int(cid), int(post_id)

    if not user_has_access_to_channel(cid=cid, uid=current_user.uid):
        # no permission, go back to channel home page
        flash("You do not have permission to visit this page")
        return redirect(url_for("view_channel"))

    text = request.form.get("comment_text")

    if text:
        comment_on_channel_post(uid=current_user.uid, text=text, post_id=post_id)
        flash("Commented successfully")
    return redirect(url_for("view_channel_post", cid=cid, post_id=post_id))


# -----{ PAGES.DEBUG }---------------------------------------------------------

@app.route('/debug')
def debug():
    """A debugging page
    not to be used in production
    """
    error = request.args.get('error') if 'error' in request.args else None
    if error is not None:
        abort(int(error))

    return render_template('debug.html', title='DEBUG', variable=f"{1}")


# -----{ ERRORS }--------------------------------------------------------------

@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return render_template("errors/error_generic.html", e=e), e.code

    # non-HTTP exceptions default to 500
    if DEBUG:
        warnings.warn(str(e))
        return render_template("errors/error_generic.html", e=InternalServerError(), fail=str(e)), 500
    return render_template("errors/error_generic.html", e=InternalServerError()), 500


# -----{ PROCESSORS }----------------------------------------------------------


@app.context_processor
def subject_processor():
    def enum_to_website_output(item: str) -> str:
        return item.replace('_', ' ').title()

    return dict(enum_to_website_output=enum_to_website_output)


@app.context_processor
def defaults():
    """Provides the default context processors

    Returns:
        dict: Variables for JINJA context
            current_user: the user the is currently logged in or the Anonymous user
            subject : A list of all subjects with their names
            grade : A list of all grades with their names
            tag : A list of all tags with their names
    """
    return dict(current_user=current_user,
                subjects=[e.name.lower() for e in Subject],
                grades=[e.name.lower() for e in Grade],
                tags=[e.replace(' ', '_') for e in get_tags().keys()])
