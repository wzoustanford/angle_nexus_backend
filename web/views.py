from flask import Blueprint, render_template, request, flash 
from . import iSearch 
from . import iCryptoSearch

views = Blueprint('views', __name__) 

@views.route('/', methods = ['GET', 'POST'])
def home():
    """Home page - AngleNexus interface with agent chat"""
    return render_template("anglenexus.html")


@views.route('/anglenexus', methods = ['GET'])
def anglenexus():
    """AngleNexus interface (alias for home)"""
    return render_template("anglenexus.html")


@views.route('/illumenti', methods = ['GET', 'POST'])
def illumenti():
    """Legacy Illumenti interface (moved from home)"""
    return render_template("index.html")


@views.route('/search', methods = ['GET', 'POST'])
def search():
    """Legacy search endpoint"""
    query = None
    search_res = None
    crypto_search_res = None
    crypto_query = None

    # For Equity
    if 'query' in request.form:
        query = request.form.get('query')
    if query:
        search_res = iSearch.query(query)
    
    # For Crypto
    if 'crypto_query' in request.form:
        crypto_query = request.form.get('crypto_query')
        
    if crypto_query:
        crypto_search_res = iCryptoSearch.query(crypto_query)

    """ render the search results """ 
    return render_template("search.html", search_results=search_res, crypto_search_res=crypto_search_res)


@views.route('/crypto', methods = ['GET', 'POST'])
def crypto():
    """Legacy crypto endpoint"""
    query = request.form.get('query')
    search_res = None
    if query:
        search_res = iCryptoSearch.query(query)
        flash("Query submitted!", category='success')

    """ render the search results """
    return render_template("home.html", search_results=search_res)


@views.route('/privacy-policy', methods = ['GET'])
def privacy_policy():
    """Privacy policy page"""
    return render_template("privacy.html")


@views.errorhandler(404)
def not_found(e):
    """404 error handler"""
    return render_template("404.html")
  