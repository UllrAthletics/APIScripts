#!/bin/bash
# Quick test script - runs analysis without sending email
# Usage: ./run_analysis.sh [P1|P1,P2|etc]

set -e  # Exit on error

# Auto-detect script directory (works on any machine)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables from shell config
if [ -f ~/.zshrc ]; then
    source ~/.zshrc
fi

# Get priorities from first argument
PRIORITIES="${1:-}"

echo "Running ticket analysis with Gemini AI (DRY RUN mode)..."
if [ -n "$PRIORITIES" ]; then
    echo "Filtering for priorities: $PRIORITIES"
else
    echo "Analyzing all ticket priorities"
fi
echo "============================================"

# Build command with optional priorities filter
CMD="python3 ticket_analyzer.py --dry-run"
if [ -n "$PRIORITIES" ]; then
    CMD="$CMD --priorities $PRIORITIES"
fi

# Run with dry-run flag to preview without sending email
eval $CMD

echo ""
echo "============================================"
echo "Dry run completed! No email was sent."
echo ""
echo "To send actual email, run:"
if [ -n "$PRIORITIES" ]; then
    echo "  python3 ticket_analyzer.py --priorities $PRIORITIES"
else
    echo "  python3 ticket_analyzer.py"
fi
