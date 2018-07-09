import os

from werkzeug.exceptions import HTTPException, Forbidden
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request

from itsdangerous import BadData, TimestampSigner

url_map = Map([
    Rule('/<any(attachments, project, user):basepath>/<p1>/<p2>/<p3>/<p4>/<p5>/<basename>'),
])


def token_is_valid(token):
    if not token:
        return False
    secret_key = os.environ['SECRET_KEY']
    signer = TimestampSigner(secret_key)
    try:
        signer.unsign(token, max_age=300)
    except BadData:
        return False
    return True


def build_path(args):
    keys = 'basepath', 'p1', 'p2', 'p3', 'p4', 'p5', 'basename'
    return '/_protected/' + '/'.join(args[k] for k in keys)


def app(environ, start_response):
    urls = url_map.bind_to_environ(environ)
    try:
        endpoint, args = urls.match()
    except HTTPException as exc:
        return exc(environ, start_response)

    request = Request(environ)
    token = request.args.get('token')
    if not token_is_valid(token):
        return Forbidden()(environ, start_response)

    print('token:', token)

    path = build_path(args)

    data = b''
    status = '200 OK'
    response_headers = [
        ('Content-Length', str(len(data))),
        ('X-Accel-Redirect', path)
    ]
    start_response(status, response_headers)
    return iter([data])


if __name__ == '__main__':  # pragma: no cover
    from werkzeug.serving import run_simple
    run_simple('localhost', 8003, app, use_reloader=True)
