"""
Database router para direcionar consultas de relatórios para o banco readonly ou regionais
"""
from .thread_local import get_current_db


class DatabaseRouter:
    """
    Router para direcionar consultas específicas para diferentes bancos de dados (default vs regionais)
    """
    GLOBAL_MODELS = {
        'customuser', 'regional', 'solicitacaocadastro', 'userprofile',
        'useractivity', 'userpermissiongroup', 'session', 'contenttype',
        'permission', 'group', 'logentry', 'linkimportante',
    }

    def db_for_read(self, model, **hints):
        """Direciona leituras para bancos específicos"""
        import sys
        # Se estiver rodando migração via terminal
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return 'default'
            
        app_label = model._meta.app_label
        model_name = model._meta.model_name

        # Modelos globais e de autenticação vão para o default
        if app_label in {'auth', 'sessions', 'contenttypes', 'admin'} or model_name in self.GLOBAL_MODELS:
            return 'default'
        
        # Roteamento dinâmico para o banco da regional ativa
        current_db = get_current_db()
        if current_db:
            return current_db
            
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Direciona escritas para o banco correspondente"""
        app_label = model._meta.app_label
        model_name = model._meta.model_name

        if app_label in {'auth', 'sessions', 'contenttypes', 'admin'} or model_name in self.GLOBAL_MODELS:
            return 'default'

        current_db = get_current_db()
        if current_db:
            return current_db

        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """Permite relações entre objetos"""
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Controla quais migrações rodam em quais bancos"""
        # Bancos regionais (db_*) precisam migrar todas as tabelas (inclusive globais)
        # para evitar erros de chaves estrangeiras (ForeignKeys) que apontam para tabelas globais.
        if db.startswith('db_'):
            return True
            
        return db == 'default'


