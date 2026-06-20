# -*- coding: utf-8 -*-
"""
Resumo gerencial semanal (Python puro, sem IA).
Por filial: total, qtd notas, mes atual vs mes anterior, top fornecedores,
e as maiores notas. Salva em Relatorios/resumo_semanal_<data>.txt e resumo_ultimo.txt
"""
import os, sys, datetime, io
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as C

REL_DIR = os.path.join(C.BASE_DIR, 'Relatorios')


def brl(v):
    return ('R$ %0.2f' % (v or 0)).replace(',', 'X').replace('.', ',').replace('X', '.')


def mes_ant(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    m -= 1
    if m == 0:
        y, m = y - 1, 12
    return '%04d-%02d' % (y, m)


def main():
    filiais = C.carregar_filiais()
    hoje = datetime.date.today()
    ym_atual = hoje.strftime('%Y-%m')
    ym_prev = mes_ant(ym_atual)

    out = io.StringIO()
    w = out.write
    w('RESUMO GERENCIAL — semana de %s\n' % hoje.strftime('%d/%m/%Y'))
    w('=' * 70 + '\n\n')

    geral = 0.0
    for f in filiais:
        nfs = C.carregar_dados(f['id']).get('nfs', [])
        if not nfs:
            continue
        total = sum(n.get('valor', 0) for n in nfs)
        geral += total
        por_mes = defaultdict(float)
        forn = defaultdict(float)
        for n in nfs:
            ym = (n.get('data') or '')[:7]
            if ym:
                por_mes[ym] += n.get('valor', 0)
            forn[(n.get('fornecedor') or '—')] += n.get('valor', 0)
        atual, prev = por_mes.get(ym_atual, 0), por_mes.get(ym_prev, 0)
        var = ((atual - prev) / prev * 100) if prev else 0

        w('%s\n' % f.get('nome', f['id']))
        w('  Total acumulado: %s  (%d notas)\n' % (brl(total), len(nfs)))
        w('  %s: %s   |   %s: %s   (%+.0f%%)\n' % (ym_atual, brl(atual), ym_prev, brl(prev), var))
        top = sorted(forn.items(), key=lambda x: -x[1])[:5]
        w('  Top fornecedores:\n')
        for nome, v in top:
            w('     - %-44s %s\n' % (nome[:44], brl(v)))
        maiores = sorted(nfs, key=lambda n: -(n.get('valor') or 0))[:3]
        w('  Maiores notas:\n')
        for n in maiores:
            w('     - NF %-10s %s  (%s)\n' % (n.get('numero'), brl(n.get('valor')), n.get('data')))
        w('\n')

    w('-' * 70 + '\n')
    w('TOTAL GERAL (todas as filiais): %s\n' % brl(geral))

    os.makedirs(REL_DIR, exist_ok=True)
    txt = out.getvalue()
    open(os.path.join(REL_DIR, 'resumo_semanal_%s.txt' % hoje.strftime('%Y-%m-%d')), 'w', encoding='utf-8').write(txt)
    open(os.path.join(REL_DIR, 'resumo_ultimo.txt'), 'w', encoding='utf-8').write(txt)
    print(txt)


if __name__ == '__main__':
    main()
