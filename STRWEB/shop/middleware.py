"""Timezone middleware: activate zone from session."""

import logging
import zoneinfo

from django.utils import timezone

logger = logging.getLogger('shop')


class TimezoneMiddleware:
    """Activate user-selected timezone for each request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz_name = request.session.get('django_timezone')
        if tz_name:
            try:
                timezone.activate(zoneinfo.ZoneInfo(tz_name))
            except zoneinfo.ZoneInfoNotFoundError:
                logger.warning('Invalid timezone in session: %s', tz_name)
                timezone.deactivate()
        else:
            timezone.deactivate()
        response = self.get_response(request)
        return response
