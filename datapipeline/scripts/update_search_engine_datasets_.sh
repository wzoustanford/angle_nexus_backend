#!/bin/bash

# Dynamically set the base directory to the location of the script
BASE_DIR=$(dirname $(dirname $(realpath "$0")))

# Define paths relative to the base directory
DATA_PIPELINE_DIR="$BASE_DIR/datapipeline"
DATA_DIR="$BASE_DIR/../data"
OUT_DIR="$DATA_DIR/out"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/aws_script.log"

# Ensure the log directory exists
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    chmod 755 "$LOG_DIR"
fi

echo "Script started at: $(date)" >> $LOG_FILE

# Debug: Log directory structure
echo "Base Directory: $BASE_DIR" >> $LOG_FILE
echo "Data Directory: $DATA_DIR" >> $LOG_FILE
echo "Output Directory: $OUT_DIR" >> $LOG_FILE
echo "Files in Data Directory: $(ls $DATA_DIR 2>/dev/null)" >> $LOG_FILE

# Ensure output directory exists
mkdir -p $OUT_DIR

# Consolidate Equity Datasets (NYSE and NASDAQ)
echo "Consolidating equity datasets..." >> $LOG_FILE

# Create headers for combined NYSE and NASDAQ files
head -1 $DATA_DIR/nyse_exported_table_equity_2.csv > $OUT_DIR/equity_nyse_exported_table.csv 2>> $LOG_FILE
head -1 $DATA_DIR/nasdaq_exported_table_equity_2.csv > $OUT_DIR/equity_nasdaq_exported_table.csv 2>> $LOG_FILE

# Standardize column names
sed -e 's/symbol/Symbol/g' -e 's/name/Name/g' $OUT_DIR/equity_nyse_exported_table.csv > $OUT_DIR/equity_nyse_exported_table_temp.csv && mv $OUT_DIR/equity_nyse_exported_table_temp.csv $OUT_DIR/equity_nyse_exported_table.csv
sed -e 's/symbol/Symbol/g' -e 's/name/Name/g' $OUT_DIR/equity_nasdaq_exported_table.csv > $OUT_DIR/equity_nasdaq_exported_table_temp.csv && mv $OUT_DIR/equity_nasdaq_exported_table_temp.csv $OUT_DIR/equity_nasdaq_exported_table.csv

# Append data from all NYSE and NASDAQ files
for FILE in $DATA_DIR/nyse_exported_table_equity_*.csv; do
    tail -n +2 $FILE >> $OUT_DIR/equity_nyse_exported_table.csv 2>> $LOG_FILE
done

for FILE in $DATA_DIR/nasdaq_exported_table_equity_*.csv; do
    tail -n +2 $FILE >> $OUT_DIR/equity_nasdaq_exported_table.csv 2>> $LOG_FILE
done

# Copy consolidated datasets to the data directory, replacing existing files
echo "Copying consolidated datasets to the data directory..." >> $LOG_FILE

cp -f $DATA_DIR/equity_nyse_exported_table.csv $DATA_DIR/equity_nyse_exported_table.csv 2>> $LOG_FILE
cp -f $DATA_DIR/equity_nasdaq_exported_table.csv $DATA_DIR/equity_nasdaq_exported_table.csv 2>> $LOG_FILE

echo "Consolidated datasets copied successfully." >> $LOG_FILE

# Copy crypto dataset (if exists)
if [ -f "$DATA_DIR/crypto_info_table.csv" ]; then
    cp $DATA_DIR/crypto_info_table.csv $DATA_DIR/crypto_info_table_full.csv
else
    echo "crypto_info_table.csv not found." >> $LOG_FILE
fi

# Clean up intermediate files (optional)
echo "Cleaning up intermediate files..." >> $LOG_FILE
# rm -f $DATA_DIR/*_equity_*.csv 2>> $LOG_FILE

# Restart application (placeholder for actual command)
echo "Restarting application..." >> $LOG_FILE
python3 $DATA_PIPELINE_DIR/scripts/restart_backend.py >> $LOG_FILE 2>&1

echo "Script completed at: $(date)" >> $LOG_FILE
echo '--------------------------------------------' >> $LOG_FILE