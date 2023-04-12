from kis.get import StockPrice, Explorer

# sp = StockPrice(exchange="NAS", symbol="QQQ")

# his = sp.current_price()
# print(his)
exp = Explorer()
r = exp.market_capitalization(1, 2)
print(r)
print(len(r))
