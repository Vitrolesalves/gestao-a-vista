from asgiref.local import Local

_thread_local = Local()

def set_current_db(db_name):
    """Seta o banco de dados ativo para a thread atual"""
    _thread_local.current_db = db_name

def get_current_db():
    """Retorna o banco de dados ativo na thread atual"""
    return getattr(_thread_local, 'current_db', None)

def clear_current_db():
    """Limpa o estado do banco de dados na thread atual"""
    if hasattr(_thread_local, 'current_db'):
        del _thread_local.current_db
