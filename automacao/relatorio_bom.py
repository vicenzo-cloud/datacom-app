# -*- coding: utf-8 -*-
"""
Gera o relatório de uma BoM (planilha de projeto) a partir do conteúdo baixado
do Google Sheets, com DIFF (antes/depois) em relação à última versão vista.

NÃO acessa o Google diretamente (isso é feito pela tarefa do Claude Code, que tem
o conector autenticado). Este script recebe o conteúdo já baixado e cuida de:
  - parsear a tabela (Previsto x Efetivo)
  - comparar com o snapshot anterior e listar o que mudou (antes -> depois)
  - gerar Relatorios/bom_<slug>_<data>.txt
  - manter Relatorios/.bom_<slug>_snapshot.json (itens + modifiedTime)

Cada planilha de projeto (BoM) tem seu próprio slug, para não sobrescrever o
relatório/snapshot de outro projeto.

Uso:
  python relatorio_bom.py <arquivo_conteudo> <modified_time> [slug] [titulo]
"""
import os, sys, json, datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL_DIR = os.path.join(BASE_DIR, 'Relatorios')


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
    """Devolve (itens_ordenados, totais, itens_por_chave)."""
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
    porchave = {}
    ocorrencias = {}
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
        item = {'eq': eq, 'marca': cell(r, ci_ma), 'modelo': cell(r, ci_mo), 'fornecedor': fo,
                'qtd': cell(r, ci_q), 'prev': p, 'efet': e, 'desp': dm}
        itens.append(item)
        # linhas com o mesmo equipamento/marca/modelo/fornecedor são itens distintos
        # (ex.: mesma câmera comprada em fases diferentes do projeto) — não podem
        # se sobrescrever no dicionário, por isso a numeração de ocorrência (#2, #3, ...).
        base = ' | '.join([eq, cell(r, ci_ma), cell(r, ci_mo), fo])
        ocorrencias[base] = ocorrencias.get(base, 0) + 1
        n = ocorrencias[base]
        chave = base if n == 1 else base + ' #%d' % n
        porchave[chave] = item
    itens.sort(key=lambda x: -x['prev'])
    return itens, (tot_prev, tot_efet, tot_desp), porchave


def _rotulo(chave, item):
    partes = [item['eq']]
    if item['fornecedor']:
        partes.append('(' + item['fornecedor'] + ')')
    return ' '.join(partes)


def _linha_item(item, so_previsto=False):
    partes = ['previsto ' + _fmt(item['prev'])]
    if not so_previsto and item['efet']:
        partes.append('efetivo ' + _fmt(item['efet']))
    if item['desp']:
        partes.append('desp.mensal ' + _fmt(item['desp']))
    return ', '.join(partes)


