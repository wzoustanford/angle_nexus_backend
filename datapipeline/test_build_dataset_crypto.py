"""
    # Commands
    python test_build_dataset_crypto.py -env dev 
    python test_build_dataset_crypto.py -env prod 
"""
import os
import argparse
from dotenv import load_dotenv
from build_dataset import BuildDataset 
bd = BuildDataset()  

load_dotenv(dotenv_path='../.env')

"""
    num_of_coins_by_marketcap: (int:)Specifies the number of coins to be processed based on market cap: (2000)
    cmc_active_coins_limit: (int:) Speficies the number of coins to be retrieve from the coinmarketcap api (max is 5000)
    cmc_mini_batch_coin_size: (int:)Coins batch processing size (99 is the max)
    retention_days: (int:)Data retention day
    save_df_as_csv: (bool:) if to save as CSV
    num_splits: (int:)
    test_samples: (int:)
"""
dev = {
    "num_of_coins_by_marketcap": 90,
    "cmc_active_coins_limit":100,
    "cmc_mini_batch_coin_size": 80,
    "coinmarketcap_api_key": os.getenv('COIN_MARKET_CAP_API_KEY'),
    'polygon_api_key': os.getenv('POLYGON_API_KEY'),
    'retention_days': 3,
    'cw_pair_limit': 5,
    'save_df_as_csv': True,
    'worker_index': 0,
    'num_splits': 2,
    'test_samples': 5,
    'cryptowatch_api_key': os.getenv('CRYPTO_WATCH_API_KEY') 
}
prod = {
    "num_of_coins_by_marketcap": 2000,
    "cmc_active_coins_limit": 5000,
    "cmc_mini_batch_coin_size": 99,
    "coinmarketcap_api_key": os.getenv('COIN_MARKET_CAP_API_KEY'), 
    'polygon_api_key': os.getenv('POLYGON_API_KEY'),
    'retention_days': 3,
    'cw_pair_limit': None,
    'save_df_as_csv': True,
    'worker_index': 0,
    'num_splits': 2,
    'test_samples': 5,
    'cryptowatch_api_key': os.getenv('CRYPTO_WATCH_API_KEY')
}

def build_tables_production(environment):
    params = dev
    if(environment == 'prod'):
        params = prod

    if(params['cmc_active_coins_limit'] > params['cmc_mini_batch_coin_size']):
            bd.get_crypto_base_table(params)
            bd.build_coin_table(params)
            bd.build_historical_data(params=params)
    else: 
        print('cmc_active_coins_limit should not be less than cmc_mini_batch_coin_size')
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-env', required=True, help='environment variable')
    args = parser.parse_args()
    
    ### --- Build datatables --- 
    build_tables_production(environment = args.env)
