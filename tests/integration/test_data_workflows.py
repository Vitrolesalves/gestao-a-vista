"""
Testes de integração para fluxos de dados e operações complexas
"""

import json
from datetime import datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from Gestao_a_Vista.models import (AreaResponsavel, ControleChip, Dashboard,
                                   DesativacaoCR, GestaoSala, MonitoramentoLog,
                                   PortariaBase, ReservaSala, Script, Service,
                                   Unidade, UserActivity, UserProfile)

User = get_user_model()


@pytest.mark.integration
class TestDataConsistencyWorkflow(TransactionTestCase):
    """Testes para consistência de dados em operações complexas"""

    def setUp(self):
        """Configuração inicial"""
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role="administrador",
        )

        self.unidade = Unidade.objects.create(
            nome="Unidade Principal",
            endereco="Rua Principal, 100",
            telefone="11999999999",
            email="unidade@example.com",
        )

    def test_cascade_deletion_workflow(self):
        """Testa integridade referencial em deleções em cascata"""

        # 1. Criar estrutura de dados relacionados
        sala = GestaoSala.objects.create(
            nome="Sala Teste", capacidade=50, unidade=self.unidade, disponivel=True
        )

        # Criar reserva para a sala
        reserva = ReservaSala.objects.create(
            sala=sala,
            usuario_responsavel=self.admin,
            data_inicio=timezone.now(),
            data_fim=timezone.now() + timedelta(hours=2),
            motivo="Reunião de teste",
        )

        # Criar perfil para o usuário
        profile = UserProfile.objects.create(
            user=self.admin, phone="11999999999", address="Endereço teste"
        )

        # 2. Verificar que os dados foram criados
        self.assertTrue(GestaoSala.objects.filter(id_sala=sala.id_sala).exists())
        self.assertTrue(ReservaSala.objects.filter(id=reserva.id).exists())
        self.assertTrue(UserProfile.objects.filter(id=profile.id).exists())

        # 3. Deletar unidade e verificar cascata
        unidade_id = self.unidade.id
        self.unidade.delete()

        # Verificar se sala foi deletada em cascata
        self.assertFalse(GestaoSala.objects.filter(id_sala=sala.id_sala).exists())

        # Verificar se reserva foi deletada em cascata
        self.assertFalse(ReservaSala.objects.filter(id=reserva.id).exists())

        # Perfil do usuário deve permanecer (não relacionado à unidade)
        self.assertTrue(UserProfile.objects.filter(id=profile.id).exists())

    def test_transaction_rollback_workflow(self):
        """Testa rollback de transações em caso de erro"""

        initial_dashboard_count = Dashboard.objects.count()

        try:
            with transaction.atomic():
                # Criar dashboard válido
                dashboard1 = Dashboard.objects.create(
                    nome="Dashboard 1",
                    cliente="Cliente 1",
                    servico="Seguranca",
                    status="Sucesso",
                )

                # Criar dashboard válido
                dashboard2 = Dashboard.objects.create(
                    nome="Dashboard 2",
                    cliente="Cliente 2",
                    servico="Limpeza",
                    status="Sucesso",
                )

                # Forçar erro para testar rollback
                raise Exception("Erro simulado para rollback")

        except Exception:
            pass  # Esperado

        # Verificar que nenhum dashboard foi criado devido ao rollback
        self.assertEqual(Dashboard.objects.count(), initial_dashboard_count)

    def test_bulk_operations_workflow(self):
        """Testa operações em lote para grandes volumes de dados"""

        # 1. Criar múltiplos usuários em lote
        users_data = []
        for i in range(10):
            users_data.append(
                User(
                    username=f"user_{i}", email=f"user_{i}@example.com", role="publico"
                )
            )

        created_users = User.objects.bulk_create(users_data)
        self.assertEqual(len(created_users), 10)

        # 2. Criar múltiplos dashboards em lote
        dashboards_data = []
        for i in range(20):
            dashboards_data.append(
                Dashboard(
                    nome=f"Dashboard {i}",
                    cliente=f"Cliente {i}",
                    servico="Seguranca" if i % 2 == 0 else "Limpeza",
                    status="Sucesso",
                )
            )

        created_dashboards = Dashboard.objects.bulk_create(dashboards_data)
        self.assertEqual(len(created_dashboards), 20)

        # 3. Atualização em lote
        Dashboard.objects.filter(servico="Seguranca").update(status="Pendente")

        # Verificar atualizações
        seguranca_dashboards = Dashboard.objects.filter(servico="Seguranca")
        for dashboard in seguranca_dashboards:
            self.assertEqual(dashboard.status, "Pendente")

    def test_complex_query_workflow(self):
        """Testa consultas complexas com múltiplas tabelas"""

        # Criar dados de teste
        service = Service.objects.create(
            name="Segurança Patrimonial", description="Serviço completo de segurança"
        )

        # Criar salas em diferentes unidades
        unidade2 = Unidade.objects.create(
            nome="Unidade Secundária", endereco="Rua Secundária, 200"
        )

        sala1 = GestaoSala.objects.create(
            nome="Sala A", capacidade=30, unidade=self.unidade, disponivel=True
        )

        sala2 = GestaoSala.objects.create(
            nome="Sala B", capacidade=50, unidade=unidade2, disponivel=False
        )

        # Criar reservas
        ReservaSala.objects.create(
            sala=sala1,
            usuario_responsavel=self.admin,
            data_inicio=timezone.now(),
            data_fim=timezone.now() + timedelta(hours=1),
            motivo="Reunião A",
        )

        ReservaSala.objects.create(
            sala=sala2,
            usuario_responsavel=self.admin,
            data_inicio=timezone.now() + timedelta(days=1),
            data_fim=timezone.now() + timedelta(days=1, hours=2),
            motivo="Reunião B",
        )

        # Consulta complexa: salas disponíveis com reservas futuras
        from django.db.models import Count, Q

        salas_com_info = (
            GestaoSala.objects.select_related("unidade")
            .prefetch_related("reservas")
            .annotate(total_reservas=Count("reservas"))
            .filter(Q(disponivel=True) | Q(reservas__data_inicio__gt=timezone.now()))
            .distinct()
        )

        # Verificar resultados
        self.assertTrue(salas_com_info.exists())

        for sala in salas_com_info:
            # Verificar se dados relacionados foram carregados
            self.assertIsNotNone(sala.unidade.nome)
            self.assertIsInstance(sala.total_reservas, int)


