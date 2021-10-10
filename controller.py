from flask import Flask, request, render_template, redirect, url_for, abort, flash, Response, jsonify
from flask_login import login_required, current_user, LoginManager
from sqlalchemy.sql.expression import func
from werkzeug.utils import secure_filename
import os
import json
import random
# If in branch use the following
from .DBFunc import *

# If in main use the following
# from DBFunc import *

app = Flask(__name__)
# NOTE: added for flush() usage
app.secret_key = "admin"

# -----------------------{ INIT }---------------------------------------------------

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "You need to be logged in to view this page"
login_manager.login_message_category = "error"

# NOTE: added for flush() usage
app.secret_key = "admin"

# File upload
app.config['UPLOAD_FOLDER'] = 'static/files/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
app.config['MAX_CONTENT_PATH'] = 50  # 50 chars long


# -----------------------------{ LOGIN }----------------------------------------------


@login_manager.user_loader
def load_user(user_id):
    """
        :param unicode user_id: user_id (email) user to retrieve
    """
    return get_user(user_id)


@app.route('/')
def index():
    """The index root directory of this website"""
    return redirect(url_for('home'))


@app.route('/home')
def home():
    """The home page of the website
    Shows recomendations based on the user profile or if not authenticated the most upvoted

    Also the end point of the search function where the search is a get method
    """
    name = "Example User"
    if 'x-kvd-payload' in request.headers:
        userjson = request.headers['x-kvd-payload']
        user = json.loads(userjson)
        name = user['user']

    data = [
        {
            'title': "Example 1",
            'img': url_for('static', filename='img/placeholder.png')
        }, {
            'title': "Example 2",
            'img': url_for('static', filename='img/placeholder.png')
        }, {
            'title': "Example 3",
            'img': url_for('static', filename='img/placeholder.png')
        }, {
            'title': "Example 4",
            'img': url_for('static', filename='img/placeholder.png')
        }, {
            'title': "Example 5",
            'img': url_for('static', filename='img/placeholder.png')
        }
    ]

    return render_template('home.html', title='Home', name=name, data=data)


@app.route('/resource')
@app.route('/resource/<int:uid>/<int:rid>', methods=["GET", "POST"])
def resource(uid=None, rid=None):
    """Page for a resource

    Shows information based on the resource type and content

    :param uid: The user id
    :param rid: The resource id
    If resource or user is invalid then redirect to 404 page
    """
    if (uid is None and rid is not None) or (uid is not None and rid is None):
        redirect(url_for('resource'))  # base resource page
    if uid is None or rid is None:
        return render_template('resource.html',
                               title='Resources',
                               subject=[e.name.lower() for e in Subject],
                               grade=[e.name.lower() for e in Grade],
                               tag=get_tags().keys(),
                               resources=find_resources())

    # individual resource page
    user, res = get_user_and_resource_instance(uid=uid, rid=rid)
    if not user or not res:
        # invalid user or resource, pop 404
        abort(404, description="Invalid user or resource id")
        # return redirect(url_for('home'))
    # elif is_user_session_expired(uid=uid):
    #     # user instance is expired, go back to login
    #     return redirect(url_for("login"))
    elif not is_resource_public(rid=rid) and not user_has_access_to_resource(uid=uid, rid=rid):
        # resource is private and user does not have access
        # todo: possibly a link to no access reminder page?
        abort(404, description=f"User {uid} does not have access to resource {rid}")

    if request.method == "GET":
        # show resource detail

        # convert to human readable form
        subject = enum_to_website_output(res.subject)
        grade = enum_to_website_output(res.grade)
        difficulty = enum_to_website_output(res.difficulty)

        # convert utc time to AEST
        created_at = res.created_at.astimezone(pytz.timezone("Australia/Brisbane"))

        # get a list of resource_comment objects
        resource_comment_list = get_resource_comments(rid=rid)
        # get a dict of resource_comment instance -> resource_comment_replies instances to that comment
        resource_comment_replies_list = get_resource_comment_replies(resource_comment_list)

        return render_template("resource_item.html", rid=rid, uid=uid,
                               res=res, difficulty=difficulty, subject=subject, grade=grade)
    elif request.method == "POST":
        # FIXME: here assume upvote and downvote are two separate buttons like Quora
        # example see https://predictivehacks.com/?all-tips=how-to-add-action-buttons-in-flask
        # update do upvote/downvote
        up, down = request.form.get("upvote"), request.form.get("downvote")
        vote_res = vote_resource(uid=uid, rid=rid, upvote=up is not None)
        if vote_res == ErrorCode.SAME_VOTE_TWICE:
            # the user voted the same vote twice
            # todo: here I do flash message, you can modify it
            flash("Oh please don't vote the same thing twice, will ya?")

        # reach here a vote is made or vote is invalid, now refresh resource page
        return redirect(url_for("resource", uid=uid, rid=rid))
    return render_template('base_old.html', title='Register')


