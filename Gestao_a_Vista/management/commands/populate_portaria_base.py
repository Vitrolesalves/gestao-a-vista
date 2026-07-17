import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from Gestao_a_Vista.models import CustomUser, PortariaBase


class Command(BaseCommand):
    help = "Popula dados de teste para Portaria Base"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Número de entradas a criar (padrão: 10)",
        )

    def handle(self, *args, **options):
        count = options["count"]

        # Verificar se há usuários no sistema
        try:
            user = CustomUser.objects.first()
            if not user:
                self.stdout.write(
                    self.style.ERROR(
                        "Nenhum usuário encontrado. Crie um usuário primeiro."
                    )
                )
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao buscar usuário: {e}"))
            return

        # Dados de exemplo
        nomes = [
            "João Silva Santos",
            "Maria Oliveira Costa",
            "Pedro Almeida Souza",
            "Ana Carolina Lima",
            "Carlos Eduardo Ferreira",
            "Juliana Santos Pereira",
            "Roberto Carlos Silva",
            "Fernanda Oliveira",
            "Lucas Martins Santos",
            "Patrícia Costa Lima",
            "Rafael Souza Alves",
            "Camila Santos Rocha",
        ]

        areas_responsaveis = [
            "TI - Tecnologia da Informação",
            "RH - Recursos Humanos",
            "Financeiro",
            "Operações",
            "Comercial",
            "Jurídico",
            "Manutenção",
            "Segurança",
            "Administração",
            "Logística",
        ]

        motivos = [
            "Reunião de trabalho",
            "Entrega de documentos",
            "Manutenção de equipamentos",
            "Visita técnica",
            "Prestação de serviços",
            "Reunião comercial",
            "Auditoria",
            "Treinamento",
            "Suporte técnico",
            "Inspeção",
        ]

        # Limpar dados existentes (opcional)
        # PortariaBase.objects.all().delete()

        created_count = 0

        for i in range(count):
            try:
                # Gerar dados aleatórios
                nome = random.choice(nomes)
                cpf = random.randint(10000000000, 99999999999)  # CPF como integer

                # Data de nascimento aleatória (18 a 65 anos)
                idade_anos = random.randint(18, 65)
                data_nascimento = (
                    datetime.now() - timedelta(days=idade_anos * 365)
                ).date()

                motivo = random.choice(motivos)
                area = random.choice(areas_responsaveis)

                # Criar entrada
                # Para ter entradas de hoje, criar algumas com data de hoje
                if i < 3:  # Primeiras 3 entradas serão de hoje
                    entrada = PortariaBase.objects.create(
                        nome=nome,
                        cpf=cpf,
                        data_nascimento=data_nascimento,
                        motivo_entrada=motivo,
                        area_responsavel=area,
                        user_cadastro=user,
                    )
                else:
                    # Outras entradas em datas aleatórias dos últimos 7 dias
                    dias_atras = random.randint(1, 7)
                    data_entrada = timezone.now() - timedelta(days=dias_atras)

                    entrada = PortariaBase(
                        nome=nome,
                        cpf=cpf,
                        data_nascimento=data_nascimento,
                        motivo_entrada=motivo,
                        area_responsavel=area,
                        user_cadastro=user,
                        data=data_entrada,
                    )
                    entrada.save()

                created_count += 1

                self.stdout.write(
                    f'✅ Entrada criada: {nome} - {entrada.data.strftime("%d/%m/%Y %H:%M")}'
                )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro ao criar entrada {i+1}: {e}"))

        self.stdout.write(
            self.style.SUCCESS(f"✅ {created_count} entradas criadas com sucesso!")
        )

        # Mostrar estatísticas
        total_entradas = PortariaBase.objects.count()
        today = timezone.now().date()
        entradas_hoje = PortariaBase.objects.filter(data__date=today).count()

        self.stdout.write(f"📊 Total de entradas no banco: {total_entradas}")
        self.stdout.write(f"📊 Entradas de hoje: {entradas_hoje}")
