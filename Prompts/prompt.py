
def q_analysis_sys_prompt():
    sys_prompt="""
        You are a highly capable assistant whose job is to analyze incoming user queries and determine the exact topics the user is asking about. For each identified topic, you must:
        1. Break Down the Query:
        - Analyze the user input and any reference documents to identify all distinct topics or areas of interest.
        - Ensure that each topic is clearly delineated, considering both the provided reference materials and additional context from the user.

        2. Identify Relevant APIs:
        - For every topic identified, determine the appropriate API that can provide the necessary data.
        - Specify which parameters must be passed to the API based on details from the user query or reference documents.
        - If an API requires a company symbol, replace any placeholder (such as "company_symbol") with the company's official symbol as provided.
        - If the same API is applicable to multiple companies in one query, ensure that each company's API call is separated as distinct JSON objects.

        3. Date Parameters:
        - If the query involves a date range (for example, “2 years statement last month last year”), automatically calculate and include the corresponding "to" and "from" dates based on today's date (which will be provided in the text).
        - Include these dates as additional keys ("to" and "from") in your JSON output.

        4. Output Format:
        - Return the results as a structured JSON object.
        - Each key in the JSON should represent a topic, and its value should be an object with at least the following keys:
            - **name:** A descriptive name for the dataset (e.g., "Company Profile Data").
            - **Key:** A unique identifier key (e.g., "company_profile_data").
            - **to:** (Optional) The calculated end date if a date range is applicable.
            - **from:** (Optional) The calculated start date if a date range is applicable.
            - **description:** A clear explanation of what the API call does, including a brief description of the data it provides.
            - **api:** The endpoint for the API call, with any placeholders replaced by actual parameters. For example, if a company symbol is needed, the placeholder should be replaced by the official symbol (e.g., **AAPL**).

        5. Example JSON Output:
        Use the following example as a guide for your output:

        ```json
        {
            "company_profile_data": {
            "name": "Company Profile Data",
            "Key": "company_profile_data",
            "to": "2023-01-02",
            "from": "2025-01-03",
            "description": "Access detailed company profile data with the FMP Company Profile Data API. This API provides key financial and operational information for a specific stock symbol, including the company's market capitalization, stock price, industry, and much more.",
            "api": "https://financialmodelingprep.com/stable/profile?*symbol*=**AAPL**"
            },
            "another_topic": {
            "name": "Another Topic Name",
            "Key": "another_topic",
            "to": "2023-01-02",
            "from": "2025-01-03",
            "description": "Description of what this API call provides, including details on parameters and returned data.",
            "api": "https://exampleapi.com/endpoint?param=value"
            }
        }```
        Additional Instructions:
        Ensure that any data or parameters required by the API are accurately extracted from the user input or reference documents.
        If multiple APIs could apply, choose the one that most closely matches the query's requirements.
        If the user query does not pertain to any relevant topics, return an empty JSON object: {}.
        Your output should strictly follow the JSON output format with the proper keys as shown in the example.
        Do not include extraneous commentary or non-JSON text in your final output.
        Your task is to interpret the incoming query, identify topics and associated API calls, and produce an output in the JSON structure as described. Ensure clarity, accuracy, and a direct mapping between the user's needs and the APIs provided.

        ---
        This prompt will guide your LLM to:
        - Identify topics from the user query.
        - Map each topic to the corresponding API call with required parameters, including the official company symbol.
        - Calculate and include "to" and "from" dates when needed.
        - Return results in a clear, structured JSON format.
        - Return an empty JSON `{}` if the query is not relevant.

        Feel free to adjust any parts further to suit your specific implementation needs.
        """
    return sys_prompt

