# -*- coding: utf-8 -*-
"""
Gera o relatório da BoM (Prefeitura de Gramado) a partir do conteúdo da planilha
do Google Sheets, com DIFF (antes/depois) em relação à última versão vista.

NÃO acessa o Google diretamente (isso é feito pela tarefa do Claude Code, que tem
o conector autenticado). Este script recebe o conteúdo já baixado e cuida de:
  - parsear a tabela (Previsto x Efetivo)
  - comparar com o snapshot anterior e listar o que mudou (antes -> depois)
  - gerar Relatorios/bom_gramado_<data>.txt
  - manter Relatorios/.bom_gramado_snapshot.json (linhas + modifiedTime)

Uso:
  python relatorio_bom.py <arquivo_conteudo> <modified_time>
"""
import os, sys, json, datetime
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL_DIR = os.path.join(BASE_DIR, 'Relatorios')
SNAP = os.path.join(REL_DIR, '.bom_gramado_snapshot.json')


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


def parse(txt):
    """Devolve (itens, totais, fornecedores, assinaturas_de_linha)."""
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
    ci_q = next((i for i, c in enumerate(hdr) if 'Quant' in c), None)
    ci_eq = next(i for i, c in enumerate(hdr) if 'Equipamento' in c)
    ci_ma = next((i for i, c in enumerate(hdr) if c.strip() == 'Marca'), None)
    ci_mo = next((i for i, c in enumerate(hdr) if 'Modelo' in c), None)
    ci_fo = next((i for i, c in enumerate(hdr) if 'Fornecedor' in c), None)
    i_prev = next(i for i, c in enumerate(hdr) if 'Custo Investimento Total' in c and 'Efetivo' not in c)
    i_efet = next((i for i, c in enumerate(hdr) if 'Custo Investimento Total' in c and 'Efetivo' in c), None)
    i_desp = next((i for i, c in enumerate(hdr) if 'Despesa Mensal Total' in c and 'Efetiva' not in c), None)

    def cell(r, i):
        return r[i] if (i is not None and i < len(r)) else ''

    tot_prev = tot_efet = tot_desp = 0.0
    itens = []
    forn = {}
    sigs = []
    for r in rows[hi + 1:]:
        if ci_eq >= len(r):
            continue
        eq = r[ci_eq]
        if not eq or eq.startswith('[merged]'):
            continue
        p = _brl(cell(r, i_prev)); e = _brl(cell(r, i_efet)); dm = _brl(cell(r, i_desp))
        if p == 0 and e == 0 and dm == 0:
            continue
        fo = cell(r, ci_fo)
        tot_prev += p; tot_efet += e; tot_desp += dm
        itens.append((eq, fo, p, e))
        forn[fo] = forn.get(fo, 0) + p
        # assinatura da linha (para o diff antes/depois)
        sigs.append(' | '.join([
            eq, cell(r, ci_ma), cell(r, ci_mo), fo,
            'Qtd=' + cell(r, ci_q), 'prev=' + _fmt(p), 'efet=' + _fmt(e), 'despM=' + _fmt(dm)
        ]))
    itens.sort(key=lambda x: -x[2])
    return itens, (tot_prev, tot_efet, tot_desp), forn, sigs


def _key(sig):
    # chave = Equipamento | Marca | Modelo (3 primeiros campos)
    return ' | '.join(sig.split(' | ')[:3])


def bloco_diff(prev_sigs, cur_sigs, prev_ts):
    """Monta a seção 'antes -> depois'."""
    L = ['ALTERAÇÕES DESDE A ÚLTIMA VERSÃO' + (' (base de ' + prev_ts + ')' if prev_ts else '')]
    if prev_sigs is None:
        L.append('  (primeira versão registrada — as alterações futuras aparecerão aqui)')
        return L
    prev_set, cur_set = set(prev_sigs), set(cur_sigs)
    removed = [s for s in prev_sigs if s not in cur_set]
    added = [s for s in cur_sigs if s not in prev_set]
    if not removed and not added:
        L.append('  (sem alterações de conteúdo desde a última versão)')
        return L
    rem_by, add_by = defaultdict(list), defaultdict(list)
    for s in removed:
        rem_by[_key(s)].append(s)
    for s in added:
        add_by[_key(s)].append(s)
    alterados, removidos, novos = [], [], []
    for k in set(list(rem_by) + list(add_by)):
        r, a = rem_by[k], add_by[k]
        n = min(len(r), len(a))
        for i in range(n):
            alterados.append((r[i], a[i]))
        removidos += r[n:]
        novos += a[n:]
    if alterados:
        L.append('  ITENS ALTERADOS: %d' % len(alterados))
        for antes, depois in alterados[:40]:
            L.append('   • ' + _key(antes))
            L.append('       antes:  ' + antes.split(' | ', 3)[3])
            L.append('       depois: ' + depois.split(' | ', 3)[3])
    if novos:
        L.append('  ITENS NOVOS: %d' % len(novos))
        for s in novos[:40]:
            L.append('   + ' + s)
    if removidos:
        L.append('  ITENS REMOVIDOS: %d' % len(removidos))
        for s in removidos[:40]:
            L.append('   - ' + s)
    return L


def main():
    if len(sys.argv) < 3:
        print('uso: relatorio_bom.py <arquivo_conteudo> <modified_time>')
        sys.exit(2)
    caminho, mtime = sys.argv[1], sys.argv[2]
    txt = carregar_conteudo(caminho)
    itens, (tot_prev, tot_efet, tot_desp), forn, sigs = parse(txt)

    # snapshot anterior (para o diff)
    prev_sigs, prev_ts = None, ''
    if os.path.exists(SNAP):
        try:
            snap = json.load(open(SNAP, encoding='utf-8'))
            prev_sigs = snap.get('sigs')
            prev_ts = snap.get('savedAt', '')
        except Exception:
            prev_sigs = None

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
    L += bloco_diff(prev_sigs, sigs, prev_ts)
    L.append('')
    L.append('TOP 12 ITENS POR CUSTO PREVISTO')
    for eq, fo, p, e in itens[:12]:
        L.append('  %-42s prev %14s' % (eq[:42], _fmt(p)))
    L.append('')
    L.append('TOP 8 FORNECEDORES/ORIGEM (por previsto)')
    for fo, v in sorted(forn.items(), key=lambda x: -x[1])[:8]:
        if fo:
            L.append('  %-30s %16s' % (fo[:30], _fmt(v)))
    rep = '\n'.join(L)

    os.makedirs(REL_DIR, exist_ok=True)
    hoje = datetime.date.today().isoformat()
    destino = os.path.join(REL_DIR, 'bom_gramado_%s.txt' % hoje)
    open(destino, 'w', encoding='utf-8-sig').write(rep)
    # salva o novo snapshot (vira o "antes" da próxima vez)
    json.dump({'modifiedTime': mtime, 'savedAt': datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), 'sigs': sigs},
              open(SNAP, 'w', encoding='utf-8'), ensure_ascii=False)
    print('Relatorio gerado: %s' % os.path.basename(destino))
    print(rep)


if __name__ == '__main__':
    main()
