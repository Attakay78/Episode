from episode.http.httpstatus import HTTPStatus


class HttpResponse:
    headers = {
        "Server": "EpisodeServer",
        "Content-Type": "text/html",
    }

    content_types = {
        "plain": "text/plain",
        "html": "text/html",
        "json": "application/json",
    }

    def write(
        self, data, extra_headers=None, status_code=HTTPStatus.OK, content_type="plain"
    ):
        response_line = self.response_line(status_code)

        response_headers = self.response_headers(content_type, extra_headers)

        blank_line = b"\r\n"

        response_body = data if type(data) == bytes else str(data).encode()

        return b"".join([response_line, response_headers, blank_line, response_body])

    def response_line(self, status_code):
        """Returns response line"""
        status_code_reason = status_code.phrase
        status_code_value = status_code.value
        line = f"HTTP/1.1 {status_code_value} {status_code_reason}\r\n"

        return line.encode()

    def response_headers(self, content_type, extra_headers=None):
        """Returns headers
        The `extra_headers` can be a dict for sending
        extra headers for the current response
        """
        self.headers.update(
            {"Content-Type": self.content_types.get(content_type, "text/plain")}
        )
        headers_copy = self.headers.copy()

        if extra_headers:
            headers_copy.update(extra_headers)

        headers = ""

        for header_key, header_value in headers_copy.items():
            headers += f"{header_key}: {header_value}\r\n"

        return headers.encode()
