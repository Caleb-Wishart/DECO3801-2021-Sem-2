import random
from typing import Optional

import pytz
from flask import jsonify, request, url_for
from flask_login import current_user

from doctrina import db_session
from doctrina.database.database import (
    ErrorCode,
    find_channel_posts,
    find_channels,
    get_all_tags_for_channel,
    get_channel_post_comments,
    get_tags,
    user_has_access_to_channel,
    vote_channel_post,
    vote_channel_post_comment,
)
from doctrina.database.models import ChannelPost, PostComment, User, dump_datetime
from doctrina.utils import flash

from . import bp

current_user: User


@bp.route("/search/channel")
def search_channel():
    """
    Returns json object of all qualified channels
    """
    name = request.args.get("name")
    is_public = request.args.get("is_public")
    is_public = True if (is_public == "true" or is_public is True) else False
    sort_by_date = True if request.args.get("sort_by_date") == "newest" else False
    uid = int(request.args.get("uid", "-1"))
    tags = request.args.getlist("tags[]") if "tags[]" in request.args else None
    tags = list(filter(lambda x: x != "", tags)) if tags is not None else None
    tags = [get_tags()[t] for t in tags if t in get_tags()] if tags is not None else None
    subject = request.args.get("subject", "").upper() if "subject" in request.args else None
    year = request.args.get("year", "").upper() if "year" in request.args else None

    out = []

    with db_session() as conn:
        for i in find_channels(
            channel_name=name,
            is_public=is_public,
            sort_by_newest_date=sort_by_date,
            tag_ids=tags,
            subject=subject,
            grade=year,
        ):
            if uid != -2 and not user_has_access_to_channel(uid=uid, cid=i.cid):
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
                poster_name = conn.query(User).filter_by(uid=most_recent_post.uid).first().username

            info["most_recent_post_time"] = recent_post_time
            info["recent_poster_username"] = poster_name
            info["post_count"] = post_count
            # info["channel_tags"] = channel_tags

            out.append(info)
    if not sort_by_date:
        # trending mode: fake a trend by shuffle
        random.shuffle(out)
    return jsonify(out)


@bp.route("/search/channel/<cid>/post")
def search_channel_post(cid: Optional[int] = None):
    """
    Returns json object of posts of a specific channel
    """
    title = request.args.get("title")
    sort_algo = request.args.get("sort_algo", "").lower()
    if cid is None:
        return jsonify({})
    cid = int(cid)

    out = []
    if sort_algo == "newest":
        posts = find_channel_posts(cid=cid, title=title, sort_algo="date")
    else:
        posts = find_channel_posts(cid=cid, title=title, sort_algo="upvote")

    with db_session() as conn:
        for i in posts:
            info = i.serialize

            poster = conn.query(User).filter_by(uid=i.uid).first()
            poster_avatar_link = poster.avatar_link
            poster_username = poster.username

            post_comments = get_channel_post_comments(post_id=i.post_id)
            comments_count = len(post_comments)

            recent_comment_time, recent_commenter_name = None, None
            if comments_count != 0:
                most_recent_comment = (
                    conn.query(PostComment).filter_by(post_id=i.post_id).order_by(PostComment.created_at.desc()).first()
                )
                recent_comment_time = most_recent_comment.created_at
                # convert to local time
                recent_comment_time = recent_comment_time.astimezone(pytz.timezone("Australia/Brisbane")).strftime(
                    "%d/%m/%Y, %H:%M:%S"
                )
                recent_commenter_name = conn.query(User).filter_by(uid=most_recent_comment.uid).first().username
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


@bp.route("/AJAX/channel/post/vote")
def vote_channel_post_or_comment():
    """
    Vote a channel post or post comment
    """
    voter_id = int(request.args.get("uid", "-1"))
    post_id_or_comment_id = int(request.args.get("id", "-1"))
    is_upvote = True if request.args.get("upvote") == "true" else False
    post_or_comment = request.args.get("post_or_comment")

    if post_or_comment == "post":
        # vote a channel post
        vote_res = vote_channel_post(uid=voter_id, post_id=post_id_or_comment_id, upvote=is_upvote)
    else:
        # vote post comment
        vote_res = vote_channel_post_comment(uid=voter_id, post_comment_id=post_id_or_comment_id, upvote=is_upvote)

    if vote_res == ErrorCode.SAME_VOTE_TWICE:
        flash("Please don't vote the same thing twice")

    with db_session() as conn:
        if post_or_comment == "post":
            res = conn.query(ChannelPost).filter_by(post_id=post_id_or_comment_id).first()
        else:
            res = conn.query(PostComment).filter_by(post_comment_id=post_id_or_comment_id).first()

        return jsonify({"upvote_count": res.upvote_count, "downvote_count": res.downvote_count})
