import os
import sys
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
from episode.route import Router


class RouterTests(unittest.TestCase):
    @classmethod
    def get_data(cls):
        return
    
    @classmethod
    def setUpClass(cls):
        cls.router = Router()

        cls.router.add_route("/users", cls.get_data, accepted_method="all")
        cls.router.add_route("/users/{id}", cls.get_data, accepted_method="GET")
        cls.router.add_route("/products", cls.get_data, accepted_method="POST")
        cls.router.add_route("/users/profiles/", cls.get_data)
        cls.router.add_route("/users/profiles/", cls.get_data, accepted_method="POST")

    @classmethod
    def tearDownClass(cls):
        del cls.router
    
    def test_root_node(self):
        root = self.router.root

        self.assertEqual(root.value, "/")

        self.assertEqual(len(root.children_nodes), 2)

        self.assertEqual(root.actions, [])
    
    def test_all_route_method(self):
        node, route_parameters = self.router.get_route_info("/users")
        
        self.assertEqual(route_parameters, {})

        self.assertEqual(node.actions[0].accepted_method, "all")
    
    def test_GET_route_method(self):
        node, route_parameters = self.router.get_route_info("/users/24")

        self.assertEqual(route_parameters, {"id": "24"})

        self.assertEqual(node.actions[0].accepted_method, "GET")
    
    def test_POST_route_method(self):
        node, _ = self.router.get_route_info("/products")

        self.assertEqual(node.actions[0].accepted_method, "POST")
    
    def test_node_with_multiple_request_methods(self):
        node, _ = self.router.get_route_info("/users/profiles/")

        self.assertEqual(len(node.actions), 2)

        expected_request_methods = ["all", "POST"]
        actual_request_methods = [action.accepted_method for action in node.actions]

        self.assertEqual(expected_request_methods, actual_request_methods)
