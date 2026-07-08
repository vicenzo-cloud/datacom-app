# -*- coding: utf-8 -*-
"""
Auditoria diaria das bases.
Gera um relatorio com:
  - Notas DUPLICADAS entre filiais (mesma nota em 2+ bases) -> numero+valor
  - Notas com valor ZERO
  - Notas SEM categoria (campo obs vazio)
  - Notas SEM fornecedor
Salva em Relatorios/auditoria_<data>.txt e Relatorios/auditoria_ultima.txt
NAO altera dados — so reporta (a remocao de duplicata e decisao do usuario).
"""
import os, sys, datetime, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as C

REL_DIR = os.path.join(C.BASE_DIR, 'Relatorios')


def chave(n):
    # mesma nota = mesmo NUMERO + mesmo FORNECEDOR
    return (str(n.get('numero', '')).strip(), C._norm(n.get('fornecedor') or ''))


def main():
    filiais = C.carregar_filiais()
    nome = {f['id']: f.get('nome', f['id']) for f in filiais}
    dados = {f['id']: C.carregar_dados(f['id']) for f in filiais}

    out = io.StringIO()
    w = out.write
    w('AUDITORIA — %s\n' % datetime.datetime.now().strftime('%d/%m/%Y %H:%M'))
    w('=' * 70 + '\n\n')

    # Resumo por filial
    w('RESUMO POR FILIAL\n')
    for f in filiais:
        nfs = dados[f['id']].get('nfs', [])
        w('  %-22s %5d notas   R$ %14.2f\n' % (nome[f['id']], len(nfs), sum(n.get('valor', 0) for n in nfs)))
    w('\n')

    # Duplicatas entre filiais
    mapa = {}
    for fid, d in dados.items():
        for n in d.get('nfs', []):
            mapa.setdefault(chave(n), set()).add(fid)
    dups = {k: v for k, v in mapa.items() if len(v) > 1}
    w('NOTAS DUPLICADAS ENTRE FILIAIS (mesma nota em 2+ bases): %d\n' % len(dups))
    for (numero, valor), fids in sorted(dups.items(), key=lambda x: -x[0][1])[:200]:
        w('  NF %-12s R$ %12.2f  ->  %s\n' % (numero, valor, ', '.join(nome[x] for x in fids)))
    if not dups:
        w('  (nenhuma — bases isoladas, OK)\n')
    w('\n')

    # Problemas por filial
    w('PENDENCIAS POR FILIAL\n')
    for f in filiais:
        nfs = dados[f['id']].get('nfs', [])
        zero = [n for n in nfs if not n.get('valor')]
        semcat = [n for n in nfs if not (n.get('obs') or '').strip()]
        semforn = [n for n in nfs if not (n.get('fornecedor') or '').strip()]
        if not nfs:
            continue
        w('  %s:\n' % nome[f['id']])
        w('     valor zero: %d | sem categoria: %d | sem fornecedor: %d\n'
          % (len(zero), len(semcat), len(semforn)))
        if semforn[:5]:
            w('     ex. sem fornecedor: %s\n' % ', '.join('NF ' + str(n.get('numero')) for n in semforn[:5]))
    w('\n')
    w('Obs.: este relatorio NAO apaga nada. Para remover duplicatas, peca ao assistente.\n')

    os.makedirs(REL_DIR, exist_ok=True)
    txt = out.getvalue()
    hoje = datetime.datetime.now().strftime('%Y-%m-%d')
    open(os.path.join(REL_DIR, 'auditoria_%s.txt' % hoje), 'w', encoding='utf-8').write(txt)
    open(os.path.join(REL_DIR, 'auditoria_ultima.txt'), 'w', encoding='utf-8').write(txt)
    print(txt)


if __name__ == '__main__':
    main()
