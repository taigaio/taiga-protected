# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2021-present Kaleidos INC

import os
import string
from unittest import mock

from werkzeug.test import create_environ, run_wsgi_app
from werkzeug.wrappers import Request

import pytest

from hypothesis import given
import hypothesis.strategies as st

# It is necessary to set environment variable before import server
os.environ.setdefault("SECRET_KEY", "taiga-secret-key")

import server


def not_valid_url(base):  # pragma: no cover
    return "/%s" % base


def not_valid_url_strategy():
    return st.builds(not_valid_url, st.text())


def sign(value):
    """Implements the same signature algorithm as the client."""
    from _vendor import itsdangerous

    signer = itsdangerous.TimestampSigner(
        os.environ["SECRET_KEY"], sep=":", salt="taiga-protected"
    )
    signature = signer.sign(value)
    signature = signature.decode("utf-8")
    return signature.replace(value + ":", "")


@given(not_valid_url_strategy())
def test_not_valid_url_raises_404(path):
    env = create_environ(method="GET", path=path)
    (app_iter, status, headers) = run_wsgi_app(server.app, env)
    status = int(status[:3])
    assert status == 404


def valid_url(base, p1, p2, p3, p4, p5, basename, ext):  # pragma: no cover
    return "/%s/%s/%s/%s/%s/%s/%s.%s" % (base, p1, p2, p3, p4, p5, basename, ext)


hexchars = "1234567890abcdef"
valid_chars = string.ascii_lowercase + string.digits + "-_"


def valid_url_strategy():
    return st.builds(
        valid_url,
        base=st.sampled_from(["attachments", "project", "user"]),
        p1=st.text(alphabet=hexchars, min_size=1, max_size=1),
        p2=st.text(alphabet=hexchars, min_size=1, max_size=1),
        p3=st.text(alphabet=hexchars, min_size=1, max_size=1),
        p4=st.text(alphabet=hexchars, min_size=1, max_size=1),
        p5=st.text(alphabet=hexchars, min_size=29, max_size=29),
        basename=st.text(alphabet=valid_chars, min_size=1, max_size=100),
        ext=st.text(alphabet=valid_chars, min_size=1, max_size=100),
    )


def protected_url_strategy():
    return st.builds(
        valid_url,
        base=st.sampled_from(["attachments"]),
        p1=st.text(alphabet=hexchars, min_size=1, max_size=1),
        p2=st.text(alphabet=hexchars, min_size=1, max_size=1),
        p3=st.text(alphabet=hexchars, min_size=1, max_size=1),
        p4=st.text(alphabet=hexchars, min_size=1, max_size=1),
        p5=st.text(alphabet=hexchars, min_size=29, max_size=29),
        basename=st.text(alphabet=valid_chars, min_size=1, max_size=100),
        ext=st.text(alphabet=valid_chars, min_size=1, max_size=100),
    )


@given(protected_url_strategy())
def test_valid_url_without_token(path):
    env = create_environ(method="GET", path=path)
    (app_iter, status, headers) = run_wsgi_app(server.app, env)
    status = int(status[:3])
    assert status == 403
    assert "X-Accel-Redirect" not in headers


@given(protected_url_strategy())
def test_valid_url_with_valid_token(path):
    env = create_environ(method="GET", path=path)
    with mock.patch("server.token_is_valid") as is_valid:
        is_valid.return_value = True
        (app_iter, status, headers) = run_wsgi_app(server.app, env)
    assert is_valid.called is True

    status = int(status[:3])
    assert status == 200
    assert "X-Accel-Redirect" in headers
    assert "/_protected" + path == headers["X-Accel-Redirect"]


@given(st.none() | st.text(), valid_url_strategy())
def test_token_is_valid_false(token, path):
    assert server.token_is_valid(token, path) is False


@given(valid_url_strategy())
def test_token_is_valid_true(path):
    token = sign(path)
    assert server.token_is_valid(token, path) is True


@pytest.mark.parametrize(
    "value, expected",
    [("42", 42), ("", None), (None, None), ("a", None), ("3.14", None)],
)
def test_safe_int(value, expected):
    assert expected == server.safe_int(value)
