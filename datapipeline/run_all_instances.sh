#!/bin/bash
for i in {0..11}
do
    echo "Starting worker index $i out of 12."    
    # Launch the script concurrently without logging:
    python3 test_build_dataset.py -wi "$i" -ns 12 &
done

# Wait for all background processes to finish.
wait
echo "All worker instances have completed."
