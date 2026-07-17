import os
from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import models, connections

class Command(BaseCommand):
    help = 'Sincronizador Universal Dinâmico: Sincroniza (UPSERT) do banco de origem (VPN) para o cache local (readonly)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--historico',
            action='store_true',
            help='Baixa todo o histórico do banco ignorando o limite de meses (Carga Única Oculta).',
        )
        parser.add_argument(
            '--origem',
            type=str,
            default='default',
            help='Nome do banco de dados de origem (ex: default ou dw_vpn). O destino sempre será readonly.',
        )

    def handle(self, *args, **options):
        is_historico = options['historico']
        origem_db = options['origem']
        destino_db = 'readonly'
        
        app_models = apps.get_app_config('Gestao_a_Vista').get_models()
        dias_corte = 90
        
        # Define a data_corte a partir de hoje
        data_corte = (timezone.now() - timedelta(days=dias_corte)).date()

        self.stdout.write(self.style.SUCCESS(
            f"=== Iniciando {'Carga Histórica (TUDO)' if is_historico else f'Varredura Incremental ({dias_corte} dias)'} ==="
        ))
        self.stdout.write(f"-> Movendo/Atualizando de [{origem_db}] para [{destino_db}] (Local/Cache)\n")

        for model in app_models:
            model_name = model.__name__
            self.stdout.write(f"\n[{model_name}] Analisando Tabela...")
            
            # Pular models não gerenciados ou proxies
            if not model._meta.managed or model._meta.proxy:
                self.stdout.write(self.style.NOTICE(f"  Skipping (unmanaged ou proxy)."))
                continue
            
            # Detecta campos de data na tabela (apenas campos locais para não bugar com herança complexa)
            date_fields = [f.name for f in model._meta.local_fields if isinstance(f, (models.DateField, models.DateTimeField))]
            
            qs_origem = model.objects.using(origem_db).all()
            
            # Se não estivermos pegando histórico cheio, tentamos filtrar pelos últimos 3 meses
            if not is_historico and date_fields:
                filter_kwargs = {f"{date_fields[0]}__gte": data_corte}
                qs_origem = qs_origem.filter(**filter_kwargs)
                self.stdout.write(f"  - Filtro Automático UPSERT ativado: {date_fields[0]} >= {data_corte}")
            elif not is_historico:
                self.stdout.write("  - Sem colunas de data (Varredura total com Upsert para garantir estado).")

            # Preparativos do UPSERT (Update or Insert)
            pk_name = model._meta.pk.name
            qs_origem = qs_origem.order_by(pk_name) # ordernar é boa pratica p/ iterator e chunking
            
            update_fields = [f.name for f in model._meta.local_fields if f.name != pk_name]
            
            chunk_size = 3000
            total_sincronizado = 0
            
            try:
                lote = []
                # Puxa os dados com iterator para economizar RAM do servidor (busca sob demanda sobre a VPN)
                for obj in qs_origem.iterator(chunk_size=chunk_size):
                    lote.append(obj)
                    if len(lote) >= chunk_size:
                        model.objects.using(destino_db).bulk_create(
                            lote,
                            update_conflicts=True,
                            unique_fields=[pk_name],
                            update_fields=update_fields if update_fields else None
                        )
                        total_sincronizado += len(lote)
                        lote = []
                
                # Despeja no destino os que sobraram
                if lote:
                    model.objects.using(destino_db).bulk_create(
                        lote,
                        update_conflicts=True,
                        unique_fields=[pk_name], # Postgres precisa do unique para bater ON CONFLICT
                        update_fields=update_fields if update_fields else None
                    )
                    total_sincronizado += len(lote)
                    
                self.stdout.write(self.style.SUCCESS(f"  OK! {total_sincronizado} registros consolidados na VPS Local."))
                
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  ERRO ao tentar fazer upsert na tabela {model_name}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS("\n=== Sincronização Flexível Finalizada! ==="))
