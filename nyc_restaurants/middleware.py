from django.core.exceptions import DisallowedHost
import logging

logger = logging.getLogger(__name__)


class DisableHostCheckMiddleware:
    """
    Middleware to completely bypass Django's ALLOWED_HOSTS validation
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Monkey patch the get_host method to always return a valid host
        original_get_host = request.get_host

        def patched_get_host():
            try:
                return original_get_host()
            except DisallowedHost:
                # Return localhost as a fallback to bypass validation
                logger.warning(
                    f"DisallowedHost bypassed for: {request.META.get('HTTP_HOST', 'unknown')}"
                )
                return "localhost"

        request.get_host = patched_get_host

        try:
            response = self.get_response(request)
        finally:
            # Restore original method
            request.get_host = original_get_host

        return response

    def process_exception(self, request, exception):
        if isinstance(exception, DisallowedHost):
            logger.warning(
                f"DisallowedHost exception caught for: {request.META.get('HTTP_HOST', 'unknown')}"
            )
            # Return a simple redirect to avoid the error
            from django.http import HttpResponseRedirect

            return HttpResponseRedirect("/inspections/search/")
        return None
