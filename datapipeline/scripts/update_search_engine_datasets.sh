#! /bin/bash

PATH=/home/ubuntu/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin

date >> /var/log/illumenti/aws_script.log 2>&1

aws s3 cp s3://illumenti-backend-datapipeline/datapipeline/output/ /home/ubuntu/data/ --recursive --include "*_equity_*csv"
aws s3 cp s3://illumenti-backend-datapipeline/datapipeline/output/crypto_info_table.csv /home/ubuntu/data/

head -1 /home/ubuntu/data/nyse_exported_table_equity_0.csv > /home/ubuntu/data/out/equity_nyse_exported_table.csv
head -1 /home/ubuntu/data/nasdaq_exported_table_equity_0.csv > /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
sed -i 's/symbol/Symbol/g' /home/ubuntu/data/out/equity_nyse_exported_table.csv
sed -i 's/name/Name/g' /home/ubuntu/data/out/equity_nyse_exported_table.csv
sed -i 's/symbol/Symbol/g' /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
sed -i 's/name/Name/g' /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_0.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_0.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_1.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_1.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_2.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_2.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_3.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_3.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_4.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_4.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_5.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_5.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_6.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_6.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_7.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_7.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_8.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_8.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_9.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_9.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_10.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_10.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_11.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_11.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_12.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_12.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_13.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_13.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv
tail +2 /home/ubuntu/data/nyse_exported_table_equity_14.csv >> /home/ubuntu/data/out/equity_nyse_exported_table.csv
tail +2 /home/ubuntu/data/nasdaq_exported_table_equity_14.csv >> /home/ubuntu/data/out/equity_nasdaq_exported_table.csv

cp /home/ubuntu/data/out/equity_nyse_exported_table.csv /home/ubuntu/illumenti/backend/data/
cp /home/ubuntu/data/out/equity_nasdaq_exported_table.csv /home/ubuntu/illumenti/backend/data/
cp /home/ubuntu/data/crypto_info_table.csv /home/ubuntu/illumenti/backend/data/crypto_info_table_full.csv

rm /home/ubuntu/data/*csv

cd /home/ubuntu/illumenti
docker-compose up -d --build >> /var/log/illumenti/aws_script.log 2>&1

sleep 5

curl http://54.237.76.59/ >> /var/log/illumenti/aws_script.log 2>&1

date >> /var/log/illumenti/aws_script.log 2>&1
echo '--------------------------------------------' >> /var/log/illumenti/aws_script.log 2>&1



