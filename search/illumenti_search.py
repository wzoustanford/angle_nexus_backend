import nltk, re, pandas as pd, sys
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from collections import Counter 
import pdb 
from dataclasses import dataclass 
import typing as t 
import numpy as np

@dataclass
class queryStruct: 
    text = [] 
    condition = [] #field, larger than (vs smaller than), value (None means bool indicates low/high) # : t.List[t.List[t.Any]]
    location = [] #State, City (headquarter) #t.List[str]
    leadership = [] #names #: t.List[str]
    ranking = [] #field, descend (true) or ascend (false) #: t.List[t.Any]

    def reset(self):
        self.text = [] 
        self.condition = [] #field, larger than (vs smaller than), value (None means bool indicates low/high) # : t.List[t.List[t.Any]]
        self.location = [] #State, City (headquarter) #t.List[str]
        self.leadership = [] #names #: t.List[str]
        self.ranking = [] #field, descend (true) or ascend (false) #: t.List[t.Any]
        
class IllumentiSearch: 
    def __init__(self): 
        self.index = dict()
        self.dataset = None 
        self.text_fields = {
            "Symbol": "text",
            "Symbol_copy1": "text",
            "Symbol_copy2": "text",
            "Symbol_copy3": "text",
            "Symbol_copy4": "text",
            "Name": "text",
            "description__profile": "text", 
            "ceo__profile": "text", 
            "industry__profile": "text", 
            }
        self.map_from_keyword_to_field_raw = {
            "pe": "pe__quote", 
            "price earnings": "pe__quote", 
            "price earnings ratio": "pe__quote", 
            "pe ratio": "pe__quote", 
            "pe-ratio": "pe__quote", 
            "price-earnings-ratio": "pe__quote",
            "price": "price__profile",
            "growth": "growthNetIncome__income_statement_growth",
            "net income growth": "growthNetIncome__income_statement_growth",
            "earnings growth": "growthNetIncome__income_statement_growth",
            "earning growth": "growthNetIncome__income_statement_growth",
            "earn growth": "growthNetIncome__income_statement_growth",
            "revenu": "revenue__income_statement",
            "debt ratio": "derived__debtRatio",
            "risk": "derived__debtRatio",
            "market cap": "mktCap__profile",
            "market capitalization": "mktCap__profile",
            "eps": "eps__income_statement",
            "cashflow": "freeCashFlow__cash_flow_statement",
            "cash": "cashAndShortTermInvestments__balance_sheet_statement",
            "income": "netIncome__income_statement",
            "net income": "netIncome__income_statement",
            "earnings": "netIncome__income_statement",
            "profit": "netIncome__income_statement",
            "ebitda": "ebitda__income_statement",
            "EBITDA": "ebitda__income_statement",
            }
        self.tokenizer = RegexpTokenizer(r'\w+')
        self.stemmer = nltk.stem.PorterStemmer()
        self.map_from_keyword_to_field = {self.stemmer.stem(k):v for k, v in self.map_from_keyword_to_field_raw.items()}        
        """ get english stop words, remove non-alphanumeric """ 
        sws = stopwords.words('english') 
        sws = [re.sub(r'[^a-zA-Z\d\s:]', '', sw) for sw in sws] 
        self.set_sws = set()
        for sw in sws:
            self.set_sws.add(self.stemmer.stem(sw.lower())) 
    
    def load_dataset(self, nasdaq_name, nyse_name): 
        print("loading datasets .... ") 
        nasdaq_table = pd.read_csv(nasdaq_name) 
        nyse_table = pd.read_csv(nyse_name) 
        self.dataset = pd.concat([nasdaq_table, nyse_table])
        self.dataset.reset_index(inplace=True)
        for i, row in self.dataset.iterrows():
            if i > 0:
                if row['derived__debtRatio'] == '__nan__':
                    self.dataset.at[i, 'derived__debtRatio'] = 0.0
                elif type(row['derived__debtRatio']) == type(''):
                    self.dataset.at[i, 'derived__debtRatio'] = float(self.dataset.at[i, 'derived__debtRatio'])
        self.dataset['Symbol_copy1'] = self.dataset['Symbol']
        self.dataset['Symbol_copy2'] = self.dataset['Symbol']
        self.dataset['Symbol_copy3'] = self.dataset['Symbol']
        self.dataset['Symbol_copy4'] = self.dataset['Symbol']
        self.map_tickers_to_index() 
        print (self.dataset)
        
    def tokenize_all_words(self): 
        print("tokenize all words ... process rows:") 
        tokens_list = [] 
        each_field_tokens_list = {}
        for field in self.text_fields:
            each_field_tokens_list[field] = [] 
        for i in range(len(self.dataset)): 
            if i % 5 == 0: 
                sys.stdout.write(str(i) + ",")
            cur_str = "" 
            for field in self.text_fields: 
                cur_str += str(self.dataset[field][i])
                cur_str += "   " 
                each_field_tokens_list[field].append(self.tokenize_string(str(self.dataset[field][i])))
            tokens_list.append(self.tokenize_string(cur_str))
        self.dataset["tokens"] = tokens_list 
        for field in self.text_fields: 
            self.dataset[field + "_tokens"] = each_field_tokens_list[field] 
        print("\ndone") 
    
    def tokenize_string(self, string, with_rm_stopwords = True): 
        """ tokenize to only alphanumeric """ 
        tmp_tokens = self.tokenizer.tokenize(str(string)) 
        
        """ lower case and stemming """ 
        tmp_tokens = [self.stemmer.stem(t.lower()) for t in tmp_tokens] 
        
        if with_rm_stopwords: 
            """ remove stop words (already stemmed) """ 
            tokens = [] 
            for t in tmp_tokens: 
                if t not in self.set_sws: 
                    tokens.append(t)
        else:
            tokens = tmp_tokens
        
        return tokens 
    
    def map_tickers_to_index(self): 
        self.tickers_to_index_map = {} 
        for i in range(len(self.dataset)): 
            self.tickers_to_index_map[self.dataset["Symbol"][i]] = i 
    
    def compute_idf(self): 
        self.df = {} 
        self.idf = {} 
        for d in range(len(self.dataset)): 
            added_set = set()
            for token in self.dataset["tokens"][d]: 
                if token not in added_set: 
                    if token not in self.df: 
                        self.df[token] = 1
                    else: 
                        self.df[token] += 1
                    added_set.add(token)
        for token in self.df: 
            self.idf[token] = 1.0 / self.df[token] 
        #print(self.idf) 
        
    def build_index(self):
        self.tokenize_all_words()
        print("building index ... process rows:") 
        self.compute_idf() 
        for i in range(len(self.dataset)): 
            if i % 5 == 0: 
                sys.stdout.write(str(i) + ",")
            ticker = self.dataset["Symbol"][i]
            word_vec = {} 
            num_words = len(self.dataset["tokens"][i])
            if num_words == 0: 
                continue 
            
            for token in self.dataset["tokens"][i]: 
                if token not in word_vec: 
                    word_vec[token] = 1 
                else: 
                    word_vec[token] += 1 
            
            for token, tf in word_vec.items(): 
                if token not in self.index: 
                    self.index[token] = {} 
                d = self.index[token] 
                d[ticker] = 1.0 * tf / num_words * self.idf[token] 
        print("\ndone") 
        #print(self.index)
    
    def query(self, Q):
        if not Q:
            return None
        use_best_conditions = True if 'best' in Q or 'lambo' in Q else False
        use_to_the_moon_conditions = True if 'to the moon' in Q else False
        
        Q = self.screen_words(Q)
        print('after screen before tokenize')
        print(Q)
        Q = self.tokenize_string(Q, with_rm_stopwords=False)
        print('before query_understand')
        Q_dataclass = self.query_understand(Q) 
        #pdb.set_trace()
        if use_best_conditions: 
            #Q_dataclass.condition.append(['pe', False, None])
            Q_dataclass.condition.append(['growth', True, None])
            Q_dataclass.condition.append(['market cap', False, None])
        
        if use_to_the_moon_conditions: 
            Q_dataclass.condition.append(['growth', True, None]) 
            Q_dataclass.condition.append(['cash', True, None])
        
        Q_dict = {} 
        for q in Q_dataclass.text: 
            q = self.stemmer.stem(q.lower())
            if q in self.index: 
                Q_dict = dict(Counter(Q_dict) + Counter(self.index[q]))
        
        indices = [self.tickers_to_index_map[k] for k in Q_dict.keys()]
        
        for ind in indices:
            # print(f"{ind}:{self.dataset['Symbol'][ind]}:(pe){self.dataset['pe__quote'][ind]}:(pgrowth):{self.dataset[self.map_from_keyword_to_field['earnings growth']][ind]}")
            print(ind)
        new_indices = self.filter_with_query_criteria(indices, Q_dataclass) 
        
        Q_dict = {self.dataset["Symbol"][ind]:Q_dict[self.dataset["Symbol"][ind]] for ind in new_indices}
        
        sorted_Q_dict = {k: v for k, v in sorted(Q_dict.items(), key=lambda item: -1.0 * item[1])}
        cnt = 0 
        res = {} 
        for k, v in sorted_Q_dict.items():
            name = self.dataset["Name"][self.tickers_to_index_map[k]].strip()
            desc = self.dataset["description__profile"][self.tickers_to_index_map[k]]
            combined_dict = {" ":name} 
            for cond in Q_dataclass.condition:
                combined_dict[cond[0]] = "{:.1f}".format(self.dataset[self.map_from_keyword_to_field[cond[0]]][self.tickers_to_index_map[k]])
                if float(combined_dict[cond[0]]) > 1000000000:
                    combined_dict[cond[0]] = "{:.1f}".format(float(combined_dict[cond[0]]) / 1000000000.0) + " bn"
                elif float(combined_dict[cond[0]]) > 1000000:
                    combined_dict[cond[0]] = "{:.1f}".format(float(combined_dict[cond[0]]) / 1000000.0) + " mm"
            combined_dict['tf-idf score'] = "{:.5f}".format(v)
            res[k] = combined_dict
            print(f"{k}:{name}:{str(combined_dict)}")
            cnt += 1 
            #if cnt > 15: 
                #break
        return res 
    
    def screen_words(self, Q):
        Q = Q.split(" ")
        Q = [q.strip().lower() for q in Q]
        if len(Q) > 1 and Q[0] == "show" and Q[1] == "me": 
            Q = Q[2:] 
        screened_words = [
            "equity",
            "what",
            "which",
            "where",
            "stock",
            "buy",
            "best",
            "stock", 
            "companies", 
            "company", 
            "ticker", 
        ]
        Q = [w for w in Q if w and w not in screened_words] 
        Q = " ".join(Q)
        return Q 
    
    def filter_with_query_criteria(self, indices, Q_dataclass): 
        print(f"in filter with conditions, indices:")
        print(indices)
        original_indices = indices 
        #location 
        if len(Q_dataclass.location) > 0: 
            new_indices = [] 
            for i in indices: 
                if all(Q_dataclass.location[j] in self.dataset["description__profile_tokens"][i] for j in range(len(Q_dataclass.location))): 
                    new_indices.append(i)
        else: 
            new_indices = indices 
        indices = new_indices; 
        #leadership 
        if len(Q_dataclass.leadership) > 0: 
            new_indices = [] 
            for i in indices: 
                if all([Q_dataclass.leadership[j] in self.dataset["ceo__profile_tokens"][i] for j in range(len(Q_dataclass.leadership))]): 
                    new_indices.append(i) 
        else: 
            new_indices = indices 
        
        #conditions 
        if len(Q_dataclass.condition) == 0: 
            return new_indices 
        print('length of conditions:')
        print(len(Q_dataclass.condition))
        print(Q_dataclass.condition)
        
        for cond in Q_dataclass.condition: 
            indices = new_indices; new_indices = [] 
            keyword = cond[0] 
            higher = cond[1] 
            value = cond[2] 
            field = self.map_from_keyword_to_field[keyword]
            #pdb.set_trace()
            
            print(f"filtering with field {field}")
            print(f"self.dataset {self.dataset[field][indices]}")

            if not field in self.dataset.columns: 
                continue 
            if value is None: 
                if higher: 
                    thresh = self.dataset[field][indices].quantile(0.75)
                    print(f"filter with thresh {thresh}")                    
                    new_indices = [ind for ind in indices if self.dataset[field][ind] > thresh]# or np.isnan(self.dataset[field][ind])] 
                else: 
                    thresh = self.dataset[field][indices].quantile(0.25)
                    print(f"filter with thresh {thresh}")
                    print(f"indices before thresholding")
                    print(indices)
                    new_indices = [ind for ind in indices if self.dataset[field][ind] < thresh] # or np.isnan(self.dataset[field][ind])]
                    print(f"new indices after thresholding")
                    print(new_indices)
            else: 
                thresh = value
                print(f"filter with thresh {thresh}")                                    
                if higher:
                    new_indices = [ind for ind in indices if self.dataset[field][ind] > thresh] 
                else: 
                    new_indices = [ind for ind in indices if self.dataset[field][ind] < thresh]                     
        return new_indices 
    
    def query_understand(self, Q:t.List[str]):
        self.Qstruct = {}
        self.Qdataclass = queryStruct()
        self.Qdataclass.reset()
        #screen words 
        if len(Q) == 0:
            res = queryStruct()
            res.reset() 
            return 
        if len(Q) == 1:
            res = queryStruct()
            res.reset()
            print('queryStruct at initialization')
            print(res.condition)
            res.text = [Q[0]]
            return res 
        
        print('before recursive_parse')
        print(Q)        
        self.recursive_parse(Q, field = "text")
        print('before parse_into_dataclass')
        self.parse_into_dataclass(self.Qstruct)
        print("Qdataclass condition:")
        print(self.Qdataclass.condition)
        return self.Qdataclass 
        
    def recursive_parse(self, Q, field):
        print('in recursive parse')
        if len(Q) == 0: 
            return 
        for i in range(len(Q)):
            # "with" 
            # "led", "by" 
            # "in" 
            # "ranked", "by" 
            if Q[i] == "with": 
                new_field = "condition"
                pre_Q = Q[:i]
                post_Q = Q[i + 1:]
                break 
            elif Q[i] == "led" and i + 1 < len(Q) and Q[i + 1] == "by": 
                new_field = "leadership"
                pre_Q = Q[:i]
                post_Q = Q[i + 2:]
                break
            elif Q[i] == "in": 
                new_field = "location"
                pre_Q = Q[:i]
                post_Q = Q[i + 1:]
                break
            elif Q[i] == "ranked" and i + 1 < len(Q) and Q[i + 1] == "by":
                new_field = "ranking"
                pre_Q = Q[:i]
                post_Q = Q[i + 2:]
                break
            else: 
                pass
        print('field')
        print(field)
        print(Q)
        print(i)
        if i == len(Q) - 1: 
            self.Qstruct[field] = Q
        else: 
            self.Qstruct[field] = pre_Q
            self.recursive_parse(post_Q, new_field)
    
    def parse_into_dataclass(self, Qstruct):
        print(f"in parse_into_dataclass")
        print(Qstruct)
        ranking = []
        if "ranking" in Qstruct: 
            if "ascend" in Qstruct["ranking"] or "descend" in Qstruct["ranking"]: 
                #assert len(Qstruct["ranking"]) == 2, "ranked by followed by two args: field and bool_descend"
                ranking = [" ".join(Qstruct["ranking"][:-1]), False if Qstruct["ranking"][-1] == "ascend" else True]
            else: 
                #assert len(Qstruct["ranking"]) == 1, "ranked by without ascend/descend keywords only allows one word"
                ranking = [" ".join(Qstruct["ranking"]), True]
        leadership = []
        if "leadership" in Qstruct:
            leadership = [w.strip() for w in" ".join(Qstruct["leadership"]).split("and")]
        location = [] 
        if "location" in Qstruct: 
            location = Qstruct["location"]
        condition = []
        if "condition" in Qstruct:
            condition_list = " ".join(Qstruct["condition"]).split("and")
            print('condition_list')
            print(condition_list)
            for cond in condition_list: 
                #w_list = cond.split(" ") 
                low_in_cond = "low" in cond and "below" not in cond and "lower" not in cond
                high_in_cond = "high" in cond and "higher" not in cond 
                if low_in_cond: 
                    condition.append([cond.split("low")[1].strip(), False, None])
                    print(condition)
                elif high_in_cond: 
                    condition.append([cond.split("high")[1].strip(), True, None])
                else: 
                    tmp_list = None 
                    if "abov" in cond: 
                        tmp_list = [w.strip() for w in cond.split("abov")]
                        above_bool = True 
                    elif "below" in cond:
                        tmp_list = [w.strip() for w in cond.split("below")]
                        above_bool = False
                    elif "higher than" in cond: 
                        tmp_list = [w.strip() for w in cond.split("higher than")]
                        above_bool = True 
                    elif "lower than" in cond: 
                        tmp_list = [w.strip() for w in cond.split("lower than")]
                        above_bool = False 
                    if tmp_list:
                        if tmp_list[1][0] == '0' and len(tmp_list[1]) > 1 and tmp_list[1][1] == ' ':
                            tmp_list[1] = tmp_list[1].replace(' ', '.')
                        if 'million' in tmp_list[1]:
                            tmp_list[1] = tmp_list[1].replace(' million', '000000')
                            tmp_list[1] = tmp_list[1].replace(' ', '')
                        if 'billion' in tmp_list[1]:
                            tmp_list[1] = tmp_list[1].replace(' billion', '000000000')
                            tmp_list[1] = tmp_list[1].replace(' ', '')
                        condition.append([tmp_list[0], above_bool, float(tmp_list[1])])
        
        print('queryStruct dataclass initialization:')
        self.Qdataclass.text = Qstruct["text"]
        print('text')
        print(self.Qdataclass.text)
        self.Qdataclass.condition = condition
        print('condition')
        print(condition)
        print(self.Qdataclass.condition)
        self.Qdataclass.leadership = leadership
        print('leadership')
        print(leadership)
        self.Qdataclass.location = location
        print('location')
        print(location)
        self.Qdataclass.ranking = ranking
        print('ranking')
        print(ranking)
        return 
