# -*- coding: utf-8 -*-
"""Funcoes comuns para as automacoes (parsing dos .xls do ERP, helpers)."""
import re, json, random, string, os, unicodedata


def _norm(s):
    """maiusculo + sem acento, para casar palavras-chave de forma robusta."""
    s = unicodedata.normalize('NFKD', (s or ''))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s.upper()


# Regras de categoria (ordem importa: a 1a que casar vence).
# Casado contra o texto NORMALIZADO de (fornecedor + especificacoes dos itens).
_REGRAS = [
    ('Combustível',            [r'AUTO POSTO', r'\bPOSTO\b', r'COMBUSTIVEL', r'\bGASOLINA\b', r'\bDIESEL\b', r'\bETANOL\b', r'\bARLA\b']),
    ('Despesa veículos',       [r'\bMOTOS\b', r'MOTOSHOP', r'\bPNEU', r'\bVOLVO\b', r'VEICULOS', r'VIVERE', r'CANDEMIL', r'VALECAR', r'LUBRIFICANT', r'\bOLEO\b', r'RETIFICA', r'LAVAGEM', r'\bFREIO', r'\bEXTREMA\b', r'HAHNEL', r'CAPACETE', r'CAPA DE CHUVA', r'\bBAU\b', r'BAULETO', r'PLACA MOTO', r'VELA IGNICAO', r'ROLAMENTO', r'VIRABREQUIM', r'VALVULA ESCAPE', r'\bBIELA\b', r'\bPISTAO\b', r'RETROVISOR', r'ESTRIBO', r'ARO DIANTEIRO', r'RAIO DIANTEIRO', r'CORRENTE COMANDO', r'\bTENSOR\b', r'\bCAMARA\b', r'KASPER', r'IDALVIR SEVERO', r'AUTO NOVA PETROPOLIS', r'BALDISSERA']),
    ('Telecom',                [r'ALGAR', r'\bCLARO\b', r'TELEFONICA', r'\bVIVO\b', r'\bTIM\b', r'TELECOM', r'\bM2M\b', r'\bCHIP\b', r'VIRTUEYES', r'TELTONIKA', r'SIM CARD', r'RASTREAD', r'\bJIMI\b', r'\bGPS\b']),
    ('Uniformes e EPI',        [r'CONFEC', r'\bEPI\b', r'UNIFORME', r'MILITARES', r'\bBOTA\b', r'BOTINA', r'\bLUVA', r'STANGHERLIN', r'SIMOES EPI', r'MALHAS', r'CALCADOS', r'VESTUARIO', r'STARKE', r'CAMISET', r'VILELI']),
    ('Hospedagem/Viagem',      [r'\bHOTEL\b', r'POUSADA', r'\bMOTEL\b', r'HOSPEDAG']),
    ('Confraternizações',      [r'ALIMENTACAO', r'\bBEBIDAS\b', r'CONFRATER', r'RESTAURANTE', r'PADARIA', r'\bPIZZA']),
    ('Móveis',                 [r'\bMOVEIS\b', r'TEKMOVEIS', r'\bCADEIRA']),
    ('Controle de Acesso',     [r'FACIAL', r'CATRACA', r'CONTROLADORA', r'FECHADURA', r'ELETROIMA', r'\bLEITOR\b', r'TORNIQUETE', r'CANCELA', r'\bMOLA\b', r'BIOMETR', r'\bRFID\b', r'INTERFONE', r'SITUATOR', r'SPDOOR', r'SPACVI', r'CONTROLE DE ACESSO', r'PORTA SP']),
    ('Alarme',                 [r'\bALARME\b', r'\bSIRENE\b', r'\bIVP\b', r'\bSENSOR', r'INFRAVERMELHO', r'CENTRAL.*ALARME', r'\bJFL\b', r'\bIRD\b', r'\bDSE\b', r'IRPET', r'\bCR4T\b', r'\bXAC\b', r'\bXAS\b', r'GRUPO SAT']),
    ('CFTV',                   [r'CAMERA', r'\bNVR\b', r'\bDVR\b', r'HIKVISION', r'HILOOK', r'SPEED DOME', r'\bDOME\b', r'DASHCAM', r'\bMDVR\b', r'\bCFTV\b', r'DIGIFORT', r'\bVIDEO']),
    ('Cabeamento/Infra',       [r'\bCABO\b', r'\bUTP\b', r'CAT5', r'CAT6', r'PATCH', r'\bRACK\b', r'KEYSTONE', r'CONECTOR', r'\bRJ45\b', r'\bFIBRA\b', r'\bSWITCH\b', r'ROUTERBOARD', r'MIKROTIK', r'\bSFP\b', r'ORGANIZADOR', r'ACCESS POINT', r'\bAP 1350', r'CANALETA', r'ABRACADEIRA', r'DUTOTEC', r'\bWIFI\b']),
    ('Periféricos / TI',       [r'\bDELL\b', r'KABUM', r'INFORMATICA', r'NOTEBOOK', r'\bMONITOR\b', r'\bMOUSE\b', r'TECLADO', r'SD CARD', r'MICRO SD', r'\bSSD\b', r'IMPRESSORA', r'MEGA BYTE', r'BELMICRO', r'SGBRAS', r'TECNOLOGIA', r'CARREGADOR', r'TECNOLIFE']),
    ('Material elétrico',      [r'ELETRICA', r'ELETRIC', r'\bABT\b', r'AUTTEC', r'\bFIO\b', r'DISJUNTOR', r'\bTOMADA', r'\bLAMPADA', r'ELETROPECAS', r'RADIONAL', r'COMPONENTES ELETRONICOS', r'FITA ISOLANTE']),
    ('Energia',                [r'BATERIA', r'NOBREAK', r'NO-BREAK', r'\bFONTE\b', r'\bUPS\b', r'GERADOR', r'PLACA SOLAR', r'OFF.?GRID', r'DISTRIBUIDORA DE BATERIAS']),
    ('Ferramentas',           [r'FERRAMENT', r'ALICATE', r'CHAVE INGLESA', r'CHAVE TESTE', r'DESENGRIPANTE', r'\bLIXA\b', r'\bBROCA', r'PARAFUSADEIRA', r'\bSERRA\b', r'PISTOLA COLA QUENTE']),
    ('Materiais de Obra',      [r'MATERIAIS DE CONSTRU', r'CONSTRUCAO', r'\bARCO\b', r'FERRAGEM', r'FERRAGENS', r'PARAFUSO', r'CADEADO', r'\bTINTA', r'CENTERMAX', r'\bCIMENTO', r'\bAREIA\b', r'HIDRAUL', r'PORTO MATERIAIS', r'QUERO-QUERO', r'PLASTICOS', r'ASSENTO TAMPA', r'ZANDONAI', r'PLACA 4X2', r'\bVIDRO\b', r'PLACA EM ALUMINIO', r'SERIGRAFIA', r'ESTAMPAS', r'GRAFICA']),
    ('Material de Escritório /Limpeza/ Consumo', [r'PAPELARIA', r'\bCLIP\b', r'LIMPEZA', r'HIPERSUL', r'PATRONATO', r'ESCRITORIO', r'\bAGUA\b', r'EMBALAGENS', r'BRINDES', r'ARACA', r'\bCAFE\b', r'ACUCAR', r'ERVA MATE', r'COPO DESCART', r'FILTRO DE CAFE', r'POST IT', r'FOLHA A4', r'CARIMBO', r'\bCANETA', r'MARCA TEXTO', r'CALCULADORA', r'FITA DUREX', r'CHAVEIRO', r'CARTAO VISITA', r'BOTIJAO', r'CHALEIRA', r'\bCOPO\b']),
]
_REGRAS_COMP = [(cat, [re.compile(k) for k in ks]) for cat, ks in _REGRAS]


