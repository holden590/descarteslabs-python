# Copyright 2018 Descartes Labs.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import io
import re
import unittest
import json
import responses

from descarteslabs.client.auth import Auth
from descarteslabs.client.services.vector import Vector
from descarteslabs.client.exceptions import BadRequestError, NotFoundError

public_token = "header.e30.signature"


class ClientTestCase(unittest.TestCase):

    def setUp(self):
        self.url = "http://example.vector.com"
        self.gcs_url = "http://example.gcs.com"

        self.client = Vector(url=self.url, auth=Auth(jwt_token=public_token, token_info_path=None))

        self.match_url = re.compile(self.url)
        self.match_gcs_url = re.compile(self.gcs_url)

        self.attrs = {
            'geometry': {'coordinates': [
                [
                    [-113.40087890624999, 40.069664523297774],
                    [-111.434326171875, 40.069664523297774],
                    [-111.434326171875, 41.918628865183045],
                    [-113.40087890624999, 41.918628865183045],
                    [-113.40087890624999, 40.069664523297774]
                ]
            ], 'type': 'Polygon'},
            'properties': {'baz': 1.0, 'foo': 'bar'}
        }

        self.product_response = {
            'data': {
                'attributes': {
                    'description': 'bar',
                    'name': 'new-test-product',
                    'owners': [
                        'org:descarteslabs',
                        'user:3d7bf4b0b1f4e6283e5cbeaadddbc6de6f16dea1'
                    ],
                    'readers': [],
                    'title': 'Test Product',
                    'writers': []
                },
                'id': '2b4552ff4b8a4bb5bb278c94005db50',
                'meta': {
                    'created': '2018-12-27T17:01:16.197369'
                },
                'type': 'product'
            }
        }

        self.status_response = {
            'data': {
                'attributes': {
                    'created': '2019-01-03T20:07:51.720000+00:00',
                    'started': '2019-01-03T20:07:51.903000+00:00',
                    'status': 'RUNNING'
                },
                'id': 'c589d688-3230-4caf-9f9d-18854f71e91d',
                'type': 'copy_query'
            }
        }

        self.feature_response = {
            'data': [
                {
                    'attributes': {
                        'created': '2019-03-28T23:08:24.991729+00:00',
                        'geometry': {
                            'coordinates': [[[-95, 42], [-95, 41], [-93, 40], [-93, 42],  [-95, 42]]],
                            'type': 'Polygon'
                        },
                        'properties': {}
                    },
                    'id': '7d724ae48d1fab595bc95b6091b005c920327',
                    'type': 'feature'
                }
            ]
        }

    def mock_response(self, method, json, status=200, **kwargs):
        responses.add(method, self.match_url, json=json, status=status, **kwargs)

    def mock_gcs(self, method, json, status=200, **kwargs):
        responses.add(method, self.match_gcs_url, json=json, status=status, **kwargs)


