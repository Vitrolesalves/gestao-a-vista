# Gerada manualmente: aplica a constraint real de PRIMARY KEY em ocorrencia_hash.
# O campo já era primary_key=True no model, mas a tabela em produção nunca teve
# a constraint de fato (nem PK, nem UNIQUE, nem índice, nem NOT NULL) — só era
# "única" por convenção do código Python, então duas requisições concorrentes
# podiam gravar o mesmo ocorrencia_hash em duas linhas diferentes.
#
# O SQL abaixo é específico de PostgreSQL (bloco DO $$, ALTER COLUMN ... SET NOT
# NULL), por isso a operação é guardada por vendor: em SQLite (testes/preview
# local) ela é um no-op — lá a tabela já nasce com a PK vinda do model, e o SQL
# quebrava qualquer 'migrate' do zero com "near ALTER: syntax error". Em
# PostgreSQL (produção e bancos das regionais, inclusive provisionamento de
# regional nova) o comportamento é EXATAMENTE o mesmo de antes.

from django.db import migrations

POSTGRES_SQL = """
    ALTER TABLE auditoria_ocorrencia_status
        ALTER COLUMN ocorrencia_hash SET NOT NULL;
    DO $$
    DECLARE
        existing_pk text;
    BEGIN
        SELECT tc.constraint_name INTO existing_pk
        FROM information_schema.table_constraints tc
        WHERE tc.table_name = 'auditoria_ocorrencia_status'
          AND tc.constraint_type = 'PRIMARY KEY';

        IF existing_pk IS NULL THEN
            ALTER TABLE auditoria_ocorrencia_status
                ADD CONSTRAINT auditoria_ocorrencia_status_pkey PRIMARY KEY (ocorrencia_hash);
        ELSIF existing_pk <> 'auditoria_ocorrencia_status_pkey' THEN
            EXECUTE format('ALTER TABLE auditoria_ocorrencia_status DROP CONSTRAINT %I', existing_pk);
            ALTER TABLE auditoria_ocorrencia_status
                ADD CONSTRAINT auditoria_ocorrencia_status_pkey PRIMARY KEY (ocorrencia_hash);
        END IF;
    END $$;
"""

POSTGRES_REVERSE_SQL = """
    ALTER TABLE auditoria_ocorrencia_status
        DROP CONSTRAINT IF EXISTS auditoria_ocorrencia_status_pkey;
    ALTER TABLE auditoria_ocorrencia_status
        ALTER COLUMN ocorrencia_hash DROP NOT NULL;
"""


def aplicar_pk_constraint(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute(POSTGRES_SQL)


def reverter_pk_constraint(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute(POSTGRES_REVERSE_SQL)


class Migration(migrations.Migration):

    dependencies = [
        ('Gestao_a_Vista', '0053_auditoria_numero_id_inicio_real'),
    ]

    operations = [
        migrations.RunPython(aplicar_pk_constraint, reverter_pk_constraint),
    ]
