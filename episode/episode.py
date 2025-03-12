import inspect
import json

from episode.tcpserver import TCPServer
from episode.http.httprequest import HttpRequest
from episode.http.httpresponse import HttpResponse
from episode.http.httpstatus import HTTPStatus
from episode.route import Router, Action
from episode.model import Model


class Episode(TCPServer):
    router = Router()

    def add_route(self, request_route, accepted_method):
        def inner(func):
            # Always strip last forward slash if one exists
            self.router.add_route(
                request_route.rstrip("/"), func, accepted_method=accepted_method
            )

            def wrapper(*args, **kwargs):
                return func(args, kwargs)

            return wrapper

        return inner

    def route(self, request_route):
        return self.add_route(request_route, accepted_method="all")

    def get(self, request_route):
        return self.add_route(request_route, "GET")

    def post(self, request_route):
        return self.add_route(request_route, "POST")

    def delete(self, request_route):
        return self.add_route(request_route, "DELETE")

    def validate_request_method(self, request, route_methods):
        accepted_route_action = None
        # Search from the end, last route takes precedence
        for action in route_methods[-1::-1]:
            if action.accepted_method == "all":
                accepted_route_action = action
                break
            elif action.accepted_method == request.method:
                accepted_route_action = action
                break
        
        if accepted_route_action is None:
            error_msg = f"<h1>Request method {request.method} is not allowed.<h1>".encode()
            return HttpResponse().write(
                error_msg, status_code=HTTPStatus.METHOD_NOT_ALLOWED
                )
        
        return accepted_route_action

    def handle_request(self, data):
        # create an instance of `HttpRequest`
        request = HttpRequest(data)

        # Extract query parameters if some exist in request uri
        if request.uri.find("?") != -1:
            request_uri, query_parameters = request.uri.split("?")
            query_parameters = query_parameters.split("&")
            for query_parameter in query_parameters:
                if query_parameter.find("=") != -1:
                    param, value = query_parameter.split("=")
                    request.query_parameters[param] = value
        else:
            request_uri = request.uri

        # now, look at the router and call the
        # appropriate route handler
        node, route_parameters = self.router.get_route_info(request_uri.rstrip("/"))
        if node and node.actions:
            action = self.validate_request_method(request, node.actions)
            if isinstance(action, Action):
                if action.terminal and action.handler:
                    handler = action.handler
                    request.route_parameters = route_parameters
                else:
                    handler = self.HTTP_401_handler
            else:
                return action
        else:
            handler = self.HTTP_401_handler

        response = self.validate_handler_parameters(handler, request)

        return response

    def validate_handler_parameters(self, handler, request):
        types = {int: "integer", str: "string", inspect._empty: "empty", None: "empty"}

        if handler == self.HTTP_401_handler:
            return handler(request)

        handler_signature = inspect.signature(handler)
        handler_params = {}
        route_parameters = request.route_parameters
        route_parameters.update(request.query_parameters)
        for param_name, param_obj in handler_signature.parameters.items():
            if param_name == "request":
                continue
            if param_name in route_parameters:
                route_parameter_value = route_parameters[param_name]
                if param_obj.annotation != inspect._empty:
                    # Match param data type
                    # Now only consider int and string
                    try:
                        if param_obj.annotation is int:
                            handler_params[param_name] = int(route_parameter_value)
                        elif param_obj.annotation is str:
                            handler_params[param_name] = str(route_parameter_value)
                    except Exception:
                        # Param data type mismatch
                        error_msg = f"<h1>Parameter {param_name} expected type {types[param_obj.annotation]} but got {types[type(route_parameter_value)]}</h1>"
                        return HttpResponse().write(
                            error_msg.encode(),
                            status_code=HTTPStatus.PRECONDITION_FAILED,
                        )
                else:
                    handler_params[param_name] = route_parameter_value
            else:
                if issubclass(param_obj.annotation, Model):
                    # TODO: check request Content-Type before deserialization
                    # TODO: check if request body is not empty
                    model_instance = param_obj.annotation(
                        **dict(json.loads(request.body.decode()))
                    )
                    handler_params[param_name] = model_instance
                elif param_obj.default != inspect._empty:
                    handler_params[param_name] = param_obj.default
                else:
                    sub_str = (
                        "route"
                        if param_name in list(request.route_parameters.keys())
                        else "query"
                    )
                    error_msg = f"<h1>Required {sub_str} parameter '{param_name}' value not provided</h1>"
                    return HttpResponse().write(
                        error_msg.encode(), status_code=HTTPStatus.PRECONDITION_FAILED
                    )

        return handler(request, **handler_params)

    def HTTP_401_handler(self, request):
        return HttpResponse().write(
            b"<h1>404 Not Found</h1>", status_code=HTTPStatus.NOT_FOUND
        )
