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
APP = Path(__file__).parent
SAIDA = APP / 'analise_por_unidade.json'

# Prioriza os arquivos enviados pela app (entrada_detalhada/resumida.xls);
# se não existirem, usa os nomes padrão do Downloads.
def _achar(preferido, *alternativos):
    if preferido.exists():
        return preferido
    for a in alternativos:
        if a.exists():
            return a
    return preferido  # retorna o preferido mesmo ausente (erro claro depois)

ARQ_DETALHADA = _achar(APP / 'entrada_detalhada.xls',
                       DOWNLOADS / 'RelatorioListagemEntradaMercadoria (2).xls')
ARQ_RESUMIDA  = _achar(APP / 'entrada_resumida.xls',
                       DOWNLOADS / 'RelatorioListagemEntradaMercadoriaResumida.xls')
print('Detalhada:', ARQ_DETALHADA.name)
print('Resumida :', ARQ_RESUMIDA.name)

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

# ── FILTRO DE VALORES EXTREMOS (erros do relatorio do sistema) ──
# Remove registros cujo preco unitario foge muito da mediana do item
# (mais de 5x acima ou abaixo), ex: R$ 0,01 ou precos inflados.
BANDA_BAIXA, BANDA_ALTA = 0.2, 5.0  # 5x abaixo / 5x acima da mediana
medianas = {}
for nome, regs in compras['__TODAS__'].items():
    pus = sorted(r['preco_unit'] for r in regs if r['preco_unit'] > 0)
    if pus:
        medianas[nome] = pus[len(pus)//2]

def preco_ok(nome, r):
    med = medianas.get(nome, 0)
    if med <= 0:
        return True
    pu = r['preco_unit']
    return (pu >= med * BANDA_BAIXA) and (pu <= med * BANDA_ALTA)

removidos = 0
for uni in list(compras.keys()):
    for nome in list(compras[uni].keys()):
        antes = len(compras[uni][nome])
        compras[uni][nome] = [r for r in compras[uni][nome] if preco_ok(nome, r)]
        if uni != '__TODAS__':
            removidos += antes - len(compras[uni][nome])
        if not compras[uni][nome]:
            del compras[uni][nome]
print('Registros com preco extremo removidos: %d' % removidos)

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
    # variacao % (preco do ultimo mes vs primeiro mes com dado)
    variacao_pct = 0.0
    if len(serie) >= 2 and serie[0]['preco_medio'] > 0:
        variacao_pct = round((serie[-1]['preco_medio'] - serie[0]['preco_medio']) / serie[0]['preco_medio'] * 100, 2)
    # preco previsto = preco medio do mes mais recente (fallback: media geral)
    preco_previsto = serie[-1]['preco_medio'] if serie else round(sum(precos)/len(precos), 2)
    # NF mais cara / mais barata (por preco unitario)
    reg_caro = max(regs, key=lambda r: r['preco_unit'])
    reg_barato = min(regs, key=lambda r: r['preco_unit'])
    def nf_info(r):
        return {'numero': r['nota'], 'preco': round(r['preco_unit'], 2), 'fornecedor': r['fornecedor'], 'data': r['data']}
    return {
        'quantidade_compras': len(regs),
        'qtd_total': round(sum(r['qtd'] for r in regs), 2),
        'preco_medio': round(sum(precos)/len(precos), 2),
        'preco_mediana': round(statistics.median(precos), 2),
        'preco_minimo': round(min(precos), 2),
        'preco_maximo': round(max(precos), 2),
        'variacao_pct': variacao_pct,
        'valor_total': round(valor_total, 2),
        'preco_previsto': preco_previsto,
        'margem_sugerida_pct': 30,
        'nf_mais_cara': nf_info(reg_caro),
        'nf_mais_barata': nf_info(reg_barato),
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

# ── CLASSIFICACAO POR CATEGORIA (palavras-chave no nome do item) ──
def categoria(nome):
    n = (nome or '').upper()
    def tem(*ws): return any(w in n for w in ws)
    if tem('GASOLINA', 'DIESEL', 'COMBUST', 'ETANOL', 'ALCOOL', 'PNEU', 'OLEO MOTOR'):
        return 'Combustível/Veículos'
    if tem('FACIAL', 'CATRACA', 'FECHADURA', 'ELETROIMA', 'ELETROÍMÃ', 'LEITOR', 'SMART ID',
           'MOLA AEREA', 'MOLA AÉREA', 'BOTOEIRA', 'CONTROLADORA', 'ACIONADOR', 'BIOMETR',
           'TORNIQUETE', 'CANCELA', 'TAG '):
        return 'Controle de Acesso'
    if tem('CAMERA', 'CÂMERA', 'NVR', 'DVR', 'SPEED DOME', 'DASHCAM', 'GRAVACAO', 'GRAVAÇÃO',
           'DISCO RIGIDO', 'DISCO RÍGIDO', 'SERVIDOR', 'MIBO', 'BULLET', 'DOME', 'HIKVISION', 'INVU'):
        return 'CFTV'
    if re.search(r'\bHD\s?\d', n):
        return 'CFTV'
    if tem('SENSOR', 'SIRENE', 'CENTRAL', 'TECLADO', 'IRPET', ' AMT', 'GPRS', 'IVP', 'INFRAVERMELHO'):
        return 'Alarme'
    if tem('CABO', 'PATCH', 'SWITCH', 'RACK', 'CONECTOR', 'RJ45', 'RJ 45', 'ROTEADOR',
           'ROUTERBOARD', 'KEYSTONE', 'GBIC', 'FIBRA', 'ORGANIZADOR', 'PATCH PANEL'):
        return 'Rede/Infraestrutura'
    if tem('BATERIA', 'NOBREAK', 'FONTE', 'OFF GRID', 'CARREGADOR', 'SOLAR', 'ENERGIA'):
        return 'Energia'
    return 'Material/Diversos'

gasto_cat = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))  # [uni][cat][mes]
cats_set = set()
for uni, itens in compras.items():
    if uni == '__TODAS__':
        continue
    for nome, regs in itens.items():
        cat = categoria(nome)
        cats_set.add(cat)
        for r in regs:
            if r['mes']:
                gasto_cat[uni][cat][r['mes']] += r['total']
                gasto_cat['__TODAS__'][cat][r['mes']] += r['total']

