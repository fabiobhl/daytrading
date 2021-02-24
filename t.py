from binance.client import Client
import keys
import pandas as pd
from datetime import datetime


client = Client(api_key=keys.key, api_secret=keys.secret)


while True:
    print(f"started at: {datetime.now()}")
    data = client.futures_klines(symbol="BTCUSDT", interval="5m", limit=5)
    data = pd.DataFrame(data)
    #clean the dataframe
    data = data.astype(float)
    data.drop(data.columns[[7,8,9,10,11]], axis=1, inplace=True)
    data.rename(columns = {0:'open_time', 1:'open', 2:'high', 3:'low', 4:'close', 5:'volume', 6:'close_time'}, inplace=True)

    #set the correct times
    data['close_time'] += 1
    data['close_time'] = pd.to_datetime(data['close_time'], unit='ms')
    data['open_time'] = pd.to_datetime(data['open_time'], unit='ms')
    
    print(data.iloc[-1,0])
    print(f"done at: {datetime.now()}")

    if data.iloc[-1,0].minute == 15:
        break