@app.route('/search')
def search():
    title = request.args.get('title')
    return jsonify([i.serialize for i in find_resources(title=title)])
    # return Response(json.dumps([i.serialize for i in find_resources(title=title)]),  mimetype='application/json')


@app.route('/register')
def register():
    """Page for a user to register for an account

    Must provide: username, email, password (with conditions)

    Optionally provide: interests / subjects tags

    Other user fields are configured in profile()
    """
    return render_template('base_old.html', title='Register')


@app.route('/login')
def login():
    """Login page for a user to authenticate

    Asks for the users email and password.

    Gives feedback on fail, redirects to referring page on success
     (through post data), if not refered then home page
    """
    return render_template('base_old.html', title='Login')


@app.route('/profile')
def profile():
    """The default view of a users profile,
    this can be used to view your own or other users profiles.
    Specified with the GET request
    /profile?<id / name>

    Shows the following content:
        Liked resources
        Created resources
        Your reviews / comments

    Additional options are available if viewing your own profile:
        Manage account settings
        Forums you are a part of
    """
    return render_template('base_old.html', title='Login')


@app.route('/profile/settings')
def settings():
    """The user configuration page,
    allows the user to edit their:
        Bio.
        Email.
        Password.
        Avatar.
        Interests
    """
    return render_template('base_old.html', title='Login')


@app.route('/about')
def about():
    """A brief page describing what the website is about"""
    return render_template('about.html', title='About Us', name="About Us")


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
    # todo: tag system not implemented

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
            thumbnail_path = os.path.join("channel_avatar", secure_filename(thumbnail.filename))
            thumbnail.save(os.path.join("static", thumbnail_path))

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
    available_tags = get_tags(mapping="id2name")

    with Session() as conn:
        for i in find_channels(channel_name=name, is_public=is_public,
                               sort_by_newest_date=sort_by_date):
            if not user_has_access_to_channel(uid=uid, cid=i.cid):
                # user does not have access to channel
                continue
            info = i.serialize

            posts = conn.query(ChannelPost).filter_by(cid=i.cid)

            post_count = posts.count()

            channel_tag_records = conn.query(ChannelTagRecord).filter_by(cid=i.cid).all()
            channel_tags = []
            for j in channel_tag_records:
                channel_tags.append(available_tags[j.tag_id])

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
            info["channel_tags"] = channel_tags

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
    # todo: posts comments cannot display for unknown reason
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
                most_recent_comment = conn.query(PostComment). \
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
            info["poster_avatar_link"] = poster_avatar_link
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
                           current_user_id=current_user.uid)


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
        flash("You do not have permission to visit this page")
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
    if not cid or not post_id:
        return redirect(url_for("view_channel"))

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


@app.errorhandler(403)
def page_not_found(error):
    """Page shown with a HTML 403 status"""
    return render_template('errors/error_403.html'), 403


@app.errorhandler(404)
def page_not_found(error):
    """Page shown with a HTML 404 status"""
    return render_template('errors/error_404.html'), 404


@app.context_processor
def subject_processor():
    def enum_to_website_output(item: str) -> str:
        return item.replace('_', ' ', 1).title()

    return dict(enum_to_website_output=enum_to_website_output)


@app.context_processor
def colour_processor():
    def strToColour(item: str) -> str:
        random.seed(item + "123")
        # return f"#{str(hex(random.randint(0, 0xFFFFFF)))[2:].zfill(6)}"
        return f"#{str(hex(random.randint(0, 0xFFFFFF)))[2:].zfill(6)}"

    return dict(strToColour=strToColour)


@app.context_processor
def tags():
    return dict(subject_tags=[e.name.lower() for e in Subject] + [e.name.lower() for e in Grade])
