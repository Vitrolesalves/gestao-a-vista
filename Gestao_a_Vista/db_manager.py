import logging
import re
from django.db import connections
from django.core.management import call_command

logger = logging.getLogger(__name__)

DB_SLUG_RE = re.compile(r'^[a-z0-9](?:[a-z0-9-]{0,48}[a-z0-9])?$')


def ensure_db_alias_registered(db_alias, db_name):
    """
    Garante que um alias de banco de dados esteja disponível para uso nesta
    requisição/processo, registrando-o em tempo de execução se ainda não
    existir. Necessário porque o Django só conhece os aliases presentes em
    settings.DATABASES no momento do import; regionais criadas depois do
    processo já estar de pé (ou vistas por outro worker do uWSGI) precisam
    se auto-registrar na primeira vez que forem usadas.
    """
    from django.conf import settings

    config = {**settings.DATABASES['default'], 'NAME': db_name}
    if db_alias not in settings.DATABASES:
        settings.DATABASES[db_alias] = config
    if db_alias not in connections.databases:
        connections.databases[db_alias] = settings.DATABASES[db_alias]


def check_and_create_regional_db(db_slug):
    """
    Verifica se o banco de dados físico de uma regional (identificada pelo
    seu db_slug, ex: 'sp', 'es', 'sp-vpa-sao-jose-dos-campos') existe.
    Caso não exista, cria-o no PostgreSQL e roda as migrações necessárias.
    """
    db_slug = db_slug.strip().lower()
    if not DB_SLUG_RE.match(db_slug):
        raise ValueError(f"db_slug inválido para provisionamento de banco: '{db_slug}'")

    # Caso especial histórico: a regional "go" sempre foi o próprio banco
    # default/gestao_a_vista, nunca um banco "go_gestao" separado.
    db_name = "db_teste" if db_slug == "go" else f"{db_slug}_gestao"
    db_alias = f"db_{db_slug}"

    ensure_db_alias_registered(db_alias, db_name)

    # Lock consultivo do Postgres, chaveado pelo db_slug: evita que duas
    # requisições concorrentes (ex.: duplo clique em "Criar Regional", ou
    # duas abas) tentem criar/migrar o MESMO banco novo ao mesmo tempo.
    # Sem isso, dois "migrate" simultâneos na mesma tabela recém-criada
    # colidem com erro tipo "column ... already exists" (a segunda chamada
    # tenta aplicar uma migration que a primeira já aplicou, mas ainda não
    # tinha commitado a linha em django_migrations quando a segunda leu a
    # lista de migrations já aplicadas). O lock é liberado automaticamente
    # se a conexão cair, e é sempre liberado no fim desta função.
    lock_conn = connections['default']
    with lock_conn.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_lock(hashtext(%s)::bigint)", [db_slug])

    try:
        logger.info(f"Verificando existência do banco de dados '{db_name}'...")

        # 1. Verificar no PostgreSQL se o banco de dados já existe
        db_exists = False
        try:
            with lock_conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", [db_name])
                db_exists = bool(cursor.fetchone())
        except Exception as e:
            logger.error(f"Erro ao verificar a existência do banco '{db_name}': {e}")
            # Se falhar a verificação, prossegue assumindo que não existe ou tentando tratar o erro
            db_exists = False

        # 2. Se não existir, criar o banco no PostgreSQL
        if not db_exists:
            logger.info(f"Banco de dados '{db_name}' não existe. Criando...")
            try:
                # CREATE DATABASE não pode rodar dentro de transação, necessita autocommit
                old_autocommit = lock_conn.autocommit
                lock_conn.autocommit = True
                try:
                    with lock_conn.cursor() as cursor:
                        # Interpolação direta é segura aqui porque db_slug já foi validado
                        # contra DB_SLUG_RE acima (CREATE DATABASE não suporta parâmetros
                        # de bind tipo %s para identificadores)
                        cursor.execute(f'CREATE DATABASE "{db_name}"')
                    logger.info(f"Banco de dados '{db_name}' criado com sucesso!")
                finally:
                    lock_conn.autocommit = old_autocommit
            except Exception as e:
                logger.error(f"Falha ao criar o banco de dados '{db_name}': {e}")
                raise RuntimeError(f"Não foi possível criar o banco de dados '{db_name}': {str(e)}")

        # 3. Rodar as migrações do Django no banco da regional (db_alias)
        logger.info(f"Executando migrações no banco '{db_alias}'...")
        try:
            call_command('migrate', database=db_alias, interactive=False)
            logger.info(f"Migrações aplicadas com sucesso no banco '{db_alias}'!")
        except Exception as e:
            logger.error(f"Erro ao rodar migrações no banco '{db_alias}': {e}", exc_info=True)
            raise e
    finally:
        with lock_conn.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_unlock(hashtext(%s)::bigint)", [db_slug])

    return True
