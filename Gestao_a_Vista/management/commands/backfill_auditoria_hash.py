"""
Preenche numero, tarefa_id e inicio_real na tabela auditoria_ocorrencia_status
para registros gravados antes dessas colunas existirem (cruza com o banco Vista
pelo mesmo hash usado em views.carregar_mais_auditoria).

Uso:
  python manage.py backfill_auditoria_hash
  python manage.py backfill_auditoria_hash --data-inicio=2026-01-01 --data-fim=2026-07-07
  python manage.py backfill_auditoria_hash --dry-run
"""
import hashlib

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.models import Q
from django.utils import timezone

from Gestao_a_Vista.models import AuditoriaOcorrenciaStatus

CHECKLIST_LIVRO_ATA_ID = '6687b862-10d0-4144-ae30-8bdc55f22ee3'


class Command(BaseCommand):
    help = "Backfill de numero/tarefa_id/inicio_real em auditoria_ocorrencia_status a partir do banco Vista"

    def add_arguments(self, parser):
        parser.add_argument('--data-inicio', default='2026-01-01', help="Data inicial (YYYY-MM-DD) no Vista. Padrão: 2026-01-01")
        parser.add_argument('--data-fim', default=None, help="Data final (YYYY-MM-DD). Padrão: hoje")
        parser.add_argument('--dry-run', action='store_true', help="Apenas mostra o que seria atualizado, sem gravar")

    def handle(self, *args, **options):
        data_inicio = options['data_inicio']
        data_fim = options['data_fim'] or timezone.now().strftime('%Y-%m-%d')
        dry_run = options['dry_run']

        pendentes_qs = AuditoriaOcorrenciaStatus.objects.using('default').filter(
            Q(tarefa_id__isnull=True) | Q(numero__isnull=True) | Q(inicio_real__isnull=True)
        )
        hashes_pendentes = set(pendentes_qs.values_list('ocorrencia_hash', flat=True))
        self.stdout.write(f"Registros pendentes de numero/tarefa_id/inicio_real: {len(hashes_pendentes)}")

        if not hashes_pendentes:
            self.stdout.write(self.style.SUCCESS("Nada para atualizar."))
            return

        db_conn_name = 'dw_vpn' if 'dw_vpn' in connections else ('readonly' if 'readonly' in connections else 'default')
        self.stdout.write(f"Consultando banco Vista ({db_conn_name}) de {data_inicio} até {data_fim}...")
        cursor = connections[db_conn_name].cursor()
        cursor.execute("SET statement_timeout = '120000';")

        query = """
            SELECT t.id AS tarefa_id, t.numero, t.inicio, ex.perguntadescricao AS item_nome
            FROM dbo.tarefa t
            INNER JOIN dbo.checklist c ON c.id = t.checklistid
            INNER JOIN dbo.estrutura e ON e.id = t.estruturaid
            INNER JOIN dbo.execucao ex ON ex.tarefaid = t.id
            WHERE c.id = %s
              AND t.status = 85
              AND e.descricao LIKE %s
              AND t.terminoreal >= %s
              AND t.terminoreal <= %s
        """
        cursor.execute(query, [
            CHECKLIST_LIVRO_ATA_ID, '% - GO - %',
            f"{data_inicio} 00:00:00", f"{data_fim} 23:59:59",
        ])
        columns = [col[0] for col in cursor.description]
        rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()
        self.stdout.write(f"Linhas trazidas do Vista: {len(rows)}")

        dados_por_hash = {}
        for row in rows:
            item_nome = (row.get('item_nome') or '').strip()
            if not item_nome:
                continue
            if ' - ' in item_nome:
                item_nome = item_nome.split(' - ')[0].strip()

            tarefa_id = str(row.get('tarefa_id') or '')
            if not tarefa_id:
                continue

            key = f"{tarefa_id}|{item_nome}"
            ocorrencia_hash = hashlib.md5(key.encode('utf-8')).hexdigest()

            if ocorrencia_hash in hashes_pendentes and ocorrencia_hash not in dados_por_hash:
                dados_por_hash[ocorrencia_hash] = {
                    'tarefa_id': tarefa_id,
                    'numero': str(row['numero']) if row.get('numero') is not None else None,
                    'inicio_real': row.get('inicio'),
                }

        self.stdout.write(f"Correspondências encontradas: {len(dados_por_hash)}")
        if not dados_por_hash:
            self.stdout.write(self.style.WARNING("Nenhuma correspondência — nada foi atualizado."))
            return

        atualizados = 0
        objetos = AuditoriaOcorrenciaStatus.objects.using('default').filter(ocorrencia_hash__in=list(dados_por_hash.keys()))
        for obj in objetos:
            dados = dados_por_hash.get(obj.ocorrencia_hash)
            if not dados:
                continue
            mudou = False
            if not obj.tarefa_id and dados['tarefa_id']:
                obj.tarefa_id = dados['tarefa_id']
                mudou = True
            if not obj.numero and dados['numero']:
                obj.numero = dados['numero']
                mudou = True
            if not obj.inicio_real and dados['inicio_real']:
                obj.inicio_real = dados['inicio_real']
                mudou = True
            if mudou:
                atualizados += 1
                if not dry_run:
                    obj.save(update_fields=['tarefa_id', 'numero', 'inicio_real'])

        if dry_run:
            self.stdout.write(self.style.WARNING(f"[DRY RUN] Registros que seriam atualizados: {atualizados}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Registros atualizados: {atualizados}"))
