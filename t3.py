from coin import Coin
import json

file_path = "config.json"

with open(file_path, "r") as json_file:
    config = json.load(json_file)

eth = Coin.create("ETHUSDT", config)

eth.klines_5m.to_csv(path_or_buf="./hallo/test.csv", index=False)