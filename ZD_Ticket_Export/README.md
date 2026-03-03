# APIScripts

A collection of API integration scripts for various platforms.

## Zendesk Ticket Exporter

Export Zendesk tickets by organization with optional full event history (audits and comments).

### Features

- Export all tickets for a specific organization
- Optional full event history including:
  - Ticket audits (status changes, field updates, assignments)
  - Comments and replies (public and private)
- Automatic pagination handling
- Rate limiting to respect API quotas
- Comprehensive error handling and logging
- Flexible configuration via environment variables or interactive prompts

### Prerequisites

- Python 3.6 or higher
- Zendesk API token with appropriate permissions
- Required Python packages:
  ```bash
  pip install requests
  ```

### Required Environment Variables

The following environment variables must be configured:

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `ZENDESK_SUBDOMAIN` | Your Zendesk subdomain (without .zendesk.com) | Yes | `mycompany` |
| `ZENDESK_EMAIL` | Email address associated with the API token | Yes | `admin@example.com` |
| `ZENDESK_API_TOKEN` | Your Zendesk API token | Yes | `abc123xyz789...` |
| `CUSTOMER_ORGANIZATION_ID` | Organization ID to export tickets from | No* | `123456789` |
| `FETCH_FULL_HISTORY` | Fetch full event history (audits & comments) | No | `true` or `false` |
| `OUTPUT_FILE_PATH` | Path where the JSON file will be saved | No | `exported_tickets.json` |

\* If not set, you'll be prompted to enter it when running the script

### Setting Environment Variables

#### Temporary (Current Session Only)

**macOS/Linux:**
```bash
export ZENDESK_SUBDOMAIN="mycompany"
export ZENDESK_EMAIL="admin@example.com"
export ZENDESK_API_TOKEN="your_api_token_here"
export CUSTOMER_ORGANIZATION_ID="123456789"
export FETCH_FULL_HISTORY="true"
export OUTPUT_FILE_PATH="exported_tickets.json"
```

**Windows (Command Prompt):**
```cmd
set ZENDESK_SUBDOMAIN=mycompany
set ZENDESK_EMAIL=admin@example.com
set ZENDESK_API_TOKEN=your_api_token_here
set CUSTOMER_ORGANIZATION_ID=123456789
set FETCH_FULL_HISTORY=true
set OUTPUT_FILE_PATH=exported_tickets.json
```

**Windows (PowerShell):**
```powershell
$env:ZENDESK_SUBDOMAIN="mycompany"
$env:ZENDESK_EMAIL="admin@example.com"
$env:ZENDESK_API_TOKEN="your_api_token_here"
$env:CUSTOMER_ORGANIZATION_ID="123456789"
$env:FETCH_FULL_HISTORY="true"
$env:OUTPUT_FILE_PATH="exported_tickets.json"
```

#### Permanent Configuration

**macOS/Linux (bash):**

1. Open your bash profile:
   ```bash
   nano ~/.bash_profile
   # or for newer macOS versions
   nano ~/.zprofile
   ```

2. Add the export commands:
   ```bash
   export ZENDESK_SUBDOMAIN="mycompany"
   export ZENDESK_EMAIL="admin@example.com"
   export ZENDESK_API_TOKEN="your_api_token_here"
   export CUSTOMER_ORGANIZATION_ID="123456789"
   export FETCH_FULL_HISTORY="true"
   export OUTPUT_FILE_PATH="exported_tickets.json"
   ```

3. Save and reload:
   ```bash
   source ~/.bash_profile
   # or
   source ~/.zprofile
   ```

**macOS/Linux (zsh):**

1. Open your zsh profile:
   ```bash
   nano ~/.zshrc
   ```

2. Add the export commands (same as above)

3. Save and reload:
   ```bash
   source ~/.zshrc
   ```

**Windows (Permanent System Variables):**

1. Open System Properties:
   - Press `Win + X` and select "System"
   - Click "Advanced system settings"
   - Click "Environment Variables"

2. Under "User variables" or "System variables", click "New"

3. Add each variable:
   - Variable name: `ZENDESK_SUBDOMAIN`
   - Variable value: `mycompany`
   - Repeat for all variables

4. Click "OK" to save

**Using a .env file (Recommended for Security):**

1. Create a `.env` file in the project directory:
   ```bash
   nano .env
   ```

2. Add your variables:
   ```
   ZENDESK_SUBDOMAIN=mycompany
   ZENDESK_EMAIL=admin@example.com
   ZENDESK_API_TOKEN=your_api_token_here
   CUSTOMER_ORGANIZATION_ID=123456789
   FETCH_FULL_HISTORY=true
   OUTPUT_FILE_PATH=exported_tickets.json
   ```

3. Install python-dotenv:
   ```bash
   pip install python-dotenv
   ```

4. Add to the top of `zendesk_exporter.py` (before other imports):
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

5. **Important:** Add `.env` to your `.gitignore` to prevent committing secrets:
   ```bash
   echo ".env" >> .gitignore
   ```

### Getting Your Zendesk API Token

1. Log in to your Zendesk account
2. Click the **Admin** icon (gear icon) in the sidebar
3. Navigate to **Apps and integrations** > **APIs** > **Zendesk API**
4. Click the **Settings** tab
5. Enable **Token Access**
6. Click the **+** button to create a new token
7. Copy the token (it will only be shown once)

### Usage

#### Basic Usage (Interactive Mode)

Run the script and follow the prompts:

```bash
python zendesk_exporter.py
```

