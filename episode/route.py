class Action:
    def __init__(self, terminal=False, handler=None, method="all"):
        self.terminal = terminal
        self.handler = handler
        self.accepted_method = method


class Node:
    def __init__(self, value):
        self.value = value
        self.children_nodes = []
        self.children_values = []
        self.action = None


class Router:
    def __init__(self):
        self.root = Node("/")

    def add_route(self, route, handler, node=None, accepted_method="all"):
        if not node:
            # First time adding a new route to the tree
            route_points = route.lstrip("/").split("/")  # strip leading / from route
            first_route_point = route_points[0]
            if not first_route_point:
                if handler:
                    self.root.action = Action(True, handler, accepted_method)
                return
            if first_route_point not in self.root.children_values:
                child_node = Node(first_route_point)
                self.root.children_nodes.append(child_node)
                self.root.children_values.append(first_route_point)
                self.add_route(route_points[1:], handler, child_node, accepted_method)
            else:
                for child_node in self.root.children_nodes:
                    if child_node.value == first_route_point:
                        self.add_route(
                            route_points[1:], handler, child_node, accepted_method
                        )
        else:
            if route:
                first_route_point = route[0]
                if first_route_point in node.children_values:
                    for child_node in node.children_nodes:
                        if child_node.value == first_route_point:
                            self.add_route(
                                route[1:], handler, child_node, accepted_method
                            )
                else:
                    child_node = Node(first_route_point)
                    node.children_nodes.append(child_node)
                    node.children_values.append(first_route_point)
                    self.add_route(route[1:], handler, child_node, accepted_method)
            else:
                node.action = Action(True, handler, accepted_method)
                return

    def print_router(self, node=None):
        if not node:
            if self.root.children_values:
                print(self.root.value + " --> " + str(self.root.children_values))
                for child_node in self.root.children_nodes:
                    self.print_router(child_node)
        else:
            if node.children_values:
                print(node.value + " --> " + str(node.children_values))
                for child_node in node.children_nodes:
                    self.print_router(child_node)

    def get_route_info(self, route, route_params=None, node=None):
        if route_params is None:  # to handle python mutable default arguments behaviour
            route_params = {}
        if not node:
            route_points = route.lstrip("/").split("/")
            first_route_point = route_points[0]
            if not first_route_point:
                return self.root, route_params
            if first_route_point not in self.root.children_values:
                has_node_with_params = False
                for child_node in self.root.children_nodes:
                    if child_node.value.startswith("{") and child_node.value.endswith(
                        "}"
                    ):
                        has_node_with_params = True
                        param = child_node.value.strip("{}")
                        route_params[param] = first_route_point
                        return self.get_route_info(
                            route_points[1:], route_params, child_node
                        )

                if not has_node_with_params:
                    return None, route_params
            else:
                index = self.root.children_values.index(first_route_point)
                return self.get_route_info(
                    route_points[1:], route_params, self.root.children_nodes[index]
                )
        else:
            if route:
                # No match if there are still route points but node has no
                # children
                if not node.children_nodes:
                    return None, route_params

                first_route_point = route[0]
                if first_route_point in node.children_values:
                    index = node.children_values.index(first_route_point)
                    return self.get_route_info(
                        route[1:], route_params, node.children_nodes[index]
                    )
                else:
                    has_node_with_params = False
                    for child_node in node.children_nodes:
                        if child_node.value.startswith(
                            "{"
                        ) and child_node.value.endswith("}"):
                            has_node_with_params = True
                            param = child_node.value.strip("{}")
                            route_params[param] = first_route_point
                            return self.get_route_info(
                                route[1:], route_params, child_node
                            )

                    if not has_node_with_params:
                        return None, route_params

            else:
                # We are at the end of the node where the route last match
                return node, route_params


# if __name__ == "__main__":
#     def get_data1():
#         return

#     def get_data2():
#         return

#     def get_data3():
#         return

#     def get_data4():
#         return

#     route1 = "/users"
#     route2 = "/users/{id}"
#     # route3 = "/users/20?a=5&b=3"
#     router = Router()

# router.add_route(route1, get_data1)
# router.add_route(route2, get_data2)
# router.add_route("/products", get_data3)
# router.add_route("/users/profiles/{id}/{name}", get_data4)
# # router.print_router()

# node, route_parameters = router.get_route_info("/users/profiles/34/clone")
# if node:
#     print(node.value)
#     # print(node.children_values)
#     # print(node.terminal)
#     # print(node.action)
#     print(route_parameters)

# node, route_parameters = router.get_route_info("/users/45")
# if node:
#     print(node.value)
#     # print(node.children_values)
#     # print(node.terminal)
#     # print(node.action)
#     print(route_parameters)
