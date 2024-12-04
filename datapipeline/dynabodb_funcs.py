import json
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from decimal import Decimal
from datetime import datetime, timedelta


# Query client and list_tables to see if table exists or not
def create_db_table(db):
    table_name = 'Equity'
    # Get an array of table names associated with the current account and endpoint.
    tables = [ table for table in list(db.tables.all()) if table.name == table_name ]
    
    if tables:
        table = tables[0]
    else:
        print ("Creating DynamoDB table {} ..".format(table_name))

        # Create the DynamoDB table called Equity
        table = db.create_table(
            TableName = table_name,
            KeySchema =
            [
                {
                    'AttributeName': 'symbol',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'ds',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions =
            [
                {
                    'AttributeName': 'symbol',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'ds',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'exchange',
                    'AttributeType': 'S'
                },
            ],
            GlobalSecondaryIndexes =
            [{
                'IndexName': 'ExchangeDSIndex',
                'KeySchema': [
                    {
                        'AttributeName': 'exchange',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'ds',
                        'KeyType': 'RANGE'
                    }
                ],
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 1,
                    'WriteCapacityUnits': 1
                },
                'Projection': {
                    'ProjectionType': 'ALL'
                },
            }],
            ProvisionedThroughput =
            {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )

        # Wait until the table exists.
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)

    return table


def create_price_db_table(db):
    table_name = 'EquityPrice'
    # Get an array of table names associated with the current account and endpoint.
    tables = [ table for table in list(db.tables.all()) if table.name == table_name ]
   
    if tables:
        table = tables[0]
    else:
        print ("Creaing DynamoDB table {} ..".format(table_name))

        # Create the DynamoDB table called Equity
        table = db.create_table(
            TableName = table_name,
            KeySchema =
            [
                {
                    'AttributeName': 'symbol',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'ds',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions =
            [
                {
                    'AttributeName': 'symbol',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'ds',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'exchange',
                    'AttributeType': 'S'
                },
            ],
            GlobalSecondaryIndexes =
            [{
                'IndexName': 'ExchangeDSIndex',
                'KeySchema': [
                    {
                        'AttributeName': 'exchange',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'ds',
                        'KeyType': 'RANGE'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
            }],
            BillingMode='PAY_PER_REQUEST',
            
        )

        # Wait until the table exists.
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)

    return table


def write_equity_df_to_db(table, df, exchange):
    now = datetime.now()
    ds = now.strftime("%Y-%m-%d")
    try:
        with table.batch_writer() as writer:
            for index, row in df.iterrows():
                row_dict = row.to_dict()
                row_dict['ds'] = ds
                row_dict['exchange'] = exchange
                row_dict = { key:val for key,val in row_dict.items()\
                        if not key.startswith('Unnamed') }
                row_dict = json.loads(json.dumps(row_dict), parse_float=Decimal)
                writer.put_item(Item=row_dict)
        print ("Loaded data ({} {} records) into table {}.".format(index, exchange, table.name))
    except ClientError:
        print ("Couldn't load data into table {}.".format(table.name))


def remove_old_equity_records(table, retention_days, exchange):
    old_date = datetime.now() - timedelta(days=retention_days)
    ds = old_date.strftime("%Y-%m-%d")
    print ("{} - Starting remove_old_equity_records({}, {}, {})"\
            .format(datetime.now().strftime("%Y:%m:%d %H:%M:%S"),\
            table.name, retention_days, exchange))
    try:
        page = 1
        response = {}
        deleted_items_count = 0
        while page == 1 or 'LastEvaluatedKey' in response:
            if response.get('LastEvaluatedKey'):
                response = table.query(
                    IndexName='ExchangeDSIndex',
                    KeyConditionExpression=Key('ds').lt(ds) & Key('exchange').eq(exchange),
                    ExclusiveStartKey=response.get('LastEvaluatedKey')
                    )
            else:
                response = table.query(
                    IndexName='ExchangeDSIndex',
                    KeyConditionExpression=Key('ds').lt(ds) & Key('exchange').eq(exchange)
                    )

            equity_items = response.get('Items') if response.get('Items') else []

            print ("{} - Page-{}: found {} items"\
                    .format(datetime.now().strftime("%Y:%m:%d %H:%M:%S"),\
                    page, len(equity_items)))
            for item in equity_items:
                table.delete_item(
                        Key={'name': item.get('name'), 'ds': item.get('ds')})
                deleted_items_count += 1
            print ("{} - Deletion Performed".\
                    format(datetime.now().strftime("%Y:%m:%d %H:%M:%S")))
            page = page + 1
        print("{} - Deleted {} {} records from {}."\
            .format(datetime.now().strftime("%Y:%m:%d %H:%M:%S"),\
                deleted_items_count, exchange, table.name))
    except ClientError:
        print("Couldn't delete items from {}.".format(table.name))
        raise


def get_equity_price(table, symbol, ds):
    try:
        response = table.get_item(Key={'symbol': symbol, 'ds': ds})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response.get('Item') or {}


""" Crypto related functions """
def create_crypto_db_table(db):
    #  Create crypto DB table
    table_name = 'Crypto'
    # Get an array of table names associated with the current account and endpoint.
    tables = [ table for table in list(db.tables.all()) if table.name == table_name ]
    
    if tables:
        table = tables[0]
    else:
        print ("Creating Crypto DynamoDB table {} ..".format(table_name))

        # Create the DynamoDB table called Equity
        table = db.create_table(
            TableName = table_name,
            KeySchema =
            [
                {
                    'AttributeName': 'symbol',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'ds',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions =
            [
                {
                    'AttributeName': 'symbol',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'ds',
                    'AttributeType': 'S'
                },
            ],
            ProvisionedThroughput =
            {
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 11
            }
        )

        # Wait until the table exists.
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)

    return table

def create_crypto_price_db_table(db):
    # Create crypto price table
    table_name = 'CryptoPrice'
    # Get an array of table names associated with the current account and endpoint.
    tables = [ table for table in list(db.tables.all()) if table.name == table_name ]
   
    if tables:
        table = tables[0]
    else:
        print ("Creating DynamoDB table {} ..".format(table_name))

        # Create the DynamoDB table called Equity
        table = db.create_table(
            TableName = table_name,
            KeySchema =
            [
                {
                    'AttributeName': 'symbol',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'ds',
                    'KeyType': 'RANGE'
                }
            ],
            AttributeDefinitions =
            [
                {
                    'AttributeName': 'symbol',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'ds',
                    'AttributeType': 'S'
                },
            ],
            BillingMode='PAY_PER_REQUEST',
            
        )

        # Wait until the table exists.
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
    return table

def remove_old_crypto_records(table, retention_days, symbol):
    old_date = datetime.now() - timedelta(days=retention_days)
    ds = old_date.strftime("%Y-%m-%d")
    try:
        print('dd')
        response = table.query(
                IndexName='ExchangeDSIndex',
                KeyConditionExpression=Key('ds').lt(ds) & Key('exchange').eq(symbol))
        crypto_items = response.get('Items') if response.get('Items') else []

        with table.batch_writer() as writer:
            for item in crypto_items:
                writer.delete_item(
                    Key={'name': item.get('name'), 'ds': item.get('ds')})
        print("Deleted {} {} records from {}.".format(len(crypto_items), symbol, table.name))
    except ClientError:
        print("Couldn't delete items from {}.".format(table.name))
        raise
