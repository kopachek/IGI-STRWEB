"""Access control decorators."""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def employee_required(view_func):
    """Allow only users with EmployeeProfile."""

    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not (request.user.is_superuser or hasattr(request.user, 'employee_profile')):
            raise PermissionDenied('Employee access required.')
        return view_func(request, *args, **kwargs)

    return _wrapped


def client_required(view_func):
    """Allow only users with ClientProfile."""

    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not hasattr(request.user, 'client_profile'):
            raise PermissionDenied('Customer account required.')
        return view_func(request, *args, **kwargs)

    return _wrapped
