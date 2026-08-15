from django.utils.deprecation import MiddlewareMixin


class AuditMiddleware(MiddlewareMixin):
    """Lightweight request context for audit logging (IP etc.)."""

    def process_request(self, request):
        request.audit_ip = self._get_client_ip(request)
        return None

    @staticmethod
    def _get_client_ip(request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