class VectorsTest(ClientTestCase):

    @responses.activate
    def test_upload_bytesio(self):
        self.mock_response(responses.POST, {
            'upload_id': 'xyz',
            'url': self.gcs_url
        })

        self.mock_gcs(responses.PUT, {})

        s = io.BytesIO()

        for i in range(10):
            s.write(b'{')
            s.write('{}'.format(self.attrs).encode('utf-8'))
            s.write(b'}\n')

        self.client.upload_features(s, 'test')

    @responses.activate
    def test_upload_stringio(self):
        self.mock_response(responses.POST, {
            'upload_id': 'xyz',
            'url': self.gcs_url
        })

        self.mock_gcs(responses.PUT, {})

        s = io.StringIO()

        for i in range(10):
            s.write(u'{')
            s.write(u'{}'.format(self.attrs))
            s.write(u'}\n')

        self.client.upload_features(s, 'test')

    @responses.activate
    def test_bad_upload(self):
        self.mock_response(responses.POST, {
            'upload_id': 'xyz',
            'url': self.gcs_url
        })

        self.mock_gcs(responses.PUT, {})

        s = ""

        for i in range(10):
            s += '{'
            s += '{}'.format(self.attrs)
            s += '}\n'

        with self.assertRaises(Exception):
            self.client.upload_features(s, 'test')

    @responses.activate
    def test_create_product_from_query(self):
        self.mock_response(responses.POST, self.product_response, status=201)

        r = self.client.create_product_from_query(
            "foo",
            "Foo",
            "Foo is a bar",
            "baz"
        )

        self.assertEqual("2b4552ff4b8a4bb5bb278c94005db50", r.data.id)

    @responses.activate
    def test_create_product_from_query_exception(self):
        self.mock_response(responses.POST, {}, status=400)

        with self.assertRaises(BadRequestError):
            self.client.create_product_from_query(
                "foo",
                "Foo",
                "Foo is a bar",
                "baz"
            )

    @responses.activate
    def test_get_product_from_query_status(self):
        self.mock_response(responses.GET, self.status_response, status=200)

        r = self.client.get_product_from_query_status("2b4552ff4b8a4bb5bb278c94005db50")

        self.assertEqual(r.data.id, "c589d688-3230-4caf-9f9d-18854f71e91d")

    @responses.activate
    def test_get_product_from_query_status_not_found(self):
        self.mock_response(responses.GET, self.status_response, status=404)

        with self.assertRaises(NotFoundError):
            self.client.get_product_from_query_status("2b4552ff4b8a4bb5bb278c94005db50")

    @responses.activate
    def delete_features_from_query(self):
        self.mock_response(responses.DELETE, self.product_response, status=202)

        r = self.client.delete_features_from_query("foo", "bar", "baz")

        self.assertEqual("2b4552ff4b8a4bb5bb278c94005db50", r.data.id)

    @responses.activate
    def delete_features_from_query_bad_request(self):
        self.mock_response(responses.DELETE, self.product_response, status=400)

        with self.assertRaises(BadRequestError):
            self.client.delete_features_from_query("foo", "bar", "baz")

    @responses.activate
    def test_get_delete_features_status(self):
        self.mock_response(responses.GET, self.status_response, status=200)

        r = self.client.get_product_from_query_status("2b4552ff4b8a4bb5bb278c94005db50")
        self.assertEqual(r.data.id, "c589d688-3230-4caf-9f9d-18854f71e91d")

    @responses.activate
    def test_get_delete_features_status_not_found(self):
        self.mock_response(responses.GET, self.status_response, status=404)

        with self.assertRaises(NotFoundError):
            self.client.get_product_from_query_status("2b4552ff4b8a4bb5bb278c94005db50")

    @responses.activate
    def test_create_feature_correct_wo(self):
        self.mock_response(responses.POST, self.feature_response, status=200)
        non_ccw = {
            'type': 'Polygon',
            'coordinates': [[[-95, 42], [-93, 42], [-93, 40], [-95, 41], [-95, 42]]]
        }

        self.client.create_feature("2b4552ff4b8a4bb5bb278c94005db50", non_ccw, correct_winding_order=True)
        expected_req_body = {
            "data": {
                "attributes": {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-95, 42], [-93, 42], [-93, 40], [-95, 41], [-95, 42]]]
                    },
                    "correct_winding_order": True,
                    "properties": None
                },
                "type": "feature"
            }
        }
        request = responses.calls[0].request
        self.assertEqual(request.body, json.dumps(expected_req_body))

    @responses.activate
    def test_create_feature_default(self):
        self.mock_response(responses.POST, self.feature_response, status=400)
        non_ccw = {
            'type': 'Polygon',
            'coordinates': [[[-95, 42], [-93, 42], [-93, 40], [-95, 41], [-95, 42]]]
        }

        self.assertRaises(
            BadRequestError,
            self.client.create_feature,
            "2b4552ff4b8a4bb5bb278c94005db50",
            non_ccw
        )

        expected_req_body = {
            "data": {
                "attributes": {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-95, 42], [-93, 42], [-93, 40], [-95, 41], [-95, 42]]]
                    },
                    "properties": None
                },
                "type": "feature"
            }
        }

        request = responses.calls[0].request
        self.assertEqual(request.body, json.dumps(expected_req_body))

    @responses.activate
    def test_create_features_correct_wo(self):
        self.mock_response(responses.POST, self.feature_response, status=200)
        non_ccw_list = [
            {
                'type': 'Polygon',
                'coordinates': [[[-95, 42], [-93, 42], [-93, 40], [-95, 41], [-95, 42]]]
            }, {
                "type": "MultiPolygon",
                "coordinates": [
                    [[[-95, 42], [-95, 41], [-93, 40], [-93, 42], [-95, 42]]],
                    [[[-91, 44], [-92, 43], [-91, 42], [-89, 43], [-91, 44]]],
                    [[[-97, 44], [-96, 42], [-95, 43], [-94, 43], [-95, 44], [-97, 44]]]
                ]
            }, {
                "type": "MultiLineString",
                "coordinates": [
                    [[-91, 44], [-89, 43], [-91, 42],  [-92, 43]],
                    [[-95, 42], [-93, 42],  [-93, 40], [-95, 41]]
                ]
            }
        ]

        self.client.create_features("2b4552ff4b8a4bb5bb278c94005db50", non_ccw_list, correct_winding_order=True)
        expected_req_body = {
            "data": [{
                    "attributes": {
                        "correct_winding_order": True,
                        "type": "Polygon",
                        "coordinates": [[[-95, 42], [-93, 42], [-93, 40], [-95, 41], [-95, 42]]]
                    },
                    "type": "feature"
                }, {
                    "attributes": {
                        "correct_winding_order": True,
                        "type": "MultiPolygon",
                        "coordinates": [
                            [[[-95, 42], [-95, 41], [-93, 40], [-93, 42], [-95, 42]]],
                            [[[-91, 44], [-92, 43], [-91, 42], [-89, 43], [-91, 44]]],
                            [[[-97, 44], [-96, 42], [-95, 43], [-94, 43], [-95, 44], [-97, 44]]]
                        ]
                    },
                    "type": "feature"
                }, {
                    "attributes": {
                        "correct_winding_order": True,
                        "type": "MultiLineString",
                        "coordinates": [
                            [[-91, 44], [-89, 43], [-91, 42], [-92, 43]],
                            [[-95, 42], [-93, 42], [-93, 40], [-95, 41]]
                        ]
                    },
                    "type": "feature"
                }
            ]
        }

        request = responses.calls[0].request
        self.assertEqual(request.body, json.dumps(expected_req_body))

    @responses.activate
    def test_create_features_default(self):
        self.mock_response(responses.POST, self.feature_response, status=400)
        non_ccw_list = [
            {
                'type': 'Polygon',
                'coordinates': [[[-95, 42], [-93, 42], [-93, 40], [-95, 41], [-95, 42]]]
            }, {
                "type": "MultiPolygon",
                "coordinates": [
                    [[[-95, 42], [-95, 41], [-93, 40], [-93, 42], [-95, 42]]],
                    [[[-91, 44], [-92, 43], [-91, 42], [-89, 43], [-91, 44]]],
                    [[[-97, 44], [-96, 42], [-95, 43], [-94, 43], [-95, 44], [-97, 44]]]
                ]
            }, {
                "type": "MultiLineString",
                "coordinates": [
                    [[-91, 44], [-89, 43], [-91, 42],  [-92, 43]],
                    [[-95, 42], [-93, 42],  [-93, 40], [-95, 41]]
                ]
            }
        ]

        self.assertRaises(
            BadRequestError,
            self.client.create_features,
            "2b4552ff4b8a4bb5bb278c94005db50",
            non_ccw_list
        )

        expected_req_body = {
            "data": [{
                    "attributes": {
                        "type": "Polygon",
                        "coordinates": [[[-95, 42], [-93, 42], [-93, 40], [-95, 41], [-95, 42]]]
                    },
                    "type": "feature"
                }, {
                    "attributes": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [[[-95, 42], [-95, 41], [-93, 40], [-93, 42], [-95, 42]]],
                            [[[-91, 44], [-92, 43], [-91, 42], [-89, 43], [-91, 44]]],
                            [[[-97, 44], [-96, 42], [-95, 43], [-94, 43], [-95, 44], [-97, 44]]]
                        ]
                    },
                    "type": "feature"
                }, {
                    "attributes": {
                        "type": "MultiLineString",
                        "coordinates": [
                            [[-91, 44], [-89, 43], [-91, 42], [-92, 43]],
                            [[-95, 42], [-93, 42], [-93, 40], [-95, 41]]
                        ]
                    },
                    "type": "feature"
                }
            ]
        }
        request = responses.calls[0].request
        self.assertEqual(request.body, json.dumps(expected_req_body))


if __name__ == "__main__":
    unittest.main()
