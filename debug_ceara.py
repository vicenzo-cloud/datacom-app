import pandas as pd

excel_file = r"C:\Users\Gattyboni\Downloads\Orçamento_B_Print_Ceará.V2 (1).xlsx"
df = pd.read_excel(excel_file, sheet_name="B.PRINT", header=None)

print("Analisando todas as linhas e colunas:")
print(f"Shape: {df.shape}")
print("\nPrimeiras 15 linhas:")
print(df.head(15))
