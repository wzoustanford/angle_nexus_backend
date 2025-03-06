
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
    text="""####### Company APIs #######
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

            Company Market Cap API
            Details: Retrieve the market capitalization for a specific company on any given date using the FMP Company Market Capitalization API. This API provides essential data to assess the size and value of a company in the stock market, helping users gauge its overall market standing.
            Endpoint: https://financialmodelingprep.com/stable/market-capitalization?symbol={company_symbol}
            params= {symbol}

            Batch Market Cap API
            Details: Retrieve market capitalization data for multiple companies in a single request with the FMP Batch Market Capitalization API. This API allows users to compare the market size of various companies simultaneously, streamlining the analysis of company valuations.
            Endpoint: https://financialmodelingprep.com/stable/market-capitalization-batch?symbols={company_symbol1,company_symbol2,…….,company_symboln}
            params= {symbols}
            Company Executives API
            Details: Retrieve detailed information on company executives with the FMP Company Executives API. This API provides essential data about key executives, including their name, title, compensation, and other demographic details such as gender and year of birth.
            Endpoint:
            https://financialmodelingprep.com/stable/key-executives?symbol={company_symbol}
            params= {symbol}
            Executive Compensation API
            Details: Retrieve comprehensive compensation data for company executives with the FMP Executive Compensation API. This API provides detailed information on salaries, stock awards, total compensation, and other relevant financial data, including filing details and links to official documents.
            Endpoint:https://financialmodelingprep.com/stable/governance-executive-compensation?symbol={company_symbol}

            ####### Chart APIs #######
            Basic Stock Chart API: 
            Details: Access simplified stock chart data using the FMP Basic Stock Chart API. This API provides essential charting information, including date, price, and trading volume, making it ideal for tracking stock performance with minimal data and creating basic price and volume charts.
            Endpoints: https://financialmodelingprep.com/stable/historical-price-eod/light?symbol={company_symbol} or if to and from date 
            https://financialmodelingprep.com/stable/historical-price-eod/light?symbol={company_symbol}&to={to_date}&from={from_date}
            Required params= {symbol}
            Optional params= {from, to}

            Stock Price and Volume Data API: 
            Details: Access full price and volume data for any stock symbol using the FMP Comprehensive Stock Price and Volume Data API. Get detailed insights, including open, high, low, close prices, trading volume, price changes, percentage changes, and volume-weighted average price (VWAP).
            Endpoints: https://financialmodelingprep.com/stable/historical-price-eod/full?symbol={company_symbol} or if to and from date
            https://financialmodelingprep.com/stable/historical-price-eod/full?symbol={company_symbol}&to={to_date}&from={from_date}
            Required params= {symbol}
            Optional params= {from, to}

            15 Min Interval Stock Chart API
            Details: Access stock price and volume data with the FMP 15-Minute Interval Stock Chart API. Retrieve detailed stock data in 15-minute intervals, including open, high, low, close prices, and trading volume. This API is ideal for creating intraday charts and analyzing medium-term price trends during the trading day.
            Endpoint:
            https://financialmodelingprep.com/stable/historical-chart/15min?symbol={company_symbol}
            or if to,from date, and nonadjusted=false by default
            https://financialmodelingprep.com/stable/historical-chart/15min?symbol={company_symbol}&to={to_date}&from={from_date}&
            Required params= {symbol}
            Optional params= {from, to,nonadjusted}

            ####### Statements APIs #######
            Real-Time Income Statement API: 
            Details: Access real-time income statement data for public companies, private companies, and ETFs with the FMP Real-Time Income Statements API. Track profitability, compare competitors, and identify business trends with up-to-date financial data.
            Endpoints: https://financialmodelingprep.com/stable/income-statement?symbol={company_symbol} or if limit and period (limit is number integer and period is like FY fiscal year, Q1,Q2….Q4)
            https://financialmodelingprep.com/stable/income-statement?symbol={company_symbol}&limit={user limit}&period={user period (FY/Q1/Q2/Q3/Q4)}
            Required params= {symbol}
            Optional parameter={limit, period}

            Balance Sheet Data API:
            Details:Access detailed balance sheet statements for publicly traded companies with the Balance Sheet Data API. Analyze assets, liabilities, and shareholder equity to gain insights into a company's financial health.
            Endpoint: https://financialmodelingprep.com/stable/balance-sheet-statement?symbol={company_symbol} or if limit and period (limit is number integer and period is like FY fiscal year, Q1,Q2….Q4)
            https://financialmodelingprep.com/stable/balance-sheet-statement?symbol={company_symbol}&limit={user limit}&period={user period (FY/Q1/Q2/Q3/Q4)}
            Required params= {symbol}
            Optional parameter={limit, period}


            Cash Flow Statement API:
            Details:Gain insights into a company's cash flow activities with the Cash Flow Statements API. Analyze cash generated and used from operations, investments, and financing activities to evaluate the financial health and sustainability of a business.
            Endpoint: https://financialmodelingprep.com/stable/cash-flow-statement?symbol={company_symbol} or if limit and period (limit is number integer and period is like FY fiscal year, Q1,Q2….Q4)
            https://financialmodelingprep.com/stable/cash-flow-statement?symbol={company_symbol}&limit={user limit}&period={user period (FY/Q1/Q2/Q3/Q4)}
            Required params= {symbol}
            Optional parameter={limit, period}

            Latest Financial Statements API
            Endpoint:https://financialmodelingprep.com/stable/latest-financial-statements 

            Financial Ratios API
            Details: Analyze a company's financial performance using the Financial Ratios API. This API provides detailed profitability, liquidity, and efficiency ratios, enabling users to assess a company's operational and financial health across various metrics.
            Endpoint:https://financialmodelingprep.com/stable/ratios?symbol={company_symbol} or if limit and period (limit is number integer and period is like FY fiscal year, Q1,Q2….Q4)
            https://financialmodelingprep.com/stable/ratios?symbol={company_symbol}&limit={user limit}&period={user period (FY/Q1/Q2/Q3/Q4)}
            Required params= {symbol}
            Optional parameter={limit, period}
        """
    return text

def combine_results_sys_promt():
    sys_prompt="""YYou are a highly capable assistant tasked with providing a final, comprehensive answer to the user's query by combining relevant data from the provided APIs JSON response and the user query. Follow these instructions:

        Analyze the Provided Data:

        Review the provided APIs JSON response and the user query.
        Identify which topics from the JSON response are relevant to the user's query.
        Combine and Summarize Answers:

        Extract key data and answers for each relevant topic from the JSON response.
        Combine these answers into one clear and cohesive response.
        Summarize the information so that the final answer directly addresses the user's query.
        Handling Irrelevance:

        If none of the topics in the APIs JSON response are relevant to the user's query, respond with:
        "Irrelevant - no suitable answer matches the provided query."
        Output Requirements:

        Provide the final answer in clear, concise language.
        Do not include any additional text, commentary, or metadata (such as "Data reflects annual filings as of...") at the end of the answer.
        The response must strictly be the answer based on the combined API data and the user query, with no appended follow-up questions or extra notes.
        Your goal is to generate a final, self-contained answer that directly addresses the user's query using the provided API data—without any extraneous appended information.
        """
    return sys_prompt