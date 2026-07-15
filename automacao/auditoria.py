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
import os, sys, datetime, io, glob, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as C

REL_DIR = os.path.join(C.BASE_DIR, 'Relatorios')

# Se a base encolher mais que isto de um dia pro outro, dispara alerta de anomalia.
LIMITE_QUEDA = 0.10  # 10%


def chave(n):
    # mesma nota = mesmo NUMERO + mesmo FORNECEDOR
    return (str(n.get('numero', '')).strip(), C._norm(n.get('fornecedor') or ''))


def _backup_anterior(fid):
    """Devolve os dados do backup diario mais recente ANTERIOR a hoje (ou None)."""
    hoje = 'dados_%s.json' % datetime.date.today().isoformat()
    bdir = os.path.join(C.FILIAIS_DIR, fid, 'Backups')
    arqs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(bdir, 'dados_*.json')))
    anteriores = [a for a in arqs if a < hoje]
    if not anteriores:
        return None
    try:
        return json.load(open(os.path.join(bdir, anteriores[-1]), encoding='utf-8')), anteriores[-1]
    except Exception:
        return None


def detectar_anomalias(filiais, nome, dados):
    """Compara cada filial com seu backup do dia anterior e reporta quedas bruscas."""
    alertas = []
    for f in filiais:
        fid = f['id']
        atual = dados[fid].get('nfs', [])
        n_atual = len(atual)
        v_atual = sum(x.get('valor', 0) or 0 for x in atual)
        prev = _backup_anterior(fid)
        if not prev:
            continue
        d_prev, arq_prev = prev
        ant = d_prev.get('nfs', [])
        n_ant = len(ant)
        v_ant = sum(x.get('valor', 0) or 0 for x in ant)
        if n_ant == 0:
            continue
        queda_n = (n_ant - n_atual) / n_ant
        queda_v = (v_ant - v_atual) / v_ant if v_ant else 0
        if queda_n > LIMITE_QUEDA or queda_v > LIMITE_QUEDA:
            alertas.append((nome[fid], arq_prev, n_ant, n_atual, v_ant, v_atual, queda_n, queda_v))
    return alertas


def main():
    filiais = C.carregar_filiais()
    nome = {f['id']: f.get('nome', f['id']) for f in filiais}
    dados = {f['id']: C.carregar_dados(f['id']) for f in filiais}

    out = io.StringIO()
    w = out.write
    w('AUDITORIA — %s\n' % datetime.datetime.now().strftime('%d/%m/%Y %H:%M'))
    w('=' * 70 + '\n\n')

    # Alertas de anomalia (queda brusca de dados x dia anterior)
    anomalias = detectar_anomalias(filiais, nome, dados)
    if anomalias:
        w('!!!' + ' ALERTA DE ANOMALIA — POSSIVEL PERDA DE DADOS ' + '!!!\n')
        w('-' * 70 + '\n')
        for nm, arq, n_ant, n_at, v_ant, v_at, qn, qv in anomalias:
            w('  %s: notas %d -> %d (%.0f%%)  |  valor R$ %.2f -> R$ %.2f (%.0f%%)\n'
              % (nm, n_ant, n_at, qn * 100, v_ant, v_at, qv * 100))
            w('     comparado com: %s\n' % arq)
        w('  >> Verifique se a queda e legitima. Para restaurar, peca ao assistente.\n')
        w('-' * 70 + '\n\n')

    # Resumo por filial
    w('RESUMO POR FILIAL\n')
    for f in filiais:
        nfs = dados[f['id']].get('nfs', [])
        w('  %-22s %5d notas   R$ %14.2f\n' % (nome[f['id']], len(nfs), sum(n.get('valor', 0) for n in nfs)))
    w('\n')

    # Duplicatas entre filiais
    mapa = {}
    valor_por_chave = {}
    for fid, d in dados.items():
        for n in d.get('nfs', []):
            k = chave(n)
            mapa.setdefault(k, set()).add(fid)
            valor_por_chave[k] = n.get('valor', 0) or 0
    dups = {k: v for k, v in mapa.items() if len(v) > 1}
    w('NOTAS DUPLICADAS ENTRE FILIAIS (mesma nota em 2+ bases): %d\n' % len(dups))
    for (numero, fornecedor), fids in sorted(dups.items(), key=lambda x: -valor_por_chave[x[0]])[:200]:
        valor = valor_por_chave[(numero, fornecedor)]
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
