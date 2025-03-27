# Widget Map Documentation

### 1. Companies/Organization/Business Widget
**Keywords:** `companies`, `organization`, `business`  
**Widget Type:** `WidgetType.entityCardImg`  
**Response Text:**  
"Here is a brief description for the equity widget and prompt."

**Parameters:**
| Parameter         | Type    | Description                          |
|-------------------|---------|--------------------------------------|
| entityCardData    | List    | List of data objects for EntityCards |
| route             | String  | Navigation route                     |
| entityName        | String  | Display name of entity               |
| currency          | String  | Currency symbol                      |
| value             | double  | Numerical value                      |
| percentageValue   | double  | Percentage change                    |
| isProfit          | bool    | Profit/loss indicator                |
| color             | Color   | Card background color                |
| dropShadow        | bool    | Shadow visibility                    |
| hasImage          | bool    | Image display toggle                 |
| imgUrl            | String  | Image URL                            |


---

### 2. Cryptocurrency Widget
**Keywords:** `crypto`, `cryptocurrencies`, `bitcoin`, `ethereum`, `btc`  
**Widget Type:** `WidgetType.cryptoCardWidget`  
**Response Text:**  
"Here is a brief description for the equity widget and prompt."

---

### 3. CEO/Leadership Widget
**Keywords:** `ceo`, `leadership`  
**Widget Type:** `WidgetType.metricsEquity`  
**Response Text:**  
"Here is a brief description for the ceo widget and prompt."

**Parameters:**
```dart
metrics: const [],  // List of metrics
person: dummyEquityModel.profile,  // CEO profile data
description: String  // Company description
```

---

### 4. Earnings/Revenue Widget
**Keywords:** `earnings`, `revenue`  
**Widget Type:** `WidgetType.customTabs`  
**Response Text:**  
"Here is the breakdown of earnings."

**Parameters:**
```dart
annualEarnings: List  // Yearly earnings data
quaterlyEarnings: List  // Quarterly earnings data
metrics: List  // Company performance metrics
```

---

### 5. Web/Internet Widget
**Keywords:** `web`, `internet`  
**Widget Type:** `WidgetType.browserWidget`  
**Response Text:**  
"Here is a brief description for the web widget and prompt."

**Parameters:**
```dart
height: 400  // Fixed height
query: params['query']  // Search query from parameters
```

---

### 6. Document/Text Widget
**Keywords:** `document`, `text`  
**Widget Type:** `WidgetType.documentWidget`  
**Response Text:**  
"Here is a brief description for the document widget and prompt."

**Parameters:**  
`SizedBox` with fixed height of 400 containing `QuillEditorWidget`

---

### 7. Stocks/Time Series Widget
**Keywords:** `stocks`, `time series`  
**Widget Type:** `WidgetType.timeSeriesWidget`  
**Response Text:**  
"Here is a brief description for the chart widget and prompt."

**Parameters:**
```dart
chartAll: ChartData  
chart1y: ChartData  
chart6m: ChartData  
chart1w: ChartData  
chart1m: ChartData  
chart1yStepLine: ChartData  
stepLineLeastValue: double  
stepLineMaxValue: double
```

---

### 8. Balance Sheet Widget
**Keywords:** `balance sheet`, `sheet`, `balance`  
**Widget Type:** `WidgetType.balanceSheetWidget`  
**Response Text:**  
"Here is a brief description for the balance sheet widget and prompt."

**Parameters:**
```dart
benchmark: List  // Benchmark data
assets: List     // Assets data
liability: List  // Liabilities data
```

---

### 9. PDF Widget
**Keywords:** `pdf`, `doc`  
**Widget Type:** `WidgetType.pdfWidget`  
**Response Text:**  
"Here is a brief description for the pdf widget and prompt."

**Parameters:**
```dart
url: String  // PDF URL (hardcoded example shown)
```

---

## Common Dependencies
- `entityCardData`: List of data objects for entity cards
- `dummyEquityModel`: Example data source containing:
    - profile data
    - earnings data
    - chart data
    - balance sheet data
- All widgets assume existence of proper data models and helper classes
