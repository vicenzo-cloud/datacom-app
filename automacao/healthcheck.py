# -*- coding: utf-8 -*-
"""
Healthcheck do app (a cada ~10 min).
Confere se o servidor responde em http://127.0.0.1:5000. Se nao, reinicia o
launcher (que tem trava de instancia unica, entao e seguro chamar).
"""
import os, sys, socket, subprocess, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _comum as C

PORTA = 5000
LAUNCHER = os.path.join(C.BASE_DIR, 'launcher.pyw')
PYW = sys.executable.replace('python.exe', 'pythonw.exe')
LOG = os.path.join(C.BASE_DIR, 'Relatorios', 'healthcheck_log.txt')


def log(msg):
    linha = '[%s] %s' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), msg)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as fh:
        fh.write(linha + '\n')
    print(linha)


def no_ar():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        return s.connect_ex(('127.0.0.1', PORTA)) == 0
    finally:
        s.close()


def main():
    if no_ar():
        return  # tudo certo, silencioso
    log('App fora do ar — reiniciando launcher...')
    try:
        subprocess.Popen([PYW, LAUNCHER], cwd=C.BASE_DIR,
                         creationflags=getattr(subprocess, 'DETACHED_PROCESS', 0))
        log('launcher disparado.')
    except Exception as e:
        log('ERRO ao reiniciar: %s' % e)


if __name__ == '__main__':
    main()
