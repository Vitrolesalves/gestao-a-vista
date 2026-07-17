"""Popula dados de demonstração do CMO Efetivo para conferência visual local.

Não representa a integração real com o OpsVista (que ainda não existe --
ver TODO em views.py / CMO_EFETIVO_ITEM_CHECKLIST_VISTA). Serve só para dar
uma visão da tela com dados nos três status e um registro de movimentação
já incluído.
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from Gestao_a_Vista.models import (
    CustomUser, CMOEfetivoConformidade, CMOEfetivoRegistroMovimentacao,
)


class Command(BaseCommand):
    help = "Popula dados de demonstração do CMO Efetivo (uso local apenas)"

    def handle(self, *args, **options):
        usuario = CustomUser.objects.filter(is_active=True).first()

        hoje = date.today()
        exemplos = [
            {"cliente_nome": "Cliente Alfa Ltda", "cr": "1001", "tipo_servico_nome": "limpeza", "status_efetivo": "aguardando_confirmacao", "colaborador_nome": "Aguardando"},
            {"cliente_nome": "Cliente Beta S.A.", "cr": "1002", "tipo_servico_nome": "seguranca", "status_efetivo": "conforme", "colaborador_nome": "Equipe completa"},
            {"cliente_nome": "Cliente Gama Serviços", "cr": "1003", "tipo_servico_nome": "manutencao", "status_efetivo": "nao_conforme", "colaborador_nome": "João da Silva", "motivo_nao_conformidade": "falta_nao_justificada"},
        ]

        criados = []
        for i, dados in enumerate(exemplos):
            registro, created = CMOEfetivoConformidade.objects.get_or_create(
                cliente_nome=dados["cliente_nome"],
                cr=dados["cr"],
                data_referencia=hoje - timedelta(days=i),
                defaults=dict(
                    tipo_servico_nome=dados["tipo_servico_nome"],
                    status_efetivo=dados["status_efetivo"],
                    colaborador_nome=dados["colaborador_nome"],
                    motivo_nao_conformidade=dados.get("motivo_nao_conformidade"),
                    responsavel_contato=usuario,
                    criado_por=usuario,
                ),
            )
            criados.append(registro)
            if created:
                self.stdout.write(f"Criado: {registro}")

        nao_conforme = next((c for c in criados if c.status_efetivo == "nao_conforme"), None)
        if nao_conforme:
            _, created = CMOEfetivoRegistroMovimentacao.objects.get_or_create(
                conformidade_origem=nao_conforme,
                nome="João da Silva",
                defaults=dict(
                    cliente_nome=nao_conforme.cliente_nome,
                    cr=nao_conforme.cr,
                    tipo_servico_nome=nao_conforme.tipo_servico_nome,
                    data_referencia=nao_conforme.data_referencia,
                    gerente="Maria Gerente",
                    cargo="Auxiliar de Limpeza",
                    posto="Portaria Principal",
                    posto_cr=nao_conforme.cr,
                    horario="07:00-19:00",
                    intervalo="12:00-13:00",
                    cobertura="Pedro Cobertura",
                    cargo_cobertura="Auxiliar de Limpeza",
                    observacao="Falta não justificada, cobertura acionada.",
                    situacao="falta",
                    situacao_cobertura="extra_entrada",
                    criado_por=usuario,
                ),
            )
            if created:
                self.stdout.write("Criado registro de movimentação de exemplo.")

        self.stdout.write(self.style.SUCCESS("Dados de demonstração do CMO Efetivo prontos."))
