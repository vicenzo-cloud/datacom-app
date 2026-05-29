import pandas as pd

excel_file = r"C:\Users\Gattyboni\Downloads\Orçamento_São_João_DarkStore_REV02 (2).xlsx"
df = pd.read_excel(excel_file, sheet_name="DarkStore (RFID)", header=None)

print("Analisando coluna por coluna (primeiras 15 linhas):")
for col in range(len(df.columns)):
    print(f"\nColuna {col}:")
    for row in range(min(15, len(df))):
        val = df.iloc[row, col]
        print(f"  Linha {row}: {repr(val)}")
