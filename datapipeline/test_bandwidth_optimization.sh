#!/bin/bash

# Quick Test Script for Bandwidth Optimizations
# Run this to test the implementation with a small sample

set -e

echo "=========================================="
echo "BANDWIDTH OPTIMIZATION TEST"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "build_dataset.py" ]; then
    echo "ERROR: Please run this from the datapipeline directory"
    echo "cd /path/to/angle_backend/datapipeline"
    exit 1
fi

# Check virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "WARNING: No virtual environment detected"
    echo "Consider activating: source ../env/bin/activate"
    echo ""
fi

# Install new dependency
echo "1️⃣  Installing pandas-market-calendars..."
pip install pandas-market-calendars -q
echo "   ✓ Installed"
echo ""

# Create logs directory if needed
mkdir -p logs

# Run test with 5 samples
echo "2️⃣  Running test with 5 sample tickers..."
echo "   This will fetch FULL history (first run baseline)"
echo ""
python3 test_build_dataset.py -wi 0 -ns 1 -samples 5

echo ""
echo "=========================================="
echo "TEST COMPLETE!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Check logs/fmp_api_queries.log for bandwidth totals"
echo "2. Run the test again tomorrow to see incremental updates"
echo "3. Look for 'BANDWIDTH-OPT' messages in logs"
echo ""
echo "For production run:"
echo "  ./run_all_instances.sh"
echo ""
