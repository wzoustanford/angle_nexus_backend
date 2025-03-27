import os
import json
import time
import boto3
import itertools
import pandas as pd
from decimal import Decimal
from datetime import datetime
#from numerize import numerize
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import And, Attr, Key
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

dynamodb = boto3.resource('dynamodb')
equity_table = dynamodb.Table('Equity')
crypto_table = dynamodb.Table('Crypto')
exchanges = ('nyse', 'nasdaq')
DUMMY_SYMBOL = 'dummy_benchmarks_ticker'
equity_data = []
crypto_data = []
equity_benchmarks = { 'volume': {}, 'Debt ratio': {}, 'PE ratio': {}}
crypto_benchmarks = { 'buy_percentage': {}, 'sell_percentage': {},\
                      'transaction_frequency': {}, 'volume': {}}

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
        proj_expr = 'symbol, transaction_frequency, buy_percentage, sell_percentage, volume_24h'
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

def update_benchmarks(table, symbol, ds, data):
    """ Save benchmark values to dynamodb table """ 
    tries = 0 
    while tries < DB_MAX_TRIES:
        try:
            tries += 1
            time.sleep(0.3)
            print (symbol, data)
            r = table.update_item(Key={'symbol': symbol, 'ds': ds},
                    UpdateExpression="set benchmarks=:b",
                    ExpressionAttributeValues={':b': data},
                    ReturnValues="UPDATED_NEW")
            print ('{} - update_benchmarks() - {} {}'.format(datetime.now(), table.name, symbol))
            if 'benchmarks' in r.get('Attributes').keys():
                break
            else:
                print ('Try-{} - benchmarks not found in UPDATED_NEW'.format(tries))
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

    for exchange in exchanges:
        equity_data.extend(fetch_data(equity_table, latest_ds, exchange))
    print ('{} - Completed fetching Equity data'.format(time.strftime("%Y-%m-%d %H:%M:%S")))

    crypto_data.extend(fetch_data(crypto_table, latest_ds))
    print ('{} - Completed fetching Crypto data'.format(time.strftime("%Y-%m-%d %H:%M:%S")))
    
    for row in equity_data:
        pe_ratio = [ km.get('value') for km in row['key_metrics'] if km.get('tag')=="PE ratio"][0]
        debt_ratio = [ km.get('value') for km in row['key_metrics'] if km.get('tag')=="Debt ratio"][0]
        row['pe_ratio'] = pe_ratio if type(pe_ratio)!=type('') else None
        row['debt_ratio'] = debt_ratio if type(debt_ratio)!=type('') else None
        
    for row in crypto_data:
        if type(row.get('buy_percentage')) == type(''):
            row['buy_percentage_copy'] = None
        else:
            row['buy_percentage_copy'] = row.get('buy_percentage')
        if type(row.get('sell_percentage')) == type(''):
            row['sell_percentage_copy'] = None
        else:
            row['sell_percentage_copy'] = row.get('sell_percentage')
        if type(row.get('transaction_frequency')) == type(''):
            row['transaction_frequency_copy'] = None
        else:
            row['transaction_frequency_copy'] = row.get('transaction_frequency')
    
    equity_df = pd.DataFrame(equity_data)
    equity_df = equity_df.set_index('symbol')
    crypto_df = pd.DataFrame(crypto_data)
    crypto_df = crypto_df.set_index('symbol')
    
    equity_benchmarks['volume']['min'] = equity_df['volume__quote'].min()
    equity_benchmarks['volume']['max'] = equity_df['volume__quote'].max()
    equity_benchmarks['volume']['median'] = Decimal(str(equity_df['volume__quote'].median()))
    equity_benchmarks['Debt ratio']['min'] = equity_df['debt_ratio'].min()
    equity_benchmarks['Debt ratio']['max'] = equity_df['debt_ratio'].max()
    equity_benchmarks['Debt ratio']['median'] = Decimal(str(equity_df['debt_ratio'].median()))
    equity_benchmarks['PE ratio']['min'] = equity_df['pe_ratio'].min()
    equity_benchmarks['PE ratio']['max'] = equity_df['pe_ratio'].max()
    equity_benchmarks['PE ratio']['median'] = Decimal(str(equity_df['pe_ratio'].median()))
    
    crypto_benchmarks['volume']['min'] = crypto_df['volume_24h'].min()
    crypto_benchmarks['volume']['max'] = crypto_df['volume_24h'].max()
    crypto_benchmarks['volume']['median'] = Decimal(str(crypto_df['volume_24h'].median()))
    crypto_benchmarks['buy_percentage']['min'] = crypto_df['buy_percentage_copy'].min()
    crypto_benchmarks['buy_percentage']['max'] = crypto_df['buy_percentage_copy'].max()
    crypto_benchmarks['buy_percentage']['median'] = Decimal(str(crypto_df['buy_percentage_copy'].median()))
    crypto_benchmarks['sell_percentage']['min'] = crypto_df['sell_percentage_copy'].min()
    crypto_benchmarks['sell_percentage']['max'] = crypto_df['sell_percentage_copy'].max()
    crypto_benchmarks['sell_percentage']['median'] = Decimal(str(crypto_df['sell_percentage_copy'].median()))
    crypto_benchmarks['transaction_frequency']['min'] = crypto_df['transaction_frequency_copy'].min()
    crypto_benchmarks['transaction_frequency']['max'] = crypto_df['transaction_frequency_copy'].max()
    crypto_benchmarks['transaction_frequency']['median'] = Decimal(str(crypto_df['transaction_frequency_copy'].median()))

    print ('=' * 80)
    print (equity_benchmarks)
    print (crypto_benchmarks)
    print ('=' * 80)
    print ('{} - Starting updating benchmarks for Equity'\
            .format(time.strftime("%Y-%m-%d %H:%M:%S")))
    i = 0
    for idx, row in equity_df.iterrows():
        #print (idx, row)
        benchmark = [
        {
          "key": "PE ratio",
          "entity_value": row['pe_ratio'] or '__nan__',
          "start_value": equity_benchmarks['PE ratio']['min'],
          "total": equity_benchmarks['PE ratio']['max'],
          "typical_value": equity_benchmarks['PE ratio']['median'],
          "type": ""
        },
        {
          "key": "Debt ratio",
          "entity_value": row['debt_ratio'] or '__nan__',
          "start_value": equity_benchmarks['Debt ratio']['min'],
          "total": equity_benchmarks['Debt ratio']['max'],
          "typical_value": equity_benchmarks['Debt ratio']['median'],
          "type": "%"
        },
        {
          "key": "Daily Volume",
          "entity_value": row['volume__quote'] or '__nan__',
          "start_value": equity_benchmarks['volume']['min'],
          "total": equity_benchmarks['volume']['max'],
          "typical_value": equity_benchmarks['volume']['median'],
          "type": ""
        }]
            
        #print (idx, benchmark)
        update_benchmarks(equity_table, idx, latest_ds, benchmark)
        i = i + 1
        #if i > 100:
        #    break
        
    print ('.......................................................')
    print ('{} - Starting updating benchmarks for Crypto'\
            .format(time.strftime("%Y-%m-%d %H:%M:%S")))
    
    i = 0
    for idx, row in crypto_df.iterrows():
        #print (idx, row)
        benchmark = [
        {
          "key": "Transaction Frequency",
          "entity_value": row['transaction_frequency_copy'] or '__nan__',
          "start_value": crypto_benchmarks['transaction_frequency']['min'],
          "total": crypto_benchmarks['transaction_frequency']['max'],
          "typical_value": crypto_benchmarks['transaction_frequency']['median'],
          "type": ""
        },
        {
          "key": "Buy Percentage",
          "entity_value": row['buy_percentage_copy'] or '__nan__',
          "start_value": crypto_benchmarks['buy_percentage']['min'],
          "total": crypto_benchmarks['buy_percentage']['max'],
          "typical_value": crypto_benchmarks['buy_percentage']['median'],
          "type": "%"
        },
        {
          "key": "Sell Percentage",
          "entity_value": row['sell_percentage_copy'] or '__nan__',
          "start_value": crypto_benchmarks['sell_percentage']['min'],
          "total": crypto_benchmarks['sell_percentage']['max'],
          "typical_value": crypto_benchmarks['sell_percentage']['median'],
          "type": "%"
        },        
        {
          "key": "Daily Volume",
          "entity_value": row['volume_24h'] or '__nan__',
          "start_value": crypto_benchmarks['volume']['min'],
          "total": crypto_benchmarks['volume']['max'],
          "typical_value": crypto_benchmarks['volume']['median'],
          "type": ""
        }]
        update_benchmarks(crypto_table, idx, latest_ds, benchmark)

    update_latest_ds(equity_table)
    dummy_symbol = 'dummy_benchmarks_ticker'
    #update_benchmarks(equity_table, dummy_symbol, latest_ds, equity_benchmarks)
    #update_benchmarks(crypto_table, dummy_symbol, latest_ds, crypto_benchmarks)
    
    results = { 'equity_benchmarks': equity_benchmarks,\
                'crypto_benchmarks': crypto_benchmarks }
    
    return {
        'statusCode': 200,
        'body': json.dumps('Equity records: {}, Crypto records: {}'.\
            format(len(equity_data), len(crypto_data)))
    }


if __name__ == "__main__":
    main()
