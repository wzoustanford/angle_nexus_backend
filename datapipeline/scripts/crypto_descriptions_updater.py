import os
import re
import json
import time
import boto3
import requests
import itertools
import pandas as pd
from decimal import Decimal
from datetime import datetime
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import And, Attr, Key
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

dynamodb = boto3.resource('dynamodb')
crypto_table = dynamodb.Table('Crypto')
crypto_data = []

DB_MAX_TRIES = 3
DB_RETRY_DELAY = 0.5


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)
        
def fetch_data(table, ds, exchange=None):

    if table.name == 'Equity':
        key_expr = Key('ds').eq(ds) & Key('exchange').eq(exchange)
        proj_expr = 'symbol, volume__quote, volavg__profile, key_metrics'
        idx_name = 'ExchangeDSIndex'
    elif table.name == 'Crypto':
        key_expr = Key('ds').eq(ds)
        proj_expr = 'symbol, description, id'
        idx_name = 'ds-index'
        
    response = table.query(KeyConditionExpression=key_expr,
            ProjectionExpression=proj_expr, IndexName=idx_name)
    data = response['Items']
    page = 0
    while 'LastEvaluatedKey' in response:
        response = table.query(ExclusiveStartKey=response.get('LastEvaluatedKey'),
                KeyConditionExpression=key_expr,
                ProjectionExpression=proj_expr, IndexName=idx_name)
        data.extend(response['Items'])
        page=page+1
        # (datetime.now(), page, len(data))

    return data

def update_description(table, symbol, ds, data):
    """ Save benchmark values to dynamodb table """ 
    tries = 0 
    while tries < DB_MAX_TRIES:
        try:
            tries += 1
            time.sleep(0.3)
            print (symbol, data[:50])
            r = table.update_item(Key={'symbol': symbol, 'ds': ds},
                    UpdateExpression="set description=:b",
                    ExpressionAttributeValues={':b': data},
                    ReturnValues="UPDATED_NEW")
            print ('{} - update_description() - {} {}'.format(datetime.now(), table.name, symbol))
            if 'description' in r.get('Attributes').keys():
                break
            else:
                print ('Try-{} - description not found in UPDATED_NEW'.format(tries))
        except ClientError as error:
            print ('Database update-item({}, {}) failure-{} for data:'\
                    .format(symbol, ds, tries))
            print (error)
            time.sleep(DB_RETRY_DELAY)


def update_latest_ds(table):
    """ Update crypto price-chart data to dynamodb table """ 
    now = datetime.now()
    latest_ds = now.strftime("%Y-%m-%d")
    dummy_ds = '2111-11-11'
    dummy_symbol = 'dummy_latestds_ticker'

    tries = 0 
    while tries < DB_MAX_TRIES:
        try:
            tries += 1
            time.sleep(0.3)

            r = table.update_item(Key={'symbol': dummy_symbol, 'ds': dummy_ds},
                    UpdateExpression="set latest_ds=:l",
                    ExpressionAttributeValues={':l': latest_ds},
                    ReturnValues="UPDATED_NEW")
            print ('{} - update_latest_ds() - {} {}'.format(now, table.name, latest_ds))
            break
        except ClientError as error:
            print ('Database update-item({}, {}) failure-{} for data:'\
                    .format(dummy_symbol, latest_ds, tries))
            print (error)
            #print (error.response['Error']['Code'], error.response['Error']['Message'])
            time.sleep(DB_RETRY_DELAY)


def main():

    now = datetime.now()
    latest_ds = now.strftime("%Y-%m-%d")

    print ('{} - Started'.format(time.strftime("%Y-%m-%d %H:%M:%S")))

    r = requests.get('https://api.coingecko.com/api/v3/coins/list')
    rj = r.json()
    print ('{} - Completed fetching Crypto coins list ({} results)'\
            .format(time.strftime("%Y-%m-%d %H:%M:%S"), len(rj)))

    crypto_data.extend(fetch_data(crypto_table, latest_ds))
    print ('{} - Completed fetching Crypto data from the database'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
    
    crypto_df = pd.DataFrame(crypto_data)
    crypto_df = crypto_df.set_index('symbol')
    
    print ('=' * 80)
    print ('{} - Starting updating descriptions for Crypto'\
            .format(time.strftime("%Y-%m-%d %H:%M:%S")))
    
    i = 0
    errs = 0
    CLEANR = re.compile('<.*?>')
    for idx, row in crypto_df.iterrows():
        for coin in rj:
            if idx.lower() == coin.get('symbol'):
                url = 'https://api.coingecko.com/api/v3/coins/{}'\
                        .format(coin.get('id').lower())
                r = requests.get(url)
                try:
                    descr = r.json().get('description').get('en')
                    print(i, coin, url, len(descr))
                except Exception as e:
                    descr = ''
                    print(i, coin, url)
                    print(e)
                    errs = errs + 1
                if len(descr) > 50:
                    i = i + 1
                    #descr = descr.replace('<a href="','').replace('">',' - ').replace('</a>','')
                    descr = re.sub(CLEANR, '', descr)
                    update_description(crypto_table, idx, latest_ds, descr)
                    time.sleep(0.95)

    print ('-' * 80)
    print ('{} - Completed updating descriptions for {} Crypto items. Total errors: {}'\
            .format(time.strftime("%Y-%m-%d %H:%M:%S"), i, errs))

    return {
        'statusCode': 200,
        'body': json.dumps('Updated descriptions for {} Crypto items'.\
            format(i))
    }


if __name__ == "__main__":
    main()
