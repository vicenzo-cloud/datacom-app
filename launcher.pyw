import webview
import http.server
import socketserver
import threading
import socket
import os
from pathlib import Path

def encontrar_porta(inicial=5000):
    for porta in range(inicial, inicial + 100):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('localhost', porta))
            s.close()
            return porta
        except OSError:
            continue
    return inicial

os.chdir(Path(__file__).parent)

porta = encontrar_porta()

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    def do_POST(self):
        if self.path == '/save-data':
            # Persiste os dados dos projetos/NFs em dados.json (backup em disco)
            import json as _json
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            try:
                _json.loads(body)  # valida que e JSON valido
                caminho = Path(__file__).parent / 'dados.json'
                # Backup do arquivo anterior antes de sobrescrever
                if caminho.exists():
                    import shutil
                    bkp = Path(__file__).parent / 'dados.backup.json'
                    shutil.copy2(caminho, bkp)
                with open(caminho, 'w', encoding='utf-8') as f:
                    f.write(body)
                resp = _json.dumps({'ok': True}).encode('utf-8')
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
        self.send_response(404)
        self.end_headers()
    def do_GET(self):
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

servidor = socketserver.TCPServer(('localhost', porta), Handler)
thread = threading.Thread(target=servidor.serve_forever, daemon=True)
thread.start()

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
