#! /bin/bash

PATH=/home/ubuntu/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin

date >> /var/log/illumenti/crypto_descriptions_updater.log 2>&1

source /home/ubuntu/flaskenv/bin/activate

/home/ubuntu/flaskenv/bin/python /home/ubuntu/illumenti/scripts/crypto_descriptions_updater.py >> /var/log/illumenti/crypto_descriptions_updater.log 2>&1

