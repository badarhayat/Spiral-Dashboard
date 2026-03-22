import pandas as pd
path='Spiral Plant Sheet.xlsx'
df=pd.read_excel(path, sheet_name='Spiral Data on Actual Run', header=1)
print(df.columns.tolist())
print(df.head(8).to_string())
