import pandas as pd
import json

# Lê o Excel sem headers automaticos
df = pd.read_excel("dados_chandon.xlsx", sheet_name="CFTV e alarme colégio", header=None)

# Extrai dados (linhas 2-4 têm os valores numéricos)
dados_valores = []
for idx in range(2, len(df)):
    quant = df.iloc[idx, 1]  # Coluna 1 = Quantidade
    if pd.notna(quant) and quant != 0:
        dados_valores.append({
            'quantidade': int(quant),
            'indice': idx - 1
        })

# Cria materiais do projeto Chandon
materiais = []
for i, item in enumerate(dados_valores):
    material = {
        "id": f"CHD-CAM-{i+1:03d}",
        "nome": f"Câmera/Equipamento CFTV {i+1}",
        "quantidade": item['quantidade'],
        "preco_unitario": 0.0,  # Sem informação de preço no Excel
        "descricao": "Projeto Chandon - CFTV e Alarme Colégio",
        "categoria": "CFTV",
        "status": "ativo",
        "projeto": "Chandon"
    }
    materiais.append(material)

# Análises
total_quantidade = sum([m['quantidade'] for m in materiais])

analise = {
    "projeto": "Chandon - Câmeras Temporárias BoM",
    "categoria": "CFTV e Alarme Colégio",
    "data_processamento": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
    "resumo": {
        "total_tipos_equipamento": len(materiais),
        "quantidade_total": total_quantidade,
        "quantidade_media": round(total_quantidade / len(materiais), 1) if materiais else 0
    },
    "equipamentos": materiais
}

# Salva JSON
with open('chandon_materiais.json', 'w', encoding='utf-8') as f:
    json.dump(analise, f, ensure_ascii=False, indent=2)

print("Arquivo criado: chandon_materiais.json")
print(f"Total de tipos de equipamento: {len(materiais)}")
print(f"Quantidade total: {total_quantidade}")
