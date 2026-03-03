#!/usr/bin/env python3
"""
Simple script to export all end users from Zendesk
"""

import requests
import csv
import os

# Zendesk Configuration
ZENDESK_SUBDOMAIN = os.getenv('ZENDESK_SUBDOMAIN', 'your-subdomain')
ZENDESK_EMAIL = os.getenv('ZENDESK_EMAIL', 'your-email@example.com')
ZENDESK_API_TOKEN = os.getenv('ZENDESK_API_TOKEN', 'your-api-token')

# API endpoint
BASE_URL = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com"
ENDPOINT = "/api/v2/users.json?role=end-user"

def get_organization(org_id):
    """Fetch organization details including custom fields"""
    if not org_id:
        return {}

    url = f"{BASE_URL}/api/v2/organizations/{org_id}.json"
    response = requests.get(
        url,
        auth=(f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
    )

    if response.status_code == 200:
        return response.json().get('organization', {})
    else:
        print(f"Warning: Could not fetch organization {org_id}: {response.status_code}")
        return {}

def export_end_users():
    """Export all end users from Zendesk with organization custom fields"""
    all_users = []
    url = BASE_URL + ENDPOINT

    print("Fetching end users from Zendesk...")

    while url:
        # Make API request
        response = requests.get(
            url,
            auth=(f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN)
        )

        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break

        data = response.json()
        users = data.get('users', [])
        all_users.extend(users)

        print(f"Fetched {len(users)} users... (Total: {len(all_users)})")

        # Get next page URL (Zendesk uses cursor-based pagination)
        url = data.get('next_page')

    # Enrich users with organization data including custom fields
    print("\nEnriching users with organization data...")
    org_cache = {}  # Cache organizations to avoid duplicate API calls

    for user in all_users:
        org_id = user.get('organization_id')
        if org_id:
            # Use cached org data if available
            if org_id not in org_cache:
                org_cache[org_id] = get_organization(org_id)

            org = org_cache[org_id]
            if org:
                # Add organization name
                user['org_name'] = org.get('name', '')

                # Add custom organization fields
                org_fields = org.get('organization_fields', {})
                for field_key, field_value in org_fields.items():
                    user[f'org_field_{field_key}'] = field_value

    print(f"Fetched data for {len(org_cache)} unique organizations")

    # Save to CSV file
    output_file = "zendesk_end_users.csv"

    if all_users:
        # Extract all unique keys from all users
        fieldnames = set()
        for user in all_users:
            fieldnames.update(user.keys())
        fieldnames = sorted(fieldnames)

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_users)

        print(f"\n✓ Successfully exported {len(all_users)} end users to {output_file}")
    else:
        print("\n! No users found to export")

if __name__ == "__main__":
    # Validate configuration
    if ZENDESK_SUBDOMAIN == 'your-subdomain' or ZENDESK_EMAIL == 'your-email@example.com':
        print("Please set your Zendesk credentials:")
        print("  export ZENDESK_SUBDOMAIN='your-subdomain'")
        print("  export ZENDESK_EMAIL='your-email@example.com'")
        print("  export ZENDESK_API_TOKEN='your-api-token'")
        exit(1)

    export_end_users()
