import posixpath
from os import path
from typing import Optional

from flask import abort, current_app, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from doctrina import db_session
from doctrina.database.database import (
    ErrorCode,
    add_resource,
    enum_to_website_output,
    get_resource_author,
    get_resource_tags,
    get_resource_thumbnail,
    get_tags,
    get_user,
    get_user_and_resource_instance,
    is_resource_public,
    modify_resource,
    user_has_access_to_resource,
    website_input_to_enum,
)
from doctrina.database.models import (
    Grade,
    PrivateResourcePersonnel,
    ResourceCreater,
    ResourceDifficulty,
    ResourceTagRecord,
    ResourceThumbnail,
    Subject,
    User,
    dump_datetime,
)
from doctrina.utils import flash

from . import bp
from .forms import ResourceForm

current_user: User


@bp.route("/resource")
@bp.route("/resource/<int:rid>")
def resource(rid: Optional[int] = None):
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
        return render_template("resource.html", title="Resources")
    uid = current_user.uid
    # individual resource page
    user, res = get_user_and_resource_instance(uid=uid, rid=rid)
    # resource does not exist
    if res is None:
        abort(404, description="The requested resource does not exist")
    # user has access to resource
    if (
        not is_resource_public(rid=rid)
        and (user is None or not user_has_access_to_resource(uid=uid, rid=rid))
        and uid != -2
    ):
        abort(
            403,
            description=(
                f"You ({current_user.username}) do not have permission"
                f"to access the resource : {res.title}\n"
                "If you think this is incorrect contact the resource owner"
            ),
        )

    if res.resource_link.startswith("resource/"):
        res.resource_link = url_for("static", filename=res.resource_link)

    # get hold resource creater's honor rating
    with db_session() as conn:
        creater = conn.query(ResourceCreater).filter_by(rid=rid).first()
        creater = conn.query(User).filter_by(uid=creater.uid).first()
    creater_rating_whole = int(creater.user_rating)
    # get if a user's honor rating is greater than int.5
    creater_rating_half = 0 if round(float(creater.user_rating), 1) - float(creater_rating_whole) < 0.5 else 1
    # empty stars
    creater_rating_unchecked = 5 - creater_rating_whole - creater_rating_half

    # render the template
    kwargs = {
        "title": res.title,
        "rid": rid,
        "uid": uid,
        "res": res,
        "rating_whole": creater_rating_whole,
        "rating_half": creater_rating_half,
        "rating_unchecked": creater_rating_unchecked,
        "created_at": dump_datetime(res.created_at),
        "difficulty": enum_to_website_output(res.difficulty),
        "subject": enum_to_website_output(res.subject),
        "grade": enum_to_website_output(res.grade),
        "resource_tags": get_resource_tags(res.rid),
        "authors": get_resource_author(res.rid),
        "banner": get_resource_thumbnail(rid)
        if get_resource_thumbnail(rid) != ErrorCode.INVALID_RESOURCE
        else {"thumbnail_link": "img/placeholder.png"},
    }
    return render_template("resource_item.html", **kwargs)


