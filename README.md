# Project Daytrading

This project is based on the following youtube-trading-strategy: https://www.youtube.com/watch?v=xbAQR1e1XY8

This Trading Strategy appears to be profitable but there are not many opportunities to trade.
Thats why this bot will scan every Crypto that you wish (needs to be on Binance) every 5 minutes and checks if there is a trading opportuninity.

Incase there is an opportunity, it will send a notification to a discord server.

Different Actions:

  - Long: You should immediately go long
  - Short: You should immediately go short
  - PrecLong: The precondition is reached for a long trade, the next 5 minute candle decides wheter you should go long or not
  - PrecShort: The precondition is reached for a short trade, the next 5 minute candle decides wheter you should go short or not
