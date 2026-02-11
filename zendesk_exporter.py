
import requests
import json
import os
import sys
import logging

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
        cursor = None
        has_more = True
        page_count = 0

        logging.info(f"Starting to fetch tickets for organization ID: {organization_id}")

        while has_more:
            page_count += 1
            params = {
                "query": f"type:ticket organization_id:{organization_id}",
                "page[size]": 100 # Max page size for search API
            }
            if cursor:
                params["page[after]"] = cursor

            logging.debug(f"Fetching page {page_count} with cursor: {cursor}")
            response_data = self.get("/search.json", params=params)
            tickets = response_data.get("results", [])
            all_tickets.extend(tickets)
            logging.info(f"Fetched {len(tickets)} tickets on page {page_count}. Total tickets: {len(all_tickets)}")

            meta = response_data.get("meta", {})
            links = response_data.get("links", {})

            has_more = meta.get("has_more")
            cursor = meta.get("after_cursor")

        logging.info(f"Finished fetching all tickets for organization ID: {organization_id}. Total: {len(all_tickets)}")
        return all_tickets

if __name__ == "__main__":
    SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")
    EMAIL = os.getenv("ZENDESK_EMAIL")
    API_TOKEN = os.getenv("ZENDESK_API_TOKEN")
    CUSTOMER_ORGANIZATION_ID = os.getenv("CUSTOMER_ORGANIZATION_ID")
    OUTPUT_FILE_PATH = os.getenv("OUTPUT_FILE_PATH", "exported_tickets.json")

    if not all([SUBDOMAIN, EMAIL, API_TOKEN, CUSTOMER_ORGANIZATION_ID]):
        logging.error("Please set ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_TOKEN, and CUSTOMER_ORGANIZATION_ID environment variables.")
        sys.exit(1)

    client = ZendeskAPIClient(SUBDOMAIN, EMAIL, API_TOKEN)

    try:
        logging.info(f"Fetching tickets for organization ID: {CUSTOMER_ORGANIZATION_ID}...")
        tickets = client.search_tickets_by_organization(CUSTOMER_ORGANIZATION_ID)
        logging.info(f"Found {len(tickets)} tickets.")

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
