from flask import abort, jsonify, request
from flask_login import current_user

from doctrina.database.database import (
    ErrorCode,
    comment_to_resource,
    find_resources,
    get_resource,
    get_resource_comment_replies,
    get_resource_comments,
    get_resource_tags,
    get_resource_thumbnail,
    get_user_and_resource_instance,
    reply_to_resource_comment,
    vote_resource,
)
from doctrina.database.models import Grade, Subject, User

from . import bp

current_user: User


@bp.route("/AJAX/resourceAJAX")
def resourceAJAX():
    """The endpoint for the AJAX search for resources using a get request
    returns it in json format
    """
    title = request.args.get("title")
    subject = request.args.get("subject", "").upper() if "subject" in request.args else None
    year = request.args.get("year", "").upper() if "year" in request.args else None
    tags = request.args.getlist("tags[]") if "tags[]" in request.args else None
    tags = list(filter(lambda x: x != "", tags)) if tags is not None else None
    sort = request.args.get("sort", "natural")
    try:
        subject = Subject[subject]
    except KeyError:
        subject = None
    try:
        year = Grade[year]
    except KeyError:
        year = None
    if title == "":
        title = None
    return jsonify(
        [
            dict(
                i.serialize,
                tags=get_resource_tags(i.rid),
                banner=get_resource_thumbnail(i.rid).serialize
                if get_resource_thumbnail(i.rid) != ErrorCode.INVALID_RESOURCE
                else {"thumbnail_link": "img/placeholder.png"},
            )
            for i in find_resources(
                title=title, subject=subject, grade=year, tags=tags, sort_by=sort, email=current_user.email
            )
        ]
    )


@bp.route("/AJAX/resourceVote")
def resourceVote():
    """The endpoint for the AJAX search for resources voting a get request
    returns it in json format
    """
    rid = request.args.get("rid") if "rid" in request.args else None
    up = request.args.get("up") if "up" in request.args else None
    down = request.args.get("down", "").upper() if "down" in request.args else None
    if rid is None:
        abort(404)
    if up is None or down is None:
        abort(404)
    vote_res = vote_resource(uid=current_user.uid, rid=rid, upvote=up == "1")
    res = get_resource(rid)
    if res is None:
        abort(404)
    return jsonify({"up": res.upvote_count, "down": res.downvote_count})


@bp.route("/AJAX/resourceComment")
def resourceComment():
    """The endpoint for the AJAX search for resource comments a get request
    returns it in json format
    """
    rid = request.args.get("rid") if "rid" in request.args else None
    if rid is None:
        abort(404)
    postType = request.args.get("type") if "type" in request.args else None
    if postType is not None:
        text = request.args.get("text") if "text" in request.args else None
        # quit if bad data
        if text is None:
            abort(404)
        if postType == "comment":
            res = comment_to_resource(current_user.uid, rid, text)
            if isinstance(res, ErrorCode):
                abort(404)
        elif postType == "reply":
            cid = request.args.get("cid") if "cid" in request.args else None
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
                rep.append(
                    {"reply": reply.serialize, "author": get_user_and_resource_instance(reply.uid, -1)[0].serialize}
                )

        comments.append(
            {
                "comment": comment.serialize,
                "resource_comment_id": comment.resource_comment_id,
                "replies": rep,
                "author": get_user_and_resource_instance(comment.uid, -1)[0].serialize,
            }
        )
    return jsonify(comments[::-1])
