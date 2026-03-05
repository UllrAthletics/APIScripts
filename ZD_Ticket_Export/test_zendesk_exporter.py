
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
            "results": [{"id": 1, "subject": "Ticket 1"}]
        }

        tickets = self.client.search_tickets_by_organization(organization_id)

        mock_get.assert_called_once_with(
            "/search.json",
            params={"query": f"type:ticket organization_id:{organization_id}", "per_page": 100, "page": 1}
        )
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0]["id"], 1)

    @patch.object(ZendeskAPIClient, 'get')
    def test_search_tickets_by_organization_no_results(self, mock_get):
        organization_id = "99999"
        mock_get.return_value = {
            "results": []
        }

        tickets = self.client.search_tickets_by_organization(organization_id)

        mock_get.assert_called_once()
        self.assertEqual(len(tickets), 0)

    @patch.object(ZendeskAPIClient, 'get')
    def test_search_tickets_by_organization_exactly_page_size(self, mock_get):
        organization_id = "55555"
        # Exactly 100 results (full page) - will fetch page 2 which returns empty
        mock_get.side_effect = [
            {"results": [{"id": i, "subject": f"Ticket {i}"} for i in range(1, 101)]},
            {"results": []}  # Page 2 is empty
        ]

        tickets = self.client.search_tickets_by_organization(organization_id)

        # Should call twice: once for page 1 (100 items), once for page 2 (0 items)
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(len(tickets), 100)

    @patch.object(ZendeskAPIClient, 'get')
    def test_search_tickets_by_organization_multi_page(self, mock_get):
        organization_id = "67890"

        # First page response (full page = 100 results)
        mock_get.side_effect = [
            {
                "results": [{"id": i, "subject": f"Ticket {i}"} for i in range(1, 101)]
            },
            # Second page response (partial page)
            {
                "results": [{"id": 101, "subject": "Ticket 101"}, {"id": 102, "subject": "Ticket 102"}]
            }
        ]

        tickets = self.client.search_tickets_by_organization(organization_id)

        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_any_call(
            "/search.json",
            params={"query": f"type:ticket organization_id:{organization_id}", "per_page": 100, "page": 1}
        )
        mock_get.assert_any_call(
            "/search.json",
            params={"query": f"type:ticket organization_id:{organization_id}", "per_page": 100, "page": 2}
        )
        self.assertEqual(len(tickets), 102)
        self.assertEqual(tickets[0]["id"], 1)
        self.assertEqual(tickets[-1]["id"], 102)

    @patch.object(ZendeskAPIClient, 'get')
    def test_get_ticket_audits_single_page(self, mock_get):
        ticket_id = 123
        mock_get.return_value = {
            "audits": [{"id": 1, "created_at": "2024-01-01"}],
            "next_page": None
        }

        audits = self.client.get_ticket_audits(ticket_id)

        mock_get.assert_called_once_with(f"/tickets/{ticket_id}/audits.json", params=None)
        self.assertEqual(len(audits), 1)
        self.assertEqual(audits[0]["id"], 1)

    @patch.object(ZendeskAPIClient, 'get')
    def test_get_ticket_audits_multi_page(self, mock_get):
        ticket_id = 456
        base_url = "https://testcompany.zendesk.com/api/v2"

        mock_get.side_effect = [
            {
                "audits": [{"id": 1, "created_at": "2024-01-01"}],
                "next_page": f"{base_url}/tickets/{ticket_id}/audits.json?page=2"
            },
            {
                "audits": [{"id": 2, "created_at": "2024-01-02"}],
                "next_page": None
            }
        ]

        audits = self.client.get_ticket_audits(ticket_id)

        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(len(audits), 2)
        self.assertEqual(audits[0]["id"], 1)
        self.assertEqual(audits[1]["id"], 2)

    @patch.object(ZendeskAPIClient, 'get')
    def test_get_ticket_comments_single_page(self, mock_get):
        ticket_id = 789
        mock_get.return_value = {
            "comments": [{"id": 1, "body": "Test comment"}],
            "next_page": None
        }

        comments = self.client.get_ticket_comments(ticket_id)

        mock_get.assert_called_once_with(f"/tickets/{ticket_id}/comments.json", params=None)
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]["body"], "Test comment")

    @patch.object(ZendeskAPIClient, 'get')
    def test_get_ticket_comments_multi_page(self, mock_get):
        ticket_id = 999
        base_url = "https://testcompany.zendesk.com/api/v2"

        mock_get.side_effect = [
            {
                "comments": [{"id": 1, "body": "Comment 1"}],
                "next_page": f"{base_url}/tickets/{ticket_id}/comments.json?page=2"
            },
            {
                "comments": [{"id": 2, "body": "Comment 2"}],
                "next_page": None
            }
        ]

        comments = self.client.get_ticket_comments(ticket_id)

        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(len(comments), 2)

    @patch('time.sleep')
    @patch.object(ZendeskAPIClient, 'get_ticket_comments')
    @patch.object(ZendeskAPIClient, 'get_ticket_audits')
    def test_enrich_tickets_with_history(self, mock_audits, mock_comments, mock_sleep):
        mock_audits.return_value = [{"id": 1, "created_at": "2024-01-01"}]
        mock_comments.return_value = [{"id": 1, "body": "Test comment"}]

        tickets = [
            {"id": 100, "subject": "Test Ticket 1"},
            {"id": 200, "subject": "Test Ticket 2"}
        ]

        enriched = self.client.enrich_tickets_with_history(tickets, include_audits=True, include_comments=True)

        self.assertEqual(len(enriched), 2)
        self.assertIn("audits", enriched[0])
        self.assertIn("comments", enriched[0])
        self.assertEqual(mock_audits.call_count, 2)
        self.assertEqual(mock_comments.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch('time.sleep')
    @patch.object(ZendeskAPIClient, 'get_ticket_audits')
    def test_enrich_tickets_audits_only(self, mock_audits, mock_sleep):
        mock_audits.return_value = [{"id": 1}]

        tickets = [{"id": 100, "subject": "Test"}]
        enriched = self.client.enrich_tickets_with_history(tickets, include_audits=True, include_comments=False)

        self.assertIn("audits", enriched[0])
        self.assertNotIn("comments", enriched[0])
        mock_audits.assert_called_once()

    @patch('time.sleep')
    @patch.object(ZendeskAPIClient, 'get_ticket_audits')
    def test_enrich_tickets_handles_http_errors(self, mock_audits, mock_sleep):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_audits.side_effect = requests.exceptions.HTTPError(response=mock_response)

        tickets = [{"id": 100, "subject": "Test"}]
        enriched = self.client.enrich_tickets_with_history(tickets, include_audits=True, include_comments=False)

        # Should still return the ticket even if enrichment fails
        self.assertEqual(len(enriched), 1)
        self.assertEqual(enriched[0]["id"], 100)

    @patch('time.sleep')
    @patch.object(ZendeskAPIClient, 'get_ticket_audits')
    def test_enrich_tickets_handles_generic_errors(self, mock_audits, mock_sleep):
        mock_audits.side_effect = Exception("Unexpected error")

        tickets = [{"id": 200, "subject": "Test 2"}]
        enriched = self.client.enrich_tickets_with_history(tickets, include_audits=True, include_comments=False)

        # Should still return the ticket even if enrichment fails with generic exception
        self.assertEqual(len(enriched), 1)
        self.assertEqual(enriched[0]["id"], 200)

    @patch('time.sleep')
    @patch.object(ZendeskAPIClient, 'get_ticket_comments')
    @patch.object(ZendeskAPIClient, 'get_ticket_audits')
    def test_enrich_tickets_with_empty_audits_and_comments(self, mock_audits, mock_comments, mock_sleep):
        mock_audits.return_value = []
        mock_comments.return_value = []

        tickets = [{"id": 300, "subject": "Empty History"}]
        enriched = self.client.enrich_tickets_with_history(tickets, include_audits=True, include_comments=True)

        self.assertEqual(len(enriched), 1)
        self.assertEqual(enriched[0]["audits"], [])
        self.assertEqual(enriched[0]["comments"], [])

    @patch.object(ZendeskAPIClient, 'get')
    def test_get_ticket_audits_empty(self, mock_get):
        ticket_id = 999
        mock_get.return_value = {
            "audits": [],
            "next_page": None
        }

        audits = self.client.get_ticket_audits(ticket_id)

        self.assertEqual(len(audits), 0)

    @patch.object(ZendeskAPIClient, 'get')
    def test_get_ticket_comments_empty(self, mock_get):
        ticket_id = 888
        mock_get.return_value = {
            "comments": [],
            "next_page": None
        }

        comments = self.client.get_ticket_comments(ticket_id)

        self.assertEqual(len(comments), 0)

if __name__ == '__main__':
    unittest.main()
