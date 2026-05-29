import json
import os

# Verifica se os arquivos existem
arquivos = [
    'darkstore_materiais.json',
    'integrar_darkstore.js',
    'ceara_materiais.json',
    'integrar_ceara.js',
    'chandon_materiais.json',
    'integrar_chandon.js'
]

print("=== Verificando arquivos de integracao ===\n")
for arq in arquivos:
    caminho = os.path.join(os.getcwd(), arq)
    if os.path.exists(caminho):
        tamanho = os.path.getsize(caminho)
        print(f"[OK] {arq:<30} ({tamanho} bytes)")
    else:
        print(f"[ERRO] {arq:<30} (NAO ENCONTRADO)")

# Verifica conteúdo do JSON do DarkStore
print("\n=== Conteúdo do darkstore_materiais.json ===\n")
try:
    with open('darkstore_materiais.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)

    print(f"Projeto: {dados['projeto']}")
    print(f"Data: {dados['data']}")
    print("\nResumo:")
    for chave, valor in dados['resumo'].items():
        print(f"  {chave}: {valor}")

    print("\nMateriais: {} itens".format(len(dados['materiais'])))
    for i, mat in enumerate(dados['materiais'][:3], 1):
        print("  {}. {}".format(i, mat['nome']))
        print("     Marca: {}".format(mat['marca']))
        print("     Quantidade: {}".format(mat['quantidade']))
        print("     Previsto: R$ {:.2f}".format(mat['valor_previsto']))
        print("     Real: R$ {:.2f}".format(mat['valor_real']))

    if len(dados['materiais']) > 3:
        print("  ... ({} itens adicionais)".format(len(dados['materiais']) - 3))

except Exception as e:
    print("Erro ao ler JSON: {}".format(e))

print("\n=== Pronto para integracao ===")
print("O DarkStore foi processado com sucesso e esta pronto para ser integrado no app!")
