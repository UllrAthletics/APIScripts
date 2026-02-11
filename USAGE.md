# Zendesk Ticket Exporter Usage

This Python script (`zendesk_exporter.py`) allows you to iteratively export Zendesk tickets for a specific customer, identified by their organization ID, into a JSON file.

## Prerequisites

*   Python 3.x installed.
*   `requests` library installed (`pip install requests`).

## Setup

Before running the script, you need to set the following environment variables:

1.  `ZENDESK_SUBDOMAIN`: Your Zendesk subdomain (e.g., `yourcompany` if your Zendesk URL is `yourcompany.zendesk.com`).
2.  `ZENDESK_EMAIL`: The email address of the Zendesk agent account used for API authentication. This agent must have appropriate permissions to access tickets and organizations.
3.  `ZENDESK_API_TOKEN`: An API token generated in your Zendesk admin interface. To generate one:
    *   Go to Admin Center > Apps and integrations > Zendesk API.
    *   Enable Token Access and click "Add API token".
    *   Copy the generated token.
4.  `CUSTOMER_ORGANIZATION_ID`: The numerical ID of the customer's organization in Zendesk whose tickets you want to export. You can find this in the Zendesk admin interface by navigating to the organization's page.
5.  `OUTPUT_FILE_PATH` (Optional): The full path where the exported JSON file will be saved. If not provided, the script defaults to `exported_tickets.json` in the current working directory.

### Example Environment Variable Setup

**For Linux/macOS:**

```bash
export ZENDESK_SUBDOMAIN="yourcompany"
export ZENDESK_EMAIL="your_email@example.com"
export ZENDESK_API_TOKEN="your_api_token"
export CUSTOMER_ORGANIZATION_ID="123456789" # Replace with actual organization ID
# export OUTPUT_FILE_PATH="/path/to/your/tickets.json" # Optional: Uncomment and set if needed
```

**For Windows (Command Prompt):**

```cmd
set ZENDESK_SUBDOMAIN="yourcompany"
set ZENDESK_EMAIL="your_email@example.com"
set ZENDESK_API_TOKEN="your_api_token"
set CUSTOMER_ORGANIZATION_ID="123456789"
rem set OUTPUT_FILE_PATH="C:\path	o\your	ickets.json"
```

## Running the Script

Once the environment variables are set, navigate to the directory containing `zendesk_exporter.py` and run the script:

```bash
python zendesk_exporter.py
```

The script will log its progress to the console and create the JSON output file at the specified `OUTPUT_FILE_PATH`.

## Output

The output will be a JSON file containing a list of ticket objects. Each object represents a Zendesk ticket and will include all standard ticket fields returned by the Zendesk Search API.
