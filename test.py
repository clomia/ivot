from kis.get import Explorer

# sp = Stock(exchange="NAS", symbol="QQQ")

# his = sp.current_price()
# print(his)
exp = Explorer()
all_data = exp.all()
print(all_data)