cat_unidades = {}
for uni in gasto_cat:
    bloco = {}
    for cat in gasto_cat[uni]:
        linha = {m: round(gasto_cat[uni][cat].get(m, 0.0), 2) for m in meses}
        linha['total'] = round(sum(gasto_cat[uni][cat].values()), 2)
        bloco[cat] = linha
    cat_unidades[uni] = bloco

cat_saida = {'meses': meses, 'categorias': sorted(cats_set), 'unidades': cat_unidades}
SAIDA_CAT = Path(__file__).parent / 'gasto_por_categoria.json'
with open(SAIDA_CAT, 'w', encoding='utf-8') as f:
    json.dump(cat_saida, f, ensure_ascii=False)
print('Salvo gasto_por_categoria.json: %d categorias' % len(cats_set))
for c in sorted(cats_set):
    tot = sum(cat_unidades['__TODAS__'][c].values()) - cat_unidades['__TODAS__'][c]['total']
    print('   %-22s R$ %12.2f' % (c, cat_unidades['__TODAS__'][c]['total']))

# ── ANALISE_PRECOS.JSON (aba Precos / Curva ABC) — dados ja filtrados ──
# Usa __TODAS__ (sem registros de preco extremo) e mantem so categorias de
# seguranca (exclui Material/Diversos e Combustivel, ex: parafuso, agua sanitaria, gasolina).
CATS_SEGURANCA = {'CFTV', 'Alarme', 'Controle de Acesso', 'Rede/Infraestrutura', 'Energia'}
precos_out = {}
for nome, regs in compras['__TODAS__'].items():
    if categoria(nome) not in CATS_SEGURANCA:
        continue
    s = stats_item(regs)
    if s:
        precos_out[nome] = s
SAIDA_PRECOS = Path(__file__).parent / 'analise_precos.json'
# Backup do arquivo antigo (gerado no outro PC) antes de sobrescrever
if SAIDA_PRECOS.exists():
    import shutil
    shutil.copy2(SAIDA_PRECOS, Path(__file__).parent / 'analise_precos.bak.json')
with open(SAIDA_PRECOS, 'w', encoding='utf-8') as f:
    json.dump(precos_out, f, ensure_ascii=False)
tot_precos = sum(i['valor_total'] for i in precos_out.values())
print('Salvo analise_precos.json: %d itens de seguranca (filtrados), R$ %.2f' % (len(precos_out), tot_precos))
