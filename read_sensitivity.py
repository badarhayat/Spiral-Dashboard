import pandas as pd
path = r'c:\Users\Admin\spiral analysis attock\Spiral Plant Sheet.xlsx'
s1 = pd.read_excel(path, sheet_name='Sensitivity Analysis Spiral 1', header=1)
print(s1.columns.tolist())
print(s1.head(20).to_string())
print('unique:', s1['Condition'].unique())
