// Service worker mínimo: só habilita a instalação (PWA).
// NÃO faz cache — os dados são centralizados no servidor (sempre online/atualizados).
self.addEventListener('install', function(e){ self.skipWaiting(); });
self.addEventListener('activate', function(e){ self.clients.claim(); });
self.addEventListener('fetch', function(e){ /* passthrough: deixa a rede responder normalmente */ });
