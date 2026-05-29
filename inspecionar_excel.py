import pandas as pd

df = pd.read_excel("dados_chandon.xlsx", sheet_name="CFTV e alarme colégio", header=None)
print("Primeiras 10 linhas:")
print(df.head(10))
print("\nShape:", df.shape)
