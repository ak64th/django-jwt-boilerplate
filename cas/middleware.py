from __future__ import unicode_literals

import logging
import traceback

from django import http
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils import six
from django.utils.deprecation import MiddlewareMixin

from cas.exceptions import APIError

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(MiddlewareMixin):
    @staticmethod
    def process_exception(request, exception):
        if isinstance(exception, http.Http404):
            blob = dict(message=six.text_type(exception))
            return http.JsonResponse(blob, 404)
        elif isinstance(exception, PermissionDenied):
            blob = dict(message=six.text_type(exception))
            return http.JsonResponse(blob, status=403)
        elif isinstance(exception, APIError):
            blob = exception.to_dict()
            return http.JsonResponse(blob, status=exception.status_code)
        else:
            exc_data = dict(message='An error occurred')
            if settings.DEBUG:
                exc_data['message'] = six.text_type(e)
                exc_data['data'] = traceback.format_exc()
            blob = exc_data
            logger.error(
                'Internal Server Error: %s', request.path,
                exc_info=True,
                extra={'status_code': 500, 'request': request}
            )
            return http.JsonResponse(blob, status=500)
