import webview
import http.server
import socketserver
import threading
import socket
import os
import sys
import webbrowser
from pathlib import Path

os.chdir(Path(__file__).parent)

# ── INSTANCIA UNICA: porta fixa 5000 ──
# Se a porta ja estiver em uso, ja existe um app rodando. Em vez de abrir
# outra copia (que brigaria pelos dados), abre o app no navegador e sai.
porta = 5000
def _porta_em_uso(p):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        usado = (s.connect_ex(('127.0.0.1', p)) == 0)
    finally:
        s.close()
    return usado

if _porta_em_uso(porta):
    try:
        webbrowser.open('http://localhost:' + str(porta))
    except Exception:
        pass
    sys.exit(0)

import json as _cfgjson, secrets

# ── Autenticacao da equipe (acesso pela rede) ──
CONFIG_PATH = Path(__file__).parent / 'config.json'
def carregar_senha():
    try:
        if CONFIG_PATH.exists():
            return _cfgjson.loads(CONFIG_PATH.read_text(encoding='utf-8')).get('senha', 'vigillare')
    except Exception:
        pass
    CONFIG_PATH.write_text(_cfgjson.dumps({'senha': 'vigillare'}, ensure_ascii=False), encoding='utf-8')
    return 'vigillare'
SENHA = carregar_senha()

# ── Usuários individuais (nome + senha + papel) ──
# papel: 'editor' (adiciona/remove) ou 'leitor' (só visualiza). O host (este PC) é sempre dono/editor.
def carregar_config():
    try:
        if CONFIG_PATH.exists():
            return _cfgjson.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    except Exception:
        pass
    return {}
def carregar_usuarios():
    cfg = carregar_config()
    us = cfg.get('usuarios')
    return us if isinstance(us, list) else []
