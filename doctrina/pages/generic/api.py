import random

from flask import jsonify
from flask_login import current_user

from doctrina.database.database import (
    ErrorCode,
    find_channels,
    find_resources,
    get_channel_post,
    get_resource_author,
    get_resource_tags,
    get_resource_thumbnail,
    get_user_and_resource_instance,
    get_user_teaching_areas,
)
from doctrina.database.models import User

from . import bp

current_user: User


@bp.route("/AJAX/homeAJAX")
def homeAJAX():
    """The endpoint for the AJAX search for resources using a get request
    returns it in json format
    """
    areas = get_user_teaching_areas(current_user.uid)
    grades = [ta.grade for ta in areas if ta.grade is not None]
    subjects = [ta.teaching_area for ta in areas if ta.teaching_area is not None]

    resources = [
        dict(
            r.serialize,
            author=get_resource_author(r.rid)[0].serialize,
            tags=get_resource_tags(r.rid),
            banner=get_resource_thumbnail(r.rid).serialize
            if get_resource_thumbnail(r.rid) != ErrorCode.INVALID_RESOURCE
            else {"thumbnail_link": "img/placeholder.png"},
        )
        for l in [find_resources(email=current_user.email, grade=g) for g in grades]
        for r in l
    ]
    resources += [
        dict(
            r.serialize,
            author=get_resource_author(r.rid)[0].serialize,
            tags=get_resource_tags(r.rid),
            banner=get_resource_thumbnail(r.rid).serialize
            if get_resource_thumbnail(r.rid) != ErrorCode.INVALID_RESOURCE
            else {"thumbnail_link": "img/placeholder.png"},
        )
        for l in [find_resources(email=current_user.email, subject=s) for s in subjects]
        for r in l
    ]
    a = []
    b = []
    for r in resources:
        if r["rid"] not in b:
            a.append(r)
            b.append(r["rid"])
    resources = a
    if len(resources) < 3:
        rec = [
            dict(
                r.serialize,
                author=get_resource_author(r.rid)[0].serialize,
                tags=get_resource_tags(r.rid),
                banner=get_resource_thumbnail(r.rid).serialize
                if get_resource_thumbnail(r.rid) != ErrorCode.INVALID_RESOURCE
                else {"thumbnail_link": "img/placeholder.png"},
            )
            for r in find_resources()
        ]
        while len(resources) != 3:
            random.shuffle(rec)
            if rec[0]["rid"] in b:
                continue
            resources += [rec[0]]
            b.append(rec[0]["rid"])

    elif len(resources) > 3:
        resources = resources[:3]

    channels = []
    channels = [
        dict(
            r.serialize,
            admin=get_user_and_resource_instance(r.admin_uid, -1)[0].serialize,
            posts=len(get_channel_post(r.cid)),
        )
        for l in [find_channels(caller_uid=current_user.uid, grade=g) for g in grades]
        for r in l
    ]
    channels += [
        dict(
            r.serialize,
            admin=get_user_and_resource_instance(r.admin_uid, -1)[0].serialize,
            posts=len(get_channel_post(r.cid)),
        )
        for l in [find_channels(caller_uid=current_user.uid, subject=s) for s in subjects]
        for r in l
    ]
    a = []
    b = []
    for r in channels:
        if r["cid"] not in b:
            a.append(r)
            b.append(r["cid"])
    channels = a
    if len(channels) < 2:
        cen = [
            dict(
                r.serialize,
                admin=get_user_and_resource_instance(r.admin_uid, -1)[0].serialize,
                posts=len(get_channel_post(r.cid)),
            )
            for r in find_channels()
        ]
        while len(channels) != 2:
            random.shuffle(cen)
            if cen[0]["cid"] in b:
                continue
            channels += [cen[0]]
            b.append(cen[0]["cid"])
    elif len(channels) > 2:
        channels = channels[:2]
    results = {"resources": resources, "channels": channels}

    return jsonify(results)
