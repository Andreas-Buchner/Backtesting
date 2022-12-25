import tiingo
import yfinance as yf
import pandas as pd

data = pd.read_csv("data/Q1_2021.csv", header=[0, 1])
adj_cl = data['Adj Close'].columns
div = data['Dividends'].columns
not_in_div = [x for x in adj_cl if x not in div]
print(not_in_div)

to_add = pd.read_csv("data/CTXS.csv")[['adjClose', 'divCash']]
print(to_add)





#df = yf.download("SNPMF", start="2021-01-01", actions=True)[['Adj Close', 'Dividends']]
#print(df)
#df.to_csv("data/SNP.csv")

#key = '9d31b307dc45132a9d8003135c3c57cff8a2ef7e'
#t_config = {'session': True, 'api_key': key}
#api = tiingo.TiingoClient(t_config)

# ERROR: PTR & SNP wrong date?
#symbol = "META"
#df = api.get_dataframe(symbol, frequency='daily', startDate="2021-01-01")
#print(df)
#df.to_csv("data/"+symbol+".csv")
