#!/bin/bash

set -euo pipefail

# ========== LOAD CONFIGURATION FROM .env ==========
# Expect a .env file in the parent directory with a line like:
ENV_FILE="$(dirname "$(realpath "${BASH_SOURCE[0]}")")/../.env"
if [[ -f "$ENV_FILE" ]]; then
  # Export KEY=VALUE lines, ignoring comments and blank lines
  export $(grep -v '^\s*#' "$ENV_FILE" | xargs)
else
  echo "ERROR: .env file not found at $ENV_FILE" >&2
  exit 1
fi

# Use TOTAL_WORKERS from .env, default to 12 if unset
total_workers=${TOTAL_WORKERS:-12}

# ========== DETERMINE CONCURRENCY ==========
max_allowed=4
detected_cores=$(nproc)
max_concurrent=$(( detected_cores < max_allowed ? detected_cores : max_allowed ))

# ========== PARSE "sample" MODE ==========
# Usage: ./run_all_instances.sh sample 10
sample_count=""
if [[ "${1-}" == "sample" && "${2-}" =~ ^[0-9]+$ ]]; then
  sample_count="$2"
  echo "→ SAMPLE MODE: limiting to $sample_count tickers per worker"
fi

# ========== LOGGING SETUP ==========
log_dir="./logs"
mkdir -p "$log_dir"
log_file="$log_dir/worker_run.log"

# ========== TELEGRAM NOTIFICATIONS ==========
send_telegram() {
  local message="$1"
  curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d chat_id="${CHAT_ID}" \
    -d text="$message" > /dev/null
}

# ========== SCRIPT START ==========
echo "==== New Run: $(date) ====" >> "$log_file"
echo "Detected $detected_cores cores; using up to $max_concurrent concurrent workers." | tee -a "$log_file"
echo "Total workers from .env: $total_workers" | tee -a "$log_file"
send_telegram "🔄 Worker job started at $(date)"
start_time=$(date +%s)

# ========== LAUNCH WORKERS ==========
for i in $(seq 0 $(( total_workers - 1 ))); do
  echo "[$(date)] Starting worker $i of $total_workers..." | tee -a "$log_file"

  if [[ -n "$sample_count" ]]; then
    python3 test_build_dataset.py \
      -wi "$i" \
      -ns "$total_workers" \
      -samples "$sample_count" \
      >> "$log_file" 2>&1 &
  else
    python3 test_build_dataset.py \
      -wi "$i" \
      -ns "$total_workers" \
      >> "$log_file" 2>&1 &
  fi

  # If we've launched a full batch, wait for them to finish
  if (( i % max_concurrent == max_concurrent - 1 )); then
    wait
  fi
done

# Final wait in case the last batch wasn't a full batch
wait

# ========== TEARDOWN ==========
end_time=$(date +%s)
duration=$(( end_time - start_time ))

echo "Finished at: $(date)" | tee -a "$log_file"
echo "Total duration: ${duration}s" | tee -a "$log_file"
echo "==== End Run ====" >> "$log_file"
send_telegram "✅ Worker job finished at $(date)\nDuration: ${duration}s."
