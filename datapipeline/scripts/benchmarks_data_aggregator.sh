#! /bin/bash

PATH=/home/ubuntu/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin

date >> /var/log/illumenti/benchmarks_data_aggregator.log 2>&1

source /home/ubuntu/flaskenv/bin/activate

/home/ubuntu/flaskenv/bin/python /home/ubuntu/illumenti/scripts/benchmarks_data_aggregator.py >> /var/log/illumenti/benchmarks_data_aggregator.log 2>&1

