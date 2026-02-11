
import unittest
from unittest.mock import patch, MagicMock
import requests
import json
import os
import sys


from zendesk_exporter import ZendeskAPIClient

class TestZendeskAPIClient(unittest.TestCase):

    def setUp(self):
        self.subdomain = "testcompany"
        self.email = "test@example.com"
        self.api_token = "test_token"
        self.client = ZendeskAPIClient(self.subdomain, self.email, self.api_token)

    def test_init(self):
        self.assertEqual(self.client.base_url, "https://testcompany.zendesk.com/api/v2")
        self.assertEqual(self.client.auth, ("test@example.com/token", "test_token"))

    @patch('requests.get')
    def test_get_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "value"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.client.get("/test.json", params={"param": "value"})

        mock_get.assert_called_once_with(
            "https://testcompany.zendesk.com/api/v2/test.json",
            auth=("test@example.com/token", "test_token"),
            params={"param": "value"}
        )
        mock_response.raise_for_status.assert_called_once()
        self.assertEqual(result, {"key": "value"})

    @patch('requests.get')
    def test_get_http_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        with self.assertRaises(requests.exceptions.HTTPError):
            self.client.get("/nonexistent.json")

        mock_response.raise_for_status.assert_called_once()

    @patch.object(ZendeskAPIClient, 'get')
    def test_search_tickets_by_organization_single_page(self, mock_get):
        organization_id = "12345"
        mock_get.return_value = {
            "results": [{"id": 1, "subject": "Ticket 1"}],
            "meta": {"has_more": False},
            "links": {}
        }

        tickets = self.client.search_tickets_by_organization(organization_id)

        mock_get.assert_called_once_with(
            "/search.json",
            params={"query": f"type:ticket organization_id:{organization_id}", "page[size]": 100}
        )
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0]["id"], 1)

    @patch.object(ZendeskAPIClient, 'get')
    def test_search_tickets_by_organization_multi_page(self, mock_get):
        organization_id = "67890"

        # First page response
        mock_get.side_effect = [
            {
                "results": [{"id": 1, "subject": "Ticket A"}],
                "meta": {"has_more": True, "after_cursor": "cursor1"},
                "links": {"next": "http://next_page_url"}
            },
            # Second page response
            {
                "results": [{"id": 2, "subject": "Ticket B"}],
                "meta": {"has_more": False},
                "links": {}
            }
        ]

        tickets = self.client.search_tickets_by_organization(organization_id)

        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_any_call(
            "/search.json",
            params={"query": f"type:ticket organization_id:{organization_id}", "page[size]": 100}
        )
        mock_get.assert_any_call(
            "/search.json",
            params={"query": f"type:ticket organization_id:{organization_id}", "page[size]": 100, "page[after]": "cursor1"}
        )
        self.assertEqual(len(tickets), 2)
        self.assertEqual(tickets[0]["id"], 1)
        self.assertEqual(tickets[1]["id"], 2)

if __name__ == '__main__':
    unittest.main()
