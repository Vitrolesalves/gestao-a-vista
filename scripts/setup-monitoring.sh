#!/bin/bash

# Script para configurar monitoramento completo do Gestão à Vista

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo -e "${BLUE}🔧 Configurando Monitoramento - Gestão à Vista${NC}"
echo -e "${BLUE}================================================${NC}"

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    print_error "Docker não está instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose não está instalado"
    exit 1
fi

print_status "Docker e Docker Compose encontrados"

# Criar diretórios necessários
print_info "Criando diretórios de monitoramento..."

mkdir -p logs/{nginx,postgresql,grafana,prometheus}
mkdir -p monitoring/{grafana,prometheus,alertmanager}
mkdir -p backups/monitoring

print_status "Diretórios criados"

# Configurar permissões
print_info "Configurando permissões..."

# Grafana precisa de UID 472
sudo chown -R 472:472 monitoring/grafana || true
sudo chown -R 65534:65534 monitoring/prometheus || true

print_status "Permissões configuradas"

# Instalar dependências Python para métricas
print_info "Instalando dependências Python..."

if [ -f "requirements-monitoring.txt" ]; then
    pip install -r requirements-monitoring.txt
else
    pip install prometheus-client python-json-logger sentry-sdk psutil
fi

print_status "Dependências Python instaladas"

# Configurar Prometheus
print_info "Configurando Prometheus..."

if [ ! -f "monitoring/prometheus/prometheus.yml" ]; then
    cp docker/prometheus.yml monitoring/prometheus/prometheus.yml
    cp docker/alert_rules.yml monitoring/prometheus/alert_rules.yml
fi

print_status "Prometheus configurado"

# Configurar Grafana
print_info "Configurando Grafana..."

mkdir -p monitoring/grafana/{dashboards,provisioning/{dashboards,datasources}}

