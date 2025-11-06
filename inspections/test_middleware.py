from django.test import TestCase, RequestFactory
from django.core.exceptions import DisallowedHost
from django.http import HttpResponse, HttpResponseRedirect

from nyc_restaurants.middleware import DisableHostCheckMiddleware


class DisableHostCheckMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_patched_get_host_returns_localhost_and_restores_original(self):
        request = self.factory.get("/")

        def raising_get_host():
            raise DisallowedHost("forbidden host")

        request.get_host = raising_get_host

        def get_response(req):
            host = req.get_host()
            return HttpResponse(host)

        middleware = DisableHostCheckMiddleware(get_response)

        response = middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), "localhost")

        with self.assertRaises(DisallowedHost):
            request.get_host()

    def test_process_exception_redirects_on_disallowedhost(self):
        request = self.factory.get("/")
        middleware = DisableHostCheckMiddleware(lambda r: HttpResponse())
        resp = middleware.process_exception(request, DisallowedHost("bad"))
        self.assertIsInstance(resp, HttpResponseRedirect)
        self.assertEqual(resp.url, "/inspections/search/")

    def test_process_exception_returns_none_for_other_exceptions(self):
        request = self.factory.get("/")
        middleware = DisableHostCheckMiddleware(lambda r: HttpResponse())
        resp = middleware.process_exception(request, ValueError("oops"))
        self.assertIsNone(resp)
