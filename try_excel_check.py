import pandas as pd

df_check = pd.read_excel('data/合格应收账款债权清单-龙湖ABN2021年度六期.xlsx',
                         sheet_name=0,
                         header=8)
print(df_check)

