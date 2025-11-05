from django.test import TestCase, RequestFactory
from django.core.exceptions import DisallowedHost
from django.http import HttpResponse
from nyc_restaurants.middleware import DisableHostCheckMiddleware


class DisableHostCheckMiddlewareTests(TestCase):
    """Tests for DisableHostCheckMiddleware."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.get_response = lambda request: HttpResponse("OK")
        self.middleware = DisableHostCheckMiddleware(self.get_response)

    def test_middleware_normal_request(self):
        """Test middleware with normal request."""
        request = self.factory.get("/")
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)

    def test_middleware_disallowed_host(self):
        """Test middleware handles DisallowedHost exception."""
        request = self.factory.get("/", HTTP_HOST="malicious-domain.com")

        # Mock get_host to raise DisallowedHost
        original_get_host = request.get_host

        def raise_disallowed():
            raise DisallowedHost("Invalid host")

        request.get_host = raise_disallowed

        response = self.middleware(request)
        # Should not crash, should handle gracefully
        self.assertIsNotNone(response)

    def test_process_exception_disallowed_host(self):
        """Test process_exception method with DisallowedHost."""
        request = self.factory.get("/", HTTP_HOST="bad-host.com")
        exception = DisallowedHost("Invalid host")

        response = self.middleware.process_exception(request, exception)

        # Should return a redirect
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/inspections/search/", response.url)

    def test_process_exception_other_exception(self):
        """Test process_exception with non-DisallowedHost exception."""
        request = self.factory.get("/")
        exception = ValueError("Some other error")

        response = self.middleware.process_exception(request, exception)

        # Should return None for other exceptions
        self.assertIsNone(response)

    def test_get_host_restoration(self):
        """Test that original get_host is restored after request."""
        request = self.factory.get("/")
        original_get_host = request.get_host

        response = self.middleware(request)

        # Original method should be restored
        self.assertEqual(request.get_host, original_get_host)
