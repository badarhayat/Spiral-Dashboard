import pandas as pd
path = 'Spiral Plant Sheet.xlsx'
xls = pd.ExcelFile(path)
print('sheets', xls.sheet_names)
for sheet in xls.sheet_names:
    df = pd.read_excel(path, sheet_name=sheet, nrows=20)
    print('sheet', sheet)
    print(df.columns.tolist())
    print(df.head(5).to_string())
