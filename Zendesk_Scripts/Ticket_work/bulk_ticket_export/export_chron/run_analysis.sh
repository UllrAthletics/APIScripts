#!/bin/bash
# Quick test script - runs analysis without sending email
# Usage: ./run_analysis.sh [claude|gemini]

set -e  # Exit on error

cd /Users/hunter-morrison/git/APIScripts/Zendesk_Scripts/Ticket_work/bulk_ticket_export

# Load environment variables from shell config
if [ -f ~/.zshrc ]; then
    source ~/.zshrc
fi

# Default to Claude if no argument provided
LLM_CHOICE="${1:-claude}"

if [ "$LLM_CHOICE" != "claude" ] && [ "$LLM_CHOICE" != "gemini" ]; then
    echo "Usage: $0 [claude|gemini]"
    echo "Default: claude"
    exit 1
fi

echo "Running ticket analysis with $LLM_CHOICE (DRY RUN mode)..."
echo "============================================"

# Run with dry-run flag to preview without sending email
python3 ticket_analyzer.py --llm "$LLM_CHOICE" --dry-run

echo ""
echo "============================================"
echo "Dry run completed! No email was sent."
echo ""
echo "To send actual email, run:"
echo "  python3 ticket_analyzer.py --llm $LLM_CHOICE"
