import pandas as pd

excel_file = r"C:\Users\Gattyboni\Downloads\Orçamento_B_Print_Ceará.V2 (1).xlsx"
xls = pd.ExcelFile(excel_file)

print("Abas disponíveis:")
print(xls.sheet_names)
print("\n" + "="*60)

for sheet in xls.sheet_names:
    df = pd.read_excel(excel_file, sheet_name=sheet)
    print(f"\nAba: {sheet}")
    print(f"Linhas: {len(df)}, Colunas: {len(df.columns)}")
    print(f"Colunas: {list(df.columns)}")
    print("\nPrimeiras linhas:")
    print(df.head(10))
    print("="*60)
