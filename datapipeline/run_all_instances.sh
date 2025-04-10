#!/bin/bash
# Loop over worker indices 0 to 11
for i in {0..11}
do
    echo "Starting worker index $i out of 12."
    # Optionally, redirect each output to a separate log file:
    # python3 test_build_dataset.py -wi "$i" -ns 12 > "worker_$i.log" 2>&1 &
    
    # Launch the script concurrently without logging:
    python3 test_build_dataset.py -wi "$i" -ns 12 &
done

# Wait for all background processes to finish.
wait
echo "All worker instances have completed."
