import posixpath

from flask import redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.sql.expression import func
from werkzeug.utils import secure_filename

from doctrina import db_session
from doctrina.database.database import (
    ErrorCode,
    comment_on_channel_post,
    create_channel,
    enum_to_website_output,
    get_all_tags_for_channel,
    get_channel_post_comments,
    get_tags,
    get_user,
    modify_channel,
    modify_channel_post,
    post_on_channel,
    user_has_access_to_channel,
    website_input_to_enum,
)
from doctrina.database.models import (
    Channel,
    ChannelPersonnel,
    ChannelPost,
    ChannelTagRecord,
    ChannelVisibility,
    Grade,
    Subject,
    User,
)
from doctrina.utils import flash

from . import bp

current_user: User


@bp.route("/channel/<cid>/edit", methods=["GET", "POST"])
@bp.route("/channel/create", methods=["POST", "GET"])
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
    if request.method == "GET":
        # reverse visibility options so PUBLIC is always the default choice for creation
        visibility_options = [enum_to_website_output(i) for i in ChannelVisibility][::-1]
        subjects = [enum_to_website_output(i) for i in Subject if i != Subject.NULL]
        grades = [enum_to_website_output(i) for i in Grade if i != Grade.NULL]
        kwargs = {
            "other_tags": get_tags().keys(),
            "visibility_options": visibility_options,
            "subjects": subjects,
            "grades": grades,
        }

        if not cid:
            kwargs["title"] = "new channel"
            # create channel
            template = "create_channel.html"
        else:
            # modify channel
            cid = int(cid)
            kwargs["applied_tags"] = [t.replace(" ", "_") for t in get_all_tags_for_channel(cid=cid)]

            if not user_has_access_to_channel(cid=cid, uid=current_user.uid):
                # no permission, go back to channel home page
                flash("You do not have permission to visit this page")
                return redirect(url_for("view_channel"))

            kwargs["title"] = f"edit channel#{cid}"

            with db_session() as conn:
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
        name, description, personnel_emails, visibility, subject, grade, thumbnail = (
            request.form.get("channel_title"),
            request.form.get("channel_description"),
            request.form.getlist("personnel_ids"),
            request.form.get("visibility_choice"),
            request.form.get("subject"),
            request.form.get("grade"),
            request.files.get("thumbnail"),
        )

        thumbnail_path = None
        if thumbnail.filename != "":
            thumbnail_path = posixpath.join("channel_avatar", secure_filename(thumbnail.filename))
            thumbnail.save(posixpath.join("static", thumbnail_path))

        visibility = website_input_to_enum(readable_string=visibility, enum_class=ChannelVisibility)

        subject = website_input_to_enum(readable_string=subject, enum_class=Subject)

        grade = website_input_to_enum(readable_string=grade, enum_class=Grade)

        tags_id = [get_tags()[t] for t in request.form if t == request.form.get(t) and t in get_tags(t)]

        # convert personnel emails to personnel ids
        personnel_ids = []
        for i in personnel_emails:
            user = get_user(i)
            if user is not None:
                personnel_ids.append(user.uid)

        if not cid:
            # create channel
            cid = create_channel(
                name=name,
                visibility=visibility,
                admin_uid=current_user.uid,
                subject=subject,
                grade=grade,
                description=description,
                personnel_id=personnel_ids,
                avatar_link=thumbnail_path,
                tags_id=tags_id,
            )
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

            modify_channel(
                cid=cid,
                name=name,
                visibility=visibility,
                admin_uid=current_user.uid,
                subject=subject,
                grade=grade,
                description=description,
                personnel_ids=personnel_ids,
                avatar_link=thumbnail_path,
                tags_id=tags_id,
            )
            flash("Channel edited")
        return redirect(url_for("view_channel", cid=cid))


@bp.route("/channel")
@bp.route("/channel/<cid>", methods=["POST", "GET"])
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
        with db_session() as conn:
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
        return render_template(
            "channel_item.html",
            channel=channel,
            admin=admin,
            user=current_user,
            is_admin=current_user.uid == channel.admin_uid,
            visibility=visibility,
            top_posts=top_posts,
            top_contributors=top_contributors,
            title=f"Channel #{channel.cid}",
        )

    # load channel home page
    return render_template("channel.html", user=current_user, title="Channel Home")


@bp.route("/channel/<cid>/post/<post_id>")
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

    with db_session() as conn:
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
        comment_info["username"] = (
            commenter.username + " (Author)" if commenter.username == author.username else commenter.username
        )
        comment_info["commenter_avatar_link"] = commenter.avatar_link
        post_comments_info.append(comment_info)

    # check if current user is admin of the channel or owner of this post
    has_edit_privilege = post.uid == current_user.uid or channel.admin_uid == current_user.uid

    return render_template(
        "post.html",
        title=f"Channel Post #{post.post_id}",
        post_info=post_info,
        comments_info=post_comments_info,
        has_edit_privilege=has_edit_privilege,
        channel=channel,
        current_user=current_user,
    )


@bp.route("/channel/<cid>/post/create", methods=["POST", "GET"])
@bp.route("/channel/<cid>/post/<post_id>/edit", methods=["POST", "GET"])
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
        flash("You do not have permission to visit this page", "info")
        return redirect(url_for("view_channel"))

    with db_session() as conn:
        channel = conn.query(Channel).filter_by(cid=cid).first()

    if request.method == "GET":
        if not post_id:
            #  create channel post page
            return render_template("create_post.html", channel=channel.serialize, title="new channel post")
        else:
            # edit channel post page
            with db_session() as conn:
                post_id = int(post_id)
                post = conn.query(ChannelPost).filter_by(post_id=post_id).one_or_none()
                if not post:
                    # post to edit does not exists
                    return redirect(url_for("view_channel"))

                return render_template(
                    "edit_post.html",
                    channel=channel.serialize,
                    title=f"edit channel post#{post.post_id}",
                    post_info=post.serialize,
                )
    else:
        # POST request
        title, text = request.form.get("title"), request.form.get("init_text")

        if not post_id:
            # creation
            post_id = post_on_channel(uid=current_user.uid, title=title, text=text, cid=channel.cid)
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


@bp.route("/channel/<cid>/post/<post_id>/comment/create", methods=["POST"])
@login_required
def add_new_post_comment(cid=None, post_id=None):
    """
    Add a new comment to a post
    """
    if cid is None or post_id is None:
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
