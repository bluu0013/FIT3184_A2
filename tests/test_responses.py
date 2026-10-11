import base64
import json
import unittest

import _paths  # noqa: F401
from ecoguard_common import responses


class JsonBodyTests(unittest.TestCase):
    def test_plain_and_base64(self):
        self.assertEqual(responses.json_body({"body": '{"a": 1}'}), {"a": 1})
        encoded = base64.b64encode(b'{"a": 2}').decode()
        self.assertEqual(responses.json_body({"body": encoded, "isBase64Encoded": True}), {"a": 2})

    def test_empty_body_is_empty_object(self):
        self.assertEqual(responses.json_body({}), {})

    def test_rejects_invalid(self):
        for body in ("not json", "[1, 2]"):
            with self.subTest(body=body):
                with self.assertRaises(ValueError):
                    responses.json_body({"body": body})


class RunTests(unittest.TestCase):
    def test_maps_exceptions_to_status_codes(self):
        def raises(exc):
            def fn(_event):
                raise exc
            return fn

        self.assertEqual(responses.run(lambda e: {"ok": 1}, {})["statusCode"], 200)
        self.assertEqual(responses.run(raises(ValueError("bad")), {})["statusCode"], 400)
        self.assertEqual(responses.run(raises(LookupError("missing")), {})["statusCode"], 404)
        self.assertEqual(responses.run(raises(ConnectionError("down")), {})["statusCode"], 502)

    def test_error_body(self):
        out = responses.run(lambda e: (_ for _ in ()).throw(ValueError("nope")), {})
        self.assertEqual(json.loads(out["body"]), {"error": "nope"})


class ClaimsTests(unittest.TestCase):
    def test_claims_and_bearer(self):
        event = {
            "requestContext": {"authorizer": {"jwt": {"claims": {"sub": "u1"}}}},
            "headers": {"authorization": "Bearer abc.def"},
        }
        self.assertEqual(responses.claims(event), {"sub": "u1"})
        self.assertEqual(responses.bearer_token(event), "abc.def")
        self.assertEqual(responses.claims({}), {})
        self.assertIsNone(responses.bearer_token({}))


if __name__ == "__main__":
    unittest.main()
