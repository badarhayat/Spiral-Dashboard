import pandas as pd
path = 'Spiral Plant Sheet.xlsx'
with open('inspect_output.txt', 'w', encoding='utf-8') as f:
    xls = pd.ExcelFile(path)
    f.write(f'sheets: {xls.sheet_names}\n')
    for sheet in xls.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)
        f.write(f'\nsheet: {sheet}\n')
        f.write(f'columns: {df.columns.tolist()}\n')
        f.write(df.head(10).to_string() + '\n')
