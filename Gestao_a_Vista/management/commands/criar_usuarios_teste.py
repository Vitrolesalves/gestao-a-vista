"""
Comando para criar usuários de teste para validação de segurança
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from Gestao_a_Vista.models import CustomUser


class Command(BaseCommand):
    help = 'Cria usuários de teste para validação de segurança'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Remove usuários de teste existentes antes de criar novos',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Lista de usuários de teste
        usuarios_teste = [
            {
                'username': 'admin_teste',
                'password': 'admin123!@#',
                'email': 'admin.teste@gestaoavista.com',
                'name': 'Administrador Teste',
                'role': 'administrador',
                'permissions': {
                    'dashboard': True,
                    'monitoramento': True,
                    'qr_generator': True,
                    'etiquetas_generator': True,
                    'desativacao_cr': True,
                    'controle_chips': True,
                    'implantacoes_opsvista': True,
                    'implantacoes_fluxo': True,
                    'desmobilizacoes_fluxo': True,
                    'portaria_base': True,
                    'gestao_salas': True,
                    'reserva_salas': True,
                    'calendario_reservas': True,
                    'livro_ata': True,
                    'planner': True,
                    'explorer': True,
                    'torre_controle': True,
                    'relatorios': True,
                }
            },
            {
                'username': 'gerente_teste',
                'password': 'gerente123!@#',
                'email': 'gerente.teste@gestaoavista.com',
                'name': 'Gerente Teste',
                'role': 'gerente',
                'permissions': {
                    'dashboard': True,
                    'monitoramento': True,
                    'qr_generator': True,
                    'etiquetas_generator': False,
                    'desativacao_cr': True,
                    'controle_chips': False,
                    'implantacoes_opsvista': False,
                    'implantacoes_fluxo': True,
                    'desmobilizacoes_fluxo': True,
                    'portaria_base': True,
                    'gestao_salas': True,
                    'reserva_salas': True,
                    'calendario_reservas': True,
                    'livro_ata': True,
                    'planner': True,
                    'explorer': True,
                    'torre_controle': False,
                    'relatorios': True,
                }
            },
            {
                'username': 'publico_teste',
                'password': 'publico123!@#',
                'email': 'publico.teste@gestaoavista.com',
                'name': 'Usuário Público Teste',
                'role': 'publico',
                'permissions': {
                    'dashboard': False,
                    'monitoramento': False,
                    'qr_generator': False,
                    'etiquetas_generator': False,
                    'desativacao_cr': False,
                    'controle_chips': False,
                    'implantacoes_opsvista': False,
                    'implantacoes_fluxo': False,
                    'desmobilizacoes_fluxo': False,
                    'portaria_base': False,
                    'gestao_salas': False,
                    'reserva_salas': True,
                    'calendario_reservas': True,
                    'livro_ata': False,
                    'planner': False,
                    'explorer': False,
                    'torre_controle': False,
                    'relatorios': False,
                }
            },
            {
                'username': 'cliente_teste',
                'password': 'cliente123!@#',
                'email': 'cliente.teste@gestaoavista.com',
                'name': 'Cliente Teste',
                'role': 'cliente',
                'permissions': {
                    'dashboard': False,
                    'monitoramento': False,
                    'qr_generator': False,
                    'etiquetas_generator': False,
                    'desativacao_cr': False,
                    'controle_chips': False,
                    'implantacoes_opsvista': False,
                    'implantacoes_fluxo': False,
                    'desmobilizacoes_fluxo': False,
                    'portaria_base': False,
                    'gestao_salas': False,
                    'reserva_salas': True,
                    'calendario_reservas': True,
                    'livro_ata': False,
                    'planner': False,
                    'explorer': False,
                    'torre_controle': False,
                    'relatorios': False,
                }
            }
        ]

        if options['reset']:
            self.stdout.write('Removendo usuários de teste existentes...')
            User.objects.filter(username__endswith='_teste').delete()

        self.stdout.write('Criando usuários de teste...')
        
        for usuario_data in usuarios_teste:
            username = usuario_data['username']
            
            # Verificar se o usuário já existe
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'Usuário {username} já existe. Pulando...')
                )
                continue
            
            # Criar o usuário
            usuario = User.objects.create_user(
                username=usuario_data['username'],
                password=usuario_data['password'],
                email=usuario_data['email'],
                name=usuario_data['name'],
                role=usuario_data['role'],
                page_permissions=usuario_data['permissions']
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Usuario {username} criado com sucesso')
            )

        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('USUARIOS DE TESTE CRIADOS'))
        self.stdout.write('='*50)
        
        for usuario_data in usuarios_teste:
            self.stdout.write(f"ROLE: {usuario_data['role'].upper()}")
            self.stdout.write(f"   Usuario: {usuario_data['username']}")
            self.stdout.write(f"   Senha: {usuario_data['password']}")
            self.stdout.write(f"   Email: {usuario_data['email']}")
            self.stdout.write('')

        self.stdout.write(self.style.WARNING('IMPORTANTE:'))
        self.stdout.write('   - Estes usuarios sao apenas para TESTES')
        self.stdout.write('   - NAO use em producao')
        self.stdout.write('   - Remova apos os testes com --reset')
        self.stdout.write('')
