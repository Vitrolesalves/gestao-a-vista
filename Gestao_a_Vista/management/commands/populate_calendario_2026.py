from datetime import date

from django.core.management.base import BaseCommand

from Gestao_a_Vista.models import EventoCalendario2026


class Command(BaseCommand):
    help = 'Popula o Calendário 2026 com os feriados da Regional Centro Oeste'

    def handle(self, *args, **options):
        feriados = [
            {
                'data': date(2026, 1, 1),
                'titulo': 'Ano Novo',
                'tipo': 'feriado',
                'descricao': 'Confraternização Universal',
                'cor': '#dc3545'
            },
            {
                'data': date(2026, 2, 16),
                'titulo': 'Carnaval',
                'tipo': 'feriado',
                'descricao': 'Feriado Nacional de Carnaval',
                'cor': '#ffc107'
            },
            {
                'data': date(2026, 4, 3),
                'titulo': 'Sexta-Feira Santa',
                'tipo': 'feriado',
                'descricao': 'Paixão de Cristo',
                'cor': '#6f42c1'
            },
            {
                'data': date(2026, 4, 21),
                'titulo': 'Dia de Tiradentes',
                'tipo': 'feriado',
                'descricao': 'Feriado Nacional',
                'cor': '#28a745'
            },
            {
                'data': date(2026, 5, 1),
                'titulo': 'Dia do Trabalho',
                'tipo': 'feriado',
                'descricao': 'Dia Mundial do Trabalho',
                'cor': '#dc3545'
            },
            {
                'data': date(2026, 6, 4),
                'titulo': 'Corpus Christi',
                'tipo': 'feriado',
                'descricao': 'Feriado Religioso',
                'cor': '#6f42c1'
            },
            {
                'data': date(2026, 9, 7),
                'titulo': 'Independência do Brasil',
                'tipo': 'feriado',
                'descricao': 'Proclamação da Independência',
                'cor': '#28a745'
            },
            {
                'data': date(2026, 10, 12),
                'titulo': 'Nossa Senhora Aparecida',
                'tipo': 'feriado',
                'descricao': 'Padroeira do Brasil',
                'cor': '#17a2b8'
            },
            {
                'data': date(2026, 10, 24),
                'titulo': 'Aniversário Goiânia',
                'tipo': 'feriado',
                'descricao': 'Aniversário da Cidade de Goiânia',
                'cor': '#fd7e14'
            },
            {
                'data': date(2026, 11, 2),
                'titulo': 'Dia de Finados',
                'tipo': 'feriado',
                'descricao': 'Feriado Nacional',
                'cor': '#6c757d'
            },
            {
                'data': date(2026, 11, 15),
                'titulo': 'Proclamação da República',
                'tipo': 'feriado',
                'descricao': 'Feriado Nacional',
                'cor': '#28a745'
            },
            {
                'data': date(2026, 11, 20),
                'titulo': 'Dia da Consciência Negra',
                'tipo': 'feriado',
                'descricao': 'Feriado Nacional',
                'cor': '#343a40'
            },
            {
                'data': date(2026, 12, 24),
                'titulo': 'Expediente até 12hs',
                'tipo': 'feriado',
                'descricao': 'Véspera de Natal - Expediente reduzido',
                'cor': '#ffc107'
            },
            {
                'data': date(2026, 12, 25),
                'titulo': 'Natal',
                'tipo': 'feriado',
                'descricao': 'Nascimento de Jesus Cristo',
                'cor': '#dc3545'
            },
            {
                'data': date(2026, 12, 31),
                'titulo': 'Expediente até 12hs',
                'tipo': 'feriado',
                'descricao': 'Véspera de Ano Novo - Expediente reduzido',
                'cor': '#ffc107'
            },
        ]

        eventos_criados = 0
        eventos_existentes = 0

        for feriado_data in feriados:
            evento, created = EventoCalendario2026.objects.get_or_create(
                data=feriado_data['data'],
                titulo=feriado_data['titulo'],
                defaults={
                    'tipo': feriado_data['tipo'],
                    'descricao': feriado_data['descricao'],
                    'cor': feriado_data['cor']
                }
            )
            if created:
                eventos_criados += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'[OK] Evento criado: {evento.titulo} - {evento.data.strftime("%d/%m/%Y")}'
                    )
                )
            else:
                eventos_existentes += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'[AVISO] Evento ja existe: {evento.titulo} - {evento.data.strftime("%d/%m/%Y")}'
                    )
                )

        total_eventos = EventoCalendario2026.objects.filter(data__year=2026).count()

        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'Eventos criados: {eventos_criados}'))
        self.stdout.write(self.style.WARNING(f'Eventos ja existentes: {eventos_existentes}'))
        self.stdout.write(self.style.SUCCESS(f'Total de eventos no Calendario 2026: {total_eventos}'))
        self.stdout.write('=' * 60 + '\n')
