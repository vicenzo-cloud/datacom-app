# -*- coding: utf-8 -*-
"""
Backup off-machine (para o OneDrive).

Protege contra falha de disco / perda total da maquina: os dados vivem so
neste PC (o git nao versiona dados). Este script zipa o estado recuperavel
de todas as filiais e copia para o OneDrive, com retencao dos ultimos N dias.

Agendar 1x por dia no Task Scheduler (tarefa "Datacom - Backup OneDrive").
"""
import os, sys, datetime, zipfile, glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as C

# Destino no OneDrive (ajuste aqui se a pasta do OneDrive mudar).
ONEDRIVE = os.path.join(os.path.expanduser('~'), 'OneDrive')
DEST_DIR = os.path.join(ONEDRIVE, 'Backups Datacom')
RETENCAO = 60  # quantos zips diarios manter

# Arquivos na raiz do app que fazem parte do estado recuperavel.
RAIZ = ['filiais.json', 'config.json', 'atividade.db',
        'precos_mercado.json', 'fornecedores_novos.json']


def log(msg):
    linha = '[%s] %s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg)
    print(linha)
    try:
        os.makedirs(DEST_DIR, exist_ok=True)
        with open(os.path.join(DEST_DIR, '_log.txt'), 'a', encoding='utf-8') as fh:
            fh.write(linha + '\n')
    except Exception:
        pass


def coletar():
    """Lista (caminho_absoluto, nome_no_zip) de tudo que entra no backup."""
    itens = []
    for nm in RAIZ:
        p = os.path.join(C.BASE_DIR, nm)
        if os.path.exists(p):
            itens.append((p, nm))
    # dados.json de cada filial
    for p in glob.glob(os.path.join(C.FILIAIS_DIR, '*', 'dados.json')):
        rel = os.path.relpath(p, C.BASE_DIR)
        itens.append((p, rel.replace(os.sep, '/')))
    return itens


def main():
    if not os.path.isdir(ONEDRIVE):
        log('ERRO: pasta do OneDrive nao encontrada em %s — backup abortado.' % ONEDRIVE)
        sys.exit(1)
    os.makedirs(DEST_DIR, exist_ok=True)

    itens = coletar()
    if not itens:
        log('ERRO: nada para fazer backup (nenhum arquivo encontrado).')
        sys.exit(1)

    hoje = datetime.date.today().isoformat()
    destino = os.path.join(DEST_DIR, 'datacom_%s.zip' % hoje)
    tmp = destino + '.tmp'
    total = 0
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        for origem, nome in itens:
            try:
                z.write(origem, nome)
                total += 1
            except Exception as e:
                log('  falha ao adicionar %s: %s' % (nome, e))
    # troca atomica: so substitui o zip do dia depois de fechar sem erro
    if os.path.exists(destino):
        os.remove(destino)
    os.replace(tmp, destino)
    tam = os.path.getsize(destino)
    log('Backup OK: %s (%d arquivos, %.1f KB)' % (os.path.basename(destino), total, tam / 1024.0))

    # Retencao: mantem apenas os RETENCAO zips mais recentes
    zips = sorted(glob.glob(os.path.join(DEST_DIR, 'datacom_*.zip')))
    for antigo in zips[:-RETENCAO]:
        try:
            os.remove(antigo)
            log('  removido antigo: %s' % os.path.basename(antigo))
        except Exception:
            pass


if __name__ == '__main__':
    main()