def FinApis_details():
    text="""Company APIs
        Company Profile Data API:
        Details: Access detailed company profile data with the FMP Company Profile Data API. This API provides key financial and operational information for a specific stock symbol, including the company's market capitalization, stock price, industry, and much more.
        Endpoint: https://financialmodelingprep.com/stable/profile?symbol={company_symbol}
        params= {symbol}

        Company Profile by CIK API:
        Details:Retrieve detailed company profile data by CIK (Central Index Key) with the FMP Company Profile by CIK API. This API allows users to search for companies using their unique CIK identifier and access a full range of company data, including stock price, market capitalization, industry, and much more.
        Endpoint: https://financialmodelingprep.com/stable/profile-cik?cik={cpmany_cik_num}
        params= {cik}

        Company Notes API: 
        Details: Retrieve detailed information about company-issued notes with the FMP Company Notes API. Access essential data such as CIK number, stock symbol, note title, and the exchange where the notes are listed.
        Endpoint: https://financialmodelingprep.com/stable/company-notes?symbol={company_symbol}
        params= {symbol}

        Stock Peer Comparison API:
        Details: Identify and compare companies within the same sector and market capitalization range using the FMP Stock Peer Comparison API. Gain insights into how a company stacks up against its peers on the same exchange.
        Endpoint: https://financialmodelingprep.com/stable/stock-peers?symbol={company_symbol}
        params= {symbol}

        Delisted Companies API: 
        Details: Stay informed with the FMP Delisted Companies API. Access a comprehensive list of companies that have been delisted from US exchanges to avoid trading in risky stocks and identify potential financial troubles.
        Endpoints: https://financialmodelingprep.com/stable/delisted-companies
        params= {no params required}
        Chart APIs

        Basic Stock Chart API: 
        Details: Access simplified stock chart data using the FMP Basic Stock Chart API. This API provides essential charting information, including date, price, and trading volume, making it ideal for tracking stock performance with minimal data and creating basic price and volume charts.
        Endpoints: https://financialmodelingprep.com/stable/historical-price-eod/light?symbol={company_symbol} 
        params= {symbol}

        Stock Price and Volume Data API: 
        Details: Access full price and volume data for any stock symbol using the FMP Comprehensive Stock Price and Volume Data API. Get detailed insights, including open, high, low, close prices, trading volume, price changes, percentage changes, and volume-weighted average price (VWAP).
        Endpoints: https://financialmodelingprep.com/stable/historical-price-eod/full?symbol={company_symbol} 
        params= {symbol}

        Unadjusted Stock Price API:
        Details: Access stock price and volume data without adjustments for stock splits with the FMP Unadjusted Stock Price Chart API. Get accurate insights into stock performance, including open, high, low, and close prices, along with trading volume, without split-related changes.
        Endpoints: https://financialmodelingprep.com/stable/historical-price-eod/non-split-adjusted?symbol={comapny_symbol}
        params= {symbol}

        Dividend Adjusted Price Chart API: 
        Details: Analyze stock performance with dividend adjustments using the FMP Dividend-Adjusted Price Chart API. Access end-of-day price and volume data that accounts for dividend payouts, offering a more comprehensive view of stock trends over time.
        Endpoints: https://financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted?symbol={company_symbol}
        params= {symbol}

        Statements APIs


        Real-Time Income Statement API: 
        Details: Access real-time income statement data for public companies, private companies, and ETFs with the FMP Real-Time Income Statements API. Track profitability, compare competitors, and identify business trends with up-to-date financial data.
        Endpoints: https://financialmodelingprep.com/stable/income-statement?symbol={company_symbol}
        params= {symbol}

        Balance Sheet Data API:
        Details:Access detailed balance sheet statements for publicly traded companies with the Balance Sheet Data API. Analyze assets, liabilities, and shareholder equity to gain insights into a company's financial health.
        Endpoint: https://financialmodelingprep.com/stable/balance-sheet-statement?symbol={company_symbol} 
        params= {symbol}

        Cash Flow Statement API:
        Details:Gain insights into a company's cash flow activities with the Cash Flow Statements API. Analyze cash generated and used from operations, investments, and financing activities to evaluate the financial health and sustainability of a business.
        Endpoint: https://financialmodelingprep.com/stable/cash-flow-statement?symbol={company_symbol} 
        params= {symbol}

        """
    return text