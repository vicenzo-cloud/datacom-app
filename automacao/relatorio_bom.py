# -*- coding: utf-8 -*-
"""
Gera o relatório da BoM (Prefeitura de Gramado) a partir do conteúdo da planilha
do Google Sheets.

NÃO acessa o Google diretamente (isso é feito pela tarefa do Claude Code, que tem
o conector autenticado). Este script recebe o conteúdo já baixado e cuida de:
  - parsear a tabela (Previsto x Efetivo)
  - gerar Relatorios/bom_gramado_<data>.txt
  - manter Relatorios/.bom_gramado_state.json (último modifiedTime visto)

Uso:
  python relatorio_bom.py <arquivo_conteudo> <modified_time>
    <arquivo_conteudo>: caminho de um arquivo com o conteúdo da planilha. Pode ser
                        o JSON {"fileContent": "..."} do conector OU o texto cru.
    <modified_time>:    o modifiedTime atual da planilha (string), guardado no state.
"""
import os, sys, json, datetime, glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL_DIR = os.path.join(BASE_DIR, 'Relatorios')
STATE = os.path.join(REL_DIR, '.bom_gramado_state.json')


def _brl(s):
    s = (s or '').replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(s)
    except Exception:
        return 0.0


def _fmt(v):
    return 'R$ ' + ('{:,.2f}'.format(v).replace(',', 'X').replace('.', ',').replace('X', '.'))


def carregar_conteudo(caminho):
    raw = open(caminho, encoding='utf-8').read()
    try:
        j = json.loads(raw)
        if isinstance(j, dict) and 'fileContent' in j:
            return j['fileContent']
    except Exception:
        pass
    return raw


def gerar_relatorio(txt):
    rows = []
    for ln in txt.splitlines():
        if '|' not in ln:
            continue
        c = [x.strip() for x in ln.split('|')]
        if c and c[0] == '':
            c = c[1:]
        if c and c[-1] == '':
            c = c[:-1]
        rows.append(c)
    hi = next((i for i, r in enumerate(rows)
               if any('Quant' in x for x in r) and any('Equipamento' in x for x in r)), None)
    if hi is None:
        raise ValueError('cabeçalho da BoM não encontrado no conteúdo')
    hdr = rows[hi]
    ci_equip = next(i for i, c in enumerate(hdr) if 'Equipamento' in c)
    ci_forn = next((i for i, c in enumerate(hdr) if 'Fornecedor' in c), None)
    i_prev = next(i for i, c in enumerate(hdr) if 'Custo Investimento Total' in c and 'Efetivo' not in c)
    i_efet = next((i for i, c in enumerate(hdr) if 'Custo Investimento Total' in c and 'Efetivo' in c), None)
    i_desp = next((i for i, c in enumerate(hdr) if 'Despesa Mensal Total' in c and 'Efetiva' not in c), None)

    tot_prev = tot_efet = tot_desp = 0.0
    itens = []
    forn = {}
    for r in rows[hi + 1:]:
        if ci_equip >= len(r):
            continue
        eq = r[ci_equip]
        if not eq or eq.startswith('[merged]'):
            continue
        p = _brl(r[i_prev]) if i_prev < len(r) else 0
        e = _brl(r[i_efet]) if (i_efet is not None and i_efet < len(r)) else 0
        dm = _brl(r[i_desp]) if (i_desp is not None and i_desp < len(r)) else 0
        if p == 0 and e == 0 and dm == 0:
            continue
        fo = r[ci_forn] if (ci_forn is not None and ci_forn < len(r)) else ''
        tot_prev += p; tot_efet += e; tot_desp += dm
        itens.append((eq, fo, p, e))
        forn[fo] = forn.get(fo, 0) + p
    itens.sort(key=lambda x: -x[2])

    L = []
    L.append('RELATORIO BoM — PREFEITURA DE GRAMADO')
    L.append('Gerado em: ' + datetime.datetime.now().strftime('%d/%m/%Y %H:%M') + '  (fonte: Google Sheets)')
    L.append('=' * 64)
    L.append('')
    L.append('RESUMO')
    L.append('  Linhas com valor:            %d' % len(itens))
    L.append('  Total PREVISTO (investim.):  ' + _fmt(tot_prev))
    L.append('  Total EFETIVO (ja gasto):    ' + _fmt(tot_efet))
    L.append('  %% executado do orcamento:    %.1f%%' % (100 * tot_efet / tot_prev if tot_prev else 0))
    L.append('  Despesa mensal prevista:     ' + _fmt(tot_desp))
    L.append('')
    L.append('TOP 12 ITENS POR CUSTO PREVISTO')
    for eq, fo, p, e in itens[:12]:
        L.append('  %-42s prev %14s' % (eq[:42], _fmt(p)))
    L.append('')
    L.append('TOP 8 FORNECEDORES/ORIGEM (por previsto)')
    for fo, v in sorted(forn.items(), key=lambda x: -x[1])[:8]:
        if fo:
            L.append('  %-30s %16s' % (fo[:30], _fmt(v)))
    return '\n'.join(L)


def main():
    if len(sys.argv) < 3:
        print('uso: relatorio_bom.py <arquivo_conteudo> <modified_time>')
        sys.exit(2)
    caminho, mtime = sys.argv[1], sys.argv[2]
    txt = carregar_conteudo(caminho)
    rep = gerar_relatorio(txt)

    os.makedirs(REL_DIR, exist_ok=True)
    hoje = datetime.date.today().isoformat()
    destino = os.path.join(REL_DIR, 'bom_gramado_%s.txt' % hoje)
    open(destino, 'w', encoding='utf-8-sig').write(rep)
    json.dump({'modifiedTime': mtime, 'generatedAt': datetime.datetime.now().isoformat(timespec='seconds')},
              open(STATE, 'w', encoding='utf-8'))
    print('Relatorio gerado: %s' % os.path.basename(destino))
    print(rep)


if __name__ == '__main__':
    main()
