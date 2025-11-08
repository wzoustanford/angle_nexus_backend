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

# #!/bin/bash

# echo "------ Script started at $(date) ------"

# cd /home/ubuntu/angle_backend || exit 1
# echo "Changed to project root"

# # Activate virtualenv
# source env/bin/activate
# echo "Virtual environment activated"

# # Load .env variables
# export $(cat .env | xargs)
# echo ".env loaded"

# cd datapipeline || exit 1
# echo "Changed to datapipeline dir"

# # Start workers and log each individually
# for i in {0..11}
# do
#     echo "Starting worker index $i at $(date)..."
#     python test_build_dataset.py -wi "$i" -ns 12 >> worker_$i.log 2>&1 &
    
#     # Wait every 2 workers
#     if (( (i+1) % 2 == 0 )); then
#         echo "Waiting for batch to finish..."
#         wait
#     fi
# done

# wait
# echo "------ Script finished at $(date) ------"