import os

from werkzeug.exceptions import HTTPException, Forbidden
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Request

from itsdangerous import BadData, TimestampSigner

url_map = Map([
    Rule('/<any(attachments, project, user):basepath>/<p1>/<p2>/<p3>/<p4>/<p5>/<basename>'),
])


class Configuration:
    def __init__(self):
        self.secret_key = None

    def load(self):
        try:
            self.secret_key = os.environ['SECRET_KEY']
        except KeyError:
            raise Exception('Invalid configuration: unable to get SECRET_KEY environment variable') from None


CONFIG = Configuration()
CONFIG.load()


def token_is_valid(token, path):
    if not token:
        return False
    signer = TimestampSigner(CONFIG.secret_key, sep=':', salt='taiga-protected')
    signature = '%s:%s' % (path, token)
    return signer.validate(signature, max_age=3600)


def build_path(args):
    keys = 'basepath', 'p1', 'p2', 'p3', 'p4', 'p5', 'basename'
    return '/'.join(args[k] for k in keys)


def app(environ, start_response):
    urls = url_map.bind_to_environ(environ)
    try:
        endpoint, args = urls.match()
    except HTTPException as exc:
        return exc(environ, start_response)

    path = build_path(args)

    request = Request(environ)
    token = request.args.get('token')
    if not token_is_valid(token, path):
        return Forbidden()(environ, start_response)

    protected_path = '/_protected/' + path
    data = b''
    status = '200 OK'
    response_headers = [
        ('Content-Length', str(len(data))),
        ('X-Accel-Redirect', protected_path)
    ]
    start_response(status, response_headers)
    return iter([data])


if __name__ == '__main__':  # pragma: no cover
    from werkzeug.serving import run_simple
    run_simple('localhost', 8003, app, use_reloader=True)