def salvar_usuarios(lista):
    cfg = carregar_config()
    cfg['usuarios'] = lista[:5]  # no máximo 5
    if 'senha' not in cfg: cfg['senha'] = SENHA
    CONFIG_PATH.write_text(_cfgjson.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
import hashlib as _hl, binascii as _ba
def hash_senha(senha):
    salt = os.urandom(16)
    dk = _hl.pbkdf2_hmac('sha256', (senha or '').encode('utf-8'), salt, 120000)
    return 'pbkdf2$120000$' + _ba.hexlify(salt).decode() + '$' + _ba.hexlify(dk).decode()
def verificar_senha(senha, armazenada):
    try:
        if not armazenada: return False
        if str(armazenada).startswith('pbkdf2$'):
            _, it, salt_hex, hash_hex = armazenada.split('$')
            dk = _hl.pbkdf2_hmac('sha256', (senha or '').encode('utf-8'), _ba.unhexlify(salt_hex), int(it))
            return _ba.hexlify(dk).decode() == hash_hex
        return senha == armazenada  # compat: senha antiga em texto puro
    except Exception:
        return False
def autenticar_usuario(nome, senha):
    nome = (nome or '').strip()
    if senha == '':
        return None
    for u in carregar_usuarios():
        if (u.get('nome','').strip().lower() == nome.lower()) and verificar_senha(senha, u.get('senha','')):
            return {'nome': u.get('nome'), 'papel': (u.get('papel') or 'editor')}
    # Compatibilidade: senha geral única (sem nome) → acesso de leitor pela rede
    if senha == SENHA:
        return {'nome': nome or 'Equipe', 'papel': 'leitor'}
    return None

# token -> {'nome':..., 'papel':...}  (persistido p/ sobreviver a reinício do app)
SESSOES_PATH = Path(__file__).parent / 'sessoes.json'
def carregar_sessoes():
    try:
        if SESSOES_PATH.exists():
            d = _cfgjson.loads(SESSOES_PATH.read_text(encoding='utf-8'))
            return d if isinstance(d, dict) else {}
    except Exception:
        pass
    return {}
def salvar_sessoes():
    try:
        SESSOES_PATH.write_text(_cfgjson.dumps(SESSOES, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass
SESSOES = carregar_sessoes()
HOST_USER = {'nome': 'Gattiboni (dono)', 'papel': 'editor'}

# ── Multi-filial: cada filial (CNPJ) tem sua pasta com os mesmos arquivos ──
BASE_DIR = Path(__file__).parent
FILIAIS_PATH = BASE_DIR / 'filiais.json'
# arquivos que são separados por filial (o resto é compartilhado)
PER_FILIAL = ['dados.json', 'analise_precos.json', 'gasto_por_unidade.json',
              'gasto_por_categoria.json', 'analise_por_unidade.json',
              'entrada_detalhada.xls', 'entrada_resumida.xls']
import re as _re
def _slug(s):
    s = (s or '').strip().lower()
    s = _re.sub(r'[^a-z0-9]+', '_', s).strip('_')
    return s or 'filial'
def carregar_filiais():
    try:
        if FILIAIS_PATH.exists():
            d = _cfgjson.loads(FILIAIS_PATH.read_text(encoding='utf-8'))
            if isinstance(d, dict) and d.get('filiais'):
                return d
    except Exception:
        pass
    return {'filialAtual': 'matriz', 'filiais': [{'id': 'matriz', 'nome': 'Matriz', 'cnpj': ''}]}
def salvar_filiais(d):
    try:
        FILIAIS_PATH.write_text(_cfgjson.dumps(d, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception as e:
        print('salvar_filiais erro:', e)
def filial_atual_id():
    d = carregar_filiais()
    ids = [f.get('id') for f in d.get('filiais', [])]
    fa = d.get('filialAtual')
    return fa if fa in ids else (ids[0] if ids else 'matriz')
def filial_dir(fid=None):
    fid = fid or filial_atual_id()
    p = BASE_DIR / 'filiais' / fid
    p.mkdir(parents=True, exist_ok=True)
    return p
def migrar_para_filiais():
    # Na 1ª vez: move os arquivos atuais (Matriz) para filiais/matriz/
    if FILIAIS_PATH.exists():
        return
    import shutil
    mat = BASE_DIR / 'filiais' / 'matriz'
    mat.mkdir(parents=True, exist_ok=True)
    for nm in PER_FILIAL:
        src = BASE_DIR / nm
        if src.exists() and not (mat / nm).exists():
            try: shutil.move(str(src), str(mat / nm))
            except Exception as e: print('migrar', nm, e)
    oldb = BASE_DIR / 'Backups'
    if oldb.exists() and not (mat / 'Backups').exists():
        try: shutil.move(str(oldb), str(mat / 'Backups'))
        except Exception: pass
    # garante um dados.json (mesmo vazio) pra Matriz
    if not (mat / 'dados.json').exists():
        (mat / 'dados.json').write_text(_cfgjson.dumps({'projects': [], 'nfs': [], '_rev': 0}, ensure_ascii=False), encoding='utf-8')
    salvar_filiais({'filialAtual': 'matriz', 'filiais': [{'id': 'matriz', 'nome': 'Matriz', 'cnpj': ''}]})
migrar_para_filiais()

# ── Banco de dados de atividades (SQLite, embutido no Python) ──
import sqlite3, datetime as _dt, threading as _th
DB_PATH = Path(__file__).parent / 'atividade.db'
_db_lock = _th.Lock()
def init_db():
    try:
        with _db_lock:
            con = sqlite3.connect(str(DB_PATH))
            con.execute('''CREATE TABLE IF NOT EXISTS log(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                usuario TEXT,
                acao TEXT,
                detalhe TEXT,
                ip TEXT
            )''')
            con.commit(); con.close()
    except Exception as e:
        print('init_db erro:', e)
def registrar_log(acao, detalhe, usuario, ip):
    try:
        with _db_lock:
            con = sqlite3.connect(str(DB_PATH))
            con.execute('INSERT INTO log(ts,usuario,acao,detalhe,ip) VALUES(?,?,?,?,?)',
                        (_dt.datetime.now().isoformat(timespec='seconds'), usuario or 'equipe', acao or '', detalhe or '', ip or ''))
            con.commit(); con.close()
        return True
    except Exception as e:
        print('registrar_log erro:', e); return False
def consultar_log(limite=500):
    try:
        with _db_lock:
            con = sqlite3.connect(str(DB_PATH))
            cur = con.execute('SELECT ts,usuario,acao,detalhe,ip FROM log ORDER BY id DESC LIMIT ?', (int(limite),))
            rows = [{'ts':r[0],'usuario':r[1],'acao':r[2],'detalhe':r[3],'ip':r[4]} for r in cur.fetchall()]
            con.close()
        return rows
    except Exception as e:
        print('consultar_log erro:', e); return []
init_db()

def ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80)); ip = s.getsockname()[0]; s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def cookie_token(headers):
    c = headers.get('Cookie', '') or ''
    for parte in c.split(';'):
        parte = parte.strip()
        if parte.startswith('dc_session='):
            return parte[len('dc_session='):]
    return None

LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Login - Projetos Suprimentos</title>
<style>body{background:#0b0e0d;color:#e2e8e4;font-family:system-ui,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}
.box{background:#14181a;padding:34px;border-radius:14px;border:1px solid #2a2f2d;width:300px;text-align:center}
.box h1{font-size:18px;margin:0}.sub{font-size:12px;color:#6b7c72;margin:4px 0 18px}
input{width:100%;padding:11px;margin:0 0 12px;border-radius:7px;border:1px solid #2a2f2d;background:#0b0e0d;color:#e2e8e4;box-sizing:border-box;font-size:14px}
button{width:100%;padding:11px;border-radius:7px;border:none;background:#00d48a;color:#0b0e0d;font-weight:bold;cursor:pointer;font-size:14px}
.err{color:#ff5252;font-size:12px;min-height:18px;margin-top:10px}</style></head>
<body><div class="box"><h1>Projetos Suprimentos</h1><div class="sub">Acesso restrito · informe seu nome e senha</div>
<input type="text" id="u" placeholder="Nome de usuário" autofocus onkeydown="if(event.key==='Enter')entrar()">
<input type="password" id="s" placeholder="Senha" onkeydown="if(event.key==='Enter')entrar()">
<button onclick="entrar()">Entrar</button><div class="err" id="e"></div></div>
<script>function entrar(){var u=document.getElementById('u').value;var s=document.getElementById('s').value;
fetch('/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usuario:u,senha:s})})
.then(function(r){return r.json();}).then(function(d){if(d.ok){location.href='/';}else{document.getElementById('e').textContent='Nome ou senha incorretos';}})
.catch(function(){document.getElementById('e').textContent='Erro de conexão';});}</script></body></html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    def _autenticado(self):
        ip = self.client_address[0]
        if ip in ('127.0.0.1', '::1', 'localhost'):
            return True  # maquina host sempre liberada
        return cookie_token(self.headers) in SESSOES
    def _sessao(self):
        ip = self.client_address[0]
        if ip in ('127.0.0.1', '::1', 'localhost'):
            return dict(HOST_USER, host=True)
        s = SESSOES.get(cookie_token(self.headers))
        return dict(s, host=False) if s else None
    def _eh_host(self):
        return self.client_address[0] in ('127.0.0.1', '::1', 'localhost')
    def _pode_editar(self):
        s = self._sessao()
        return bool(s) and s.get('papel') == 'editor'
    def do_POST(self):
        if self.path == '/login':
            import json as _json
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                _d = _json.loads(body); usuario = _d.get('usuario',''); senha = _d.get('senha', '')
            except Exception:
                usuario = ''; senha = ''
            user = autenticar_usuario(usuario, senha)
            if user:
                tok = secrets.token_hex(16); SESSOES[tok] = user; salvar_sessoes()
                registrar_log('Acesso pela rede (login OK)', user['nome']+' · papel: '+user['papel'], user['nome'], self.client_address[0])
                resp = _json.dumps({'ok': True, 'nome': user['nome'], 'papel': user['papel']}).encode('utf-8')
                self.send_response(200)
                self.send_header('Set-Cookie', 'dc_session=' + tok + '; Path=/; Max-Age=86400; SameSite=Lax')
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers(); self.wfile.write(resp)
            else:
                registrar_log('Tentativa de login falhou', 'usuario: '+(usuario or '(vazio)'), usuario or 'rede', self.client_address[0])
                resp = _json.dumps({'ok': False}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers(); self.wfile.write(resp)
            return
        if not self._autenticado():
            self.send_response(401); self.end_headers(); return
        # Somente editores podem gravar/alterar dados
        if self.path in ('/save-data', '/upload-relatorio', '/reprocessar') and not self._pode_editar():
            import json as _json
            registrar_log('Ação bloqueada (somente leitura)', self.path, (self._sessao() or {}).get('nome','?'), self.client_address[0])
            self.send_response(403); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
            self.wfile.write(_json.dumps({'ok': False, 'erro': 'Sem permissão: seu usuário é somente leitura.'}).encode('utf-8'))
            return
        if self.path == '/upload-relatorio':
            # Recebe um relatorio .xls enviado pela app e salva no disco
            import json as _json
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                data = _json.loads(body)
                tipo = data.get('tipo')  # 'detalhada' ou 'resumida'
                conteudo = data.get('content', '')
                nome = 'entrada_detalhada.xls' if tipo == 'detalhada' else 'entrada_resumida.xls'
                with open(filial_dir() / nome, 'w', encoding='utf-8') as f:
                    f.write(conteudo)
                resp = _json.dumps({'ok': True, 'arquivo': nome, 'tamanho': len(conteudo)}).encode('utf-8')
                self.send_response(200)
            except Exception as e:
                resp = _json.dumps({'ok': False, 'erro': str(e)}).encode('utf-8')
                self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(resp)
            return
        if self.path == '/reprocessar':
            # Roda o gerar_analise_unidade.py e devolve o log
            import json as _json, subprocess, sys
            try:
                script = Path(__file__).parent / 'gerar_analise_unidade.py'
                proc = subprocess.run([sys.executable, str(script), str(filial_dir())],
                                      capture_output=True, text=True, timeout=120,
                                      cwd=str(Path(__file__).parent))
                ok = proc.returncode == 0
                resp = _json.dumps({'ok': ok, 'log': (proc.stdout or '')[-3000:], 'erro': (proc.stderr or '')[-1500:]}).encode('utf-8')
                self.send_response(200 if ok else 500)
            except Exception as e:
                resp = _json.dumps({'ok': False, 'erro': str(e)}).encode('utf-8')
                self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(resp)
            return
        if self.path == '/save-data':
            # Persiste os dados dos projetos/NFs em dados.json (backup em disco)
            import json as _json
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                obj = _json.loads(body)  # valida que e JSON valido
                _fdir = filial_dir()
                caminho = _fdir / 'dados.json'
                # ── Controle de revisão (evita 2 editores se sobrescreverem) ──
                atual_rev = 0
                if caminho.exists():
                    try: atual_rev = int(_json.loads(caminho.read_text(encoding='utf-8')).get('_rev', 0) or 0)
                    except Exception: atual_rev = 0
                cli_rev = self.headers.get('X-Rev', '')
                if cli_rev not in ('', None):
                    try: cli_rev_i = int(cli_rev)
                    except Exception: cli_rev_i = None
                    if cli_rev_i is not None and cli_rev_i != atual_rev:
                        resp = _json.dumps({'ok': False, 'conflito': True, 'rev': atual_rev}).encode('utf-8')
                        self.send_response(409)
                        self.send_header('Content-type', 'application/json; charset=utf-8')
                        self.end_headers(); self.wfile.write(resp); return
                novo_rev = atual_rev + 1
                obj['_rev'] = novo_rev
                body = _json.dumps(obj, ensure_ascii=False)
                # Backup do arquivo anterior antes de sobrescrever
                if caminho.exists():
                    import shutil
                    bkp = _fdir / 'dados.backup.json'
                    shutil.copy2(caminho, bkp)
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.write(body)
                # Backup diario versionado (1 por dia, na pasta Backups da filial)
                try:
                    import datetime
                    pasta_bkp = _fdir / 'Backups'
                    pasta_bkp.mkdir(exist_ok=True)
                    hoje = datetime.date.today().isoformat()
                    diario = pasta_bkp / ('dados_' + hoje + '.json')
                    with open(diario, 'w', encoding='utf-8') as f:
                        f.write(body)
                    # Mantem apenas os 30 backups diarios mais recentes
                    backups = sorted(pasta_bkp.glob('dados_*.json'))
                    for antigo in backups[:-30]:
                        antigo.unlink()
                except Exception:
                    pass
                resp = _json.dumps({'ok': True, 'rev': novo_rev}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                resp = _json.dumps({'ok': False, 'erro': str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(resp)
            return
        if self.path == '/save-report':
            import json as _json
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                data = _json.loads(body)
                filename = data.get('filename', 'relatorio.txt')
                content = data.get('content', '')
                # Sanitiza nome do arquivo
                filename = ''.join(c for c in filename if c.isalnum() or c in '-_.')
                pasta = Path(__file__).parent / 'Relatorios'
                pasta.mkdir(exist_ok=True)
                caminho = pasta / filename
                with open(caminho, 'w', encoding='utf-8-sig') as f:
                    f.write(content)
                resp = _json.dumps({'ok': True, 'path': str(caminho)}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                resp = _json.dumps({'ok': False, 'erro': str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(resp)
            return
        if self.path == '/log':
            import json as _json
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                data = _json.loads(body)
                _s = self._sessao() or {}
                _quem = _s.get('nome') or 'equipe'  # backend carimba quem está logado (mais seguro)
                ok = registrar_log(data.get('acao',''), data.get('detalhe',''), _quem, self.client_address[0])
                resp = _json.dumps({'ok': ok}).encode('utf-8')
                self.send_response(200 if ok else 500)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(resp)
            except Exception as e:
                self.send_response(500); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': False, 'erro': str(e)}).encode('utf-8'))
            return
        if self.path == '/restore-backup':
            import json as _json, shutil as _sh
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            if not self._pode_editar():
                self.send_response(403); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': False, 'erro': 'Sem permissão.'}).encode('utf-8')); return
            try:
                _fdir = filial_dir()
                fn = os.path.basename((_json.loads(body).get('filename') or ''))
                src = _fdir / 'Backups' / fn
                if not (fn.startswith('dados_') and fn.endswith('.json') and src.exists()):
                    self.send_response(400); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                    self.wfile.write(_json.dumps({'ok': False, 'erro': 'Backup inválido.'}).encode('utf-8')); return
                obj = _json.loads(src.read_text(encoding='utf-8'))
                dst = _fdir / 'dados.json'
                atual_rev = 0
                if dst.exists():
                    try: atual_rev = int(_json.loads(dst.read_text(encoding='utf-8')).get('_rev', 0) or 0)
                    except Exception: atual_rev = 0
                    _sh.copy2(dst, _fdir / 'dados.backup.json')
                obj['_rev'] = atual_rev + 1
                dst.write_text(_json.dumps(obj, ensure_ascii=False), encoding='utf-8')
                _s = self._sessao() or {}
                registrar_log('Backup restaurado', fn, _s.get('nome','equipe'), self.client_address[0])
                self.send_response(200); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': True, 'rev': obj['_rev']}).encode('utf-8'))
            except Exception as e:
                self.send_response(500); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': False, 'erro': str(e)}).encode('utf-8'))
            return
        if self.path == '/usuarios':
            import json as _json
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            if not self._eh_host():
                self.send_response(403); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': False, 'erro': 'Só o computador host gerencia usuários.'}).encode('utf-8')); return
            try:
                data = _json.loads(body)
                lista = data.get('usuarios', [])
                # senha em branco = manter a atual (hash já salvo)
                existentes = {}
                for x in carregar_usuarios():
                    existentes[(x.get('nome','') or '').strip().lower()] = x.get('senha','')
                limpa = []
                for u in lista[:5]:
                    nome = (u.get('nome') or '').strip()
                    senha = (u.get('senha') or '')
                    papel = 'editor' if (u.get('papel')=='editor') else 'leitor'
                    if not nome: continue
                    senha_arm = hash_senha(senha) if senha else existentes.get(nome.lower(), '')
                    if senha_arm:
                        limpa.append({'nome': nome, 'senha': senha_arm, 'papel': papel})
                salvar_usuarios(limpa)
                registrar_log('Usuários atualizados', str(len(limpa))+' usuário(s) cadastrado(s)', 'Gattiboni (dono)', self.client_address[0])
                self.send_response(200); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': True, 'usuarios': limpa}, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(500); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': False, 'erro': str(e)}).encode('utf-8'))
            return
        if self.path == '/set-filial':
            import json as _json
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            if not self._pode_editar():
                self.send_response(403); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': False, 'erro': 'Sem permissão (somente leitura).'}).encode('utf-8')); return
            try:
                fid = (_json.loads(body).get('id') or '').strip()
                d = carregar_filiais()
                ids = [f.get('id') for f in d.get('filiais', [])]
                if fid not in ids:
                    self.send_response(400); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                    self.wfile.write(_json.dumps({'ok': False, 'erro': 'Filial inexistente.'}).encode('utf-8')); return
                d['filialAtual'] = fid
                salvar_filiais(d)
                # garante dados.json (mesmo vazio) p/ a filial — evita herdar dados de outra
                fd = filial_dir(fid)
                if not (fd / 'dados.json').exists():
                    (fd / 'dados.json').write_text(_json.dumps({'projects': [], 'nfs': [], '_rev': 0}, ensure_ascii=False), encoding='utf-8')
                nome = next((f.get('nome') for f in d['filiais'] if f.get('id')==fid), fid)
                _s = self._sessao() or {}
                registrar_log('Trocou de filial', nome, _s.get('nome','equipe'), self.client_address[0])
                self.send_response(200); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': True, 'filialAtual': fid}).encode('utf-8'))
            except Exception as e:
                self.send_response(500); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': False, 'erro': str(e)}).encode('utf-8'))
            return
        if self.path == '/filiais':
            import json as _json
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            if not self._eh_host():
                self.send_response(403); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': False, 'erro': 'Só o computador host gerencia filiais.'}).encode('utf-8')); return
            try:
                entrada = _json.loads(body).get('filiais', [])
                d = carregar_filiais()
                usados = set(); limpa = []
                for f in entrada[:20]:
                    nome = (f.get('nome') or '').strip()
                    if not nome: continue
                    cnpj = (f.get('cnpj') or '').strip()
                    fid = (f.get('id') or '').strip() or _slug(nome)
                    base = fid; i = 2
                    while fid in usados: fid = base + '_' + str(i); i += 1
                    usados.add(fid)
                    limpa.append({'id': fid, 'nome': nome, 'cnpj': cnpj})
                    # cria pasta + dados.json vazio p/ filial nova
                    fd = filial_dir(fid)
                    if not (fd / 'dados.json').exists():
                        (fd / 'dados.json').write_text(_json.dumps({'projects': [], 'nfs': [], '_rev': 0}, ensure_ascii=False), encoding='utf-8')
                if not limpa:
                    limpa = [{'id': 'matriz', 'nome': 'Matriz', 'cnpj': ''}]
                atual = d.get('filialAtual')
                if atual not in [f['id'] for f in limpa]:
                    atual = limpa[0]['id']
                salvar_filiais({'filialAtual': atual, 'filiais': limpa})
                registrar_log('Filiais atualizadas', str(len(limpa))+' filial(is)', 'Gattiboni (dono)', self.client_address[0])
                self.send_response(200); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': True, 'filiais': limpa, 'filialAtual': atual}, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(500); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': False, 'erro': str(e)}).encode('utf-8'))
            return
        self.send_response(404)
        self.end_headers()
    def do_GET(self):
        # ── BLOQUEIO DE ARQUIVOS SENSIVEIS ──
        # Impede o download direto de credenciais, tokens de sessao, banco de
        # atividades, backups e codigo-fonte — mesmo por usuario ja autenticado.
        # O frontend nao busca nenhum destes (usa endpoints /whoami, /usuarios, etc.).
        _limpo = self.path.split('?')[0].lstrip('/')
        _base = os.path.basename(_limpo).lower()
        _proibidos = {'config.json', 'sessoes.json', 'atividade.db',
                      'atividade.db-wal', 'atividade.db-shm', 'dados.backup.json',
                      'analise_precos.bak.json', 'fornecedores_novos.json'}
        if (_base in _proibidos or _base.endswith(('.py', '.pyw', '.bak'))
                or _limpo.lower().startswith('filiais/') and _base == 'dados.backup.json'
                or '/backups/' in ('/' + _limpo.lower())):
            self.send_response(403)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write('403 - acesso negado'.encode('utf-8'))
            return
        # Arquivos do PWA são públicos (senão o celular recebe a tela de login no lugar deles)
        if self.path.split('?')[0] in ('/manifest.json', '/icon.svg', '/sw.js'):
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        if not self._autenticado():
            body = LOGIN_HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers(); self.wfile.write(body)
            return
        # Arquivos separados por filial: serve a versão da filial ativa
        _basef = self.path.split('?')[0].lstrip('/')
        if _basef in PER_FILIAL:
            qs = ('?' + self.path.split('?', 1)[1]) if '?' in self.path else ''
            self.path = '/filiais/' + filial_atual_id() + '/' + _basef + qs
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        if self.path == '/historico' or self.path.startswith('/historico?'):
            import json as _json
            rows = consultar_log(800)
            resp = _json.dumps({'ok': True, 'log': rows}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers(); self.wfile.write(resp)
            return
        if self.path == '/whoami' or self.path.startswith('/whoami?'):
            import json as _json
            s = self._sessao() or {'nome':'?','papel':'leitor','host':False}
            resp = _json.dumps({'ok': True, 'nome': s.get('nome'), 'papel': s.get('papel'), 'host': bool(s.get('host'))}, ensure_ascii=False).encode('utf-8')
            self.send_response(200); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(resp)
            return
        if self.path == '/filiais' or self.path.startswith('/filiais?'):
            import json as _json
            d = carregar_filiais()
            resp = _json.dumps({'ok': True, 'filialAtual': filial_atual_id(), 'filiais': d.get('filiais', [])}, ensure_ascii=False).encode('utf-8')
            self.send_response(200); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(resp)
            return
        if self.path == '/usuarios' or self.path.startswith('/usuarios?'):
            import json as _json
            if not self._eh_host():
                self.send_response(403); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': False, 'erro': 'Só o computador host gerencia usuários.'}).encode('utf-8')); return
            # devolve a lista SEM a senha (hash) — só nome/papel + se tem senha
            seguro = [{'nome': u.get('nome'), 'papel': (u.get('papel') or 'editor'), 'tem_senha': bool(u.get('senha'))} for u in carregar_usuarios()]
            resp = _json.dumps({'ok': True, 'usuarios': seguro}, ensure_ascii=False).encode('utf-8')
            self.send_response(200); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(resp)
            return
        if self.path == '/backups' or self.path.startswith('/backups?'):
            import json as _json, datetime as _dtb
            if not self._pode_editar():
                self.send_response(403); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers()
                self.wfile.write(_json.dumps({'ok': False, 'erro': 'Sem permissão.'}).encode('utf-8')); return
            pasta = filial_dir() / 'Backups'
            arr = []
            if pasta.exists():
                for f in sorted(pasta.glob('dados_*.json'), reverse=True):
                    try:
                        st = f.stat()
                        arr.append({'nome': f.name, 'tamanho': st.st_size, 'data': _dtb.datetime.fromtimestamp(st.st_mtime).isoformat(timespec='seconds')})
                    except Exception: pass
            resp = _json.dumps({'ok': True, 'backups': arr}, ensure_ascii=False).encode('utf-8')
            self.send_response(200); self.send_header('Content-type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(resp)
            return
        if self.path == '/' or self.path == '':
            self.path = '/index.html'
        elif self.path == '/setup':
            # Endpoint que injeta dados e faz reload
            response = """<html><head><meta charset="utf-8"><title>Setup</title></head><body>
<h1 style="font-family:monospace;color:#55ff55;text-align:center;padding:50px">Loading data...</h1>
<script>
function uid(){return Math.random().toString(36).substr(2,7);}
var S={projects:[
{id:'datacom',nome:'Datacom',desc:'',cliente:'',data:'',items:[],services:[]},
{id:'edificio_sharm',nome:'Edificio Sharm',desc:'',cliente:'',data:'',items:[],services:[]},
{id:'darkstore',nome:'DarkStore',desc:'',cliente:'',data:'',items:[],services:[]},
{id:'chandon',nome:'CHANDON',desc:'',cliente:'',data:'',items:[],services:[]},
{id:'escola_mesquita',nome:'Escola Mesquita',desc:'',cliente:'',data:'',items:[],services:[]},
{id:'lifar_torniquete',nome:'LIFAR TORNIQUETE',desc:'',cliente:'',data:'',items:[],services:[]},
{id:'alegrete',nome:'ALEGRETE',desc:'',cliente:'',data:'',items:[],services:[]},
{id:'b_print_ceara',nome:'B_Print_Ceara',desc:'',cliente:'',data:'',items:[],services:[]},
{id:'new_print_sca',nome:'New_Print_SCA',desc:'',cliente:'',data:'',items:[],services:[]},
{id:'cd_sao_jose',nome:'CD SAO JOSE',desc:'',cliente:'',data:'',items:[],services:[]}
],nfs:[],curProj:null,view:'dashboard',tab:'resumo'};
var sh=S.projects.find(p=>p.id==='edificio_sharm');
sh.items=[
{id:uid(),nome:'NVR 32',prev:1846.88,real:1768,cat:'CFTV',extra:false},
{id:uid(),nome:'HD 6TB',prev:1089.10,real:1790,cat:'CFTV',extra:false},
{id:uid(),nome:'Camera',prev:3101.40,real:0,cat:'CFTV',extra:false},
{id:uid(),nome:'Switch',prev:1578.07,real:1578.07,cat:'CFTV',extra:false},
{id:uid(),nome:'Router',prev:442,real:436.45,cat:'CFTV',extra:false},
{id:uid(),nome:'Controlador (x6)',prev:4674,real:4388.76,cat:'Controle de Acesso',extra:false},
{id:uid(),nome:'Mola (x5)',prev:936.60,real:936.60,cat:'Controle de Acesso',extra:false},
{id:uid(),nome:'Eletroima (x5)',prev:1278,real:1278,cat:'Controle de Acesso',extra:false},
{id:uid(),nome:'Fonte (x5)',prev:1173.15,real:760.85,cat:'Controle de Acesso',extra:false},
{id:uid(),nome:'Leitor UHF (x2)',prev:5980.80,real:5980.80,cat:'Controle de Acesso',extra:false},
{id:uid(),nome:'Tag UHF (x100)',prev:1091,real:1091,cat:'Controle de Acesso',extra:false},
{id:uid(),nome:'Controladora',prev:1000.36,real:960.35,cat:'Controle de Acesso',extra:false},
{id:uid(),nome:'Botoeira (x2)',prev:154.84,real:154.84,cat:'Controle de Acesso',extra:false},
{id:uid(),nome:'Acionador (x5)',prev:643.70,real:643.70,cat:'Controle de Acesso',extra:false},
{id:uid(),nome:'Quadro',prev:352,real:352,cat:'Infraestrutura',extra:false},
{id:uid(),nome:'Suporte (x2)',prev:800,real:800,cat:'Infraestrutura',extra:false}
];
var dk=S.projects.find(p=>p.id==='darkstore');
dk.items=[
{id:uid(),nome:'Camera (x16)',prev:3147.84,real:2888.32,cat:'CFTV',extra:false},
{id:uid(),nome:'NVR',prev:840.98,real:840.98,cat:'CFTV',extra:false},
{id:uid(),nome:'HD',prev:1279.90,real:1682.48,cat:'Materiais',extra:false},
{id:uid(),nome:'Caixa Ext (x6)',prev:87.24,real:82.86,cat:'Materiais',extra:false},
{id:uid(),nome:'Caixa Int (x10)',prev:68.50,real:68.40,cat:'Materiais',extra:false},
{id:uid(),nome:'Rack',prev:182.49,real:204.74,cat:'Infraestrutura',extra:false},
{id:uid(),nome:'Cabo',prev:851.00,real:435.71,cat:'Cabeamento',extra:false},
{id:uid(),nome:'Organizador',prev:47.96,real:50.15,cat:'Cabeamento',extra:false},
{id:uid(),nome:'Patch',prev:27.15,real:28.38,cat:'Cabeamento',extra:false},
{id:uid(),nome:'Regua',prev:70.14,real:70.13,cat:'Energia',extra:false},
{id:uid(),nome:'Switch',prev:939.97,real:939.96,cat:'Rede',extra:false},
{id:uid(),nome:'Alarme',prev:436.54,real:0,cat:'Alarme',extra:false},
{id:uid(),nome:'Sirene',prev:19.87,real:0,cat:'Alarme',extra:false},
{id:uid(),nome:'Teclado',prev:195.64,real:0,cat:'Alarme',extra:false},
{id:uid(),nome:'Botao',prev:62.97,real:0,cat:'Alarme',extra:false},
{id:uid(),nome:'Sensor',prev:2069.28,real:2069.28,cat:'Alarme',extra:false},
{id:uid(),nome:'Licenca',prev:0,real:0,cat:'Software',extra:false}
];
var ce=S.projects.find(p=>p.id==='b_print_ceara');
ce.items=[
{id:uid(),nome:'Camera',prev:3120.40,real:2995.00,cat:'CFTV',extra:false},
{id:uid(),nome:'Licenca',prev:2186.89,real:2842.96,cat:'Software',extra:false}
];
localStorage.setItem('dc_v5',JSON.stringify(S));
var t=0;
S.projects.forEach(p=>{p.items.forEach(i=>t+=Number(i.real)||0);p.services.forEach(s=>t+=Number(s.real)||0);});
document.body.innerHTML='<h1 style=\"color:#55ff55;font-family:monospace;text-align:center;padding:50px\">OK: R$ '+t.toFixed(2)+'</h1>';
setTimeout(()=>window.location.href='/',1500);
</script>
</body></html>""".encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(response)
            return
        elif self.path == '/complete-data':
            # Endpoint que retorna JavaScript para completar dados
            response = """<html><head><title>Completa Dados</title></head><body>
<pre id="log"></pre>
<script>
function uid(){return Math.random().toString(36).substr(2,7);}
var log_el = document.getElementById('log');
function log(msg){log_el.innerHTML += msg + '\\n'; console.log(msg);}

try {
  var S = JSON.parse(localStorage.getItem('dc_v5') || '{}');
  log('Projetos: ' + S.projects.length);
  log('OK');
} catch(e) {
  log('ERROR: ' + e.message);
}
</script>
</body></html>
""".encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(response)
            return
        return super().do_GET()

class ServidorThreaded(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

servidor = ServidorThreaded(('0.0.0.0', porta), Handler)
thread = threading.Thread(target=servidor.serve_forever, daemon=True)
thread.start()

# Grava o endereco de acesso da rede num arquivo para o usuario compartilhar
try:
    _hostname = socket.gethostname()
    # Lista todos os IPv4 da maquina (Wi-Fi, Ethernet, etc.)
    _ips = []
    try:
        for _info in socket.getaddrinfo(_hostname, None, socket.AF_INET):
            _a = _info[4][0]
            if _a not in _ips and not _a.startswith('127.') and not _a.startswith('169.'):
                _ips.append(_a)
    except Exception:
        pass
    if not _ips:
        _ips = [ip_local()]
    _linhas_ip = ''.join(['        http://' + _a + ':' + str(porta) + '\n' for _a in _ips])
    _txt = ('COMO OUTRAS PESSOAS ACESSAM (mesma rede / Wi-Fi)\n'
            '================================================\n\n'
            'OPCAO 1 (recomendada - NAO muda quando o IP troca):\n'
            '        http://' + _hostname + ':' + str(porta) + '\n\n'
            'OPCAO 2 (por IP - pode mudar de tempos em tempos):\n'
            + _linhas_ip + '\n'
            'Senha da equipe:  ' + SENHA + '\n\n'
            '------------------------------------------------\n'
            'IMPORTANTE - se nao abrir no outro computador:\n'
            '  - Libere a porta no Firewall do Windows (uma vez).\n'
            '    Abra o PowerShell COMO ADMINISTRADOR e cole:\n'
            '    New-NetFirewallRule -DisplayName "Projetos Suprimentos" -Direction Inbound -Protocol TCP -LocalPort ' + str(porta) + ' -Action Allow\n'
            '  - Este computador precisa estar ligado e com o app aberto.\n'
            '  - Para trocar a senha: edite config.json e reabra o app.\n')
    (Path(__file__).parent / 'ACESSO_REDE.txt').write_text(_txt, encoding='utf-8')
except Exception:
    pass

import json, random, string

def uid():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))

novos_items = [
    {"id": uid(), "nome": "NVR 32 Canais — Hikvision DS-7632NXI-K2", "prev": 1846.88, "real": 1768.00, "cat": "CFTV", "extra": False},
    {"id": uid(), "nome": "HD 6TB — Seagate Skyhawk", "prev": 1089.10, "real": 1790.00, "cat": "CFTV", "extra": False},
    {"id": uid(), "nome": "Câmera IP 2MP (×20) — Hilook IPC-B121H-C", "prev": 3101.40, "real": 0.00, "cat": "CFTV", "extra": False},
    {"id": uid(), "nome": "Rack 8U — Intelbras MRM 537", "prev": 189.17, "real": 0.00, "cat": "CFTV", "extra": False},
    {"id": uid(), "nome": "Bandeja Rack 1U — Intelbras P290", "prev": 64.77, "real": 0.00, "cat": "CFTV", "extra": False},
    {"id": uid(), "nome": "Guia de Cabos — Intelbras P50", "prev": 26.24, "real": 26.24, "cat": "CFTV", "extra": False},
    {"id": uid(), "nome": "Switch PoE 24 Portas — Intelbras S2328G-A", "prev": 1578.07, "real": 1578.07, "cat": "CFTV", "extra": False},
    {"id": uid(), "nome": "Routerboard — Mikrotik RB 750GR3", "prev": 442.00, "real": 436.45, "cat": "CFTV", "extra": False},
    {"id": uid(), "nome": "Caixa de Passagem CFTV (×20) — Intelbras VBOX 1100E", "prev": 303.40, "real": 303.40, "cat": "CFTV", "extra": False},
    {"id": uid(), "nome": "Cabo UTP CAT5E (780m) — Intelbras IL5CAZ", "prev": 1318.20, "real": 1029.60, "cat": "CFTV", "extra": False},
    {"id": uid(), "nome": "Controlador Facial (×6) — Hikvision DS-K1T671M-L", "prev": 4674.00, "real": 4388.76, "cat": "Controle de Acesso", "extra": False},
    {"id": uid(), "nome": "Sistema Controle de Acesso Cloud — Seventh App CA", "prev": 0.00, "real": 0.00, "cat": "Controle de Acesso", "extra": False},
    {"id": uid(), "nome": "Mola Aérea (×5) — Intelbras MH 104A", "prev": 936.60, "real": 936.60, "cat": "Controle de Acesso", "extra": False},
    {"id": uid(), "nome": "Eletroímã 150kgf (×5) — Intelbras FE 20150", "prev": 1278.00, "real": 1278.00, "cat": "Controle de Acesso", "extra": False},
    {"id": uid(), "nome": "Fonte Nobreak 12V c/ Bateria (×5) — JFL Full Power 512", "prev": 1173.15, "real": 760.85, "cat": "Controle de Acesso", "extra": False},
    {"id": uid(), "nome": "Botoeira (×2) — Intelbras BT 3000 IN", "prev": 154.84, "real": 154.84, "cat": "Controle de Acesso", "extra": False},
    {"id": uid(), "nome": "Acionador de Emergência (×5) — Intelbras AS 2010", "prev": 643.70, "real": 643.70, "cat": "Controle de Acesso", "extra": False},
    {"id": uid(), "nome": "Controladora de Acesso 2 Portas — Intelbras CT 3000 2PB", "prev": 1000.36, "real": 960.35, "cat": "Controle de Acesso", "extra": False},
    {"id": uid(), "nome": "Leitor Tag Veicular UHF (×2) — Solid Leitor Integrado", "prev": 5980.80, "real": 5980.80, "cat": "Controle de Acesso", "extra": False},
    {"id": uid(), "nome": "Tag UHF Interno (×100) — Solid Tag 110", "prev": 1091.00, "real": 1091.00, "cat": "Controle de Acesso", "extra": False},
    {"id": uid(), "nome": "Quadro de Comando — Diversos", "prev": 352.00, "real": 352.00, "cat": "Infraestrutura", "extra": False},
    {"id": uid(), "nome": "Suporte para Leitor UHF (×2) — Serralheria", "prev": 800.00, "real": 800.00, "cat": "Infraestrutura", "extra": False},
]

items_json = json.dumps(novos_items, ensure_ascii=False)

hot_reload_js = """
(function(){
  var lastHash = '';
  setInterval(function(){
    fetch(window.location.href + '?t=' + Date.now())
      .then(r => r.text())
      .then(html => {
        var hash = html.substring(html.indexOf('<style>'), html.indexOf('</style>') + 8);
        if(lastHash && hash !== lastHash){
          console.log('🔄 Arquivo alterado, recarregando...');
          location.reload();
        }
        lastHash = hash;
      })
      .catch(e => {});
  }, 1000);
})();
"""

js_inject = f"""
(function(){{
  var raw = localStorage.getItem('dc_v5');
  if(!raw) return;
  var S = JSON.parse(raw);
  var proj = S.projects.find(function(p){{ return p.nome.toLowerCase().includes('sharm'); }});
  if(!proj) return;
  if(!proj.items) proj.items = [];
  var jaInjetado = proj.items.find(function(i){{ return i.nome && i.nome.includes('NVR 32 Canais'); }});
  if(jaInjetado) return;
  var novos = {items_json};
  proj.items = proj.items.concat(novos);
  localStorage.setItem('dc_v5', JSON.stringify(S));
  location.reload();
}})();
"""

def on_loaded(window):
    pass

window = webview.create_window(
    'Projetos Suprimentos',
    f'http://localhost:{porta}',
    width=1400,
    height=900,
    min_size=(800, 600)
)
webview.start(on_loaded, window)
