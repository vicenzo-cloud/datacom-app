# -*- coding: utf-8 -*-
"""
Auto-importador de notas fiscais.

Como usar:
  Largue os arquivos .xls (Resumida e Detalhada) na subpasta da filial dentro de
  '_importar/'. Ex: _importar/filial_de_canela/.
  Este script (agendado) detecta os arquivos, importa para a filial correta,
  ignora notas que ja existem (por numero+valor) e arquiva os arquivos processados.

Roteamento = pela PASTA (cada subpasta = uma filial). Sem adivinhar pelo conteudo.
"""
import os, sys, shutil, datetime, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as C

INBOX = os.path.join(C.BASE_DIR, '_importar')
LOG = os.path.join(INBOX, '_log.txt')


def log(msg):
    linha = '[%s] %s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg)
    print(linha)
    try:
        os.makedirs(INBOX, exist_ok=True)
        with open(LOG, 'a', encoding='utf-8') as fh:
            fh.write(linha + '\n')
    except Exception:
        pass


def chave(n):
    # Duplicata = mesmo NUMERO + mesmo FORNECEDOR (numero repetido de outro
    # fornecedor e nota distinta e deve entrar).
    return (str(n.get('numero', '')).strip(), C._norm(n.get('fornecedor') or ''))


def processar_filial(fid):
    pasta = os.path.join(INBOX, fid)
    # set() de-duplica: em FS case-insensitive (Windows) *.xls e *.XLS casam os mesmos arquivos
    arqs = sorted({os.path.normcase(os.path.abspath(p))
                   for p in glob.glob(os.path.join(pasta, '*.xls')) + glob.glob(os.path.join(pasta, '*.XLS'))})
    if not arqs:
        return
    resumidas, detalhadas, ignorados = [], [], []
    for p in arqs:
        t = C.tipo_arquivo(p)
        if t == 'resumida':
            resumidas.append(p)
        elif t == 'detalhada':
            detalhadas.append(p)
        else:
            ignorados.append(p)
    if ignorados:
        log('  [%s] arquivos nao reconhecidos (ignorados): %s' % (fid, [os.path.basename(x) for x in ignorados]))
    if not resumidas and not detalhadas:
        return

    novas = C.nfs_de_arquivos(resumidas, detalhadas)
    if not novas:
        log('  [%s] nenhuma nota lida dos arquivos.' % fid)
        return

    dados = C.carregar_dados(fid)
    existentes = {chave(n) for n in dados.get('nfs', [])}
    add = [n for n in novas if chave(n) not in existentes]
    dup = len(novas) - len(add)

    if add:
        dados['nfs'] = dados.get('nfs', []) + add
        dados['nfs'].sort(key=lambda x: x.get('data', ''))
        C.salvar_dados(fid, dados)
    total_add = sum(n['valor'] for n in add)
    log('  [%s] arquivos: %dR/%dD | lidas: %d | novas: %d (R$ %.2f) | ja existiam: %d'
        % (fid, len(resumidas), len(detalhadas), len(novas), len(add), total_add, dup))

    # arquiva
    destino = os.path.join(pasta, 'processados', datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'))
    os.makedirs(destino, exist_ok=True)
    for p in resumidas + detalhadas + ignorados:
        try:
            shutil.move(p, os.path.join(destino, os.path.basename(p)))
        except Exception as e:
            log('  [%s] falha ao arquivar %s: %s' % (fid, os.path.basename(p), e))


def main():
    os.makedirs(INBOX, exist_ok=True)
    filiais = C.carregar_filiais()
    if not filiais:
        log('Sem filiais.json — nada a fazer.')
        return
    # garante subpastas
    for f in filiais:
        os.makedirs(os.path.join(INBOX, f['id']), exist_ok=True)
    achou = any(glob.glob(os.path.join(INBOX, f['id'], '*.xls')) for f in filiais)
    if achou:
        log('=== Importacao iniciada ===')
    for f in filiais:
        try:
            processar_filial(f['id'])
        except Exception as e:
            log('  [%s] ERRO: %s' % (f['id'], e))
    if achou:
        log('=== Importacao concluida ===')


if __name__ == '__main__':
    main()
