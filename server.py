# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

__version__ = '6.8.0'


import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from werkzeug.exceptions import HTTPException, Forbidden
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request

from _vendor import itsdangerous


logger = logging.getLogger("taiga_protected.server")


# Load config file if exists
config_file = Path(__file__).parent / ".env"
load_dotenv(str(config_file))


url_map = Map(
    [
        Rule("/health", endpoint="health"),
        Rule(
            "/<any(attachments, project, user):basepath>/<p1>/<p2>/<p3>/<p4>/<p5>/<basename>"
        )
    ]
)


def safe_int(s):
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


class Configuration:
    def __init__(self):
        self.secret_key = None
        self.max_age = safe_int(os.environ.get("MAX_AGE", None)) or 3600
        self.subpath = os.environ.get("TAIGA_SUBPATH", "") or ""

    def load(self):
        try:
            self.secret_key = os.environ["SECRET_KEY"]
        except KeyError:  # pragma: no cover
            raise Exception(
                "Invalid configuration: unable to get SECRET_KEY environment variable"
            ) from None


CONFIG = Configuration()
CONFIG.load()


def token_is_valid(token, path):
    if not token:
        return False
    signer = itsdangerous.TimestampSigner(
        CONFIG.secret_key, sep=":", salt="taiga-protected"
    )
    signature = "%s:%s" % (path, token)

    try:
        value, ts = signer.unsign(
            signature, max_age=CONFIG.max_age, return_timestamp=True
        )
    except itsdangerous.BadData as exc:
        logger.warning(
            "Token is not valid signature=%r max_age=%s date_signed=%r",
            signature,
            CONFIG.max_age,
            getattr(exc, "date_signed", "Empty"),
            exc_info=True,
        )
        return False

    logger.debug("path=%r ts=%s ", value, ts)
    return True


def build_path(args):
    keys = "basepath", "p1", "p2", "p3", "p4", "p5", "basename"
    return "/".join(args[k] for k in keys)


def app(environ, start_response):
    urls = url_map.bind_to_environ(environ)
    try:
        endpoint, args = urls.match()
    except HTTPException as exc:
        return exc(environ, start_response)

    if endpoint == "health":
        response = Response("OK", status=200)
        return response(environ, start_response)

    path = build_path(args)

    if args["basepath"] == "attachments":
        request = Request(environ)
        token = request.args.get("token")
        if not token_is_valid(token, path):
            return Forbidden()(environ, start_response)

    protected_path = f"{CONFIG.subpath}/_protected/{path}"
    data = b""
    status = "200 OK"
    response_headers = [
        ("Content-Length", str(len(data))),
        ("X-Accel-Redirect", protected_path),
    ]
    start_response(status, response_headers)
    return iter([data])


if __name__ == "__main__":  # pragma: no cover
    from werkzeug.serving import run_simple

    run_simple("localhost", 8003, app, use_reloader=True)
