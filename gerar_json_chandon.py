import pandas as pd
import json

excel_file = r"dados_chandon.xlsx"
df = pd.read_excel(excel_file, sheet_name="CFTV e alarme colégio")

# Limpa dados
df = df.dropna(how='all')

# Converte para JSON
dados = {
    "projeto": "Chandon - Câmeras Temporárias BoM",
    "aba": "CFTV e alarme colégio",
    "dados": df.fillna("").to_dict(orient='records')
}

with open('dados_chandon.json', 'w', encoding='utf-8') as f:
    json.dump(dados, f, ensure_ascii=False, indent=2)

print("JSON criado: dados_chandon.json")
print(f"Total de registros: {len(dados['dados'])}")