def classificar(fornecedor, itens=None):
    """Devolve a categoria sugerida (ou '' se nenhuma regra casar)."""
    txt = _norm((fornecedor or '') + ' ' + ' '.join(itens or []))
    for cat, pats in _REGRAS_COMP:
        for p in pats:
            if p.search(txt):
                return cat
    return ''

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../datacom-app
FILIAIS_DIR = os.path.join(BASE_DIR, 'filiais')
FILIAIS_JSON = os.path.join(BASE_DIR, 'filiais.json')


def cells(row):
    cs = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.S | re.I)
    return [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', c).replace('&nbsp;', ' ')).strip() for c in cs]


def _grid(path):
    h = open(path, encoding='utf-8', errors='replace').read()
    return [cells(r) for r in re.findall(r'<tr[^>]*>(.*?)</tr>', h, re.S | re.I)]


def parse(path):
    """Le um .xls (HTML) do ERP e devolve lista de dicts {coluna: valor}."""
    g = _grid(path)
    hi = next((i for i, x in enumerate(g)
               if 'mero nota' in ' '.join(x).lower() and 'fornecedor' in ' '.join(x).lower()), None)
    if hi is None:
        return []
    hd = g[hi]
    return [{hd[j]: (x[j] if j < len(x) else '') for j in range(len(hd))}
            for x in g[hi + 1:] if any(x) and x[:3] != hd[:3]]


def tipo_arquivo(path):
    """Classifica como 'resumida', 'detalhada' ou None."""
    g = _grid(path)
    hdr = next((x for x in g if 'mero nota' in ' '.join(x).lower() and 'fornecedor' in ' '.join(x).lower()), None)
    if not hdr:
        return None
    cols = ' '.join(hdr).lower()
    if 'especifica' in cols or 'total nota' in cols:
        return 'detalhada'
    if 'valor l' in cols or 'total produtos' in cols or 'valor bruto' in cols:
        return 'resumida'
    return None


def brl(s):
    s = (s or '').strip().replace('.', '').replace(',', '.')
    try:
        return round(float(s), 2)
    except Exception:
        return 0.0


def data_iso(s):
    m = re.match(r'(\d{2})/(\d{2})/(\d{4})', (s or '').strip())
    return '%s-%s-%s' % (m.group(3), m.group(2), m.group(1)) if m else ''


def uid():
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(7))