@bp.route("/resource/new", methods=["GET", "POST"])
@login_required
def resource_new():
    """The user creates a new resource"""
    form = ResourceForm()
    if form.validate_on_submit():
        title = form.title.data
        resource_url = form.resource_url.data
        resource_file, resource_link = None, None
        if resource_url == "":
            # no url provided, get file
            resource_file = request.files[form.files.name]
            resource_link = resource_file.filename
        resource_thumbnail_file = request.files[form.thumbnail.name]
        resource_thumbnail_links = resource_thumbnail_file.filename

        difficulty = ResourceDifficulty.EASY
        try:
            subject = Subject[request.form.get("subject", "").replace(" ", "_").upper()]
        except KeyError:
            subject = None
        try:
            grade = Grade[request.form.get("grades", "").replace(" ", "_").upper()]
        except KeyError:
            grade = None
        creaters_id = [current_user.uid]
        private_personnel_id = [
            get_user(email).uid for email in request.form.getlist("personnel_ids") if get_user(email) is not None
        ]
        is_public = len(private_personnel_id) == 0

        tags_id = [get_tags()[t] for t in request.form if t == request.form.get(t) and t in get_tags(t)]
        description = form.description.data

        if resource_url == "":
            i = 0
            while path.isfile(
                path.join(current_app.config["UPLOAD_FOLDER"], "resource", secure_filename(resource_link))
            ):
                root, ext = path.splitext(resource_link)
                resource_link = root + "_" + str(i) + ext
                i += 1
            resource_file.save(
                path.join(current_app.config["UPLOAD_FOLDER"], "resource", secure_filename(resource_link))
            )

        i = 0
        while path.isfile(
            path.join(current_app.config["UPLOAD_FOLDER"], "thumbnail", secure_filename(resource_thumbnail_links))
        ):
            root, ext = path.splitext(resource_thumbnail_links)
            resource_thumbnail_links = root + "_" + str(i) + ext
            i += 1

        resource_thumbnail_file.save(
            path.join(current_app.config["UPLOAD_FOLDER"], "thumbnail", secure_filename(resource_thumbnail_links))
        )

        if resource_url == "":
            rid = add_resource(
                title,
                path.join("resource", secure_filename(resource_link)),
                difficulty,
                subject,
                grade,
                creaters_id,
                is_public,
                private_personnel_id,
                tags_id,
                description,
                [path.join("thumbnail", secure_filename(resource_thumbnail_links))],
            )
        else:
            rid = add_resource(
                title,
                resource_url,
                difficulty,
                subject,
                grade,
                creaters_id,
                is_public,
                private_personnel_id,
                tags_id,
                description,
                [path.join("thumbnail", secure_filename(resource_thumbnail_links))],
            )
        if isinstance(rid, ErrorCode):
            abort(400)
        flash("Resource created", "info")
        return redirect(url_for("resource", rid=rid))
    return render_template("resource_create.html", title="New Resource", form=form)


@bp.route("/resource/<rid>/edit", methods=["GET", "POST"])
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

    with db_session() as conn:
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

        with db_session() as conn:
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

        return render_template(
            "resource_edit.html",
            title=f"Edit resource #{rid}",
            form=form,
            filename=filename,
            thumbnails_filename=thumbnails_filename,
            subject=current_subject,
            grade=current_grade,
            current_visibility=visibility,
            personnel_emails=personnel_email,
            applied_tags=applied_tags,
            rid=rid,
        )
    elif request.method == "POST":
        # update resource: currently do not update other tags
        title = form.title.data
        resource_thumbnail_file = request.files[form.thumbnail.name]
        subject = website_input_to_enum(request.form.get("subject", ""), Subject)
        grade = website_input_to_enum(request.form.get("grades", ""), Grade)
        description = form.description.data
        is_public = True if request.form.get("visibility_choice") == "Public" else False
        tags_id = [get_tags()[t] for t in request.form if t == request.form.get(t) and t in get_tags(t)]

        thumbnail_path = None
        if resource_thumbnail_file and resource_thumbnail_file.filename != "":
            thumbnail_path = posixpath.join("thumbnail", secure_filename(resource_thumbnail_file.filename))
            resource_thumbnail_file.save(posixpath.join(current_app.config["UPLOAD_FOLDER"], thumbnail_path))
        thumbnail_path = [thumbnail_path] if thumbnail_path else []

        if not description:
            description = "NULL"

        if isinstance(
            modify_resource(
                rid=rid,
                title=title,
                subject=subject,
                grade=grade,
                is_public=is_public,
                description=description,
                resource_thumbnail_links=thumbnail_path,
                tags_id=tags_id,
            ),
            ErrorCode,
        ):
            flash("Something went wrong, please try again.", "error")
            return redirect(url_for("resource_edit", rid=rid))

        flash("Edited successfully.", "info")
        return redirect(url_for("resource", rid=rid))

    # invalid call, go back to resource home page
    return redirect(url_for("resource"))
