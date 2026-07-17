// Service Worker para Gestão à Vista PWA - Regional Centro Oeste
const CACHE_NAME = 'gestao-vista-v2';
const CACHE_VERSION = '2.0.0';

// URLs para cache inicial (arquivos estáticos críticos)
const STATIC_CACHE_URLS = [
  '/',
  '/home/',
  '/dashboard/',
  '/qr-generator/',
  '/gestao-qualidade/',
  '/monitoramento/',
  '/static/img/logo.png',
  '/static/img/background.png',
  '/static/manifest.json',
  '/static/js/notifications.min.js',
  // CDNs são carregados dinamicamente
];

// URLs da API que devem ser cacheadas para offline
const API_CACHE_URLS = [
  '/api/gestao-qualidade/treinamento/',
  '/api/gestao-qualidade/visita-tecnica/',
  '/api/gestao-qualidade/nao-conformidade/',
  '/api/gestao-qualidade/plano-acao/',
  '/api/locations/',
  '/api/service-logo/',
];

// ============ INSTALAÇÃO ============
self.addEventListener('install', (event) => {
  console.log('[SW] Instalando Service Worker...');

  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Cache aberto, adicionando URLs estáticas...');
      // Adiciona URLs estáticas ao cache
      return cache.addAll(STATIC_CACHE_URLS.map(url => new Request(url, {cache: 'reload'})));
    }).then(() => {
      console.log('[SW] Service Worker instalado com sucesso!');
      return self.skipWaiting(); // Ativa imediatamente
    }).catch((error) => {
      console.error('[SW] Erro ao instalar Service Worker:', error);
    })
  );
});

// ============ ATIVAÇÃO ============
self.addEventListener('activate', (event) => {
  console.log('[SW] Ativando Service Worker...');

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Remove caches antigos
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Removendo cache antigo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[SW] Service Worker ativado!');
      return self.clients.claim(); // Assume controle imediatamente
    })
  );
});

// ============ FETCH (Interceptação de Requisições) ============
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignora requisições não-HTTP/HTTPS
  if (!request.url.startsWith('http')) {
    return;
  }

  // Ignora requisições POST/PUT/DELETE (mantém online-only)
  if (request.method !== 'GET') {
    return;
  }

  // ===== ESTRATÉGIA: Cache First para recursos estáticos =====
  if (isStaticAsset(url)) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          console.log('[SW] Cache hit (estático):', url.pathname);
          return cachedResponse;
        }

        // Não está no cache, busca da rede e cacheia
        return fetch(request).then((networkResponse) => {
          // Só cacheia respostas OK
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return networkResponse;
        }).catch((error) => {
          console.error('[SW] Erro ao buscar recurso estático:', error);
          // Retorna página offline se disponível
          return caches.match('/offline.html');
        });
      })
    );
    return;
  }

  // ===== ESTRATÉGIA: Network First com Cache Fallback para API =====
  if (isApiRequest(url)) {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          // Se sucesso, atualiza cache e retorna
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseToCache);
              console.log('[SW] API cacheada:', url.pathname);
            });
          }
          return networkResponse;
        })
        .catch(() => {
          // Se falhar, tenta buscar do cache
          console.log('[SW] Rede falhou, buscando do cache:', url.pathname);
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              console.log('[SW] Cache hit (API offline):', url.pathname);
              return cachedResponse;
            }
            // Se não tem cache, retorna erro offline
            return new Response(
              JSON.stringify({
                error: 'Sem conexão com a internet',
                offline: true,
                message: 'Você está offline. Os dados podem estar desatualizados.'
              }),
              {
                status: 503,
                statusText: 'Service Unavailable',
                headers: { 'Content-Type': 'application/json' }
              }
            );
          });
        })
    );
    return;
  }

  // ===== ESTRATÉGIA: Network First para páginas HTML =====
  if (isHtmlRequest(url)) {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          // Cacheia a resposta
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseToCache);
          });
          return networkResponse;
        })
        .catch(() => {
          // Se falhar, busca do cache
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            // Fallback para página offline
            return caches.match('/gestao-qualidade/');
          });
        })
    );
    return;
  }

  // ===== Padrão: Network Only para todo o resto =====
  event.respondWith(fetch(request));
});

// ============ FUNÇÕES AUXILIARES ============

function isStaticAsset(url) {
  const staticExtensions = ['.css', '.js', '.png', '.jpg', '.jpeg', '.svg', '.ico', '.woff', '.woff2', '.ttf'];
  return staticExtensions.some(ext => url.pathname.endsWith(ext)) || url.pathname.includes('/static/');
}

function isApiRequest(url) {
  return url.pathname.startsWith('/api/');
}

function isHtmlRequest(url) {
  return url.pathname.endsWith('/') ||
         url.pathname.endsWith('.html') ||
         (!url.pathname.includes('.') && !url.pathname.startsWith('/api/'));
}

// ============ MENSAGENS DO CLIENTE ============
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('[SW] Recebido SKIP_WAITING, ativando nova versão...');
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CACHE_URLS') {
    console.log('[SW] Recebido pedido para cachear URLs:', event.data.urls);
    event.waitUntil(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.addAll(event.data.urls);
      })
    );
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    console.log('[SW] Limpando cache...');
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      }).then(() => {
        console.log('[SW] Cache limpo!');
        return self.clients.matchAll();
      }).then((clients) => {
        clients.forEach(client => {
          client.postMessage({ type: 'CACHE_CLEARED' });
        });
      })
    );
  }
});

// ============ SINCRONIZAÇÃO EM BACKGROUND ============
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync event:', event.tag);

  if (event.tag === 'sync-quality-data') {
    event.waitUntil(
      // Aqui você pode implementar sincronização de dados pendentes
      syncQualityData()
    );
  }
});

async function syncQualityData() {
  console.log('[SW] Sincronizando dados da qualidade...');
  // Implementar lógica de sincronização quando necessário
  return Promise.resolve();
}

// ============ NOTIFICAÇÕES PUSH (Opcional) ============
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification recebida');

  const options = {
    body: event.data ? event.data.text() : 'Nova atualização disponível',
    icon: '/static/img/icon-192x192.png',
    badge: '/static/img/icon-72x72.png',
    vibrate: [200, 100, 200],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Ver agora',
        icon: '/static/img/icon-192x192.png'
      },
      {
        action: 'close',
        title: 'Fechar',
        icon: '/static/img/icon-192x192.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('Gestão à Vista', options)
  );
});

self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notificação clicada:', event.action);
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/gestao-qualidade/')
    );
  }
});

console.log('[SW] Service Worker carregado - versão', CACHE_VERSION);
