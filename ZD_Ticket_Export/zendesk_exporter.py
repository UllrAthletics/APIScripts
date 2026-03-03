
import requests
import json
import os
import sys
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ZendeskAPIClient:
    def __init__(self, subdomain, email, api_token):
        self.base_url = f"https://{subdomain}.zendesk.com/api/v2"
        self.auth = (f"{email}/token", api_token)
        logging.info(f"Initialized ZendeskAPIClient for subdomain: {subdomain}")

    def get(self, path, params=None):
        url = f"{self.base_url}{path}"
        logging.debug(f"Making GET request to: {url} with params: {params}")
        response = requests.get(url, auth=self.auth, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()

    def search_tickets_by_organization(self, organization_id):
        all_tickets = []
        page_number = 1
        per_page = 100 # Max page size for search API

        logging.info(f"Starting to fetch tickets for organization ID: {organization_id}")

        while True:
            params = {
                "query": f"type:ticket organization_id:{organization_id}",
                "per_page": per_page,
                "page": page_number
            }

            logging.debug(f"Fetching page {page_number} with {per_page} items per page")
            response_data = self.get("/search.json", params=params)
            tickets = response_data.get("results", [])
            all_tickets.extend(tickets)
            logging.info(f"Fetched {len(tickets)} tickets on page {page_number}. Total tickets: {len(all_tickets)}")

            if not tickets or len(tickets) < per_page:
                break # No more tickets or last page

            page_number += 1

        logging.info(f"Finished fetching all tickets for organization ID: {organization_id}. Total: {len(all_tickets)}")
        return all_tickets

    def get_ticket_audits(self, ticket_id):
        """Fetch all audit events for a ticket (status changes, field updates, etc.)"""
        all_audits = []
        url = f"/tickets/{ticket_id}/audits.json"

        logging.debug(f"Fetching audits for ticket ID: {ticket_id}")

        while url:
            response_data = self.get(url, params=None)
            audits = response_data.get("audits", [])
            all_audits.extend(audits)

            # Handle pagination via cursor
            url = response_data.get("next_page")
            if url:
                # Extract path from full URL
                url = url.replace(self.base_url, "")

        logging.debug(f"Fetched {len(all_audits)} audits for ticket ID: {ticket_id}")
        return all_audits

    def get_ticket_comments(self, ticket_id):
        """Fetch all comments for a ticket"""
        all_comments = []
        url = f"/tickets/{ticket_id}/comments.json"

        logging.debug(f"Fetching comments for ticket ID: {ticket_id}")

        while url:
            response_data = self.get(url, params=None)
            comments = response_data.get("comments", [])
            all_comments.extend(comments)

            # Handle pagination
            url = response_data.get("next_page")
            if url:
                url = url.replace(self.base_url, "")

        logging.debug(f"Fetched {len(all_comments)} comments for ticket ID: {ticket_id}")
        return all_comments

    def enrich_tickets_with_history(self, tickets, include_audits=True, include_comments=True):
        """Enrich tickets with their full event history (audits and comments)"""
        enriched_tickets = []
        total = len(tickets)

        logging.info(f"Starting to enrich {total} tickets with event history...")

        for index, ticket in enumerate(tickets, 1):
            ticket_id = ticket.get("id")

            try:
                logging.info(f"Processing ticket {index}/{total}: ID {ticket_id}")

                # Add audits if requested
                if include_audits:
                    ticket["audits"] = self.get_ticket_audits(ticket_id)

                # Add comments if requested
                if include_comments:
                    ticket["comments"] = self.get_ticket_comments(ticket_id)

                enriched_tickets.append(ticket)

                # Rate limiting: sleep to avoid hitting API limits
                # Zendesk has a limit of 700 requests per minute for Enterprise
                # Adding a small delay to be safe
                time.sleep(0.1)

            except requests.exceptions.HTTPError as e:
                logging.warning(f"Failed to fetch history for ticket {ticket_id}: {e.response.status_code} - {e.response.text}")
                # Still add the ticket without enrichment
                enriched_tickets.append(ticket)
            except Exception as e:
                logging.warning(f"Unexpected error fetching history for ticket {ticket_id}: {e}")
                enriched_tickets.append(ticket)

        logging.info(f"Finished enriching tickets with event history")
        return enriched_tickets

if __name__ == "__main__":
    SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")
    EMAIL = os.getenv("ZENDESK_EMAIL")
    API_TOKEN = os.getenv("ZENDESK_API_TOKEN")
    OUTPUT_FILE_PATH = os.getenv("OUTPUT_FILE_PATH", "exported_tickets.json")

    if not all([SUBDOMAIN, EMAIL, API_TOKEN]):
        logging.error("Please set ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, and ZENDESK_API_TOKEN environment variables.")
        sys.exit(1)

    # Get organization ID from environment variable or user input
    CUSTOMER_ORGANIZATION_ID = os.getenv("CUSTOMER_ORGANIZATION_ID")

    if not CUSTOMER_ORGANIZATION_ID:
        try:
            CUSTOMER_ORGANIZATION_ID = input("Enter the Customer Organization ID: ").strip()
            if not CUSTOMER_ORGANIZATION_ID:
                logging.error("Organization ID cannot be empty.")
                sys.exit(1)
        except KeyboardInterrupt:
            logging.info("\nOperation cancelled by user.")
            sys.exit(0)
    else:
        logging.info(f"Using organization ID from environment variable: {CUSTOMER_ORGANIZATION_ID}")

    # Validate organization ID is numeric
    if not CUSTOMER_ORGANIZATION_ID.isdigit():
        logging.error(f"Invalid organization ID: {CUSTOMER_ORGANIZATION_ID}. Organization ID must be numeric.")
        sys.exit(1)

    # Option to fetch full event history
    FETCH_FULL_HISTORY = os.getenv("FETCH_FULL_HISTORY", "").lower() in ["true", "1", "yes"]

    if not FETCH_FULL_HISTORY:
        try:
            response = input("Fetch full event history (audits & comments) for each ticket? This will be slower. (y/n): ").strip().lower()
            FETCH_FULL_HISTORY = response in ["y", "yes"]
        except KeyboardInterrupt:
            logging.info("\nOperation cancelled by user.")
            sys.exit(0)

    client = ZendeskAPIClient(SUBDOMAIN, EMAIL, API_TOKEN)

    try:
        logging.info(f"Fetching tickets for organization ID: {CUSTOMER_ORGANIZATION_ID}...")
        tickets = client.search_tickets_by_organization(CUSTOMER_ORGANIZATION_ID)
        logging.info(f"Found {len(tickets)} tickets.")

        # Enrich with full event history if requested
        if FETCH_FULL_HISTORY:
            logging.info("Fetching full event history for each ticket (this may take a while)...")
            tickets = client.enrich_tickets_with_history(tickets, include_audits=True, include_comments=True)
        else:
            logging.info("Skipping full event history. Only ticket metadata will be exported.")

        with open(OUTPUT_FILE_PATH, "w") as f:
            json.dump(tickets, f, indent=4)
        logging.info(f"Exported {len(tickets)} tickets to {OUTPUT_FILE_PATH}")

    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP Error during Zendesk API request: {e.response.status_code} - {e.response.text}")
        sys.exit(1)
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Connection Error during Zendesk API request: {e}")
        sys.exit(1)
    except requests.exceptions.Timeout as e:
        logging.error(f"Timeout Error during Zendesk API request: {e}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        logging.error(f"General Request Error during Zendesk API request: {e}")
        sys.exit(1)
    except IOError as e:
        logging.error(f"Error writing to output file {OUTPUT_FILE_PATH}: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)
