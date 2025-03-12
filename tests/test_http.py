import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from episode.http.httprequest import HttpRequest
from episode.http.httpresponse import HttpResponse
from episode.http.httpstatus import HTTPStatus

get_request_info = b"""GET /library/\r
Host: www.cloudacademy.com\r
User-Agent: Chrome\r
Accept: text/html,application/xml\r
Accept-Language: en-GB
"""

post_request_info = b"""POST /library/\r
Host: www.cloudacademy.com\r
User-Agent: Chrome\r
Accept: text/html,application/xml\r
Accept-Language: en-GB\r\n\r
{"first_name": "John", "last_name": "Doe", "age": 34}
"""


class HttpRequestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.get_request_obj = HttpRequest(get_request_info.rstrip(b"\n"))
        cls.post_request_obj = HttpRequest(post_request_info.rstrip(b"\n"))

    def test_request_methods(self):
        http_request_method = self.get_request_obj.method
        self.assertEqual(http_request_method, "GET")

        http_request_method = self.post_request_obj.method
        self.assertEqual(http_request_method, "POST")

    def test_request_headers(self):
        http_request_headers = self.get_request_obj.headers
        expected_request_headers = {
            'Host': ['www.cloudacademy.com'], 
            'User-Agent': ['Chrome'], 
            'Accept': ['text/html,application/xml'], 
            'Accept-Language': ['en-GB']
        }

        self.assertEqual(http_request_headers, expected_request_headers)
    
    def test_request_uri(self):
        self.assertEqual(self.get_request_obj.uri, "/library/")
    
    def test_request_body(self):
        http_request_body = self.post_request_obj.body.decode()
        self.assertEqual(http_request_body, '{"first_name": "John", "last_name": "Doe", "age": 34}')


class HttpResponseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.response_obj = HttpResponse()
    
    def test_write(self):
        response = self.response_obj.write(b"Success")
        expected_response = b'HTTP/1.1 200 OK\r\nServer: EpisodeServer\r\nContent-Type: text/plain\r\n\r\nSuccess'

        self.assertEqual(expected_response, response)
    
    def test_response_line(self):
        response_line = self.response_obj.response_line(HTTPStatus.OK)
        expected_response_line = b'HTTP/1.1 200 OK\r\n'

        self.assertEqual(expected_response_line, response_line)

    def test_response_headers(self):
        response_headers = self.response_obj.response_headers(content_type="plain")
        expected_response_headers = b'Server: EpisodeServer\r\nContent-Type: text/plain\r\n'

        self.assertEqual(expected_response_headers, response_headers)
