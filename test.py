import requests
import pandas as pd
url = 'http://stock2.finance.sina.com.cn/futures/api/json.php/IndexService.getInnerFuturesMiniKLine5m?symbol=AU0'
# 提数据
raw = requests.get(url)
# 转为json
json = raw.json()
# 转为DataFrame
df_data = pd.DataFrame(json, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
df_data['open'] = df_data['close'].astype(float)
df_data['high'] = df_data['close'].astype(float)
df_data['low'] = df_data['close'].astype(float)
df_data['close'] = df_data['close'].astype(float)

df_data.to_excel('xxx.xlsx')
