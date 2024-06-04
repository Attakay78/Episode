class HTTPRequest:
    def __init__(self, data):
        self.method = None
        self.uri = None
        self.headers = dict()
        self.body = None
        self.http_version = (
            "1.1"  # default to HTTP/1.1 if request doesn't provide a version
        )
        self.route_parameters = dict()
        self.query_parameters = dict()

        # call self.parse() method to parse the request data
        self.parse(data)

    def parse(self, data):
        lines = data.split(b"\r\n")

        request_line = lines[0]

        words = request_line.split(b" ")

        self.method = words[0].decode()  # call decode to convert bytes to str

        if len(words) > 1:
            # we put this in an if-block because sometimes
            # browsers don't send uri for homepage
            self.uri = words[1].decode()  # call decode to convert bytes to str

        if len(words) > 2:
            self.http_version = words[2]

        # Parse request_headers and body
        headers = lines[1:]
        for index, data in enumerate(headers):
            if data:
                header_key, *header_values = data.decode().split(" ")
                header_key = header_key.rstrip(":")

                if len(header_values) > 1:
                    header_values = [" ".join(header_values)]
                self.headers[header_key] = header_values
            else:
                # Gotten to the blank line that separates the request header and body
                # Extract the request body
                self.body = headers[index + 1]
                break

    # TODO
    # Handle parsing error (client request error)
