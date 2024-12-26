from flask import Flask
import os

from search.illumenti_search import IllumentiSearch
from search.illumenti_crypto_search import IllumentiCryptoSearch

# Initialize search objects
iSearch = IllumentiSearch()
iCryptoSearch = IllumentiCryptoSearch()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'wearetherebels'

    # Blueprint imports
    from .views import views

    app.register_blueprint(views, url_prefix='/')

    # Use relative paths for dataset loading
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_path, '..', 'data')

    # Load datasets
    iSearch.load_dataset(
        os.path.join(data_path, 'equity_nyse_exported_table.csv'),
        os.path.join(data_path, 'equity_nasdaq_exported_table.csv')
    )
    iSearch.build_index()

    iCryptoSearch.load_dataset(os.path.join(data_path, 'crypto_info_table_full.csv'))
    iCryptoSearch.build_index()

    return app


# from flask import Flask 
# import sys
# import os
# root_path = os.path.dirname(os.path.realpath(__file__)) + "/../.."
# search_path = root_path + "/search"
# sys.path.insert(1, search_path)
# from search.illumenti_search import IllumentiSearch
# from search.illumenti_crypto_search import IllumentiCryptoSearch

# iSearch = IllumentiSearch()
# iCryptoSearch = IllumentiCryptoSearch()

# def create_app():
#     app = Flask(__name__)
#     app.config['SECRET_KEY'] = 'wearetherebels'
    
#     from .views import views 
#     from .auth import auth 
    
#     app.register_blueprint(views, url_prefix='/') 
#     app.register_blueprint(auth, url_prefix='/')

#     iSearch.load_dataset(
#         root_path + '/backend/data/equity_nyse_exported_table.csv',
#         root_path + '/backend/data/equity_nasdaq_exported_table.csv'
#     )
#     iSearch.build_index()

#     iCryptoSearch.load_dataset(root_path + '/backend/data/crypto_info_table_full.csv')
#     iCryptoSearch.build_index()
    
#     return app

