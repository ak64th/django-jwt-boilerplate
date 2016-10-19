from __future__ import unicode_literals

import simplejson as json
from django.http import JsonResponse
from django.utils import six
from django.views.decorators.http import require_http_methods

from auth.authentiaction import jwt_encode_callback, jwt_required
from cas.exceptions import APIError
from db import username_index


def parse_request_body_json(request, force=True):
    """Parse request.body as json
    """
    if request.body:
        meta = request.META
        content_type = meta.get('CONTENT_TYPE', meta.get('HTTP_CONTENT_TYPE', ''))

        if not (force or 'application/json' in content_type):
            return

        try:
            return json.loads(request.body.decode('utf8'))
        except ValueError as e:
            raise APIError('JSON parse error - %s' % six.text_type(e), status_code=400)


def username_login_callback(username, password):
    user = username_index.get(username, None)
    if user and user.password.encode('utf-8') == password.encode('utf-8'):
        return user
    return {}


@require_http_methods(["POST"])
def jwt_login(request):
    try:
        data = parse_request_body_json(request)
        credential_type = data.get('type')
        credential = data.get('credential')
    except AttributeError:
        raise APIError('Invalid credentials')

    if credential_type == 'username':
        identity = username_login_callback(**credential)
    else:
        raise NotImplementedError

    if identity:
        access_token = jwt_encode_callback(identity)
        return JsonResponse({'access_token': access_token.decode('utf-8')})
    else:
        raise APIError('Invalid credentials')


@require_http_methods(["GET"])
@jwt_required()
def info(request):
    user = request.identity
    return JsonResponse({'id': user.id, 'username': user.username})


@require_http_methods(["GET"])
@jwt_required()
def refresh(request):
    access_token = jwt_encode_callback(request.identity)
    return JsonResponse({'access_token': access_token.decode('utf-8')})
