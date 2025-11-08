#!/bin/bash

set -euo pipefail

# ========== LOAD CONFIGURATION FROM .env ==========
ENV_FILE="$(cd "$(dirname "$0")" && cd .. && pwd)/.env"
if [ -f "$ENV_FILE" ]; then
  set -a
  source "$ENV_FILE"
  set +a
else
  echo "ERROR: .env file not found at $ENV_FILE" >&2
  exit 1
fi

# Default to 12 workers if not set
total_workers=${TOTAL_WORKERS:-12}
if ! echo "$total_workers" | grep -Eq '^[1-9][0-9]*$'; then
  echo "ERROR: TOTAL_WORKERS must be a positive integer, got: $total_workers" >&2
  exit 1
fi

# Use system-independent method for CPU detection
if command -v getconf >/dev/null 2>&1; then
  detected_cores=$(getconf _NPROCESSORS_ONLN || echo 4)
else
  detected_cores=4
fi

max_allowed=4
if [ "$detected_cores" -lt "$max_allowed" ]; then
  max_concurrent=$detected_cores
else
  max_concurrent=$max_allowed
fi

# SAMPLE MODE
sample_count=""
per_worker_samples=""
if [ "${1:-}" = "sample" ]; then
  if ! echo "${2:-}" | grep -Eq '^[0-9]+$'; then
    echo "ERROR: sample mode requires a number. Usage: $0 sample <number>" >&2
    exit 1
  fi
  sample_count="$2"
  per_worker_samples=$(( (sample_count + total_workers - 1) / total_workers ))
  echo "→ SAMPLE MODE: limiting to $sample_count total tickers across $total_workers workers (≈ $per_worker_samples each)"
fi

# LOGGING
log_dir="./logs"
mkdir -p "$log_dir"
timestamp=$(date '+%Y%m%d_%H%M%S')
log_file="$log_dir/worker_run_${timestamp}.log"

# TELEGRAM
send_telegram() {
  local message="$1"
  if [ -n "${BOT_TOKEN:-}" ] && [ -n "${CHAT_ID:-}" ]; then
    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
      -d chat_id="${CHAT_ID}" -d text="$message" > /dev/null || \
    echo "Warning: Telegram send failed" >&2
  fi
}

# CLEANUP
cleanup() {
  echo "Cleaning up..." >&2
  jobs -p | xargs -r kill 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# START
send_telegram "🔄 Starting $total_workers workers at $(date)"
echo "==== Starting at $(date) ====" | tee "$log_file"
echo "Detected $detected_cores cores; using up to $max_concurrent workers." | tee -a "$log_file"
echo "Total workers: $total_workers" | tee -a "$log_file"

if [ ! -f "test_build_dataset.py" ]; then
  echo "ERROR: test_build_dataset.py not found." >&2
  exit 1
fi

start_time=$(date +%s)
declare -a job_pids=()

# WORKERS
for i in $(seq 0 $((total_workers - 1))); do
  echo "[$(date)] Launching worker $i..." | tee -a "$log_file"
  worker_log="$log_dir/worker_${i}_${timestamp}.log"

  cmd=(python3 test_build_dataset.py -wi "$i" -ns "$total_workers")
  if [ -n "$per_worker_samples" ]; then
    cmd+=( -samples "$per_worker_samples" )
  fi
  "${cmd[@]}" > "$worker_log" 2>&1 &
  job_pids+=("$!")

  if [ $(((i + 1) % max_concurrent)) -eq 0 ]; then
    wait
    job_pids=()
  fi

  echo "Worker $i started, logging to $worker_log" | tee -a "$log_file"
done

# Final wait
wait

# CHECK
failed=0
for i in $(seq 0 $((total_workers - 1))); do
  worker_log="$log_dir/worker_${i}_${timestamp}.log"
  if grep -qiE 'error|exception|traceback' "$worker_log"; then
    echo "Worker $i failed. Check $worker_log" | tee -a "$log_file"
    ((failed++))
  fi
  echo "=== Log: Worker $i ===" >> "$log_file"
  cat "$worker_log" >> "$log_file"
  echo "=== End ===" >> "$log_file"
done

end_time=$(date +%s)
duration=$((end_time - start_time))
duration_fmt=$(printf '%02d:%02d:%02d' $((duration/3600)) $((duration%3600/60)) $((duration%60)))

# END
if [ "$failed" -eq 0 ]; then
  send_telegram "✅ All $total_workers workers completed. Time: $duration_fmt"
else
  send_telegram "⚠️ $failed/$total_workers workers failed. Time: $duration_fmt"
fi

echo "Done in $duration_fmt" | tee -a "$log_file"
exit $failed
