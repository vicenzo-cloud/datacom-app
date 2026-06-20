# -*- coding: utf-8 -*-
"""
Relatorio mensal por categoria/fornecedor (roda dia 1, referente ao mes anterior).
Gera CSVs (UTF-8 BOM, separador ';' — abre direto no Excel pt-BR) em
Relatorios/mensal/<AAAA-MM>/<filial>.csv e um consolidado.csv
"""
import os, sys, csv, datetime
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as C


def mes_anterior(d):
    primeiro = d.replace(day=1)
    fim_ant = primeiro - datetime.timedelta(days=1)
    return fim_ant.strftime('%Y-%m')


def escrever_csv(path, linhas):
    with open(path, 'w', encoding='utf-8-sig', newline='') as fh:
        w = csv.writer(fh, delimiter=';')
        for ln in linhas:
            w.writerow(ln)


def main(ref=None):
    ref = ref or mes_anterior(datetime.date.today())
    dest = os.path.join(C.BASE_DIR, 'Relatorios', 'mensal', ref)
    os.makedirs(dest, exist_ok=True)
    consolidado = [['Filial', 'Categoria', 'Qtd notas', 'Total (R$)']]

    for f in C.carregar_filiais():
        nfs = [n for n in C.carregar_dados(f['id']).get('nfs', [])
               if (n.get('data') or '')[:7] == ref]
        if not nfs:
            continue
        por_cat = defaultdict(lambda: [0, 0.0])
        por_forn = defaultdict(lambda: [0, 0.0])
        for n in nfs:
            cat = (n.get('obs') or '(sem categoria)')
            forn = (n.get('fornecedor') or '(sem fornecedor)')
            por_cat[cat][0] += 1; por_cat[cat][1] += n.get('valor', 0)
            por_forn[forn][0] += 1; por_forn[forn][1] += n.get('valor', 0)

        linhas = [['== %s — %s ==' % (f.get('nome', f['id']), ref)], []]
        linhas.append(['POR CATEGORIA', 'Qtd', 'Total (R$)'])
        for cat, (q, v) in sorted(por_cat.items(), key=lambda x: -x[1][1]):
            linhas.append([cat, q, ('%.2f' % v).replace('.', ',')])
            consolidado.append([f.get('nome', f['id']), cat, q, ('%.2f' % v).replace('.', ',')])
        linhas += [[], ['POR FORNECEDOR', 'Qtd', 'Total (R$)']]
        for forn, (q, v) in sorted(por_forn.items(), key=lambda x: -x[1][1]):
            linhas.append([forn, q, ('%.2f' % v).replace('.', ',')])
        total = sum(n.get('valor', 0) for n in nfs)
        linhas += [[], ['TOTAL', len(nfs), ('%.2f' % total).replace('.', ',')]]

        nome_arq = ''.join(c if c.isalnum() else '_' for c in f['id']) + '.csv'
        escrever_csv(os.path.join(dest, nome_arq), linhas)

    escrever_csv(os.path.join(dest, 'consolidado.csv'), consolidado)
    print('Relatorio mensal de %s gerado em: %s' % (ref, dest))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
