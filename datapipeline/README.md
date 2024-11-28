#Illumenti Backend Data-pipelines

Backend data build pipeline and integration with dynamoDB

1. the code is meant to integrate with AWS data pipeline using the 'ShellCommandActivity' option 
see https://aws.amazon.com/datapipeline/
2. the backend code can be developed on an EC2 instance (tx.small) in Oregon (us-west-2), then run with Amazon Machine Image (AMI) in the data pipeline
3. the code should leverage boto3 (python SDK for AWS) to directly create and add to DynamoDB tables
see https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html

---
Dependencies:
pip install pandas
[note this dep won't exist after using boto3 with dyanmodb, install boto3 and aws cli]
[https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html]
[https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html]

---
Usage:

python3 test_build_dataset.py
[this runs 30 tickers in nasdaq and 30 tickers in nyse]

the class/function definitions are in build_dataset.py


python3 datapipeline/test_build_dataset.py -wi 2 -ns 4
python3 test_build_dataset_crypto.py -env dev


Profile page resonse

```json
// Profile Page response
var profileResponse = [
  {
    'id': 'equity_nasdaq_tsla',
    'name': 'Tesla Inc.',
    'ticker': 'TSLA',
    'logo': 'http://www.illumenti.ai/logo/nasdaq_tsla.jpg',
    'current_price': 1040.1,
    'currency': 'USD',
    '1d_change': 4.1,
    '1y_change': 613.5,
    'tags': ['Big Cap', 'Technology'],
    'price_chart': [
      {'type': '1w', 'date': '2020-11-28', 'value': 151.4},
      {'type': '1w', 'date': '2020-11-28', 'value': 151.4},
      {'type': '1m', 'date': '2020-11-28', 'value': 151.4},
      {'type': '1m', 'date': '2020-11-28', 'value': 151.4},
      {'type': '6m', 'date': '2020-11-28', 'value': 151.4},
      {'type': '6m', 'date': '2020-11-28', 'value': 151.4},
      {'type': '1y', 'date': '2020-11-28', 'value': 151.4},
      {'type': '1y', 'date': '2020-11-28', 'value': 151.4},
    ],
    'key_metrics': [
      {'tag': 'Market Cap', 'value': 104000000},
      {'tag': 'PE ratio', 'value': 52000}
    ],
    'leadership_profile': [
      {
        'image':
            'https://upload.wikimedia.org/wikipedia/commons/7/78/MS-Exec-Nadella-Satya-2017-08-31-22_%28cropped%29.jpg',
        'name': 'Satya Nadella',
        'role': 'Chairman/CEO',
        'bio':
            'Satya Narayana Nadella is an Indian-born American business executive. He is the executive chairman and CEO of Microsoft, succeeding Steve Ballmer in 2014 as CEO and John W. Thompson in 2021 as chairman.',
        'url':
            'https://www.nasdaq.com/articles/microsoft-names-ceo-satya-nadella-as-chairman-2021-06-16',
      }
    ],
    'annual_earnings': [
      {'period': '2018', 'net_profit': 60, 'revenue': 40, 'units': 'MM'},
      {'period': '2019', 'net_profit': 50, 'revenue': 50, 'units': 'MM'},
      {'period': '2020', 'net_profit': 40, 'revenue': 60, 'units': 'B'},
      {'period': '2021', 'net_profit': 30, 'revenue': 70, 'units': 'MM'},
    ],
    'quaterly_earnings': [
      {'period': 'Q1 ‘21', 'net_profit': 60, 'revenue': 40, 'units': 'B'},
      {'period': 'Q2 ‘21', 'net_profit': 50, 'revenue': 50, 'units': 'MM'},
      {'period': 'Q3 ‘21', 'net_profit': 40, 'revenue': 60, 'units': 'B'},
      {'period': 'Q4 ‘21', 'net_profit': 40, 'revenue': 60, 'units': 'MM'},
    ],
    'assets': [
      {'key': 'Cash', 'value': '45.5B'},
      {'key': 'S/T', 'value': '15.5B'},
      {'key': 'L/T', 'value': '5.5B'},
    ],
    'equity_liabilities': [
      {'key': 'Equity', 'value': '45.5B'},
      {'key': 'S/T', 'value': '15.5B'},
      {'key': 'L/T', 'value': '5.5B'},
    ],
    'benchmarks': [
      {
        'key': 'PE ratio',
        'total': 8,
        'entity_value': 3,
        'typical_value': 5,
        'type': 'days',
      },
      {
        'key': 'Debt ratio',
        'total': 100,
        'entity': 55,
        'typical_value': 15,
        'type': '%',
      },
      {
        'key': 'Daily Volume',
        'total': 100,
        'entity': 55,
        'typical_value': 15,
        'type': 'B',
      },
      {
        'key': 'News Sentiment Score',
        'total': 115,
        'entity': 55,
        'typical_value': 65,
        'type': '%',
      },
    ],
    'similar_entities': [
      {
        'name': 'NVDA',
        'value': 316.5,
        'currency': '\$',
        'is_profitable': true,
        'profit_value': 0.6
      },
      {
        'name': 'KLAC',
        'value': 86.5,
        'currency': '\$',
        'is_profitable': false,
        'profit_value': -0.6
      },
      {
        'name': 'SONY',
        'value': 316.5,
        'currency': '\$',
        'is_profitable': true,
        'profit_value': 0.6
      },
    ],
    'entity_investors': [
      {
        'name': 'Warrior Banana',
        'value': 24.5,
        'is_profitable': true,
        'growth': [
          {
            'x': 1,
            'y': 10,
          },
          {
            'x': 2,
            'y': 20,
          },
          {
            'x': 3,
            'y': 30,
          }
        ]
      },
      {
        'name': 'Moon Rocket',
        'value': 24.5,
        'is_profitable': false,
        'growth': [
          {
            'x': 1,
            'y': 5,
          },
          {
            'x': 2,
            'y': 3,
          },
          {
            'x': 3,
            'y': 1,
          }
        ]
      }
    ]
  }
];
```