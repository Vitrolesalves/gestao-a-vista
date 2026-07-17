import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from Gestao_a_Vista.models import CustomUser, Projeto, TipoServico


class Command(BaseCommand):
    help = "Popula dados de teste para o planner"

    def handle(self, *args, **options):
        # Criar tipos de serviço se não existirem
        tipos_servico = [
            {
                "nome": "Desenvolvimento",
                "cor": "#3B82F6",
                "descricao": "Projetos de desenvolvimento de software",
            },
            {
                "nome": "Infraestrutura",
                "cor": "#10B981",
                "descricao": "Projetos de infraestrutura e TI",
            },
            {
                "nome": "Treinamento",
                "cor": "#F59E0B",
                "descricao": "Programas de treinamento e capacitação",
            },
            {
                "nome": "Consultoria",
                "cor": "#8B5CF6",
                "descricao": "Projetos de consultoria",
            },
            {
                "nome": "Manutenção",
                "cor": "#EF4444",
                "descricao": "Projetos de manutenção e suporte",
            },
        ]

        for tipo_data in tipos_servico:
            tipo, created = TipoServico.objects.get_or_create(
                nome=tipo_data["nome"], defaults=tipo_data
            )
            if created:
                self.stdout.write(f"Criado tipo de serviço: {tipo.nome}")

        # Obter usuários existentes
        usuarios = list(CustomUser.objects.filter(is_active=True))
        if not usuarios:
            self.stdout.write(self.style.ERROR("Nenhum usuário ativo encontrado"))
            return

        tipos = list(TipoServico.objects.all())

        # Projetos de exemplo
        projetos_exemplo = [
            {
                "nome": "Sistema de Autenticação SSO",
                "descricao": "Implementação de sistema de Single Sign-On para unificar acessos",
                "status": "Em andamento",
                "prioridade": "Alto",
                "progresso": 65,
            },
            {
                "nome": "Atualização Infraestrutura Cloud",
                "descricao": "Migração de servidores para cloud AWS com maior capacidade",
                "status": "Ativo",
                "prioridade": "Médio",
                "progresso": 30,
            },
            {
                "nome": "Treinamento Equipe DevOps",
                "descricao": "Capacitação da equipe em práticas DevOps e CI/CD",
                "status": "Concluído",
                "prioridade": "Alto",
                "progresso": 100,
            },
            {
                "nome": "Portal do Cliente v2.0",
                "descricao": "Nova versão do portal com interface modernizada",
                "status": "Em andamento",
                "prioridade": "Alto",
                "progresso": 85,
            },
            {
                "nome": "Backup Automatizado",
                "descricao": "Sistema automatizado de backup e recovery",
                "status": "Pausado",
                "prioridade": "Médio",
                "progresso": 20,
            },
            {
                "nome": "API Gateway",
                "descricao": "Implementação de gateway para APIs microserviços",
                "status": "Ativo",
                "prioridade": "Alto",
                "progresso": 15,
            },
            {
                "nome": "Monitoramento de Performance",
                "descricao": "Sistema de monitoramento e alertas em tempo real",
                "status": "Em andamento",
                "prioridade": "Médio",
                "progresso": 50,
            },
            {
                "nome": "Consultoria Segurança",
                "descricao": "Auditoria de segurança e implementação de melhorias",
                "status": "Ativo",
                "prioridade": "Alto",
                "progresso": 10,
            },
        ]

        projetos_criados = 0
        hoje = timezone.now().date()

        for i, projeto_data in enumerate(projetos_exemplo):
            # Gerar datas aleatórias
            data_inicial = hoje - timedelta(days=random.randint(1, 90))
            data_conclusao = data_inicial + timedelta(days=random.randint(30, 180))

            projeto, created = Projeto.objects.get_or_create(
                nome=projeto_data["nome"],
                defaults={
                    "descricao": projeto_data["descricao"],
                    "responsavel": random.choice(usuarios),
                    "data_inicial": data_inicial,
                    "data_conclusao": data_conclusao,
                    "prioridade": projeto_data["prioridade"],
                    "status": projeto_data["status"],
                    "tipo_servico": random.choice(tipos),
                    "progresso": projeto_data["progresso"],
                    "created_by": random.choice(usuarios),
                },
            )

            if created:
                projetos_criados += 1
                self.stdout.write(f"Criado projeto: {projeto.nome}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Processo concluído. {projetos_criados} projetos criados."
            )
        )
