import pandas as pd
import json

# Le o Excel do Chandon
excel_file = r"dados_chandon.xlsx"
df = pd.read_excel(excel_file, sheet_name="CFTV e alarme colégio")

# Limpa
df = df.dropna(how='all')
df = df.fillna("")

# Cria estrutura de materiais
materiais = []
for idx, row in df.iterrows():
    material = {
        "id": f"CHD-{idx+1}",
        "nome": str(row.get('VALORES PREVISTOS', f'Item {idx+1}')),
        "quantidade": int(row.get('Unnamed: 1', 0)) if pd.notna(row.get('Unnamed: 1')) else 0,
        "preco_unitario": float(row.get('Unnamed: 2', 0)) if pd.notna(row.get('Unnamed: 2')) else 0,
        "descricao": "Chandon - Câmeras Temporárias",
        "categoria": "CFTV",
        "status": "ativo",
        "projeto": "Chandon"
    }
    materiais.append(material)

# Calcula totalizadores
total_quantidade = sum([m['quantidade'] for m in materiais])
total_valor = sum([m['quantidade'] * m['preco_unitario'] for m in materiais])

analise = {
    "projeto": "Chandon - Câmeras Temporárias BoM",
    "data_analise": pd.Timestamp.now().strftime("%Y-%m-%d"),
    "total_itens": len(materiais),
    "total_quantidade": total_quantidade,
    "total_valor_previsto": round(total_valor, 2),
    "valor_medio_item": round(total_valor / len(materiais), 2) if materiais else 0,
    "materiais": materiais
}

# Salva JSON
with open('chandon_materiais.json', 'w', encoding='utf-8') as f:
    json.dump(analise, f, ensure_ascii=False, indent=2)

print("Arquivo criado: chandon_materiais.json")
print(f"Total de itens: {len(materiais)}")
print(f"Valor total previsto: R$ {total_valor:.2f}")