def bloco_mudancas(prev_itens, cur_itens, prev_ts):
    """Lista o que mudou, item por item, em linguagem direta."""
    L = []
    if prev_itens is None:
        if not cur_itens:
            L.append('PRIMEIRO REGISTRO — planilha sem itens com valor ainda.')
        elif len(cur_itens) <= 20:
            L.append('ITENS DESTA VERSÃO (primeiro registro — mudanças futuras aparecerão aqui):')
            for chave, item in cur_itens.items():
                L.append('  • ' + _rotulo(chave, item) + ' — ' + _linha_item(item))
        else:
            L.append('PRIMEIRO REGISTRO: %d itens com valor (lista grande demais para exibir aqui — mudanças futuras aparecerão item a item).' % len(cur_itens))
        return L

    L.append('MUDANÇAS DESDE ' + (prev_ts or 'A ÚLTIMA VERSÃO'))
    chaves_prev, chaves_cur = set(prev_itens), set(cur_itens)
    alterados = [k for k in (chaves_prev & chaves_cur)
                 if (prev_itens[k]['prev'], prev_itens[k]['efet'], prev_itens[k]['desp'], prev_itens[k]['qtd'])
                 != (cur_itens[k]['prev'], cur_itens[k]['efet'], cur_itens[k]['desp'], cur_itens[k]['qtd'])]
    novos = [k for k in chaves_cur - chaves_prev]
    removidos = [k for k in chaves_prev - chaves_cur]

    if not alterados and not novos and not removidos:
        L.append('  (nada mudou)')
        return L

    for k in alterados:
        antes, depois = prev_itens[k], cur_itens[k]
        L.append('  • ' + _rotulo(k, depois))
        if antes['qtd'] != depois['qtd']:
            L.append('      quantidade: %s → %s' % (antes['qtd'] or '-', depois['qtd'] or '-'))
        if antes['prev'] != depois['prev']:
            L.append('      previsto:   %s → %s' % (_fmt(antes['prev']), _fmt(depois['prev'])))
        if antes['efet'] != depois['efet']:
            L.append('      efetivo:    %s → %s' % (_fmt(antes['efet']), _fmt(depois['efet'])))
        if antes['desp'] != depois['desp']:
            L.append('      desp.mensal: %s → %s' % (_fmt(antes['desp']), _fmt(depois['desp'])))
    for k in novos:
        L.append('  + ' + _rotulo(k, cur_itens[k]) + ' — ' + _linha_item(cur_itens[k]))
    for k in removidos:
        L.append('  − ' + _rotulo(k, prev_itens[k]) + ' (estava: ' + _linha_item(prev_itens[k]) + ')')
    return L


def main():
    if len(sys.argv) < 3:
        print('uso: relatorio_bom.py <arquivo_conteudo> <modified_time> [slug] [titulo]')
        sys.exit(2)
    caminho, mtime = sys.argv[1], sys.argv[2]
    slug = sys.argv[3] if len(sys.argv) > 3 else 'gramado'
    titulo = sys.argv[4] if len(sys.argv) > 4 else 'PREFEITURA DE GRAMADO'
    snap = os.path.join(REL_DIR, '.bom_%s_snapshot.json' % slug)
    txt = carregar_conteudo(caminho)
    itens, (tot_prev, tot_efet, tot_desp), porchave = parse(txt)

    # snapshot anterior (para o diff) — só entende o formato novo (itens_por_chave);
    # um snapshot no formato antigo (sigs) é tratado como "sem histórico" uma vez.
    prev_itens, prev_ts = None, ''
    if os.path.exists(snap):
        try:
            snap_j = json.load(open(snap, encoding='utf-8'))
            prev_itens = snap_j.get('itens')
            prev_ts = snap_j.get('savedAt', '')
        except Exception:
            prev_itens = None

    L = []
    L.append('RELATORIO BoM — ' + titulo.upper())
    L.append('Gerado em: ' + datetime.datetime.now().strftime('%d/%m/%Y %H:%M') + '  (fonte: Google Sheets)')
    L.append('Total previsto: %s   |   Total efetivo: %s (%.1f%% executado)' %
              (_fmt(tot_prev), _fmt(tot_efet), (100 * tot_efet / tot_prev if tot_prev else 0)))
    L.append('=' * 64)
    L.append('')
    L += bloco_mudancas(prev_itens, porchave, prev_ts)
    rep = '\n'.join(L)

    os.makedirs(REL_DIR, exist_ok=True)
    hoje = datetime.date.today().isoformat()
    destino = os.path.join(REL_DIR, 'bom_%s_%s.txt' % (slug, hoje))
    open(destino, 'w', encoding='utf-8-sig').write(rep)
    # salva o novo snapshot (vira o "antes" da próxima vez)
    json.dump({'modifiedTime': mtime, 'savedAt': datetime.datetime.now().strftime('%d/%m/%Y %H:%M'), 'itens': porchave},
              open(snap, 'w', encoding='utf-8'), ensure_ascii=False)
    print('Relatorio gerado: %s' % os.path.basename(destino))
    print(rep)


if __name__ == '__main__':
    main()