def limpa_forn(s):
    s = (s or '').strip()
    return '' if (not s or set(s) <= {'*'}) else s


def num(r):
    return (r.get('Número nota') or r.get('Número nota') or '').strip()


def chave_nf(n):
    """Chave de identidade de uma NF para deduplicação.
    Prioriza NÚMERO + CNPJ (pega nome fantasia x razão social da mesma empresa).
    Sem CNPJ, cai no fallback NÚMERO + FORNECEDOR normalizado."""
    numero = str(n.get('numero', '')).strip()
    cnpj = (n.get('cnpj') or '').strip()
    if cnpj:
        return (numero, 'CNPJ:' + cnpj)
    return (numero, _norm(n.get('fornecedor') or ''))


def carregar_filiais():
    try:
        d = json.load(open(FILIAIS_JSON, encoding='utf-8'))
        return d.get('filiais', [])
    except Exception:
        return []


def carregar_dados(fid):
    p = os.path.join(FILIAIS_DIR, fid, 'dados.json')
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return {'projects': [], 'nfs': [], '_rev': 0}


def salvar_dados(fid, dados):
    import shutil, datetime
    p = os.path.join(FILIAIS_DIR, fid, 'dados.json')
    bdir = os.path.join(FILIAIS_DIR, fid, 'Backups')
    os.makedirs(bdir, exist_ok=True)
    if os.path.exists(p):
        ts = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
        shutil.copy(p, os.path.join(bdir, 'auto_%s.json' % ts))
    dados['_rev'] = dados.get('_rev', 0) + 1
    json.dump(dados, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


def nfs_de_arquivos(resumidas, detalhadas):
    """Recebe listas de caminhos resumida/detalhada e devolve lista de NFs no formato do app."""
    res, det = [], []
    for p in resumidas:
        res += parse(p)
    for p in detalhadas:
        det += parse(p)
    total_nota, det_forn, det_itens, det_fin, det_status, det_cnpj = {}, {}, {}, {}, {}, {}
    for r in det:
        n = num(r)
        if not n:
            continue
        if n not in total_nota:
            total_nota[n] = brl(r.get('Total Nota'))
        if n not in det_forn:
            det_forn[n] = (r.get('Fornecedor') or '').strip()
        if not det_cnpj.get(n):
            det_cnpj[n] = (r.get('CNPJ') or '').strip()
        if n not in det_fin:
            det_fin[n] = (r.get('Gerou Financeiro') or '').strip()
        st = (r.get('Status') or '').strip()
        # Se QUALQUER linha da nota estiver como cancelada, a nota inteira é cancelada.
        if 'CANCEL' in _norm(st) or 'CANCEL' in _norm(det_status.get(n, '')):
            det_status[n] = 'Cancelada'
        elif n not in det_status:
            det_status[n] = st
        esp = (r.get('Especificação') or '').strip()
        if esp:
            det_itens.setdefault(n, []).append(esp)

    def _cancelada(n):
        return 'CANCEL' in _norm(det_status.get(n, ''))

    nfs, vis = [], set()
    for r in res:
        n = num(r)
        if not n:
            continue
        if _cancelada(n):  # nota cancelada no ERP não entra no app
            continue
        forn = limpa_forn(r.get('Fornecedor')) or limpa_forn(det_forn.get(n))
        cnpj = (r.get('CNPJ') or '').strip() or det_cnpj.get(n, '')
        # Duplicata = mesmo NUMERO + mesmo CNPJ (mesma empresa, mesmo nome fantasia
        # ou razao social). Sem CNPJ, cai no fallback numero + fornecedor.
        k = (n, cnpj) if cnpj else (n, _norm(forn))
        if k in vis:
            continue
        vis.add(k)
        valor = total_nota.get(n)
        if valor is None:  # sem detalhada -> usa Valor Bruto da resumida
            valor = brl(r.get('Valor Bruto'))
        nfs.append({'id': uid(), 'numero': n, 'fornecedor': forn, 'valor': valor,
                    'data': data_iso(r.get('Data emissão')),
                    'projId': '', 'obs': classificar(forn, det_itens.get(n)),
                    'centro': '', 'det': '', 'cnpj': cnpj, 'finGerado': det_fin.get(n, '')})
    # Se nao houve resumida mas ha detalhada, monta a partir da detalhada
    if not res and det:
        for n in sorted(total_nota):
            if _cancelada(n):  # nota cancelada no ERP não entra
                continue
            forn = limpa_forn(det_forn.get(n))
            nfs.append({'id': uid(), 'numero': n, 'fornecedor': forn,
                        'valor': total_nota[n], 'data': '',
                        'projId': '', 'obs': classificar(forn, det_itens.get(n)),
                        'centro': '', 'det': '', 'cnpj': det_cnpj.get(n, ''), 'finGerado': det_fin.get(n, '')})
    nfs.sort(key=lambda x: x['data'])
    return nfs
