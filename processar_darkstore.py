import pandas as pd
import json

excel_file = r"C:\Users\Gattyboni\Downloads\Orçamento_São_João_DarkStore_REV02 (2).xlsx"
df = pd.read_excel(excel_file, sheet_name="DarkStore (RFID)", header=None)

materiais = []

# Dados começam na linha 2 (índice 2)
for idx in range(2, len(df)):
    quant = df.iloc[idx, 2]  # Coluna 2 = Quantidade
    equipamento = df.iloc[idx, 3]  # Coluna 3 = Equipamento
    marca = df.iloc[idx, 4]  # Coluna 4 = Marca
    modelo = df.iloc[idx, 5]  # Coluna 5 = Modelo
    valor_unit_prev = df.iloc[idx, 6]  # Coluna 6 = Valor unitário previsto
    valor_total_prev = df.iloc[idx, 7]  # Coluna 7 = Valor total previsto
    valor_unit_real = df.iloc[idx, 9]  # Coluna 9 = Valor unitário real
    valor_total_real = df.iloc[idx, 10]  # Coluna 10 = Valor total real

    if pd.notna(quant) and quant > 0 and pd.notna(equipamento):
        material = {
            "id": f"DARKSTORE-{idx}",
            "nome": str(equipamento),
            "marca": str(marca) if pd.notna(marca) else "",
            "modelo": str(modelo) if pd.notna(modelo) else "",
            "quantidade": int(quant),
            "valor_previsto": float(valor_total_prev) if pd.notna(valor_total_prev) else 0,
            "valor_real": float(valor_total_real) if pd.notna(valor_total_real) else 0
        }
        materiais.append(material)

# Totais
total_previsto = sum([m['valor_previsto'] for m in materiais])
total_real = sum([m['valor_real'] for m in materiais])
diferenca = total_previsto - total_real
economia_pct = ((diferenca / total_previsto * 100) if total_previsto > 0 else 0)

analise = {
    "projeto": "DarkStore - São João RFID",
    "data": pd.Timestamp.now().strftime("%Y-%m-%d"),
    "resumo": {
        "total_itens": len(materiais),
        "valor_previsto": round(total_previsto, 2),
        "valor_real": round(total_real, 2),
        "diferenca": round(diferenca, 2),
        "economia_percentual": round(economia_pct, 2)
    },
    "materiais": materiais
}

with open('darkstore_materiais.json', 'w', encoding='utf-8') as f:
    json.dump(analise, f, ensure_ascii=False, indent=2)

print("Processado com sucesso!")
print(f"Total de itens: {len(materiais)}")
print(f"Valor previsto: R$ {total_previsto:.2f}")
print(f"Valor real: R$ {total_real:.2f}")
print(f"Diferença: R$ {diferenca:.2f}")
print(f"Economia percentual: {economia_pct:.2f}%")