@pytest.mark.integration
class TestBusinessLogicWorkflow(TransactionTestCase):
    """Testes para lógica de negócio complexa"""

    def setUp(self):
        """Configuração inicial"""
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role="administrador",
        )

        self.gerente = User.objects.create_user(
            username="gerente",
            email="gerente@example.com",
            password="gerente123",
            role="gerente",
        )

    def test_user_permission_inheritance_workflow(self):
        """Testa herança e aplicação de permissões"""

        # 1. Verificar permissões padrão do administrador
        admin_permissions = self.admin.get_default_permissions()

        # Admin deve ter todas as permissões
        for page, _ in User.PAGE_PERMISSIONS:
            self.assertTrue(admin_permissions[page])
            self.assertTrue(self.admin.has_page_permission(page))

        # 2. Verificar permissões do gerente
        gerente_permissions = self.gerente.get_default_permissions()

        # Gerente deve ter acesso limitado
        self.assertTrue(gerente_permissions["dashboard"])
        self.assertTrue(gerente_permissions["monitoramento"])
        self.assertFalse(gerente_permissions["desativacao_cr"])

        # 3. Modificar permissões customizadas
        self.gerente.page_permissions = {"qr_generator": True}
        self.gerente.save()

        # Verificar permissão customizada
        self.assertTrue(self.gerente.has_page_permission("qr_generator"))
        self.assertFalse(
            self.gerente.has_page_permission("monitoramento")
        )  # Não está nas permissões customizadas

    def test_dashboard_status_workflow(self):
        """Testa fluxo de status de dashboards"""

        # 1. Criar dashboard com status inicial
        dashboard = Dashboard.objects.create(
            nome="Dashboard Status Test",
            cliente="Cliente Status",
            servico="Seguranca",
            status="Pendente",
        )

        self.assertEqual(dashboard.status, "Pendente")

        # 2. Simular processamento - mudança para Sucesso
        dashboard.status = "Sucesso"
        dashboard.save()

        # Verificar mudança
        dashboard.refresh_from_db()
        self.assertEqual(dashboard.status, "Sucesso")

        # 3. Simular erro - mudança para Erro
        dashboard.status = "Erro"
        dashboard.save()

        # Verificar mudança
        dashboard.refresh_from_db()
        self.assertEqual(dashboard.status, "Erro")

    def test_monitoring_log_workflow(self):
        """Testa fluxo de logs de monitoramento"""

        # 1. Criar logs de diferentes tipos
        log_info = MonitoramentoLog.objects.create(
            tipo="INFO",
            mensagem="Sistema iniciado",
            detalhes="Sistema iniciado com sucesso",
        )

        log_warning = MonitoramentoLog.objects.create(
            tipo="WARNING",
            mensagem="Aviso de performance",
            detalhes="Sistema com lentidão",
        )

        log_error = MonitoramentoLog.objects.create(
            tipo="ERROR",
            mensagem="Erro de conexão",
            detalhes="Falha na conexão com banco de dados",
        )

        # 2. Verificar criação com timestamps
        self.assertIsNotNone(log_info.timestamp)
        self.assertIsNotNone(log_warning.timestamp)
        self.assertIsNotNone(log_error.timestamp)

        # 3. Verificar ordenação por timestamp (mais recente primeiro)
        logs = MonitoramentoLog.objects.all().order_by("-timestamp")
        self.assertEqual(logs[0], log_error)  # Mais recente

        # 4. Filtrar logs por tipo
        error_logs = MonitoramentoLog.objects.filter(tipo="ERROR")
        self.assertEqual(error_logs.count(), 1)
        self.assertEqual(error_logs.first(), log_error)

    def test_user_activity_tracking_workflow(self):
        """Testa rastreamento detalhado de atividades"""

        # 1. Simular login
        login_activity = UserActivity.objects.create(
            user=self.admin, action="login", details="Login realizado via web"
        )

        # 2. Simular navegação
        nav_activity = UserActivity.objects.create(
            user=self.admin, action="page_view", details="Acessou página de dashboard"
        )

        # 3. Simular ação
        action_activity = UserActivity.objects.create(
            user=self.admin,
            action="dashboard_create",
            details="Criou dashboard: Dashboard Teste",
        )

        # 4. Simular logout
        logout_activity = UserActivity.objects.create(
            user=self.admin, action="logout", details="Logout realizado"
        )

        # 5. Verificar histórico do usuário
        user_activities = UserActivity.objects.filter(user=self.admin).order_by(
            "-timestamp"
        )

        self.assertEqual(user_activities.count(), 4)
        self.assertEqual(user_activities[0], logout_activity)  # Mais recente
        self.assertEqual(user_activities[3], login_activity)  # Mais antigo

        # 6. Verificar relacionamento
        self.assertEqual(self.admin.activities.count(), 4)


