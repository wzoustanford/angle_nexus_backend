import os
from dotenv import load_dotenv

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))

# Construct the path to the .env file in the parent directory
dotenv_path = os.path.join(script_dir, '../.env')

# Load the .env file
load_dotenv(dotenv_path=dotenv_path)

import argparse
from build_dataset import BuildDataset 
from ticker_list import TICKERS 
from datetime import datetime

bd = BuildDataset()  
small_ticker_list = TICKERS[:5] 
category = "income-statement" 

def test_query():
    for ticker in small_ticker_list: 
        r = bd.query_fmp_api(ticker, category)

def test_query_yearly():
    for ticker in small_ticker_list:
        r = bd.query_fmp_api(ticker, category, period='year')
        print (r)

def test_query_quarterly():
    for ticker in small_ticker_list:
        r = bd.query_fmp_api(ticker, category, period='quarter')
        print (r)

def test_build_tables(wi, ns, test_samples = 5):
    bd.build_base_tables(wi, ns, test_samples=test_samples)

def test_export_tables():
    test_build_tables(worker_index, num_splits) 
    bd.export_tables('unit_testing_05_08') 

def test_query_build_full_tables():
    test_build_tables(test_samples = 3) 
    bd.query_build_full_tables()
    bd.export_tables('data_pipeline_testing_on_ec2_jan_4')

def query_build_full_tables(): 
    test_build_tables(test_samples = None) 
    bd.query_build_full_tables() 
    bd.export_tables('export_05_23_all') 

def build_tables_test(worker_index, num_splits, test_samples):
    bd.build_base_tables(worker_index, num_splits, test_samples)
    bd.query_build_full_tables()

    #bd.export_tables('export_{}'.format(datetime.now().strftime("%Y_%m_%d")))
    bd.export_tables('equity_{}'.format(worker_index))

def build_tables_production(worker_index, num_splits):
    bd.build_base_tables(worker_index, num_splits)
    bd.query_build_full_tables()
    #bd.export_tables('export_{}'.format(datetime.now().strftime("%Y_%m_%d")))
    bd.export_tables('equity_{}'.format(worker_index))

### --- for ec2 testing this runs 30 equity tickers in nasdaq and 30 tickers in nyse --- 
#test_query_build_full_tables()
#test_build_tables()

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-wi', required=True,
                        help='worker index')
    parser.add_argument('-ns', required=True,
                        help='number of splits')
    parser.add_argument('-samples', required=False,
                        help='sample number of tickers')
    args = parser.parse_args()
    if int(args.wi) < int(args.ns):
        if args.samples:
            build_tables_test(int(args.wi), int(args.ns), int(args.samples))
        else:
            build_tables_production(int(args.wi), int(args.ns))
    else:
        print ('wi must have a smaller value than ns.')
