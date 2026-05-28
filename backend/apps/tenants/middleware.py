import threading

_thread_locals = threading.local()


def get_current_tenant():
    return getattr(_thread_locals, "tenant", None)


def set_current_tenant(tenant):
    _thread_locals.tenant = tenant


class TenantMiddleware:
    """Attach tenant from authenticated user to request and thread-local."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = None
        if request.user.is_authenticated and hasattr(request.user, "tenant"):
            tenant = request.user.tenant
        request.tenant = tenant
        set_current_tenant(tenant)
        response = self.get_response(request)
        set_current_tenant(None)
        return response
