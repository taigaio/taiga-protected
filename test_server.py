import os
import string
from unittest import mock

from werkzeug.test import create_environ, run_wsgi_app
from werkzeug.wrappers import Request

from hypothesis import given
import hypothesis.strategies as st

# It is necessary to set environment variable before import server
os.environ.setdefault("SECRET_KEY", "taiga-secret-key")

import server


def not_valid_url(base):  # pragma: no cover
    return "/%s" % base


def not_valid_url_strategy():
    return st.builds(not_valid_url, st.text())


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


@given(valid_url_strategy())
def test_valid_url_without_token(path):
    env = create_environ(method="GET", path=path)
    (app_iter, status, headers) = run_wsgi_app(server.app, env)
    status = int(status[:3])
    assert status == 403
    assert "X-Accel-Redirect" not in headers


@given(valid_url_strategy())
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


def sign(value):
    """Implements the same signature algorithm as the client."""
    from _vendor import itsdangerous

    signer = itsdangerous.TimestampSigner(os.environ["SECRET_KEY"], sep=":", salt="taiga-protected")
    signature = signer.sign(value)
    signature = signature.decode("utf-8")
    return signature.replace(value + ":", "")


@given(valid_url_strategy())
def test_token_is_valid_true(path):
    token = sign(path)
    assert server.token_is_valid(token, path) is True


def test_max_epoch_base_is_correct():
    """Test EPOCH .

    The package `itsdangerous` used to use base the EPOCH from 2011/01/01 in UTC

    .. code::

        EPOCH = 1293840000

    It was solved in https://github.com/pallets/itsdangerous/commit/9981a90b46160ac71505cb790c4bda4ee037ebb4
    but, as of Aug 3rd, there is no release yet.

    To test this behaviour I just issued a signature in the past
    that should always fail.

    .. code::

        >>> from django.core.signing import TimestampSigner
        >>> signer = TimestampSigner("taiga-secret-key", sep=":", salt="taiga-protected")
        >>> name = 'attachments/1/2/3/4/5/filename.ext'
        >>> signature = signer.sign(name)
        >>> print(signature.partition(":")[-1])
        1flYWO:E3Ph3KR0BuhId4RVyJBwSjpzN38

    """

    path = 'attachments/1/2/3/4/5/filename.ext'
    token = '1flYWO:E3Ph3KR0BuhId4RVyJBwSjpzN38'
    assert server.token_is_valid(token, path) is False
