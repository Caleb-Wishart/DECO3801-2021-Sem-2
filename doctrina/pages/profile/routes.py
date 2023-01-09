from os import path

from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

from doctrina import db_session
from doctrina.database.database import (
    ErrorCode,
    find_channels,
    get_resource_thumbnail,
    get_user,
    get_user_and_resource_instance,
    get_user_teaching_areas,
    modify_user,
)
from doctrina.database.models import (
    ChannelVisibility,
    PrivateResourcePersonnel,
    Resource,
    ResourceCreater,
    Subject,
    User,
)

from . import bp

current_user: User


@bp.route("/profile", methods=["GET"])
@bp.route("/profile/<uid>", methods=["GET"])
@login_required
def profile(uid=None):
    """
    The default view of a users profile,
    this can be used to view your own profiles.
    Specified with the GET request
    """
    is_user_themself = True

    if not uid or (uid.isnumeric() and int(uid) == current_user.uid):
        # not uid specified, load current user's profile
        user = current_user
    else:
        # load up other user's profile
        is_user_themself = False
        uid = int(uid)
        user = get_user(identifier=uid)

        if user is None:
            abort(404, description="This user does not exist.")

    # get user rating number
    user_rating_whole = int(user.user_rating)
    # get if a user's honor rating is greater than int.5
    user_rating_half = 0 if round(float(user.user_rating), 1) - float(user_rating_whole) < 0.5 else 1
    # empty stars
    user_rating_unchecked = 5 - user_rating_whole - user_rating_half
    user.serialize
    return render_template(
        "profile.html",
        title="Profile",
        user=user.serialize,
        teaching_areas=get_user_teaching_areas(user.uid),
        rating_whole=user_rating_whole,
        is_user_themself=is_user_themself,
        rating_half=user_rating_half,
        rating_unchecked=user_rating_unchecked,
    )


@bp.route("/profile/studio_contents", methods=["GET"])
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

    if sort_algo not in ["ascending", "descending"]:
        sort_algo = "ascending"
    sort_algo = sort_algo.lower()

    if title == "":
        title = None

    is_resource = True if load_type == "resource" else False
    is_create = True if create_or_access == "create" else False

    out = []
    if is_resource:
        # deal with resource
        qualified_ids = []
        with db_session() as conn:
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
            res = res.filter(Resource.title.ilike(f"%{title}%"))
        if sort_algo == "ascending":
            res = res.order_by(Resource.created_at.asc()).all()
        else:
            res = res.order_by(Resource.created_at.desc()).all()
        for item in res:
            info = item.serialize

            with db_session() as conn:
                creater = conn.query(ResourceCreater).filter_by(rid=item.rid, uid=uid).first()

            if not creater:
                # fill manage link to null
                info["manage_link"] = None
            else:
                info["manage_link"] = url_for("resource_edit", rid=item.rid)

            info["avatar_link"] = (
                get_resource_thumbnail(item.rid).serialize["thumbnail_link"]
                if get_resource_thumbnail(item.rid) != ErrorCode.INVALID_RESOURCE
                else "img/placeholder.png"
            )
            info["view_link"] = url_for("resource", rid=item.rid)
            info["is_public"] = "Public" if info["is_public"] else "Private"

            out.append(info)
    else:
        # deal with channel
        sort_by_newest_date = True if sort_algo == "descending" else False
        if create_or_access == "create":
            # channels created by user
            res = find_channels(channel_name=title, admin_uid=uid, sort_by_newest_date=sort_by_newest_date)
        else:
            # channels user has access to: private only
            res = find_channels(
                channel_name=title, caller_uid=uid, sort_by_newest_date=sort_by_newest_date, is_public=False
            )

        for item in res:
            info = item.serialize

            if item.visibility != ChannelVisibility.PUBLIC:
                info["visibility"] = "Private"
            info["is_public"] = info["visibility"]
            del info["visibility"]

            # need to change attribute "name"  to "title"
            info["title"] = info["name"]
            del info["name"]

            # add upvote_count, downvote_count to '-'
            info["upvote_count"], info["downvote_count"] = "-", "-"

            if item.admin_uid != uid:
                # fill manage link to null
                info["manage_link"] = None
            else:
                info["manage_link"] = url_for("create_or_modify_channel", cid=item.cid)
            info["view_link"] = url_for("view_channel", cid=item.cid)
            out.append(info)
    return jsonify(out)


@bp.route("/profile/settings", methods=["GET", "POST"])
@login_required
def settings():
    """
    Render user settings page when receiving GET request.

    Update user settings when receiving POST request.
    """
    if request.method == "GET":
        return render_template(
            "settings.html",
            title="User Settings",
            user_info=current_user.serialize,
            teaching_areas=[ta.teaching_area.name.lower() for ta in get_user_teaching_areas(current_user.uid)],
        )
    else:
        # POST method
        username, bio, old_password, new_password = (
            request.form.get("username"),
            request.form.get("bio"),
            request.form.get("old_password"),
            request.form.get("new_password"),
        )
        avatar, profile_background = request.files.get("avatar"), request.files.get("profile_background")

        subjects = [t for t in request.form if t == request.form.get(t)]
        teaching_areas = {}
        for s in subjects:
            try:
                teaching_areas[Subject[s.replace(" ", "_").upper()]] = [True]
            except KeyError:
                continue

        if not bio:
            bio = "NULL"

        avatar_path, profile_background_path = "NULL", "NULL"
        if avatar and avatar.filename != "":
            avatar_path = path.join("avatar", secure_filename(avatar.filename))
            avatar.save(path.join("static", avatar_path))

        if profile_background and profile_background.filename != "":
            profile_background_path = path.join("profile_background", secure_filename(profile_background.filename))
            profile_background.save(path.join("static", profile_background_path))

        user, _ = get_user_and_resource_instance(uid=current_user.uid, rid=-1)

        if not old_password and not check_password_hash(user.hash_password, old_password):
            # old password does not match, do not change password
            new_password = None

        if isinstance(
            modify_user(
                uid=current_user.uid,
                username=username,
                password=new_password,
                bio=bio,
                avatar_link=avatar_path,
                profile_background_link=profile_background_path,
                teaching_areas_to_add=teaching_areas,
            ),
            ErrorCode,
        ):
            # invalid action
            flash("Cannot modify user profile at this time, try later", "error")
            return redirect(url_for("profile.settings"))
        # success
        flash("Profile modified successfully", "info")
        return redirect(url_for("profile.profile"))
