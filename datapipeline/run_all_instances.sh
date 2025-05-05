#!/bin/bash

# ========== CONFIGURATION ==========
# Total number of worker tasks to run
total_workers=12

# Max concurrent workers (capped)
max_allowed=8
detected_cores=$(nproc)
max_concurrent=$(( detected_cores < max_allowed ? detected_cores : max_allowed ))

# Log file location (persisted outside Docker)
# log_dir="/app/logs"
log_dir="./logs"
mkdir -p "$log_dir"
log_file="$log_dir/worker_run.log"

# Telegram Bot
BOT_TOKEN="8087474387:AAEFYyAm1qLC2yKLBSt1ea9uLFtgl-9-RLs"
CHAT_ID="5815360770"

send_telegram() {
    message="$1"
    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
    -d chat_id="$CHAT_ID" \
    -d text="$message" > /dev/null
}

# ========== SCRIPT START ==========
echo "==== New Run: $(date) ====" >> "$log_file"
echo "Detected $detected_cores cores. Using max $max_concurrent concurrent workers." | tee -a "$log_file"

send_telegram "🔄 Worker job started at $(date)\nRunning $total_workers workers (max $max_concurrent concurrently)."

start_time=$(date +%s)
echo "Started at: $(date)" | tee -a "$log_file"

# ========== LAUNCH WORKERS ==========
for i in $(seq 0 $((total_workers - 1)))
do
    echo "[$(date)] Starting worker $i of $total_workers..." | tee -a "$log_file"
    # sleep 15
    python3 test_build_dataset.py -wi "$i" -ns "$total_workers" >> "$log_file" 2>&1 &

    if (( i % max_concurrent == max_concurrent - 1 )); then
        wait
    fi
done

# Final wait for any remaining
wait

end_time=$(date +%s)
duration=$(( end_time - start_time ))

echo "Finished at: $(date)" | tee -a "$log_file"
echo "Total duration: ${duration}s" | tee -a "$log_file"
echo "==== End Run ====" >> "$log_file"

send_telegram "✅ Worker job finished at $(date).\nDuration: ${duration}s."
# ========== END OF SCRIPT ==========