# -*- coding: utf-8 -*-
"""
Alerta de gasto anomalo (diario), com pouco ruido:
- Nota atipica = valor acima de (media + 3 desvios-padrao) da filial, com piso.
- Pico de mes = mes COMPLETO com total > 1.5x a media dos demais meses.
- So reporta NOVIDADES: guarda o que ja foi alertado em .alertas_estado.json,
  entao depois da 1a varredura (catch-up) fica quieto ate surgir algo novo.
Saida: Relatorios/alertas_<data>.txt e alertas_ultima.txt
"""
import os, sys, json, datetime, io, statistics
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as C

PISO_NOTA = 1500.0
SIGMA = 3.0
FATOR_MES = 1.5
REL = os.path.join(C.BASE_DIR, 'Relatorios')
ESTADO = os.path.join(REL, '.alertas_estado.json')


def brl(v):
    return ('R$ %0.2f' % (v or 0)).replace(',', 'X').replace('.', ',').replace('X', '.')


def carregar_estado():
    try:
        d = json.load(open(ESTADO, encoding='utf-8'))
        return set(d.get('notas', [])), set(d.get('meses', []))
    except Exception:
        return set(), set()


def salvar_estado(notas, meses):
    os.makedirs(REL, exist_ok=True)
    json.dump({'notas': sorted(notas), 'meses': sorted(meses)},
              open(ESTADO, 'w', encoding='utf-8'), ensure_ascii=False)


def main():
    vistas, meses_vistos = carregar_estado()
    ym_atual = datetime.date.today().strftime('%Y-%m')
    out = io.StringIO(); w = out.write
    w('ALERTAS DE GASTO — %s\n' % datetime.datetime.now().strftime('%d/%m/%Y %H:%M'))
    w('=' * 70 + '\n\n')
    achou = False

    for f in C.carregar_filiais():
        fid = f['id']
        nfs = [n for n in C.carregar_dados(fid).get('nfs', []) if n.get('valor')]
        if len(nfs) < 8:
            continue
        valores = [n['valor'] for n in nfs]
        media = statistics.mean(valores)
        dp = statistics.pstdev(valores)
        limite = max(PISO_NOTA, media + SIGMA * dp)

        novas = []
        for n in nfs:
            if n['valor'] <= limite:
                continue
            k = '%s|%s|%.2f|%s' % (fid, n.get('numero'), n['valor'], n.get('data'))
            if k in vistas:
                continue
            vistas.add(k); novas.append(n)
        novas.sort(key=lambda n: -n['valor'])

        # picos de mes (completos)
        por_mes = defaultdict(float)
        for n in nfs:
            ym = (n.get('data') or '')[:7]
            if ym:
                por_mes[ym] += n['valor']
        completos = {k: v for k, v in por_mes.items() if k != ym_atual}
        picos = []
        if len(completos) >= 3:
            for ym, tot in completos.items():
                outros = [v for k, v in completos.items() if k != ym]
                m = sum(outros) / len(outros)
                mk = '%s|%s' % (fid, ym)
                if m > 0 and tot > FATOR_MES * m and mk not in meses_vistos:
                    meses_vistos.add(mk); picos.append((ym, tot, m))

        if novas or picos:
            achou = True
            w('%s   (limiar de nota atipica: %s)\n' % (f.get('nome', fid), brl(limite)))
            for n in novas[:15]:
                w('   ! NF %-10s %s  %s  (%s)\n'
                  % (n.get('numero'), brl(n['valor']), (n.get('fornecedor') or '')[:34], n.get('data')))
            for ym, tot, m in sorted(picos):
                w('   ^ pico em %s: %s (media dos outros %s, +%.0f%%)\n'
                  % (ym, brl(tot), brl(m), (tot / m - 1) * 100))
            w('\n')

    if not achou:
        w('Sem novidades. Nenhuma anomalia nova desde a ultima verificacao.\n')

    salvar_estado(vistas, meses_vistos)
    os.makedirs(REL, exist_ok=True)
    txt = out.getvalue()
    open(os.path.join(REL, 'alertas_%s.txt' % datetime.date.today().strftime('%Y-%m-%d')), 'w', encoding='utf-8').write(txt)
    open(os.path.join(REL, 'alertas_ultima.txt'), 'w', encoding='utf-8').write(txt)
    print(txt)


if __name__ == '__main__':
    main()