You'll be prompted for:
1. Organization ID (if not set in environment)
2. Whether to fetch full event history (if not set in environment)

#### Environment Variables Only (Non-Interactive)

Set all required variables and run:

```bash
export ZENDESK_SUBDOMAIN="mycompany"
export ZENDESK_EMAIL="admin@example.com"
export ZENDESK_API_TOKEN="your_token"
export CUSTOMER_ORGANIZATION_ID="123456789"
export FETCH_FULL_HISTORY="true"

python zendesk_exporter.py
```

#### Mixed Mode

Set required credentials as environment variables, provide organization ID interactively:

```bash
export ZENDESK_SUBDOMAIN="mycompany"
export ZENDESK_EMAIL="admin@example.com"
export ZENDESK_API_TOKEN="your_token"

python zendesk_exporter.py
# Enter organization ID when prompted
# Choose whether to fetch full history when prompted
```

### Output Format

The script generates a JSON file with the following structure:

**Basic export (metadata only):**
```json
[
  {
    "id": 12345,
    "url": "https://mycompany.zendesk.com/api/v2/tickets/12345.json",
    "subject": "Customer inquiry",
    "description": "Initial ticket description",
    "status": "open",
    "priority": "normal",
    "type": "question",
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-01-16T14:20:00Z",
    "organization_id": 123456789,
    "requester_id": 987654321,
    "assignee_id": 111222333,
    "tags": ["customer", "inquiry"]
  }
]
```

**Full export (with event history):**
```json
[
  {
    "id": 12345,
    "subject": "Customer inquiry",
    "status": "open",
    "...": "... (all metadata fields)",
    "audits": [
      {
        "id": 67890,
        "ticket_id": 12345,
        "created_at": "2026-01-15T10:30:00Z",
        "author_id": 111222333,
        "events": [
          {
            "id": 98765,
            "type": "Create",
            "field_name": "status",
            "value": "new"
          },
          {
            "id": 98766,
            "type": "Change",
            "field_name": "status",
            "previous_value": "new",
            "value": "open"
          }
        ]
      }
    ],
    "comments": [
      {
        "id": 11111,
        "type": "Comment",
        "author_id": 987654321,
        "body": "Thank you for contacting support...",
        "html_body": "<p>Thank you for contacting support...</p>",
        "plain_body": "Thank you for contacting support...",
        "public": true,
        "created_at": "2026-01-15T10:35:00Z"
      }
    ]
  }
]
```

### Performance Considerations

- **Metadata only**: Fast, ~1-2 API calls per 100 tickets
- **Full history**: Slower, ~200 API calls per 100 tickets
  - 10 tickets: ~2-3 seconds
  - 100 tickets: ~20-30 seconds
  - 1,000 tickets: ~3-5 minutes

The script includes automatic rate limiting (0.1s delay between requests) to respect Zendesk API quotas.

### Troubleshooting

#### Authentication Errors

```
HTTP Error during Zendesk API request: 401 - Unauthorized
```

**Solution:** Verify your credentials:
- Check that `ZENDESK_EMAIL` is correct
- Ensure `ZENDESK_API_TOKEN` is valid (regenerate if needed)
- Confirm token access is enabled in Zendesk Admin settings

#### Invalid Organization ID

```
Invalid organization ID: abc123. Organization ID must be numeric.
```

**Solution:** Organization ID must be a number. Find it by:
1. Going to Zendesk Admin > Customers > Organizations
2. Clicking on the organization
3. The ID is in the URL: `https://mycompany.zendesk.com/agent/organizations/123456789`

#### Rate Limiting

```
HTTP Error during Zendesk API request: 429 - Too Many Requests
```

**Solution:** The script includes rate limiting, but if you still hit limits:
- Wait a few minutes before running again
- Consider exporting in smaller batches
- Contact Zendesk to increase your rate limit

#### Permission Errors

```
HTTP Error during Zendesk API request: 403 - Forbidden
```

**Solution:** Your API token doesn't have permission to access the requested resource:
- Verify the token has read access to tickets
- Check that your user account has permission to view the organization's tickets
- Contact your Zendesk admin to grant necessary permissions

### Security Best Practices

1. **Never commit API tokens to version control**
   - Add `.env` to `.gitignore`
   - Use environment variables or secure secret management

2. **Rotate tokens regularly**
   - Generate new tokens periodically
   - Revoke old tokens after updating

3. **Limit token permissions**
   - Use the minimum required permissions (read-only for exports)
   - Create separate tokens for different purposes

4. **Secure exported data**
   - Exported JSON files contain sensitive customer data
   - Store in secure locations with appropriate access controls
   - Delete after processing if no longer needed

### Finding Your Organization ID

**Method 1: Via Zendesk Admin UI**
1. Log in to Zendesk
2. Click **Admin** (gear icon)
3. Navigate to **Customers** > **Organizations**
4. Click on the organization you want to export
5. The URL will show the ID: `https://mycompany.zendesk.com/agent/organizations/123456789`

**Method 2: Via API**
```bash
curl -u your_email@example.com/token:your_api_token \
  https://mycompany.zendesk.com/api/v2/organizations.json
```

**Method 3: Search by name**
```bash
curl -u your_email@example.com/token:your_api_token \
  "https://mycompany.zendesk.com/api/v2/organizations/search.json?name=Organization%20Name"
```

### License

MIT License

### Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Zendesk API documentation: https://developer.zendesk.com/api-reference/
3. Open an issue in this repository
