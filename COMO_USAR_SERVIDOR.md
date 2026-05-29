# 🚀 Servidor Local Datacom App

## ⚡ Rápido Start (2 passos)

### Passo 1️⃣: Iniciar Servidor
1. Na pasta `C:\Users\Gattyboni\datacom-app`
2. **Duplo clique em: `INICIAR_SERVIDOR.bat`**
3. Verá uma janela com:
   ```
   ✅ Servidor iniciado com sucesso!
   🌐 Acesse em: http://localhost:5000
   ```

### Passo 2️⃣: Acessar o App
1. Abra seu navegador (Chrome, Firefox, Edge, etc)
2. Na barra de endereço, digite:
   ```
   http://localhost:5000
   ```
3. Pressione **ENTER** ✅

---

## 🔄 Como usar

**Opção A - Automático:**
- Duplo clique em `ACESSAR_APP.bat` (abre navegador automaticamente)

**Opção B - Manual:**
- Copie e cole na barra: `http://localhost:5000`

---

## 📋 Estrutura

```
datacom-app/
├── INICIAR_SERVIDOR.bat      ← Inicia o servidor
├── ACESSAR_APP.bat           ← Abre no navegador
├── servidor.py               ← Código do servidor (Flask)
├── index.html                ← Seu app (372 KB)
├── COMO_USAR_SERVIDOR.md     ← Este guia
└── requirements.txt          ← Dependências
```

---

## ⚙️ Informações Técnicas

- **Servidor**: Flask (Python)
- **Endereço**: http://localhost:5000
- **Porta**: 5000
- **Acesso**: Apenas você (local)
- **Offline**: Funciona sem internet (recursos externos via CDN)

---

## 🛑 Para Parar o Servidor

Clique na janela do servidor e pressione:
```
CTRL + C
```

Aparecerá:
```
✅ App fechado
```

---

## ❓ Troubleshooting

### "Python não encontrado"
- Instale: https://python.org/downloads
- Marque "Add Python to PATH"
- Reinicie o computador

### "Porta 5000 já está em uso"
- Feche outras aplicações
- Ou edite `servidor.py` e mude `port=5000` para `port=5001`

### "Não consegue conectar"
- Verifique se servidor está rodando (veja a janela do bat)
- Tente: `http://127.0.0.1:5000`
- Aguarde 3 segundos após iniciar o servidor

---

## 💾 Resumo Rápido

| O que? | Como? |
|--------|-------|
| Iniciar servidor | Duplo clique: `INICIAR_SERVIDOR.bat` |
| Acessar app | `http://localhost:5000` ou clique em `ACESSAR_APP.bat` |
| Parar servidor | `CTRL + C` na janela do servidor |

---

**Pronto para usar! 🎉**

```
Servidor → http://localhost:5000 → Navegador
```
