from __future__ import unicode_literals

from datetime import timedelta, datetime

import jwt
from django.conf import settings
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.utils import six

from cas.exceptions import APIError
from db import user_index


class ConfigDefaults(object):
    JWT_ALGORITHM = 'HS256'
    JWT_LEEWAY = timedelta(seconds=10)
    JWT_AUTH_HEADER_PREFIX = 'Bearer'
    JWT_EXPIRATION_DELTA = timedelta(seconds=300)
    JWT_NOT_BEFORE_DELTA = timedelta(seconds=0)
    JWT_VERIFY_CLAIMS = ['signature', 'exp', 'nbf', 'iat']
    JWT_REQUIRED_CLAIMS = ['exp', 'iat', 'nbf']


def _config(key):
    try:
        if key == 'JWT_SECRET_KEY':
            return getattr(settings, key, settings.SECRET_KEY)
        else:
            return getattr(settings, key, getattr(ConfigDefaults, key))
    except AttributeError:
        raise ImproperlyConfigured(
            "The auth module lacks setting {}".format(key))


def request_callback(request):
    auth_header_value = request.META.get('HTTP_AUTHORIZATION', None)
    auth_header_prefix = _config('JWT_AUTH_HEADER_PREFIX')

    if not auth_header_value:
        return

    parts = auth_header_value.split()

    if parts[0].lower() != auth_header_prefix.lower():
        raise APIError('Unsupported authorization type')
    elif len(parts) == 1:
        raise APIError('Token missing')
    elif len(parts) > 2:
        raise APIError('Token contains spaces')

    return parts[1]


def _jwt_required(request):
    token = request_callback(request)

    if not token:
        raise PermissionDenied('Authorization Required')

    secret = _config('JWT_SECRET_KEY')
    algorithm = _config('JWT_ALGORITHM')
    leeway = _config('JWT_LEEWAY')
    verify_claims = _config('JWT_VERIFY_CLAIMS')
    required_claims = _config('JWT_REQUIRED_CLAIMS')

    try:
        options = {'verify_' + claim: True for claim in verify_claims}
        options.update({'require_' + claim: True for claim in required_claims})
        payload = jwt.decode(token, secret, options=options, algorithms=[algorithm], leeway=leeway)
    except jwt.InvalidTokenError as e:
        raise APIError('Invalid token: {}'.format(e.message))

    user_id = payload['identity']
    request.identity = identity = user_index.get(user_id, None)

    if identity is None:
        raise APIError('User does not exist')

    return identity


def jwt_required():
    def wrapper(fn):
        @six.wraps(fn)
        def decorator(request, *args, **kwargs):
            _jwt_required(request)
            return fn(request, *args, **kwargs)

        return decorator

    return wrapper


def jwt_encode_callback(identity):
    secret = _config('JWT_SECRET_KEY')
    algorithm = _config('JWT_ALGORITHM')

    iat = datetime.utcnow()
    exp = iat + _config('JWT_EXPIRATION_DELTA')
    nbf = iat + _config('JWT_NOT_BEFORE_DELTA')
    identity = getattr(identity, 'id') or identity['id']
    payload = {'exp': exp, 'iat': iat, 'nbf': nbf, 'identity': identity}
    return jwt.encode(payload, secret, algorithm=algorithm)
