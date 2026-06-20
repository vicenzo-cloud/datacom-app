# -*- coding: utf-8 -*-
"""
Limpeza de arquivos antigos (mensal).
Regra: mantem tudo dos ultimos DIAS_MANTER dias E sempre os MIN_MANTER mais
recentes de cada pasta (rede de seguranca). Apaga o resto.
Atinge: filiais/*/Backups, _importar/*/processados, e relatorios datados.
NUNCA apaga dados.json nem os relatorios *_ultima/_ultimo.
"""
import os, sys, time, datetime, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as C

DIAS_MANTER = 90
MIN_MANTER = 5
LOG = os.path.join(C.BASE_DIR, 'Relatorios', 'limpeza_log.txt')


def log(msg):
    linha = '[%s] %s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg)
    print(linha)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as fh:
        fh.write(linha + '\n')


def limpar_pasta(pasta, padrao='*'):
    """Apaga arquivos antigos da pasta, mantendo os MIN_MANTER mais novos."""
    arqs = [p for p in glob.glob(os.path.join(pasta, padrao)) if os.path.isfile(p)]
    if not arqs:
        return 0
    arqs.sort(key=lambda p: os.path.getmtime(p), reverse=True)  # mais novo primeiro
    limite = time.time() - DIAS_MANTER * 86400
    apagados = 0
    for i, p in enumerate(arqs):
        if i < MIN_MANTER:
            continue  # sempre mantem os N mais recentes
        if os.path.getmtime(p) < limite:
            try:
                os.remove(p)
                apagados += 1
            except Exception as e:
                log('  erro ao apagar %s: %s' % (p, e))
    return apagados


def limpar_dir_recursivo(raiz):
    """Apaga subpastas antigas (ex: processados/AAAA-MM-DD_HHMMSS)."""
    import shutil
    if not os.path.isdir(raiz):
        return 0
    limite = time.time() - DIAS_MANTER * 86400
    subs = [os.path.join(raiz, d) for d in os.listdir(raiz) if os.path.isdir(os.path.join(raiz, d))]
    subs.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    apagadas = 0
    for i, d in enumerate(subs):
        if i < MIN_MANTER:
            continue
        if os.path.getmtime(d) < limite:
            try:
                shutil.rmtree(d)
                apagadas += 1
            except Exception as e:
                log('  erro ao apagar pasta %s: %s' % (d, e))
    return apagadas


def main():
    total = 0
    for f in C.carregar_filiais():
        bdir = os.path.join(C.FILIAIS_DIR, f['id'], 'Backups')
        n = limpar_pasta(bdir, '*.json')
        if n:
            log('Backups [%s]: %d apagados' % (f['id'], n))
        total += n
        # processados do importador
        proc = os.path.join(C.BASE_DIR, '_importar', f['id'], 'processados')
        m = limpar_dir_recursivo(proc)
        if m:
            log('Processados [%s]: %d pastas apagadas' % (f['id'], m))
        total += m
    # relatorios datados (mantem *_ultima/_ultimo)
    rel = os.path.join(C.BASE_DIR, 'Relatorios')
    for padrao in ('auditoria_2*.txt', 'resumo_semanal_*.txt'):
        n = limpar_pasta(rel, padrao)
        total += n
    log('Limpeza concluida. Total de itens removidos: %d' % total)


if __name__ == '__main__':
    main()
