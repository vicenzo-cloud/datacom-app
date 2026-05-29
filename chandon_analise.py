import pandas as pd
import json

# Lê o Excel corretamente
df = pd.read_excel("dados_chandon.xlsx", sheet_name="CFTV e alarme colégio", header=None)

# Dados com os índices corretos (linhas 2-4)
materiais = []
total_previsto = 0
total_real = 0

for idx in range(2, len(df)):
    quant = df.iloc[idx, 0]  # Coluna 0 = Quantidade
    equip = df.iloc[idx, 1]  # Coluna 1 = Equipamento
    marca = df.iloc[idx, 2]  # Coluna 2 = Marca
    modelo = df.iloc[idx, 3]  # Coluna 3 = Modelo
    valor_unit = df.iloc[idx, 5] if pd.notna(df.iloc[idx, 5]) else 0  # Coluna 5 = Valor Unitário
    valor_total = df.iloc[idx, 6] if pd.notna(df.iloc[idx, 6]) else 0  # Coluna 6 = Valor Total
    valor_real = df.iloc[idx, 11] if pd.notna(df.iloc[idx, 11]) else 0  # Coluna 11 = Valor Real

    if pd.notna(quant) and quant > 0:
        material = {
            "id": f"CHD-{idx-1:02d}",
            "quantidade": int(quant),
            "equipamento": str(equip),
            "marca": str(marca),
            "modelo": str(modelo),
            "valor_unitario": float(valor_unit),
            "valor_total_previsto": float(valor_total),
            "valor_total_real": float(valor_real),
            "categoria": "CFTV",
            "projeto": "Chandon",
            "status": "ativo"
        }
        materiais.append(material)
        total_previsto += float(valor_total)
        total_real += float(valor_real)

# Análises
analise = {
    "projeto": "Chandon - Câmeras Temporárias BoM",
    "data": pd.Timestamp.now().strftime("%Y-%m-%d"),
    "resumo": {
        "total_tipos": len(materiais),
        "total_unidades": sum([m['quantidade'] for m in materiais]),
        "valor_previsto": round(total_previsto, 2),
        "valor_real": round(total_real, 2),
        "diferenca": round(total_previsto - total_real, 2),
        "economia_percentual": round(((total_previsto - total_real) / total_previsto * 100), 2) if total_previsto > 0 else 0
    },
    "materiais": materiais
}

# Salva JSON
with open('chandon_materiais.json', 'w', encoding='utf-8') as f:
    json.dump(analise, f, ensure_ascii=False, indent=2)

print("Processado com sucesso!")
print(f"Total de tipos: {len(materiais)}")
print(f"Total de unidades: {sum([m['quantidade'] for m in materiais])}")
print(f"Valor previsto: R$ {total_previsto:.2f}")
print(f"Valor real: R$ {total_real:.2f}")
print(f"Economia: R$ {total_previsto - total_real:.2f}")