# Copiar configurações de provisioning
cp -r docker/grafana/provisioning/* monitoring/grafana/provisioning/

# Criar dashboard básico
cat > monitoring/grafana/dashboards/gestao-a-vista-overview.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Gestão à Vista - Overview",
    "tags": ["gestao-a-vista"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "HTTP Requests Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(django_http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ],
        "yAxes": [
          {
            "label": "requests/sec"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        }
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(django_http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(django_http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ],
        "yAxes": [
          {
            "label": "seconds"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 0
        }
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(django_http_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "5xx errors"
          },
          {
            "expr": "rate(django_http_requests_total{status=~\"4..\"}[5m])",
            "legendFormat": "4xx errors"
          }
        ],
        "yAxes": [
          {
            "label": "errors/sec"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 8
        }
      },
      {
        "id": 4,
        "title": "Active Users",
        "type": "singlestat",
        "targets": [
          {
            "expr": "django_user_sessions_active"
          }
        ],
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 8
        }
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
EOF

print_status "Grafana configurado"

# Configurar Alertmanager
print_info "Configurando Alertmanager..."

mkdir -p monitoring/alertmanager

cat > monitoring/alertmanager/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@gestaoavista.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  email_configs:
  - to: 'admin@gestaoavista.com'
    subject: 'Gestão à Vista Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
  webhook_configs:
  - url: 'http://localhost:5001/webhook'
    send_resolved: true

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
EOF

print_status "Alertmanager configurado"

# Configurar ELK Stack
print_info "Configurando ELK Stack..."

mkdir -p monitoring/elasticsearch/data
mkdir -p monitoring/kibana/config

# Configuração do Kibana
cat > monitoring/kibana/config/kibana.yml << 'EOF'
server.name: kibana
server.host: "0.0.0.0"
elasticsearch.hosts: [ "http://elasticsearch:9200" ]
monitoring.ui.container.elasticsearch.enabled: true
EOF

# Configurar permissões para Elasticsearch
sudo chown -R 1000:1000 monitoring/elasticsearch || true

print_status "ELK Stack configurado"

# Criar docker-compose para monitoramento
print_info "Criando docker-compose para monitoramento..."

cat > docker-compose.monitoring.yml << 'EOF'
version: '3.8'

services:
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    restart: unless-stopped
    networks:
      - monitoring

  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - ./monitoring/grafana:/etc/grafana/provisioning
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-piechart-panel,grafana-worldmap-panel
    restart: unless-stopped
    networks:
      - monitoring

  # Alertmanager
  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager:/etc/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
    restart: unless-stopped
    networks:
      - monitoring

  # Node Exporter
  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    restart: unless-stopped
    networks:
      - monitoring

  # Elasticsearch
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.8.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    volumes:
      - ./monitoring/elasticsearch/data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    restart: unless-stopped
    networks:
      - monitoring

  # Logstash
  logstash:
    image: docker.elastic.co/logstash/logstash:8.8.0
    container_name: logstash
    volumes:
      - ./docker/logstash/pipeline:/usr/share/logstash/pipeline
      - ./docker/logstash/templates:/usr/share/logstash/templates
      - ./logs:/logs:ro
    environment:
      - "LS_JAVA_OPTS=-Xmx256m -Xms256m"
      - ENVIRONMENT=${ENVIRONMENT:-development}
    depends_on:
      - elasticsearch
    restart: unless-stopped
    networks:
      - monitoring

  # Kibana
  kibana:
    image: docker.elastic.co/kibana/kibana:8.8.0
    container_name: kibana
    ports:
      - "5601:5601"
    volumes:
      - ./monitoring/kibana/config:/usr/share/kibana/config
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    restart: unless-stopped
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
    driver: bridge
EOF

print_status "Docker Compose para monitoramento criado"

# Criar script de inicialização
print_info "Criando script de inicialização..."

cat > scripts/start-monitoring.sh << 'EOF'
#!/bin/bash

echo "🚀 Iniciando stack de monitoramento..."

# Iniciar serviços de monitoramento
docker-compose -f docker-compose.monitoring.yml up -d

echo "⏳ Aguardando serviços iniciarem..."
sleep 30

# Verificar se serviços estão rodando
echo "🔍 Verificando serviços..."

services=("prometheus:9090" "grafana:3000" "elasticsearch:9200" "kibana:5601")

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if curl -f "http://localhost:$port" > /dev/null 2>&1; then
        echo "✅ $name está rodando em http://localhost:$port"
    else
        echo "❌ $name não está respondendo"
    fi
done

echo ""
echo "🎉 Stack de monitoramento iniciado!"
echo ""
echo "📊 Acesse os serviços:"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo "  - Kibana: http://localhost:5601"
echo "  - Alertmanager: http://localhost:9093"
echo ""
echo "📈 Para parar os serviços:"
echo "  docker-compose -f docker-compose.monitoring.yml down"
EOF

chmod +x scripts/start-monitoring.sh

print_status "Script de inicialização criado"

# Criar requirements para monitoramento
print_info "Criando requirements para monitoramento..."

cat > requirements-monitoring.txt << 'EOF'
# Monitoramento e Métricas
prometheus-client==0.19.0
python-json-logger==2.0.7
sentry-sdk[django]==1.38.0
psutil==5.9.6

# Logging estruturado
structlog==23.2.0
colorlog==6.8.0

# Métricas de sistema
py-cpuinfo==9.0.0
GPUtil==1.4.0

# Alertas
requests==2.31.0
slack-sdk==3.26.1
EOF

print_status "Requirements criado"

# Atualizar settings.py com configurações de monitoramento
print_info "Atualizando configurações Django..."

cat >> Gestao_a_Vista/settings.py << 'EOF'

# Configurações de Monitoramento
from .logging_config import LOGGING_CONFIG
import os

# Aplicar configuração de logging
LOGGING = LOGGING_CONFIG

# Middleware de monitoramento
MIDDLEWARE += [
    'Gestao_a_Vista.monitoring_middleware.HealthCheckMiddleware',
    'Gestao_a_Vista.monitoring_middleware.MonitoringMiddleware',
    'Gestao_a_Vista.monitoring_middleware.SecurityMiddleware',
    'Gestao_a_Vista.monitoring_middleware.UserActivityMiddleware',
    'Gestao_a_Vista.monitoring_middleware.PerformanceMiddleware',
]

# Configurações de métricas
PROMETHEUS_METRICS_EXPORT_PORT = 8001
PROMETHEUS_METRICS_EXPORT_ADDRESS = '0.0.0.0'

# Health check
HEALTH_CHECK_ENABLED = True
HEALTH_CHECK_URL = '/health/'

# Sentry (se configurado)
if 'SENTRY_DSN' in os.environ:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    
    sentry_sdk.init(
        dsn=os.environ['SENTRY_DSN'],
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
EOF

print_status "Configurações Django atualizadas"

# Criar documentação
print_info "Criando documentação de monitoramento..."

cat > docs/MONITORING.md << 'EOF'
# 📊 Monitoramento - Gestão à Vista

## Visão Geral

O sistema de monitoramento do Gestão à Vista inclui:

- **Prometheus**: Coleta de métricas
- **Grafana**: Dashboards e visualização
- **Elasticsearch**: Armazenamento de logs
- **Logstash**: Processamento de logs
- **Kibana**: Análise de logs
- **Alertmanager**: Gerenciamento de alertas

## Inicialização

```bash
# Configurar monitoramento
./scripts/setup-monitoring.sh

# Iniciar serviços
./scripts/start-monitoring.sh
```

## Acesso aos Serviços

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601
- **Alertmanager**: http://localhost:9093

## Métricas Disponíveis

### Aplicação
- `django_http_requests_total`: Total de requisições HTTP
- `django_http_request_duration_seconds`: Duração das requisições
- `django_user_sessions_active`: Sessões ativas
- `django_failed_logins_total`: Tentativas de login falhadas

### Sistema
- `node_cpu_seconds_total`: Uso de CPU
- `node_memory_MemTotal_bytes`: Memória total
- `node_filesystem_size_bytes`: Espaço em disco

## Alertas Configurados

- Aplicação indisponível
- Alta taxa de erro
- Tempo de resposta alto
- Uso excessivo de recursos
- Eventos de segurança

## Logs Estruturados

Os logs são enviados para Elasticsearch com os seguintes tipos:

- `django`: Logs da aplicação
- `security`: Eventos de segurança
- `audit`: Trilha de auditoria
- `performance`: Métricas de performance
- `nginx`: Logs do servidor web

## Dashboards

### Overview
- Taxa de requisições
- Tempo de resposta
- Taxa de erro
- Usuários ativos

### Security
- Tentativas de login
- Eventos suspeitos
- Bloqueios por IP
- Análise geográfica

### Performance
- Queries lentas
- Uso de recursos
- Cache hit rate
- Throughput

## Troubleshooting

### Serviços não iniciam
```bash
# Verificar logs
docker-compose -f docker-compose.monitoring.yml logs

# Verificar permissões
sudo chown -R 472:472 monitoring/grafana
sudo chown -R 1000:1000 monitoring/elasticsearch
```

### Métricas não aparecem
```bash
# Verificar se middleware está ativo
curl http://localhost:8000/metrics/

# Verificar configuração Prometheus
curl http://localhost:9090/targets
```
EOF

print_status "Documentação criada"

# Finalização
echo ""
echo -e "${GREEN}🎉 Configuração de monitoramento concluída!${NC}"
echo ""
echo -e "${BLUE}📋 Próximos passos:${NC}"
echo "1. Execute: ./scripts/start-monitoring.sh"
echo "2. Acesse Grafana em http://localhost:3000"
echo "3. Configure alertas no Alertmanager"
echo "4. Personalize dashboards conforme necessário"
echo ""
echo -e "${BLUE}📚 Documentação:${NC}"
echo "- Consulte docs/MONITORING.md para detalhes"
echo "- Veja logs em logs/ para troubleshooting"
echo ""
echo -e "${YELLOW}⚠️  Lembre-se:${NC}"
echo "- Configure senhas seguras em produção"
echo "- Ajuste retenção de dados conforme necessário"
echo "- Configure backup dos dados de monitoramento"
EOF

chmod +x scripts/setup-monitoring.sh

print_status "Script de configuração criado e executável"