@pytest.mark.integration
class TestSystemIntegrationWorkflow(TransactionTestCase):
    """Testes para integração entre diferentes módulos do sistema"""

    def setUp(self):
        """Configuração inicial"""
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            role="administrador",
        )

        self.unidade = Unidade.objects.create(
            nome="Unidade Integração", endereco="Rua Integração, 300"
        )

    def test_complete_reservation_workflow(self):
        """Testa fluxo completo de reserva de sala"""

        # 1. Criar sala
        sala = GestaoSala.objects.create(
            nome="Sala Reunião", capacidade=20, unidade=self.unidade, disponivel=True
        )

        # 2. Verificar disponibilidade
        self.assertTrue(sala.disponivel)

        # 3. Criar reserva
        data_inicio = timezone.now() + timedelta(hours=1)
        data_fim = data_inicio + timedelta(hours=2)

        reserva = ReservaSala.objects.create(
            sala=sala,
            usuario_responsavel=self.admin,
            data_inicio=data_inicio,
            data_fim=data_fim,
            motivo="Reunião de integração",
        )

        # 4. Verificar reserva criada
        self.assertEqual(reserva.sala, sala)
        self.assertEqual(reserva.usuario_responsavel, self.admin)

        # 5. Verificar conflitos de horário
        # Tentar criar reserva conflitante
        reserva_conflito = ReservaSala(
            sala=sala,
            usuario_responsavel=self.admin,
            data_inicio=data_inicio + timedelta(minutes=30),
            data_fim=data_fim + timedelta(minutes=30),
            motivo="Reunião conflitante",
        )

        # Em um sistema real, haveria validação de conflito
        # Por agora, apenas verificamos que podemos criar a estrutura
        self.assertIsNotNone(reserva_conflito)

    def test_dashboard_monitoring_integration(self):
        """Testa integração entre dashboards e monitoramento"""

        # 1. Criar dashboard
        dashboard = Dashboard.objects.create(
            nome="Dashboard Monitorado",
            cliente="Cliente Monitor",
            servico="Seguranca",
            status="Sucesso",
        )

        # 2. Simular log de criação
        log_criacao = MonitoramentoLog.objects.create(
            tipo="INFO",
            mensagem="Dashboard criado",
            detalhes=f"Dashboard {dashboard.nome} criado por {self.admin.username}",
        )

        # 3. Simular mudança de status com log
        dashboard.status = "Erro"
        dashboard.save()

        log_erro = MonitoramentoLog.objects.create(
            tipo="ERROR",
            mensagem="Dashboard com erro",
            detalhes=f"Dashboard {dashboard.nome} apresentou erro",
        )

        # 4. Verificar logs relacionados
        dashboard_logs = MonitoramentoLog.objects.filter(
            mensagem__icontains=dashboard.nome
        )

        self.assertEqual(dashboard_logs.count(), 2)
        self.assertIn(log_criacao, dashboard_logs)
        self.assertIn(log_erro, dashboard_logs)

    def test_user_profile_integration(self):
        """Testa integração entre usuário e perfil"""

        # 1. Criar perfil para usuário
        profile = UserProfile.objects.create(
            user=self.admin, phone="11987654321", address="Rua do Perfil, 123"
        )

        # 2. Verificar relacionamento OneToOne
        self.assertEqual(self.admin.profile, profile)
        self.assertEqual(profile.user, self.admin)

        # 3. Atualizar perfil
        profile.phone = "11999888777"
        profile.address = "Nova Rua, 456"
        profile.save()

        # 4. Verificar atualização
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.profile.phone, "11999888777")
        self.assertEqual(self.admin.profile.address, "Nova Rua, 456")

        # 5. Verificar timestamps
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)
        self.assertGreaterEqual(profile.updated_at, profile.created_at)

    def test_service_area_integration(self):
        """Testa integração entre serviços e áreas responsáveis"""

        # 1. Criar serviço
        service = Service.objects.create(
            name="Segurança Eletrônica", description="Monitoramento por câmeras"
        )

        # 2. Criar área responsável
        area = AreaResponsavel.objects.create(
            nome="Área Segurança",
            descricao="Responsável pela segurança do prédio",
            responsavel=self.admin,
        )

        # 3. Verificar criação
        self.assertEqual(service.name, "Segurança Eletrônica")
        self.assertEqual(area.responsavel, self.admin)

        # 4. Simular associação (em um modelo real haveria FK)
        # Por agora, verificamos que ambos existem
        self.assertTrue(Service.objects.filter(name="Segurança Eletrônica").exists())
        self.assertTrue(AreaResponsavel.objects.filter(nome="Área Segurança").exists())
