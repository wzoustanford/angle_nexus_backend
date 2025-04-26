""" 
build a first dataset using pandas and rest api 
1. financialmodelingprep.com 
2. build csv's with pandas 
""" 

import os
import math
import boto3
from time import sleep 
import cryptowatch as cw
from dynabodb_funcs import *
from numerize import numerize
from collections import Counter
from dotenv import load_dotenv
from math import floor, ceil, isnan
import pandas as pd, requests, json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import csv

# Load environment variables from the .env file
load_dotenv(dotenv_path='../.env')

# Ensure the data directory exists
root_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
os.makedirs(root_data_dir, exist_ok=True)

# JSON encoder class to convert to decimal
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

class BuildDataset: 
    def __init__(self): 
        """ Account info FinancialModelingPrep """ 
        self.API_KEY = os.getenv('FINANCIAL_MODELING_PREP_API_KEY') 
        self.url_pref = "https://financialmodelingprep.com/api/v3/"
        self.aws_region = os.getenv('AWS_REGION') 
        self.istmnt_years = 4
        self.istmnt_quarters = 6
        self.special_cols = ['revenue__income-statement'] # 'netIncome__income-statement']
        self.retention_days = 5
        self.DB_MAX_TRIES = 3
        self.DB_RETRY_DELAY = 0.5
        self.save_df_as_csv = True
        self.chart_datapoints = 250
        self.chart_datapoints_sm = 50
        self.unitnames = ['','K','M','B','T']
        """
        profile; quote; key-executives; income-statement; balance-sheet-statement; cash-flow-statement; 
        income-statement-growth; ratios-ttm; ratios; enterprise-values; key-metrics-ttm; key-metrics; 
        financial-growth; rating; historical-rating; discounted-cash-flow; market-capitalization; 
        stock_news;
        """ 
        self.url_post = "?apikey="+self.API_KEY 
        self.prototype_data_nasdaq = "../data/nasdaq_all_base_table.csv" 
        self.prototype_data_nyse = "../data/nyse_all_base_table.csv"
        self.prototype_price_chart_sample = "../data/historical-chart-sample.csv" # TODO: remove this
        
        """ this following dictionary 'category and field dict', 
            stores all fields to be queried from FMP 
            the key indicates category and the actual FMP-API to call 
            they value is a list whose element indicate the fine-level field-key in the returned json
            both strings will be concatengated to be the field in the table schema 
        """
        self.cat_and_field_dict = { 
            "profile":["description", "ceo", "industry", "price", "currency",\
                    "mktCap", "image", "volAvg"],
            #"quote-short":["price"],
            #"historical-chart":{"30min":"close", "", "", ""},
            "quote":["pe", "change", "volume"], 
            "income-statement": ["ebitda","netIncome","revenue","eps", "epsdiluted"], 
            "balance-sheet-statement": ["totalAssets", "totalCurrentAssets",
                    "cashAndShortTermInvestments", "totalLiabilities",\
                    "netReceivables", "longTermInvestments",\
                    "totalCurrentLiabilities", "cashAndCashEquivalents" ],
            "cash-flow-statement":["freeCashFlow"], 
            "income-statement-growth":["growthEBITDA", "growthNetIncome", "growthEPS"],
            "historical-price-full/stock_dividend": ["dividend", "date"],
            }
        
        self.fmp_last_submit_time = datetime.now() 
        self.fmp_requests_per_minute = 300.0 
        self.db = boto3.resource('dynamodb', self.aws_region)
        self.ttl_timestamp = datetime.now() + timedelta(days=self.retention_days)
        self.ttl_timestamp = floor(self.ttl_timestamp.timestamp())
        # Set Crypto watch API
        cw.api_key = os.getenv('CRYPTO_WATCH_API_KEY')
        # Create crypto dynamodb table 
        self.crypto_table = create_crypto_db_table(self.db)
        # Create crypto price dynamodb table 
        self.crypto_price_table = create_crypto_price_db_table(self.db)
        

    def get_crypto_base_table(self, params):
        """ Builds the crypto base table from a single coinmarketcap data point """
        # (1) Query API and rank by market cap to get the top 2000 coins
        # (2) Calls slice_base_table function to handle data sharding
        self.cmc_headers = {'X-CMC_PRO_API_KEY': params['coinmarketcap_api_key']}
        
        # Define crypto table
        self.crypto_table_df = pd.DataFrame()

        # query API rank by market cap and get top (2000) coins
        self.crypto_base_table = self.extract_coins_by_market_cap(headers=self.cmc_headers, max_num=params['num_of_coins_by_marketcap'])

        # Returns list of all active cryptocurrencies with latest market data.
        listings_url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?limit={params["cmc_active_coins_limit"]}'
        self.markets = self.query_cryptoapi(url=listings_url,headers=self.cmc_headers)

        # Implement data-sharding logic and table split 
        # Leader determination, data retention deletion logic 
        if params['num_splits'] > 0 and params['worker_index'] < params['num_splits']:
                self.crypto_base_table = self.slice_base_table(self.crypto_base_table, params['worker_index'],  params['num_splits'])


    def build_base_tables(self, worker_index, num_splits, test_samples=None):
        self.equity_table = create_db_table(self.db)
        self.equity_price_table = create_price_db_table(self.db)
        self.is_leader = True if worker_index==0 else False
        self.is_last_worker = True if worker_index==num_splits-1 else False
        self.table_nasdaq_base = pd.read_csv(self.prototype_data_nasdaq) 
        self.table_nyse_base = pd.read_csv(self.prototype_data_nyse)
        if num_splits > 0 and worker_index < num_splits:
            self.table_nyse_base = self.slice_base_table(self.table_nyse_base, worker_index, num_splits)
            self.table_nasdaq_base = self.slice_base_table(self.table_nasdaq_base, worker_index, num_splits)
        if test_samples: 
            #self.table_nasdaq_base = self.table_nasdaq_base.sort_values(by=['Market Cap'], ascending = False) 
            #self.table_nyse_base = self.table_nyse_base.sort_values(by=['Market Cap'], ascending = False) 
            self.table_nasdaq_base = self.table_nasdaq_base[:test_samples] 
            self.table_nyse_base = self.table_nyse_base[:test_samples]
        self.cols = self.build_template_row()
        self.table_nasdaq = pd.DataFrame(columns=self.cols) 
        self.table_nyse = pd.DataFrame(columns=self.cols)
        print(self.table_nasdaq) 
        print(self.table_nyse)

    def slice_base_table(self, table_df, worker_index, num_splits):
        total_rows = len(table_df)
        if total_rows > 0:
            start = (floor(total_rows / num_splits)) * worker_index
            end = (floor(total_rows / num_splits)) * (worker_index+1) if worker_index!=num_splits-1 else total_rows
            sliced_table = table_df[start:end]
        else:
            sliced_table = table_df
        return sliced_table
    
    def build_template_row(self): 
        cols = ["symbol", "name"]
        table_start_idx = self.table_nasdaq_base.index[0]
        queried_cols, row_data = self.query_and_get_table_row(self.table_nasdaq_base["Symbol"][table_start_idx])
        row_data = [self.table_nasdaq_base["Symbol"][table_start_idx],\
                self.table_nasdaq_base["Name"][table_start_idx]] + row_data
        cols += queried_cols 
        cols += ["derived__netIncomeMargin"] 
        cols += ["derived__debtRatio"] 
        row_data += [0.2, 0.3] 
        self.template_row = pd.DataFrame(columns = cols)
        self.template_row.loc[0] = row_data 
        return cols
    
    def query_build_full_tables(self):
        """ build tables for all exchanges """
        print("building NASDAQ+NYSE price-history-charts w. api queries")
        self.populate_price_history_data()
        print("building NASDAQ w. api queries")
        self.query_build_exchange_table(self.table_nasdaq_base, self.table_nasdaq, 'nasdaq') 
        print("building NYSE w. api queries")
        self.query_build_exchange_table(self.table_nyse_base, self.table_nyse, 'nyse') 
        print('self.is_last_worker:', self.is_last_worker)

        self.update_latest_ds(self.equity_table) # TODO: REMOVE LATER
        if self.is_last_worker: 
            self.update_latest_ds(self.equity_table)
    
    def query_build_exchange_table(self, base_table, table, exchange): 
        """ build a table for one exchange """
        now = datetime.now()
        ds = now.strftime("%Y-%m-%d")
        for idx, ticker in base_table[["Symbol", "Name"]].iterrows():
            if "^" in ticker.Symbol:
                continue
            queried_cols, row_data = self.query_and_get_table_row(ticker.Symbol)
            row_data = [ticker.Symbol, ticker.Name] + row_data
            row_data = self.compute_derived_data_per_row(row_data)
            col_names = ['Symbol', 'Name'] + queried_cols + ['derived__netIncomeMargin', 'derived__debtRatio']
            row_data_dict = self.prepare_row_for_dynamodb(col_names, row_data, ds, exchange)
            self.equity_put_item(self.equity_table, row_data_dict)
            if self.save_df_as_csv == True:
                table.loc[len(table)] = row_data
        if self.is_leader:
            pass
            #remove_old_equity_records(self.equity_table, self.retention_days, exchange)
            #remove_old_equity_records(self.equity_price_table, self.retention_days, exchange)


    def equity_put_item(self, table, item):
        tries = 0
        while tries < self.DB_MAX_TRIES:
            try:
                tries += 1
                resp = table.put_item(Item=item)
                break
            except ClientError as error:
                print ('Database insertion failure-{} for data:'.format(tries), item)
                print (error)
                #print (error.response['Error']['Code'], response['Error']['Message'])
                sleep(self.DB_RETRY_DELAY)
                
    def prepare_row_for_dynamodb(self, cols_list, row_data, ds, exchange):
        """ prepare data in a format which is acceptable to boto3 put_item """
        fields_map = { 
                'image__profile': 'logo',
                'price__profile': 'current_price',
                'currency__profile': 'currency',
                'change__quote': 'change_1d',
                }
        benchmarks_map = {
                'pe__quote': 'PE ratio',
                'derived__debtRatio': 'Debt ratio',
                'volavg__profile': 'Average (daily) Volume',
                }
        key_metrics_map = {
                'mktCap__profile': 'Market Cap',
                'pe__quote': 'PE ratio',
                'derived__debtRatio': 'Debt ratio',
                }
        assets_map = { 
                'cashAndCashEquivalents__balance_sheet_statement': 'Cash',
                'totalCurrentAssets__balance_sheet_statement': 'TotalCurrentAssets',
                'totalAssets__balance_sheet_statement': 'TotalAssets',
                'totalLiabilities__balance_sheet_statement': 'TotalLiabilities',
                'totalCurrentLiabilities__balance_sheet_statement': 'TotalCurrentLiabilities',
                }
        benchmarks = []
        key_metrics = []

        data_dict = { 'ds': ds, 'exchange': exchange }
        for idx, col_name in enumerate(cols_list):
            if col_name in fields_map.keys():
                data_dict[fields_map[col_name]] = row_data[idx]
            elif col_name in benchmarks_map.keys() or col_name in key_metrics_map.keys():
                if col_name in benchmarks_map.keys():
                    key = benchmarks_map[col_name]
                    total = row_data[idx] or '__nan__'
                    if key=='Debt ratio':
                        unit = "%"
                    else:
                        unit = ""
                    benchmarks.append(
                            { 'key': key, 'total': total, 'unit': unit } )
                if col_name in key_metrics_map.keys():
                    tag = key_metrics_map[col_name]
                    val = numerize.numerize(row_data[idx])\
                            if row_data[idx] and tag=='Market Cap' else row_data[idx]
                    if tag=='Debt ratio':
                        unit = "%"
                    elif tag=='Market Cap':
                        unit = val[-1] if val else ""
                        val = val[:-1] if val else "__nan__"
                    else:
                        unit = ""
                    key_metrics.append(
                            { 'tag': tag, 'value': val, 'unit': unit })
            elif col_name in assets_map.keys():
                data_dict[assets_map[col_name]] = row_data[idx]
            elif col_name == 'ceo__profile':
                leadership_profile = { 'name': row_data[idx], 'role': 'CEO' }
                data_dict['leadership_profile'] = leadership_profile
            else:
                data_dict[col_name.lower()] = row_data[idx]

        data_dict['id'] = 'equity_{}_{}'.format(data_dict.get('exchange'),\
                data_dict.get('symbol').lower())
        data_dict['benchmarks'] = benchmarks
        data_dict['key_metrics'] = key_metrics
        data_dict['assets'] = self.get_assets(data_dict)
        data_dict['equity_liabilities'] = self.get_eq_liabilities(data_dict)
        data_dict['is_positive_change'] = float(data_dict.get('change_1d') or 0) > 0.0
        key_metrics.append(self.get_dividend(data_dict))
        key_metrics.append(self.get_earnings_growth_yoy(data_dict))
        data_dict['key_metrics'] = key_metrics

        ep = get_equity_price(self.equity_price_table, data_dict.get('symbol'), ds)
        try:
            price_change_1y = ep.get('data').get('1y')[0].get('y') / ep.get('data').get('1y')[-1].get('y') - 1
        except:
            price_change_1y = 0.0
        try:
            price_change_1w = ep.get('data').get('1w')[0].get('y') / ep.get('data').get('1w')[-1].get('y') - 1
        except:
            price_change_1w = 0.0
        data_dict['change_1y'] = float(price_change_1y) if price_change_1y else '__nan__'
        data_dict['change_1w'] = float(price_change_1w) if price_change_1w else '__nan__'
        data_dict = json.loads(json.dumps(data_dict), parse_float=Decimal)
        chart = ep.get('data') or {}
        data_dict['chart'] = chart
        data_dict['ttl_timestamp'] = self.ttl_timestamp
        return data_dict

    def get_earnings_growth_yoy(self, data):
        """ prepare earnings_growth_yoy dictionary """
        annual_earnings = data.get('annual_earnings')
        if len(annual_earnings) > 1:
            try:
                value_growth_yoy = annual_earnings[0].get('net_profit') / annual_earnings[1].get('net_profit') - 1
            except:
                print ('Failed to calculate value_growth_yoy')
                print (annual_earnings[0].get('net_profit'), annual_earnings[1].get('net_profit'))
                print (data)
                value_growth_yoy = '__nan__'
        else:
            value_growth_yoy = '__nan__'

        earnings_growth_yoy = {
          "tag": "Earning Growth (YoY)",
          "value": value_growth_yoy,
          "unit": "%",
          "show_alt_val": False,
          "alt_value": ""
        }

        return earnings_growth_yoy


    def get_dividend(self, data):
        """ prepare dividend dictionary """
        threshold_date = datetime.now() - relativedelta(months=6)
        dividends = data.get('dividend__historical-price-full/stock_dividend')
        dividend_dates = data.get('date__historical-price-full/stock_dividend')

        try:
            recent_div_date = datetime.strptime(dividend_dates[0], '%Y-%m-%d')
        except:
            recent_div_date = datetime.now() - relativedelta(years=2)

        try:
            oldest_div_yr = datetime.strptime(dividend_dates[1], '%Y-%m-%d').year
        except:
            oldest_div_yr = "" 

        try:
            dividend = dividends[0]
        except:
            dividend = "None"

        if recent_div_date > threshold_date:
            alt_value = "since {}".format(oldest_div_yr)
            show_alt_val = True
        else:
            alt_value = ""
            dividend = "None"
            show_alt_val = False

        return { 'tag': 'Dividends',
                 'value': dividend,
                 'alt_value': alt_value,
                 'show_alt_value': show_alt_val }

    def get_assets(self, data):
        """ prepare a list of assets """
        try:
            value_cash = numerize.numerize(data.get('Cash'))
        except:
            value_cash = '__nan__'

        try:
            value_st = numerize.numerize(data.get('TotalCurrentAssets') - data.get('Cash'))
        except:
            value_st = '__nan__'

        try:
            value_lt = numerize.numerize(data.get('TotalAssets') - data.get('TotalCurrentAssets'))
        except:
            value_lt = '__nan__'

        assets = [
                {
                    "key": "Cash",
                    "value": value_cash
                },
                {
                    "key": "S/T",
                    "value": value_st
                },
                {
                    "key": "L/T",
                    "value": value_lt
                }
            ]

        return assets


    def get_eq_liabilities(self, data):
        """ prepare a list of equity_liabilities """
        try:
            value_equity = numerize.numerize(data.get('TotalAssets') - data.get('TotalLiabilities'))
        except:
            value_equity = '__nan__'

        try:
            value_st = numerize.numerize(data.get('TotalCurrentLiabilities'))
        except:
            value_st = '__nan__'

        try:
            value_lt = numerize.numerize(data.get('TotalLiabilities') - data.get('TotalCurrentLiabilities'))
        except:
            value_lt = '__nan__'

        equity_liabilities = [
                {
                    "key": "Equity",
                    "value": value_equity
                },
                {
                    "key": "S/T",
                    "value": value_st
                },
                {
                    "key": "L/T",
                    "value": value_lt
                }
            ]

        return equity_liabilities


    def populate_price_history_data(self):
        """ build a table for one exchange """
        now = datetime.now() 
        ds = now.strftime("%Y-%m-%d")
        one_week_old_date = now - timedelta(days=7)
        all_tickers = self.table_nyse_base.assign(exchange='nyse')\
            .append(self.table_nasdaq_base.assign(exchange='nasdaq'))
        all_tickers = all_tickers.filter(['Symbol','exchange'], axis=1)
        all_tickers.rename({'Symbol': 'symbol'}, axis=1, inplace=True)
        for idx, ticker in all_tickers.iterrows():
            if "^" in ticker.symbol:
                continue
            data_1w = []
            hourly_data = self.get_historic_price_data(ticker.symbol, '1hour')
            for row in hourly_data:
                row_dt = datetime.strptime(row.get('date'), '%Y-%m-%d %H:%M:%S')
                if row_dt > one_week_old_date:
                    data_1w.append({
                        'x': row.get('date'),\
                        'y': row.get('close'),\
                        'z': row.get('volume')})
            ipo_date = self.get_ipo_date(ticker.symbol)
            daily_data = self.get_historic_price_data(ticker.symbol, 'daily', ipo_date)
            data_1m = self.subsample_historic_price_data(daily_data, '1m')
            data_6m = self.subsample_historic_price_data(daily_data, '6m')
            data_1y = self.subsample_historic_price_data(daily_data, '1y')
            data_all = self.subsample_historic_price_data(daily_data, 'all',\
                    self.chart_datapoints)
            data_1y_sm = self.subsample_historic_price_data(daily_data, '1y_sm',\
                    self.chart_datapoints_sm)
            db_item = { 'symbol': ticker.symbol,
                        'ds': ds,
                        'exchange': ticker.exchange,
                        'ipo_date': ipo_date,
                        'data': {
                            '1w': data_1w,
                            '1m': data_1m,
                            '6m': data_6m,
                            '1y': data_1y,
                            '1y_sm': data_1y_sm,
                            'all': data_all,
                            },
                        'ttl_timestamp': self.ttl_timestamp
                        }
            db_item = json.loads(json.dumps(db_item), parse_float=Decimal)
            self.equity_put_item(self.equity_price_table, db_item)
            
            print ("{} ({}) - {} - hourly={}, total_daily={}, 1w={}, 1m={}, 6m={}, 1y={}, all={}, 1y_min={}".\
                    format(ticker.symbol, ticker.exchange, ipo_date,
                        len(hourly_data), len(daily_data), len(data_1w),
                        len(data_1m), len(data_6m), len(data_1y),
                        len(data_all), len(data_1y_sm)))

    def get_ipo_date_old(self, ticker, years_ago):
        """ return the oldest date from from the historic price data """
        period = self.get_dates_period(years_ago)
        data = self.query_fmp_api(ticker, 'historical-price-full', period)
        last_row = data[-1]
        ipo_date = last_row.get('date') or datetime.now().strftime("%Y-%m-%d")
        return ipo_date

    def get_ipo_date(self, ticker):
        """ return the oldest date from from the historic price data """
        data_rows = self.query_fmp_api(ticker, 'historical-price-full', 'serietype=line')
        if data_rows:
            last_row = data_rows[-1]
            ipo_date = last_row.get('date') or datetime.now().strftime("%Y-%m-%d")
        else:
            ipo_date = '__nan__'
        return ipo_date

    def get_dates_period(self, years):
        """ return a date range string according to the years given """
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - relativedelta(years=years)).strftime("%Y-%m-%d")
        dates_period = f'from={from_date}&to={to_date}'
        return dates_period

    def get_historic_price_data(self, ticker, type, ipo_date=None):
        """"""
        if type == '1hour':
            data = self.query_fmp_api(ticker, 'historical-chart/1hour')
        elif type == 'daily':
            date_period = "from={}".format(ipo_date) if ipo_date else ''
            data = self.query_fmp_api(ticker, 'historical-price-full', date_period)
        if not data:
            data = []
        return data

    def subsample_historic_price_data(self, data_rows, period_type,\
            chart_datapoints=None):
        """ 
            subsample the historic data into: 
                1m: 30 datapoints (inc. weekends)
                6m: 60 datapoints (inc. weekends)
                1y: 300+ datapoints
                all: 200-300 from the date of IPO
        """
        partial_data = []
        if period_type == '1m':
            start_date = datetime.now() - relativedelta(months=1) 
        elif period_type == '6m':
            start_date = datetime.now() - relativedelta(months=6) 
        elif period_type == '1y':
            start_date = datetime.now() - relativedelta(years=1) 
        elif period_type == 'all' and data_rows:
            data_dict = {}
            ipo_date = data_rows[-1].get('date')
            sample_data_count = min(chart_datapoints, len(data_rows))
            gap = floor(len(data_rows)/sample_data_count)
            df = pd.DataFrame(data_rows)
            df['date'] = pd.to_datetime(df['date'])
            sampled_by = '{}B'.format(gap)
            r_df = df.resample(sampled_by, on='date').mean()

            for idx, data_row in r_df.iterrows():
                data_dict = {}
                data_dict['x'] = datetime.strftime(idx.to_pydatetime(), '%Y-%m-%d')
                try:
                    data_dict['y'] = data_row.close if not isnan(data_row.close) else '__nan__'
                except:
                    data_dict['y'] = '__nan__'
                try:
                    data_dict['z'] = data_row.volume if not isnan(data_row.volume) else '__nan__'
                except:
                    data_dict['z'] = '__nan__'
                partial_data.append(data_dict)
            return (partial_data)
        elif period_type == '1y_sm' and data_rows:
            start_date = datetime.now() - relativedelta(years=1) 

        if period_type not in ('all', '1y_sm'):
            for row in data_rows:
                row_datetime = datetime.strptime(row.get('date'), '%Y-%m-%d')
                if row_datetime > start_date:
                    partial_data.append({ 'x': row.get('date'),\
                                          'y': row.get('close'),\
                                          'z': row.get('volume') })
                else:
                    break

        if period_type == '1y_sm' and data_rows:
            print (len(partial_data))
            data_rows_1y = []
            for row in data_rows:
                row_datetime = datetime.strptime(row.get('date'), '%Y-%m-%d')
                if row_datetime > start_date:
                    data_rows_1y.append(row)
            if len(data_rows_1y) == 0:
                return [] 
            partial_data = []
            sample_data_count = min(chart_datapoints, len(data_rows_1y))
            gap = floor(len(data_rows_1y)/sample_data_count)
            df = pd.DataFrame(data_rows_1y)
            df['date'] = pd.to_datetime(df['date'])
            sampled_by = '{}B'.format(gap)
            r_df = df.resample(sampled_by, on='date').mean()

            for idx, data_row in r_df.iterrows():
                data_dict = {}
                data_dict['x'] = datetime.strftime(idx.to_pydatetime(), '%Y-%m-%d')
                try:
                    data_dict['y'] = data_row.close if not isnan(data_row.close) else '__nan__'
                except:
                    data_dict['y'] = '__nan__'
                try:
                    data_dict['z'] = data_row.volume if not isnan(data_row.volume) else '__nan__'
                except:
                    data_dict['z'] = '__nan__'
                partial_data.append(data_dict)

        return partial_data

    
    def query_build_exchange_table_col_by_col(self, table):
        """ build a table for one exchange """
        for category in self.cat_and_field_dict: 
            for field in self.cat_and_field_dict[category]: 
                col_name =  field + "__" + category
                col_name = col_name.replace('-', '_')
                self.query_and_add_col_to_table(table, category, field, col_name) 
        self.compute_derived_data(table)
    
    # def export_tables(self, postfix): 
    #     print(f"exporting tables...") 
    #     # self.table_nasdaq.to_csv("./data/nasdaq_exported_table_" + postfix + ".csv")
    #     # self.table_nyse.to_csv("./data/nyse_exported_table_" + postfix + ".csv")
    #     self.table_nasdaq.to_csv(os.path.join(root_data_dir, "./nasdaq_exported_table_" + postfix + ".csv"))
    #     self.table_nyse.to_csv(os.path.join(root_data_dir, "./nyse_exported_table_" + postfix + ".csv"))
    #     print("done")

    def export_tables(self, postfix): 
        print("Exporting tables...")
        
        nasdaq_file_path = os.path.join(root_data_dir, f"nasdaq_exported_table_{postfix}.csv")
        nyse_file_path = os.path.join(root_data_dir, f"nyse_exported_table_{postfix}.csv")
        
        self.table_nasdaq.to_csv(nasdaq_file_path)
        print(f"NASDAQ table exported to: {nasdaq_file_path}")
        
        self.table_nyse.to_csv(nyse_file_path)
        print(f"NYSE table exported to: {nyse_file_path}")
        
        print("Done")

    
    def compute_derived_data_per_row(self, row_data): 
        print(f"computing derived data per row ...") 
        """ net income margin / ratio """ 
        #col_name = "derived__netIncomeMargin"
        try: 
             ni_margin = 1.0 * row_data[self.template_row.columns.get_loc("netIncome__income_statement_anul_0")] / row_data[self.template_row.columns.get_loc("revenue__income_statement_anul_0")]
        except:
             ni_margin = "__nan__"
        row_data.append(ni_margin) 
        
        """ debt ratio """ 
        #col_name = "derived__debtRatio"
        try: 
            debt_ratio = 1.0 * row_data[self.template_row.columns.get_loc("totalLiabilities__balance_sheet_statement")] / row_data[self.template_row.columns.get_loc("totalAssets__balance_sheet_statement")]
        except:
            debt_ratio = "__nan__"
        row_data.append(debt_ratio) 
        print("done") 
        return row_data
    
    def compute_derived_data(self, table): 
        print(f"computing derived data ...") 
        """ net income margin / ratio """ 
        col_name = "derived__netIncomeMargin"
        col_data = 1.0 * table["netIncome__income_statement_anul_0"] / table["revenue__income_statement_anul_0"]
        table[col_name] = col_data 
        
        """ debt ratio """ 
        col_name = "derived__debtRatio" 
        col_data = 1.0 * table["totalLiabilities__balance_sheet_statement"] / table["totalAssets__balance_sheet_statement"] 
        table[col_name] = col_data 
        print("done") 
    
    def query_and_get_table_row(self, ticker):
        print(f"Processing (query-add-rol) for ticker: {ticker}") 
        row_data = []
        queried_cols = []
        for category in self.cat_and_field_dict:
            json_res_annual_all = self.query_fmp_api(ticker, category, 'year')
            if category == 'income-statement': 
                json_res_quarterly_all = self.query_fmp_api(ticker, category, 'quarter')
            for field in self.cat_and_field_dict[category]:
                col_name =  field + "__" + category
                if col_name in self.special_cols:
                    earnings_col_name = "annual_earnings"
                    earnings_col_val = []
                    for yr in range(0, self.istmnt_years):
                        rev_col_name = f"{col_name}_anul_{yr}"
                        try:
                            rev_value = json_res_annual_all[yr][field]
                            calendar_year = json_res_annual_all[yr]['calendarYear']
                            net_income = json_res_annual_all[yr]['netIncome']
                            (rev_value, net_income, unit) = self.unify_nums(rev_value, net_income)
                            earnings_col_val.append(
                                { 'period': calendar_year,
                                  'revenue': rev_value,
                                  'unit': unit,
                                  'net_profit': net_income })
                        except:
                            print ('{} year-{} data is not available for {}'\
                                   .format(rev_col_name, yr, ticker))
                         
                    queried_cols.append(earnings_col_name)
                    row_data.append(earnings_col_val)
                    earnings_col_name = "quaterly_earnings"
                    earnings_col_val = []
                    for qrt in range(0, self.istmnt_quarters):
                        rev_col_name = f"{col_name}_quart_{qrt}"
                        try:
                            rev_value = json_res_quarterly_all[qrt][field]
                            calender_year = json_res_quarterly_all[qrt]['calendarYear']
                            period = json_res_quarterly_all[qrt]['period']
                            net_income = json_res_quarterly_all[qrt]['netIncome']
                            (rev_value, net_income, unit) = self.unify_nums(rev_value, net_income)
                            earnings_col_val.append(
                                { 'period': "{} '{}".format(period, calender_year[-2:]),
                                    'revenue': rev_value,
                                    'unit': unit,
                                    'net_profit': net_income })
                        except:
                            rev_value = "__nan__"
                            print ('{} qrt-{} data is not available for {}'\
                                   .format(rev_col_name, qrt, ticker))
                    queried_cols.append(earnings_col_name)
                    row_data.append(earnings_col_val)
                elif category.endswith('stock_dividend'):
                    try:
                        json_res = None if json_res_annual_all is None else\
                                [json_res_annual_all[0][field], json_res_annual_all[-1][field]]
                    except:
                        json_res = "__nan__"
                        print ('Setting value to str:__nan__ for {} as field-{} data is not available for {}'\
                               .format(col_name, field, ticker))
                    queried_cols.append(col_name)
                    row_data.append(json_res)
                elif category == 'historical-chart':
                    # Get last 14 records i.e. 1 week
                    for hr4 in range(0, 41):
                        pass
                else:
                    col_name = col_name.replace('-', '_')
                    queried_cols.append(col_name)
                    try:
                        json_res = None if json_res_annual_all is None else json_res_annual_all[0][field]
                    except:
                        json_res = "__nan__"
                        print ('Setting value to str:__nan__ for {} as field-{} data is not available for {}'\
                               .format(col_name, field, ticker))
                    row_data.append(json_res)
        print("done")

        return queried_cols, row_data
    
    def query_and_add_col_to_table(self, table, category, field, col_name='dummy'):
        print(f"Processing (query-add-col) for category: {category}, field: {field}, with col_name: {col_name}") 
        col_data = [] 
        for ticker in table["Symbol"]:
            json_res = self.query_fmp_api(ticker, category) 
            json_res = None if json_res is None else json_res[field]
            col_data.append(json_res) 
        if col_name == 'dummy':
            col_name += str(len(table.columns))
        table[col_name] = col_data 
        print("done")
        
    def query_fmp_api(self, ticker: str, category: str, period=''):

        """
        compose the full URL 
        """ 
        rest_url = self.url_pref + category + "/" + ticker + self.url_post
        if category == 'historical-price-full/stock_dividend':
            # Do nothing
            pass
        elif ('year' in period or 'quarter' in period):
            rest_url = rest_url + f'&period={period}'
        else:
            rest_url = rest_url + f'&{period}'
        print(rest_url)
        
        """ rate limit for querying FMP
        """ 
        self.fmp_last_submit_time 
        micro_per_second = 1000000.0 
        required_interval_sec = 60.0 / self.fmp_requests_per_minute 
        if datetime.now() - self.fmp_last_submit_time < timedelta(seconds = required_interval_sec): 
            sleep_sec = (self.fmp_last_submit_time + timedelta(seconds = required_interval_sec) - datetime.now()).total_seconds()
            print(f"sleeping for {sleep_sec} sec") 
            sleep(sleep_sec) 
        
        tries = 0
        while tries < 3: 
            try: 
                response = requests.get(rest_url, timeout=10) 
            except BaseException as err: 
                print("Query timedout: -- ") 
                print(err)
                response = None 
            if response and len(response.json()) != 0: 
                break 
            sleep(2) 
            tries += 1
        
        #response = requests.get(rest_url) 
        if not response or len(response.json()) == 0:
            return None
        
        if period == 'year' and category != 'historical-price-full/stock_dividend':
            res = response.json()[:self.istmnt_years]
        elif period == 'quarter' and category != 'historical-price-full/stock_dividend':
            res = response.json()[:self.istmnt_quarters]
        elif category == 'historical-price-full':
            res = response.json().get('historical')
        elif category.startswith('historical-chart'):
            res = response.json()
        elif category in ['historical-price-full/stock_dividend']:
            res = response.json().get('historical')
        else:
            res = response.json()[0]

        print("-- Queried FMP API, ticker: " + ticker + ";  category: " + category) 
        return res 

    def query_cryptoapi(self, url, headers):
        """ This function queries the Cryptos APIs
        """
        self.fmp_last_submit_time 
        requests_per_minute = 29
        required_interval_sec = 60.0 / requests_per_minute
        if datetime.now() - self.fmp_last_submit_time < timedelta(seconds = required_interval_sec): 
            sleep_sec = (self.fmp_last_submit_time + timedelta(seconds = required_interval_sec) - datetime.now()).total_seconds()
            print(f"sleeping for {sleep_sec} sec") 
            sleep(sleep_sec) 
        
        tries = 0
        while tries < 3: 
            try: 
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
            except BaseException as err: 
                print("Query timedout: -- ") 
                print(err)
                response = None 
            if response and len(response.json()) != 0: 
                break 
            sleep(2) 
            tries += 1 
    
    def extract_coins_by_market_cap(self, max_num=2000, headers=None):
        """ This method makes an API call to coinmarketcap 
            retrieves a list of coins and filters the top coins based on market cap
            The default is 2000 is no value is passed
            returns a list coins baseed on the  market cap
        """
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/map'
        cryptos_list = self.query_cryptoapi(url=url,headers=headers)
        cryptos_df = pd.DataFrame(cryptos_list['data'])
        self.extracted_coins_list = cryptos_df[cryptos_df['rank'] <= max_num]
        return self.extracted_coins_list[['id','symbol']].copy()


    def mini_batch_coins(self,coins_list):
        """ Groups the list of coins into batches 
            this will reduce the number of calls to the CoinMarketCap API 
        """
        slugs = []
        for index, tuple in enumerate(coins_list):
            slug = ','.join(map(str, coins_list[index])) 
            slugs.append(slug)
        return slugs 

    def compute_buy_sell_percentage(self, coin, date, api_key):
        """ 
            Compute buy and sell percentages and extracts transaction frequency 
        """
        historic_url = f'https://api.polygon.io/v3/trades/X:{coin}-USD?apiKey={api_key}&timestamp={date}&limit=50000'
        polygon_response = self.query_cryptoapi(url=historic_url,headers=None)

        if polygon_response['results']:
            print('Polygon ', coin, ' has results')

            # Extract all values from conditions 1:(buy) and 2:(sell)
            n_1 = [user for user in polygon_response['results'] if 1 in user['conditions']]
            n_2 = [user for user in polygon_response['results'] if 2 in user['conditions']]
            
            # Sum up all the values in list
            N_1 = sum(list(map(lambda n: n['price'], n_1)))
            N_2 = sum(list(map(lambda n: n['price'], n_2)))

            print(f'POLYGON_RESULTS: PRICE_N1:{N_1} - PRICE_N2:{N_2}')

            buy_percentage = N_1 / (N_1+N_2)
            sell_percentage = N_2 / (N_1+N_2)
            transaction_frequency = len(polygon_response['results'])

            return {'buy_percentage':buy_percentage,'sell_percentage':sell_percentage,'transaction_frequency':transaction_frequency }
        else:
            print(coin, ' has No Polygon results')
            return {'buy_percentage':'__nan__','sell_percentage':'__nan__','transaction_frequency':'__nan__' }

    def prepare_crypto_row_for_dynamodb(self, cols_list, row_data, ds, crypto):
        """ prepare crypto data in a format which is acceptable to boto3 put_item """
        data_dict = { 'ds': ds, 'coin': crypto, 'ttl_timestamp': self.ttl_timestamp }
        return json.loads(json.dumps(dict({**data_dict, **row_data})))
        
    def crypto_put_item(self, table, item):
        """ Write crypto dataframe to dynamodb table 
        """
        tries = 0
        while tries < self.DB_MAX_TRIES:
            try:
                tries += 1
                sleep(0.3) 
                item = json.loads(json.dumps(item), parse_float=Decimal)
                table.put_item(Item=item)
                break
            except ClientError as error:
                print ('Database insertion failure-{} for data:'.format(tries), item)
                print (error)
                #print (error.response['Error']['Code'], error.response['Error']['Message'])
                sleep(self.DB_RETRY_DELAY)

    def crypto_price_put_item(self, table, item):
        """ Write crypto dataframe to dynamodb table """
        tries = 0
        while tries < self.DB_MAX_TRIES:
            try:
                tries += 1
                sleep(0.3) 
                item = json.loads(json.dumps(item, cls=JSONEncoder), parse_float=Decimal)
                table.put_item(Item=item)
                break
            except ClientError as error:
                print ('Database insertion failure-{} for data:'.format(tries), item)
                print (error)
                #print (error.response['Error']['Code'], error.response['Error']['Message'])
                sleep(self.DB_RETRY_DELAY)


    def crypto_price_update_item(self, table, item):
        """ Update crypto price-chart data to dynamodb table """

        tries = 0
        while tries < self.DB_MAX_TRIES:
            try:
                tries += 1
                sleep(0.3)
                item = json.loads(json.dumps(item, cls=JSONEncoder), parse_float=Decimal)
                symbol = item.get('symbol').replace('usd','').upper()
                ds = item.get('ds')
                chart = item.get('data')
                try:
                    price_1y = chart.get('1y')
                    change_1y = float(price_1y[0].get('close')) / float(price_1y[-1].get('close')) - 1.0
                    change_1y = str(change_1y)
                except:
                    change_1y = '__nan__'

                r = table.update_item(Key={'symbol': symbol, 'ds': ds},
                        UpdateExpression="set chart=:c, change_1y=:y",
                        ExpressionAttributeValues={':c': chart, ':y': change_1y},
                        ReturnValues="UPDATED_NEW")
                print ('crypto_price_update_item() - {} {} {}'.format(symbol, ds, change_1y))
                break
            except ClientError as error:
                print ('Database update-item({}, {}) failure-{} for data:'\
                        .format(symbol, ds, tries), chart, change_1y)
                print (error)
                #print (error.response['Error']['Code'], error.response['Error']['Message'])
                sleep(self.DB_RETRY_DELAY)


    def build_coin_table(self, params):
        # Extract coin ids from dictionary into a single list
        coin_ids = list(map(lambda item: item['id'], self.extracted_coins_list.to_dict('records')))

        # Convert all coin ids into a batch of list for mini batching
        list_all_coins = list(zip(*(iter(coin_ids),)*int(params['cmc_mini_batch_coin_size'])))
        batch_coins = self.mini_batch_coins(list_all_coins)

        # Current time
        now = datetime.now()
        ds = now.strftime("%Y-%m-%d")
        yesterday_ds = (now - timedelta(days=1)).strftime("%Y-%m-%d")

        # Table column names
        col_names = ["id","name","symbol", "category", "description", "slug",
                "logo", "official_website", "white_paper", "price", "date_added",
                "tags","tag-names", "tag-groups", "volume_24h", "volume_change_24h", 
                "last_updated", "percent_change_1h", "percent_change_24h", "percent_change_7d",
                "percent_change_30d", "percent_change_60d", "percent_change_90d",
                "market_cap", "market_cap_dominance", "fully_diluted_market_cap",
                "buy_percentage", "sell_percentage", "transaction_frequency",
                "retention_days", "key_metrics", "benchmarks", "profile_id",
                "is_positive_change"]

        for index, slug in enumerate(batch_coins):
            print('slug: ', slug)
            # Batch processing 
            symbol_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/info?id='+batch_coins[index]
            response = self.query_cryptoapi(url=symbol_url,headers=self.cmc_headers)

            if(response is not None):
                for key, coin_value in response['data'].items():
                    print('Key:', key)
                    # Filters objects where id matches each other.  
                    coin_data = list(filter(lambda obj: obj['id'] == coin_value['id'], self.markets['data']))
                    percentage = {'buy_percentage': None,'sell_percentage': None,'transaction_frequency': None }

                    # Checks if coin data exists
                    if coin_data:
                        coin_value.update(coin_data[0]['quote']['USD'])
                        coin_value.update({'retention_days': params['retention_days']})
                        today = datetime.strftime(datetime.now(), '%Y-%m-%d')
                        coin_value['official_website'] = coin_value.get('urls').get('technical_doc')[0]\
                                if coin_value.get('urls').get('technical_doc') else '__nan__'
                        coin_value['white_paper'] = ', '.join(coin_value.get('urls').get('technical_doc') or [])
                        coin_value['profile_id'] = 'crypto_{}'.format(coin_value.get('symbol').lower())
                        coin_value['is_positive_change'] = coin_value.get('percent_change_24h') > 0

                        item = self.crypto_table.get_item(\
                                Key={'symbol': coin_value.get('symbol'), 'ds': yesterday_ds},\
                                ProjectionExpression='id, description, symbol')

                        if 'Item' in item:
                            print ('Crypto description fetched:', coin_value.get('symbol'), yesterday_ds)
                            coin_value['description'] = item.get('Item').get('description')
                        else:
                            print ('Problem fetching Crypto Description:', coin_value.get('symbol'), yesterday_ds)

                        print(f'DATE:: {str(today)}')
                    
                        # Computes buy and sell percentages for the current coin
                        computed_percentage = self.compute_buy_sell_percentage(coin=str(coin_value['symbol']), date=str(today), api_key=params['polygon_api_key'])
                        # computed_percentage = None
                        
                        if computed_percentage:
                            percentage = computed_percentage
                        
                        coin_value.update(percentage)

                        coin_value['key_metrics'] = self.get_crypto_key_metrics(coin_value)

                        coin_data = {k.replace('-', '_'): v for k, v in coin_value.items()}
                        self.crypto_table_df = self.crypto_table_df.append(coin_data, ignore_index=True)
                        self.crypto_table_df = self.crypto_table_df.filter(col_names)
                        
                        # Extract specific fields from dictionary
                        coin_data = dict((k, coin_data[k]) for k in col_names if k in coin_data)

                        # Convert crypto data to format accpetable by boto3
                        row_data_dict = self.prepare_crypto_row_for_dynamodb(col_names, coin_data, ds, 'crypto')
                        
                        # # Write data to dynamoDB crypto 
                        self.crypto_put_item(table=self.crypto_table, item=row_data_dict)


        # Define crypto dataframe
        # if(params["save_df_as_csv"]):
        #     # self.crypto_table_df.to_csv('./data/crypto_info_table.csv', mode='w', index=True, header=True)
        #     self.crypto_table_df.to_csv(os.path.join(root_data_dir, './data/crypto_info_table.csv', mode='w', index=True, header=True))
        #     print('Crypto CSV generated!!')

        # Define crypto dataframe
        if params["save_df_as_csv"]:
            output_path = os.path.join(root_data_dir, './crypto_info_table.csv')
            self.crypto_table_df.to_csv(output_path, mode='w', index=True, header=True)
            print('Crypto CSV generated!!')

        
        # If current worker is leader, remove row with that matches retention days
        self.is_leader = True if params['worker_index']==0 else False
        if self.is_leader:
            #remove_old_crypto_records(self.crypto_table, params['retention_days'], 'crypto')
            print('Old crypto record removed')

    def get_crypto_key_metrics(self, coin_data):

        try:
            market_cap_val = float(numerize.numerize(coin_data.get('market_cap'))[:-1])
            market_cap_sign = numerize.numerize(coin_data.get('market_cap'))[-1]
        except:
            market_cap_val = '__nan__'
            market_cap_sign = ''

        try:
            trade_vol_val = float(numerize.numerize(coin_data.get('volume_24h'))[:-1])
            trade_vol_sign = numerize.numerize(coin_data.get('volume_24h'))[-1]
        except:
            trade_vol_val = '__nan__'
            trade_vol_sign = ''

        try:
            buy_val = coin_data.get('buy_percentage')
            buy_sign = '%'
        except:
            buy_val = '__nan__'
            buy_sign = ''

        try:
            sell_val = coin_data.get('sell_percentage')
            sell_sign = '%'
        except:
            sell_val = '__nan__'
            sell_sign = ''

        key_metrics = [
                { 'tag': 'Market cap', 'value': market_cap_val, 'sign': market_cap_sign },
                { 'tag': 'Trading volume', 'value': trade_vol_val, 'sign': trade_vol_sign },
                { 'tag': 'Buy', 'value': buy_val, 'sign': buy_sign },
                { 'tag': 'Sell', 'value': sell_val, 'sign': sell_sign }]

        return key_metrics

    def get_crypto_benchmarks(self, coin_data):

        pass

    def calc_subsample_value(self, argument):
        """ Calculate subsampling value for the weeks 1,4,24,52,600 """
        switcher = {
            1: 2,
            4: 4,
            24: 2,
            52: 4,
            600: None,
        }
        return switcher.get(argument, None)

    def filter_dates_btw_epoch(self, candle, weeks):
        """  Returns dates that falls between 2 time epochs  """
        current_time =  datetime.now() 
        current_time_epoch = int(current_time.timestamp())
        # Calculate epoch from curent time to supplied time in weeks
        time_ago_epoch = current_time - timedelta(weeks=int(weeks))
        time_ago_epoch = int(time_ago_epoch.timestamp()) 
        if time_ago_epoch <= int(candle[0]) <= current_time_epoch:
            return candle

    
    def extract_data(self, data_loc, weeks, small_subset=False):
        """ Extract and returns chatting data from cryptomarketwatch response """
        keys = ["close_timestamp", "close"]
        data_points = []
        for candle in data_loc:
            new_candle = [candle[0], candle[4]]
            new_candle = self.filter_dates_btw_epoch(new_candle, weeks)
        
            # Update close_timestamp from timestamp
            if new_candle is not None:
              new_candle[0] = str(datetime.fromtimestamp(new_candle[0]))
              res = dict(zip(keys, new_candle))
              data_points.append({'x': res.get('close_timestamp'), 'y': res.get('close')})

        data_points.reverse()
        
        # Subsample data points
        # If less than 200 extract data points
        if(len(data_points) <= 200):
            sub_value = self.calc_subsample_value(weeks)
            return data_points[::sub_value]
        elif small_subset:
            sub_length = len(data_points) * 1.0 / self.chart_datapoints_sm
            data_points = data_points[::int(ceil(sub_length))]
            return data_points[-self.chart_datapoints_sm:]
        else:
            sub_length = len(data_points) * 1.0 / 200
            data_points = data_points[::int(ceil(sub_length))]
            return data_points[-200:]


    def crypto_historical_price(self, params):
        """ 
            This method builds historical price data from cryptowatch 
        """
        markets_url = 'https://api.cryptowat.ch/markets'
        response = self.query_cryptoapi(url=markets_url, headers=None)
        
        if(response is not None):
            all_coins = [ m.get('pair').upper() for m in response['result'] ]
            
            # Filter coins with values equated to USD (i.e ends with USD)
            market_list = list(filter(lambda n: n['pair'].endswith('usd'), response['result']))

            # coins_list = [m['pair'].replace('usd', '').upper() for m in market_list]
            # Filter based on the coins already processed 
            selected_coins = self.crypto_table_df['symbol'].tolist()

            # market_list = list(filter(lambda n: n['pair'].replace('usd', '').upper() in selected_coins, market_list))
            # Since all pairs ends with 'USD', remove the last 3 characters in the string
            market_list = list(filter(lambda n: n['pair'][:-3].upper() in selected_coins, market_list))

            # Remove duplicate crypto pairs from the market list
            select_pairs = [x['pair'] for x in market_list]
            new_market_list=[]
            for i in Counter(select_pairs):
                all = [x for x in market_list if x['pair']==i]
                new_market_list.append(max(all, key=lambda x: x['exchange']))
            
            # Define current time
            now = datetime.now()
            ds = now.strftime("%Y-%m-%d")
            
            for item in new_market_list:
                # Filter pairs that belong to the current pair we are looping through
                # and select the first item in the list
                fl_exchange = list(filter(lambda x: x['pair'] == item['pair'], market_list))
                if fl_exchange is not None:
                    print(fl_exchange[0]['exchange'], ' : ',fl_exchange[0]['pair'])                    
                    candles = cw.markets.get(f"{fl_exchange[0]['exchange']}:{fl_exchange[0]['pair']}", ohlc=True)
                    if candles._http_response.status_code == 200:
                        """
                            1w :2 hours candles: [of_2h] 
                            1m :2 hours candles: [of_2h] 
                            6m :1 day candles: [of_1d] 
                            1y :1 day candles: [of_1d] 
                            All :1 week candles starting on Thursday [of_1d]
                        """
                        _1w = None
                        _1m = None
                        _6m = None
                        _1y = None
                        _all = None

                        # Get current time epoch
                        # Get epoch of time ago [e.g 1 week, 1 month, 6 month, 1 year]
                        # Filter elements what are within the range
                        # Perform subsampling on those elements if they are more than 200 
                        # If greater than 200 compute number of data points to extract

                        if hasattr(candles, 'of_2h'):
                            _1w = self.extract_data(data_loc=candles.of_2h, weeks=1)
                            _1m = self.extract_data(data_loc=candles.of_2h, weeks=4) 
                            
                        if hasattr(candles, 'of_1d'):
                            _6m = self.extract_data(data_loc=candles.of_1d, weeks=24)
                            _1y = self.extract_data(data_loc=candles.of_1d, weeks=52)
                            _1y_sm = self.extract_data(data_loc=candles.of_1d, weeks=52, small_subset=True)
                            _all = self.extract_data(data_loc=candles.of_1d, weeks=600)
 
                        fl_exchange_pair = fl_exchange[0]['pair']
                        print('Exchange Pair: ',fl_exchange_pair)

                        """ Model schema """
                        schema = {
                            'symbol':  item['pair'][:-3].upper(),
                            'exchange': fl_exchange[0]['exchange'],
                            'ds': ds,
                            'data': {
                                    '1w': _1w,
                                    '1m': _1m,
                                    '6m': _6m,
                                    '1y': _1y,
                                    '1y_sm': _1y_sm,
                                    'all': _all,
                            },
                            'ttl_timestamp': self.ttl_timestamp,
                        }

                        # Write to dynamoDB
                        #self.crypto_price_put_item(table=self.crypto_price_table, item=schema)
                        self.crypto_price_update_item(table=self.crypto_table, item=schema)

                        # Write to file
                        if(params['save_df_as_csv']):
                            with open('../data/coin_history.json', 'w') as outfile:
                                outfile.write(json.dumps(schema))
                                outfile.write(",")
                                outfile.close()
                    else:
                        print('Error from market response')
        else:
            print('Error from cryptowatch API')                

    def build_historical_data(self, params):
        """ Builds a historical data table """
        self.crypto_historical_price(params=params)
        print('Crypto history done and saved to file.')


    def update_latest_ds(self, table):
        """ Update crypto price-chart data to dynamodb table """
        print('Updating update_latest_ds')
        now = datetime.now()
        latest_ds = now.strftime("%Y-%m-%d")
        dummy_ds = '2111-11-11'
        dummy_symbol = 'dummy_latestds_ticker'

        print('now, table.name, latest_ds', now, table.name, latest_ds)

        tries = 0
        while tries < self.DB_MAX_TRIES:
            try:
                tries += 1
                sleep(0.3)

                r = table.update_item(Key={'symbol': dummy_symbol, 'ds': dummy_ds},
                        UpdateExpression="set latest_ds=:l",
                        ExpressionAttributeValues={':l': latest_ds},
                        ReturnValues="UPDATED_NEW")
                print ('{} - update_latest_ds() - {} {}'.format(now, table.name, latest_ds))
                print('rrrr', r)
                break
            except ClientError as error:
                print ('Database update-item({}, {}) failure-{} for data:'\
                        .format(dummy_symbol, latest_ds, tries))
                print (error)
                #print (error.response['Error']['Code'], error.response['Error']['Message'])
                sleep(self.DB_RETRY_DELAY)

    def unitify(self, n):
        n = float(n)
        millidx = max(0, min(len(self.unitnames)-1,
                        int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))

        return '{:.2f}{}'.format(n / 10**(3 * millidx), self.unitnames[millidx])

    def unify_nums(self, n1, n2):
        num1_with_unit = self.unitify(n1)
        num2_with_unit = self.unitify(n2)
        num1_unit = num1_with_unit[-1] if not num1_with_unit[-1].isnumeric() else ""
        num2_unit = num2_with_unit[-1] if not num2_with_unit[-1].isnumeric() else ""
        num1_without_unit = num1_with_unit[:-1] if not num1_with_unit[-1].isnumeric() else num1_with_unit
        num2_without_unit = num2_with_unit[:-1] if not num2_with_unit[-1].isnumeric() else num2_with_unit
        num1_without_unit = float(num1_without_unit)
        num2_without_unit = float(num2_without_unit)

        if num1_unit == num2_unit:
            out_num1 = num1_without_unit
            out_num2 = num2_without_unit
        else:
            mf = 1000 ** (self.unitnames.index(num1_unit) - self.unitnames.index(num2_unit))
            out_num1 = num1_without_unit * mf
            out_num2 = num2_without_unit

        return (out_num1, out_num2, num2_unit)

