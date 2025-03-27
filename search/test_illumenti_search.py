from illumenti_search import IllumentiSearch 

path_prefix = '/Users/wiz/code/'
path_prefix = '../backend/data/'
iSearch = IllumentiSearch() 
iSearch.load_dataset(
    path_prefix + 'equity_nyse_exported_table.csv', #nasdaq_exported_table_first_export_05_16_midcap_all.csv', 
    path_prefix + 'equity_nasdaq_exported_table.csv', #nasdaq_exported_table_first_export_05_16_midcap_all.csv', 
#    path_prefix + 'nyse_exported_table_export_05_23_all.csv', #nyse_exported_table_first_export_05_16_midcap_all.csv', 
#    path_prefix + 'nyse_exported_table_export_05_23_all.csv', #nyse_exported_table_first_export_05_16_midcap_all.csv', 
    )
iSearch.build_index() 
#res = iSearch.query('show me hat clothing clothes equity with high pe and high growth')
#res = iSearch.query('Show me companies ranked by market cap')
#res = iSearch.query('TM')
res = iSearch.query('gpu with high market cap')
#res = iSearch.query('Show me electronic companies')
#res = iSearch.query('Show me internet companies in california')
#res = iSearch.query('Show me companies that makes biscuits with revenue over 99999000 million')
#res = iSearch.query('show me biscuits companies with revenue above 100 million')
#res = iSearch.query('show me biscuits companies with high earning growth')
#res = iSearch.query('show me food companies with high price')
#res = iSearch.query('Biotechnology comanies with low price and high earning growth')
#res = iSearch.query('show me food companies with low debt ratio')
#res = iSearch.query('show me food companies with high debt ratio')
#res = iSearch.query('show me food companies with Debt ratio below 0.5')
#res = iSearch.query('show me food companies with Debt ratio above 0.5')

print(res)
print(len(res.keys()))
