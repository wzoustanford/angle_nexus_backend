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


""" Bandwidth Optimization Functions - Added 2026-03-23 """

def get_latest_price_date(table, ticker):
    """
    Query EquityPrice table for the most recent date with price data.
    Returns datetime object of most recent date, or None if no data exists.
    
    This function enables incremental price fetching to reduce bandwidth.
    """
    try:
        response = table.query(
            KeyConditionExpression=Key('symbol').eq(ticker),
            ScanIndexForward=False,  # Descending order by ds (date)
            Limit=1,
            ProjectionExpression='ds'
        )
        if response.get('Items'):
            last_ds = response['Items'][0]['ds']
            return datetime.strptime(last_ds, '%Y-%m-%d')
    except ClientError as e:
        print(f"Error querying latest price for {ticker}: {e.response['Error']['Message']}")
    except Exception as e:
        print(f"Unexpected error getting latest price date for {ticker}: {e}")
    
    return None


def is_trading_day(date=None):
    """
    Check if a given date (or today) is a US stock market trading day.
    Uses pandas_market_calendars to check NYSE calendar.
    
    Returns True if trading day, False otherwise.
    Fallback to weekday check if pandas_market_calendars not available.
    """
    date = date or datetime.now()
    
    try:
        import pandas_market_calendars as mcal
        nyse = mcal.get_calendar('NYSE')
        schedule = nyse.schedule(start_date=date, end_date=date)
        return not schedule.empty
    except ImportError:
        # Fallback: simple weekday check (Monday=0, Sunday=6)
        print("Warning: pandas_market_calendars not installed. Using simple weekday check.")
        print("Install with: pip install pandas_market_calendars")
        return date.weekday() < 5  # Monday-Friday
    except Exception as e:
        print(f"Error checking trading day: {e}. Assuming it's a trading day.")
        return True  # Fail safe - continue processing


def should_refetch_category(table, ticker, category, current_ds):
    """
    Determine if a data category should be re-fetched based on smart caching rules.
    
    Categories are classified as:
    - STATIC: Profile data (CEO, logo, industry) - refetch monthly
    - QUARTERLY: Financial statements - refetch weekly to catch quarterly updates
    - DAILY: Quote data (price, volume) - refetch daily
    
    Args:
        table: DynamoDB Equity table reference
        ticker: Stock symbol
        category: API category name (e.g., 'profile', 'income-statement', 'quote')
        current_ds: Current date string (YYYY-MM-DD)
    
    Returns:
        Boolean indicating whether to refetch this category
    """
    STATIC_CATEGORIES = ['profile']  # Refetch monthly
    QUARTERLY_CATEGORIES = [
        'income-statement', 
        'balance-sheet-statement',
        'cash-flow-statement', 
        'income-statement-growth',
        'historical-price-full/stock_dividend'
    ]
    DAILY_CATEGORIES = ['quote']
    
    try:
        # Get the last fetched record for this ticker
        response = table.query(
            KeyConditionExpression=Key('symbol').eq(ticker),
            ScanIndexForward=False,  # Descending order
            Limit=1,
            ProjectionExpression='ds,data_freshness'
        )
        
        if not response.get('Items'):
            return True  # No previous data - fetch everything
        
        item = response['Items'][0]
        data_freshness = item.get('data_freshness', {})
        last_fetch_str = data_freshness.get(category)
        
        if not last_fetch_str:
            return True  # Category never fetched
        
        last_fetch = datetime.strptime(last_fetch_str, '%Y-%m-%d')
        current_date = datetime.strptime(current_ds, '%Y-%m-%d')
        days_since_fetch = (current_date - last_fetch).days
        
        # Apply caching rules
        if category in STATIC_CATEGORIES:
            return days_since_fetch > 30  # Monthly refresh
        elif category in QUARTERLY_CATEGORIES:
            return days_since_fetch > 7  # Weekly refresh to catch quarterly updates
        elif category in DAILY_CATEGORIES:
            return days_since_fetch >= 1  # Daily refresh
        else:
            return True  # Unknown category - fetch it
            
    except Exception as e:
        print(f"Error checking fetch freshness for {ticker}/{category}: {e}")
        return True  # On error, fetch the data
