#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera analise_por_unidade.json cruzando:
- RelatorioListagemEntradaMercadoria (detalhada): item + qtd + preco por nota
- RelatorioListagemEntradaMercadoriaResumida: nota -> unidade de negocio
Casa pelo numero da nota. Agrupa consumo/preco por (unidade, item).
"""
import re, json, statistics
from pathlib import Path
from collections import defaultdict

DOWNLOADS = Path.home() / 'Downloads'
SAIDA = Path(__file__).parent / 'analise_por_unidade.json'

# Ajuste aqui se os nomes dos arquivos mudarem:
ARQ_DETALHADA = DOWNLOADS / 'RelatorioListagemEntradaMercadoria (2).xls'
ARQ_RESUMIDA  = DOWNLOADS / 'RelatorioListagemEntradaMercadoriaResumida.xls'

def parse_xls(fn):
    raw = open(fn, encoding='utf-8', errors='ignore').read()
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', raw, re.DOTALL | re.IGNORECASE)
    out = []
    for r in rows:
        cs = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', r, re.DOTALL | re.IGNORECASE)
        out.append([re.sub(r'<[^>]+>', '', c).replace('&nbsp;', ' ').strip() for c in cs])
    return out

def num(s):
    s = (s or '').replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

def mes_de(data):
    m = re.match(r'(\d{2})/(\d{2})/(\d{4})', data or '')
    return (m.group(2) + '/' + m.group(3)) if m else ''

# 1) Resumida: nota -> unidade
R = parse_xls(ARQ_RESUMIDA)
rh = next(x for x in R if 'Unidade' in x and 'Número nota' in x)
rin, riu = rh.index('Número nota'), rh.index('Unidade')
nota2uni = {}
for x in R:
    if len(x) >= len(rh) and x != rh and x[rin] and x[rin] != 'Número nota':
        if x[riu]:
            nota2uni[x[rin]] = x[riu]
print('Resumida: %d notas com unidade' % len(nota2uni))

# 2) Detalhada: linhas de item
D = parse_xls(ARQ_DETALHADA)
dh = next(x for x in D if 'Número nota' in x and 'Especificação' in x)
i_n  = dh.index('Número nota')
i_esp= dh.index('Especificação')
i_q  = dh.index('Quantidade')
i_pu = dh.index('Preço Bruto')   # preco UNITARIO
i_pt = dh.index('Preço')         # total da linha
i_d  = dh.index('Data entrada')
i_f  = dh.index('Fornecedor')

# 3) Agrega por (unidade, item)
# estrutura: dados[unidade][item] = lista de compras
compras = defaultdict(lambda: defaultdict(list))
sem_uni = 0
linhas = 0
for x in D:
    if len(x) < len(dh) or x == dh: continue
    nota = x[i_n]
    if not nota or nota == 'Número nota': continue
    nome = (x[i_esp] or '').upper().strip()
    if not nome: continue
    uni = nota2uni.get(nota)
    if not uni:
        sem_uni += 1
        continue
    pu = num(x[i_pu])
    if pu <= 0: continue
    reg = {
        'qtd': num(x[i_q]),
        'preco_unit': pu,
        'total': num(x[i_pt]),
        'mes': mes_de(x[i_d]),
        'fornecedor': x[i_f],
        'nota': nota,
        'data': x[i_d],
    }
    compras[uni][nome].append(reg)
    compras['__TODAS__'][nome].append(reg)
    linhas += 1
print('Linhas de item casadas: %d (sem unidade: %d)' % (linhas, sem_uni))

def stats_item(regs):
    precos = [r['preco_unit'] for r in regs if r['preco_unit'] > 0]
    if not precos: return None
    valor_total = sum(r['total'] for r in regs)
    # serie temporal por mes (preco medio unitario + qtd)
    por_mes = defaultdict(lambda: {'precos': [], 'qtd': 0})
    for r in regs:
        if r['mes']:
            por_mes[r['mes']]['precos'].append(r['preco_unit'])
            por_mes[r['mes']]['qtd'] += r['qtd']
    def chave_mes(m):
        p = m.split('/'); return p[1] + p[0]
    serie = []
    for m in sorted(por_mes, key=chave_mes):
        pr = por_mes[m]['precos']
        serie.append({'mes': m, 'preco_medio': round(sum(pr)/len(pr), 2), 'qtd': round(por_mes[m]['qtd'], 2)})
    # fornecedores
    forn = defaultdict(lambda: {'precos': [], 'qtd': 0})
    for r in regs:
        f = r['fornecedor'] or '—'
        forn[f]['precos'].append(r['preco_unit'])
        forn[f]['qtd'] += r['qtd']
    fornecedores = {}
    for f, d in forn.items():
        fornecedores[f] = {
            'qtd': round(d['qtd'], 2),
            'preco_medio': round(sum(d['precos'])/len(d['precos']), 2),
            'preco_min': round(min(d['precos']), 2),
            'preco_max': round(max(d['precos']), 2),
        }
    return {
        'quantidade_compras': len(regs),
        'qtd_total': round(sum(r['qtd'] for r in regs), 2),
        'preco_medio': round(sum(precos)/len(precos), 2),
        'preco_mediana': round(statistics.median(precos), 2),
        'preco_minimo': round(min(precos), 2),
        'preco_maximo': round(max(precos), 2),
        'valor_total': round(valor_total, 2),
        'fornecedores': fornecedores,
        'serie_temporal': serie,
    }

resultado = {}
for uni, itens in compras.items():
    bloco = {}
    for nome, regs in itens.items():
        s = stats_item(regs)
        if s: bloco[nome] = s
    resultado[uni] = bloco

# Resumo
print('\nUnidades geradas:')
for uni in sorted(resultado, key=lambda u: -len(resultado[u])):
    tot = sum(i['valor_total'] for i in resultado[uni].values())
    print('  %-22s %4d itens  R$ %12.2f' % (uni, len(resultado[uni]), tot))

with open(SAIDA, 'w', encoding='utf-8') as f:
    json.dump(resultado, f, ensure_ascii=False)
print('\nSalvo em: %s (%d unidades)' % (SAIDA, len(resultado)))

# ── GASTO POR UNIDADE x MES (valores exatos = soma dos totais de linha) ──
def chave_mes(m):
    p = m.split('/'); return p[1] + p[0]   # AAAA + MM

gasto = defaultdict(lambda: defaultdict(float))   # gasto[unidade][mes]
meses_set = set()
for uni, itens in compras.items():
    if uni == '__TODAS__':
        continue
    for nome, regs in itens.items():
        for r in regs:
            if r['mes']:
                gasto[uni][r['mes']] += r['total']
                meses_set.add(r['mes'])

meses = sorted(meses_set, key=chave_mes)
unidades_out = {}
for uni in gasto:
    linha = {m: round(gasto[uni].get(m, 0.0), 2) for m in meses}
    linha['total'] = round(sum(gasto[uni].values()), 2)
    unidades_out[uni] = linha

totais_mes = {m: round(sum(gasto[u].get(m, 0.0) for u in gasto), 2) for m in meses}

gasto_saida = {
    'meses': meses,
    'unidades': unidades_out,
    'totais_mes': totais_mes,
    'total_geral': round(sum(totais_mes.values()), 2),
}
SAIDA_GASTO = Path(__file__).parent / 'gasto_por_unidade.json'
with open(SAIDA_GASTO, 'w', encoding='utf-8') as f:
    json.dump(gasto_saida, f, ensure_ascii=False)
print('Salvo gasto_por_unidade.json: %d meses, %d unidades, total R$ %.2f'
      % (len(meses), len(unidades_out), gasto_saida['total_geral']))
