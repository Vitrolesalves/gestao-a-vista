"""
Modelos para consulta de relatórios no banco local (sincronizado)
"""

from django.db import models, connection, connections
from django.utils.translation import gettext_lazy as _

class TarefaRelatorio(models.Model):
    """
    Modelo mantido por compatibilidade.
    """
    _use_readonly_db = True
    
    id = models.CharField(max_length=255, primary_key=True)
    numero = models.CharField(_("número"), max_length=255, blank=True, null=True)
    nome = models.CharField(_("nome"), max_length=500, blank=True, null=True)
    estruturaid = models.CharField(_("estrutura ID"), max_length=255, blank=True, null=True)
    checklistid = models.CharField(_("checklist ID"), max_length=255, blank=True, null=True)
    status = models.CharField(_("status"), max_length=10, blank=True, null=True)
    terminoreal = models.DateTimeField(_("término real"), blank=True, null=True)
    
    class Meta:
        db_table = "dbo.tarefa"
        managed = False
        verbose_name = _("Tarefa Relatório")
        verbose_name_plural = _("Tarefas Relatório")
    
    def __str__(self):
        return f"{self.numero} - {self.nome}"


class ExecucaoRelatorio(models.Model):
    """
    Modelo mantido por compatibilidade.
    """
    _use_readonly_db = True
    
    id = models.CharField(max_length=255, primary_key=True)
    tarefaid = models.CharField(_("tarefa ID"), max_length=255, blank=True, null=True)
    criadoporhash = models.CharField(_("criado por hash"), max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = "dbo.execucao"
        managed = False
        verbose_name = _("Execução Relatório")
        verbose_name_plural = _("Execuções Relatório")


class RecursoRelatorio(models.Model):
    """
    Modelo mantido por compatibilidade.
    """
    _use_readonly_db = True
    
    id = models.CharField(max_length=255, primary_key=True)
    codigohash = models.CharField(_("código hash"), max_length=255, blank=True, null=True)
    nome = models.CharField(_("nome"), max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = "dbo.recurso"
        managed = False
        verbose_name = _("Recurso Relatório")
        verbose_name_plural = _("Recursos Relatório")
    
    def __str__(self):
        return self.nome or ""


class EstruturaRelatorio(models.Model):
    """
    Modelo mantido por compatibilidade.
    """
    _use_readonly_db = True
    
    id = models.CharField(max_length=255, primary_key=True)
    descricao = models.CharField(_("descrição"), max_length=500, blank=True, null=True)
    
    class Meta:
        db_table = "dbo.estrutura"
        managed = False
        verbose_name = _("Estrutura Relatório")
        verbose_name_plural = _("Estruturas Relatório")
    
    def __str__(self):
        return self.descricao or ""


# =====================================================================
# NOVA VIEW DE RELATÓRIOS (APONTADA PARA A TABELA SINCRONIZADA LOCAL)
# =====================================================================

class RelatorioView:
    """
    Classe para consultas de relatórios usando SQL direto na tabela clonada local
    """
    
    # IDs dos checklists
    CHECKLIST_APR_VIAGEM_SEGURA = '10759f2e-4e9a-4c89-89fd-a684d9b2f824'
    CHECKLIST_INSPECAO_EPI = '8754329b-d29e-4f35-91aa-ec29d387720a'
    
    @staticmethod
    def get_relatorios(checklist_id, filtros=None, user=None):
        """
        Busca relatórios do banco LOCAL usando a tabela Gestao_a_Vista_relatorios_sync
        """
        # SQL base (não requer mais os INNER JOINs lentos)
        sql = """
        SELECT DISTINCT
            t.tarefa_id AS id,
            t.numero AS "numero",
            t.nome AS "nome",
            t.cr AS "cr",
            t.responsavel AS "responsavel",
            t.data_termino AS "data"
        FROM public."Gestao_a_Vista_relatorios_sync" t
        """
        
        # Se não for adm global, precisamos do JOIN com a estrutura para filtrar por regional
        if user and not getattr(user, 'is_global_admin', False):
            sql += ' LEFT JOIN public.estrutura e ON t.cr = e.cr'
            
        sql += " WHERE 1=1"
        
        params = []
        
        # Filtros do usuário (Regional/CRs)
        if user and not getattr(user, 'is_global_admin', False):
            user_crs = [c.strip() for c in user.crs.split(',') if c.strip()] if getattr(user, 'crs', None) else []
            if user_crs:
                sql += " AND t.cr IN (" + ",".join(["%s"] * len(user_crs)) + ")"
                params.extend(user_crs)
            elif getattr(user, 'regional', None):
                regional_terms = []
                if user.regional.nome:
                    regional_terms.append(user.regional.nome.strip().lower())
                if user.regional.cidade:
                    regional_terms.append(user.regional.cidade.strip().lower())
                if user.regional.estado:
                    regional_terms.append(user.regional.estado.strip().lower())
                regional_terms = list(set([t for t in regional_terms if t]))
                
                if regional_terms:
                    or_conditions = []
                    for term in regional_terms:
                        or_conditions.append("LOWER(e.nivel_4) = %s")
                        params.append(term)
                        or_conditions.append("LOWER(e.nivel_4) LIKE %s")
                        params.append(f"%{term}%")
                    sql += f" AND ({' OR '.join(or_conditions)})"
        
        # Aplicar filtros se fornecidos pelo utilizador na interface
        if filtros:
            if filtros.get('search'):
                sql += " AND (LOWER(t.numero) LIKE LOWER(%s) OR LOWER(t.nome) LIKE LOWER(%s))"
                search_param = f"%{filtros['search']}%"
                params.extend([search_param, search_param])
            
            if filtros.get('responsavel') and filtros['responsavel'] != 'all':
                sql += " AND t.responsavel = %s"
                params.append(filtros['responsavel'])
            
            if filtros.get('cr') and filtros['cr'] != 'all':
                sql += " AND t.cr = %s"
                params.append(filtros['cr'])
            
            if filtros.get('data_inicial'):
                sql += " AND t.data_termino >= %s"
                params.append(filtros['data_inicial'])
            
            if filtros.get('data_final'):
                sql += " AND t.data_termino <= %s"
                params.append(filtros['data_final'])
        
        # Ordenar por data mais recente
        sql += " ORDER BY t.data_termino DESC"
        
        # Usamos a conexão dinâmica correta (readonly/dw_vpn se existir, senão default)
        db_conn_name = 'dw_vpn' if 'dw_vpn' in connections else ('readonly' if 'readonly' in connections else 'default')
        with connections[db_conn_name].cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    @staticmethod
    def get_responsaveis_list(checklist_id, user=None):
        """
        Busca lista de responsáveis únicos para o filtro (Rápido, no banco local)
        """
        sql = """
        SELECT DISTINCT t.responsavel
        FROM public."Gestao_a_Vista_relatorios_sync" t
        """
        
        if user and not getattr(user, 'is_global_admin', False):
            sql += ' LEFT JOIN public.estrutura e ON t.cr = e.cr'
            
        sql += " WHERE t.responsavel IS NOT NULL AND t.responsavel != ''"
        
        params = []
        if user and not getattr(user, 'is_global_admin', False):
            user_crs = [c.strip() for c in user.crs.split(',') if c.strip()] if getattr(user, 'crs', None) else []
            if user_crs:
                sql += " AND t.cr IN (" + ",".join(["%s"] * len(user_crs)) + ")"
                params.extend(user_crs)
            elif getattr(user, 'regional', None):
                regional_terms = []
                if user.regional.nome:
                    regional_terms.append(user.regional.nome.strip().lower())
                if user.regional.cidade:
                    regional_terms.append(user.regional.cidade.strip().lower())
                if user.regional.estado:
                    regional_terms.append(user.regional.estado.strip().lower())
                regional_terms = list(set([t for t in regional_terms if t]))
                
                if regional_terms:
                    or_conditions = []
                    for term in regional_terms:
                        or_conditions.append("LOWER(e.nivel_4) = %s")
                        params.append(term)
                        or_conditions.append("LOWER(e.nivel_4) LIKE %s")
                        params.append(f"%{term}%")
                    sql += f" AND ({' OR '.join(or_conditions)})"
                    
        sql += " ORDER BY t.responsavel"
        
        db_conn_name = 'dw_vpn' if 'dw_vpn' in connections else ('readonly' if 'readonly' in connections else 'default')
        with connections[db_conn_name].cursor() as cursor:
            cursor.execute(sql, params)
            return [row[0] for row in cursor.fetchall()]
    
    @staticmethod
    def get_crs_list(checklist_id, user=None):
        """
        Busca lista de CRs únicos para o filtro (Rápido, no banco local)
        """
        sql = """
        SELECT DISTINCT t.cr
        FROM public."Gestao_a_Vista_relatorios_sync" t
        """
        
        if user and not getattr(user, 'is_global_admin', False):
            sql += ' LEFT JOIN public.estrutura e ON t.cr = e.cr'
            
        sql += " WHERE t.cr IS NOT NULL AND t.cr != ''"
        
        params = []
        if user and not getattr(user, 'is_global_admin', False):
            user_crs = [c.strip() for c in user.crs.split(',') if c.strip()] if getattr(user, 'crs', None) else []
            if user_crs:
                sql += " AND t.cr IN (" + ",".join(["%s"] * len(user_crs)) + ")"
                params.extend(user_crs)
            elif getattr(user, 'regional', None):
                regional_terms = []
                if user.regional.nome:
                    regional_terms.append(user.regional.nome.strip().lower())
                if user.regional.cidade:
                    regional_terms.append(user.regional.cidade.strip().lower())
                if user.regional.estado:
                    regional_terms.append(user.regional.estado.strip().lower())
                regional_terms = list(set([t for t in regional_terms if t]))
                
                if regional_terms:
                    or_conditions = []
                    for term in regional_terms:
                        or_conditions.append("LOWER(e.nivel_4) = %s")
                        params.append(term)
                        or_conditions.append("LOWER(e.nivel_4) LIKE %s")
                        params.append(f"%{term}%")
                    sql += f" AND ({' OR '.join(or_conditions)})"
                    
        sql += " ORDER BY t.cr"
        
        db_conn_name = 'dw_vpn' if 'dw_vpn' in connections else ('readonly' if 'readonly' in connections else 'default')
        with connections[db_conn_name].cursor() as cursor:
            cursor.execute(sql, params)
            return [row[0] for row in cursor.fetchall()]