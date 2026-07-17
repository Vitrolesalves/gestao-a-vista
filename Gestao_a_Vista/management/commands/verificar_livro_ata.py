"""
Verifica se os CRs com QR Code do Livro Ata cadastrado tiveram o turno
diurno/noturno preenchido e notifica os responsáveis pelo CR:
  - Coordenador e Supervisor: WhatsApp (uazapi)
  - Gerente: e-mail

Uso (agendado via cron):
  python manage.py verificar_livro_ata --turno=diurno   # rodar logo após as 18:00
  python manage.py verificar_livro_ata --turno=noturno  # rodar logo após as 06:00
"""
import re
from datetime import datetime, timedelta, time

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.db import connections
from django.template.loader import render_to_string

from Gestao_a_Vista.models import CustomUser, LivroAtaQRCode
from Gestao_a_Vista.uazapi_client import enviar_whatsapp

CHECKLIST_LIVRO_ATA_ID = '6687b862-10d0-4144-ae30-8bdc55f22ee3'


class Command(BaseCommand):
    help = "Verifica CRs com Livro Ata pendente no turno e notifica coordenador/supervisor (WhatsApp) e gerente (e-mail)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--turno',
            required=True,
            choices=['diurno', 'noturno'],
            help="Turno a verificar: 'diurno' (06h-18h) ou 'noturno' (18h-06h)",
        )

    def handle(self, *args, **options):
        turno = options['turno']
        hoje = datetime.now().date()

        if turno == 'diurno':
            inicio = datetime.combine(hoje, time(6, 0, 0))
            fim = datetime.combine(hoje, time(18, 0, 0))
        else:
            inicio = datetime.combine(hoje - timedelta(days=1), time(18, 0, 0))
            fim = datetime.combine(hoje, time(6, 0, 0))

        crs = list(LivroAtaQRCode.objects.using('default').all())
        if not crs:
            self.stdout.write("Nenhum CR com QR Code do Livro Ata cadastrado.")
            return

        db_conn_name = 'dw_vpn' if 'dw_vpn' in connections else ('readonly' if 'readonly' in connections else 'default')

        pendentes = [
            livro_ata for livro_ata in crs
            if livro_ata.cr_id and not self.turno_foi_preenchido(db_conn_name, livro_ata.cr_id, inicio, fim)
        ]

        if not pendentes:
            self.stdout.write(f"Turno {turno} ({inicio} - {fim}): todos os CRs preencheram o Livro Ata.")
            return

        responsaveis = list(
            CustomUser.objects.using('default')
            .filter(notificar_livro_ata=True, role__in=['coordenador', 'supervisor', 'gerente'], is_active=True)
        )
        if not responsaveis:
            self.stdout.write("Nenhum coordenador/supervisor/gerente com notificação de Livro Ata habilitada (Controle de Usuários).")
            return

        for livro_ata in pendentes:
            cr_nome = livro_ata.cr_descricao or livro_ata.cr_id

            destinatarios_whatsapp = []
            destinatarios_email = []
            for user in responsaveis:
                if not self.usuario_cobre_cr(user, cr_nome):
                    continue
                if user.role in ('coordenador', 'supervisor') and user.whatsapp_notificacao:
                    destinatarios_whatsapp.append(user.whatsapp_notificacao)
                elif user.role == 'gerente' and user.email:
                    destinatarios_email.append(user.email)

            mensagem = (
                "⚠️ *Livro Ata não preenchido*\n\n"
                f"CR: {cr_nome}\n"
                f"Turno: {turno.upper()} ({inicio.strftime('%d/%m %H:%M')} - {fim.strftime('%d/%m %H:%M')})\n\n"
                "Nenhum registro de plantão foi encontrado para esse período. "
                "Verifique com o responsável pelo posto."
            )
            for numero in destinatarios_whatsapp:
                sucesso, detalhe = enviar_whatsapp(numero, mensagem)
                status = "OK" if sucesso else f"FALHOU: {detalhe}"
                self.stdout.write(f"CR {cr_nome} -> WhatsApp {numero}: notificação {status}")

            if destinatarios_email:
                self.enviar_email_gerentes(destinatarios_email, cr_nome, turno, inicio, fim)

    def usuario_cobre_cr(self, user, cr_nome):
        """Replica o critério de cobertura de CR já usado no restante do sistema
        (CustomUser.is_general / CustomUser.crs) para decidir quem é notificado."""
        if user.is_general:
            return True
        if not user.crs:
            return False

        cr_num_match = re.search(r'\d+', str(cr_nome))
        cr_num = cr_num_match.group() if cr_num_match else None

        crs_nums = [m.group() for c in user.crs.split(',') if (m := re.search(r'\d+', c))]
        if cr_num and cr_num in crs_nums:
            return True
        return cr_nome.strip() in [c.strip() for c in user.crs.split(',')]

    def enviar_email_gerentes(self, destinatarios, cr_nome, turno, inicio, fim):
        assunto = f"Livro Ata não preenchido - CR {cr_nome}"
        contexto = {
            'cr_nome': cr_nome,
            'turno': turno.upper(),
            'inicio': inicio.strftime('%d/%m/%Y %H:%M'),
            'fim': fim.strftime('%d/%m/%Y %H:%M'),
        }
        html_content = render_to_string('emails/alerta_livro_ata.html', contexto)
        texto_simples = (
            f"O CR {cr_nome} não teve o Livro Ata preenchido no turno {contexto['turno']} "
            f"({contexto['inicio']} - {contexto['fim']})."
        )
        for destinatario in destinatarios:
            email_msg = EmailMultiAlternatives(
                assunto, texto_simples, settings.DEFAULT_FROM_EMAIL, [destinatario],
            )
            email_msg.attach_alternative(html_content, "text/html")
            try:
                email_msg.send()
                self.stdout.write(f"CR {cr_nome} -> E-mail {destinatario}: notificação OK")
            except Exception as e:
                self.stdout.write(f"CR {cr_nome} -> E-mail {destinatario}: FALHOU: {e}")

    def turno_foi_preenchido(self, db_conn_name, cr_id, inicio, fim):
        """Retorna True se existe ao menos um registro concluído (não expirado) no período."""
        cursor = connections[db_conn_name].cursor()
        try:
            query = """
                SELECT COUNT(*)
                FROM dbo.tarefa t
                INNER JOIN dbo.checklist c ON c.id = t.checklistid
                WHERE c.id = %s
                  AND t.status = 85
                  AND t.estruturaid = %s
                  AND (t.expirada = false OR t.expirada IS NULL)
                  AND t.terminoreal >= %s
                  AND t.terminoreal < %s
            """
            cursor.execute(query, [
                CHECKLIST_LIVRO_ATA_ID,
                cr_id,
                inicio.strftime('%Y-%m-%d %H:%M:%S'),
                fim.strftime('%Y-%m-%d %H:%M:%S'),
            ])
            count = cursor.fetchone()[0]
            return count > 0
        finally:
            cursor.close()
