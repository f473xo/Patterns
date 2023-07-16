import pytest

from framework.utils.tests import url


def test_basic_route(api):
    @api.route("/")
    def home(req, resp):
        resp.text = "Welcome Home."


def test_basic_alternative_route(api):
    def home(req, resp):
        resp.text = "Alternative way to add a route"

    api.add_route("/alternative", home)


def test_route_overlap_throws_exception(api):
    @api.route("/")
    def home(req, resp):
        resp.text = "Welcome Home."

    with pytest.raises(AssertionError):
        @api.route("/")
        def home2(req, resp):
            resp.text = "Welcome Home2."


def test_alternative_route_overlap_throws_exception(api):
    def home(req, resp):
        resp.text = "Welcome Home."

    def home2(req, resp):
        resp.text = "Welcome Home2."

    api.add_route("/alternative", home)

    with pytest.raises(AssertionError):
        api.add_route("/alternative", home2)


def test_parameterized_route(api, client):
    @api.route("/{name}")
    def hello(req, resp, name):
        resp.text = f"hey {name}"

    assert client.get(url("/matthew")).text == "hey matthew"


def test_class_based_handler_route_registration(api):
    @api.route("/book")
    class BookResource:
        def get(self, req, resp):
            resp.text = "yolo"


def test_receive_and_decode_post_request_parameters(api, client):
    requests_text = "?param1=value1&param2=value2&param3=value3"
    response_text = {"param1": "value1", "param2": "value2", "param3": "value3"}

    @api.route("/tests")
    class AnyParams:
        def get(self, req, resp):
            resp.json = response_text

        def post(self, req, resp):
            resp.json = response_text

    assert client.get(url(f"/tests{requests_text}")).json() == response_text
    assert client.post(url(f"/tests{requests_text}")).json() == response_text
