# middleware.py

from django.utils.deprecation import MiddlewareMixin

class BypassCSRFForAdminMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith('/admin/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
