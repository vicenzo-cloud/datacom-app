import pandas as pd

excel_file = r"C:\Users\Gattyboni\Downloads\Orçamento_B_Print_Ceará.V2 (1).xlsx"
df = pd.read_excel(excel_file, sheet_name="B.PRINT", header=None)

print("Analisando coluna por coluna:")
for col in range(len(df.columns)):
    print(f"\nColuna {col}:")
    for row in range(len(df)):
        val = df.iloc[row, col]
        print(f"  Linha {row}: {repr(val)}")
