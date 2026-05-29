import pandas as pd

df = pd.read_excel("dados_chandon.xlsx", sheet_name="CFTV e alarme colégio", header=None)

print("Analisando colunas:")
for col in range(len(df.columns)):
    print(f"\nColuna {col}:")
    for row in range(min(5, len(df))):
        val = df.iloc[row, col]
        print(f"  Linha {row}: {repr(val)} (tipo: {type(val).__name__})")
