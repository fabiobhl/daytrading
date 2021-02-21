import plotly.graph_objs as go
from coin import Coin
from utils import timer

eth = Coin("ETHUSDT")

candlestick_data_5m = go.Candlestick(x=eth.klines_5m["open_time"], open=eth.klines_5m["open"], high=eth.klines_5m["high"], low=eth.klines_5m["low"], close=eth.klines_5m["close"])
ema_data = go.Scatter(x=eth.klines_5m["open_time"], y=eth.klines_5m["ema"], line=dict(color='purple', width=1))
fig_5m = go.Figure(data=[candlestick_data_5m, ema_data])
print(eth.klines_5m)
fig_5m.show()


while True:
    update = timer()
    if update == "betweenUpdate":
        eth.update_data_between()
        print(eth.buy_signal_detection())

        candlestick_data_5m = go.Candlestick(x=eth.klines_5m["open_time"], open=eth.klines_5m["open"], high=eth.klines_5m["high"], low=eth.klines_5m["low"], close=eth.klines_5m["close"])
        ema_data = go.Scatter(x=eth.klines_5m["open_time"], y=eth.klines_5m["ema"], line=dict(color='purple', width=1))
        fig_5m = go.Figure(data=[candlestick_data_5m, ema_data])
        print(eth.klines_5m)
        fig_5m.show()
        

    elif update == "fullUpdate":
        eth.update_data_full()
        print(eth.buy_signal_detection())

        candlestick_data_5m = go.Candlestick(x=eth.klines_5m["open_time"], open=eth.klines_5m["open"], high=eth.klines_5m["high"], low=eth.klines_5m["low"], close=eth.klines_5m["close"])
        ema_data = go.Scatter(x=eth.klines_5m["open_time"], y=eth.klines_5m["ema"], line=dict(color='purple', width=1))
        fig_5m = go.Figure(data=[candlestick_data_5m, ema_data])
        print(eth.klines_5m)
        fig_5m.show()
