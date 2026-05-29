import pandas as pd
import json

excel_file = r"C:\Users\Gattyboni\Downloads\Orçamento_B_Print_Ceará.V2 (1).xlsx"
df = pd.read_excel(excel_file, sheet_name="B.PRINT", header=None)

# Extrai dados (linhas 1-2 têm os itens)
materiais = []

for idx in range(1, 3):  # Linhas 1 e 2
    quant = df.iloc[idx, 2]  # Coluna 2
    cat = df.iloc[idx, 3]  # Coluna 3
    equip = df.iloc[idx, 4]  # Coluna 4
    marca = df.iloc[idx, 5]  # Coluna 5
    modelo = df.iloc[idx, 6]  # Coluna 6
    valor_prev = df.iloc[idx, 9] if pd.notna(df.iloc[idx, 9]) else 0  # Coluna 9 = Total Previsto
    valor_real = df.iloc[idx, 14] if pd.notna(df.iloc[idx, 14]) else 0  # Coluna 14 = Total Real

    if pd.notna(quant) and quant > 0:
        material = {
            "id": f"CEARA-{idx}",
            "nome": str(equip),
            "categoria": str(cat),
            "marca": str(marca),
            "modelo": str(modelo),
            "quantidade": int(quant),
            "valor_previsto": float(valor_prev),
            "valor_real": float(valor_real)
        }
        materiais.append(material)

# Totais
total_previsto = sum([m['valor_previsto'] for m in materiais])
total_real = sum([m['valor_real'] for m in materiais])

analise = {
    "projeto": "Ceará - Orçamento B.PRINT",
    "data": pd.Timestamp.now().strftime("%Y-%m-%d"),
    "resumo": {
        "total_itens": len(materiais),
        "valor_previsto": round(total_previsto, 2),
        "valor_real": round(total_real, 2),
        "diferenca": round(total_previsto - total_real, 2),
        "economia_percentual": round(((total_previsto - total_real) / total_previsto * 100), 2) if total_previsto > 0 else 0
    },
    "materiais": materiais
}

# Salva JSON
with open('ceara_materiais.json', 'w', encoding='utf-8') as f:
    json.dump(analise, f, ensure_ascii=False, indent=2)

print("Processado com sucesso!")
print(f"Total de itens: {len(materiais)}")
print(f"Valor previsto: R$ {total_previsto:.2f}")
print(f"Valor real: R$ {total_real:.2f}")
print(f"Diferenca: R$ {total_previsto - total_real:.2f}")
