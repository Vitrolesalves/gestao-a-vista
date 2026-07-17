from __future__ import annotations

import pandas as pd

from .config import AlertThresholds


ALERT_ORDER = {"sem_alerta": 0, "atencao": 1, "critico": 2, "estourado": 3, "sem_orcamento": 4}


def prepare_financial_view(data: pd.DataFrame, thresholds: AlertThresholds) -> pd.DataFrame:
    if data.empty:
        return data.copy()

    view = data.copy()
    view["orcado_abs"] = view["orcado"].abs()
    view["realizado_abs"] = view["realizado"].abs()
    view["tipo"] = view.apply(classify_row_type, axis=1)
    view["consumo_pct"] = view.apply(consumption_pct, axis=1)
    view["saldo_abs"] = view["orcado_abs"] - view["realizado_abs"]
    view["excesso_abs"] = (view["realizado_abs"] - view["orcado_abs"]).clip(lower=0)
    view["nivel_alerta"] = view.apply(lambda row: alert_level(row, thresholds), axis=1)
    return view


def classify_row_type(row: pd.Series) -> str:
    text = f"{row.get('conta_contabil', '')} {row.get('descricao_conta', '')}".lower()
    if any(word in text for word in ("receita", "faturamento", "entrada")):
        return "receita"
    if row.get("realizado", 0) < 0 or row.get("orcado", 0) < 0:
        return "custo"
    return "custo"


def consumption_pct(row: pd.Series) -> float:
    budget = float(row.get("orcado_abs", 0) or 0)
    if budget <= 0:
        return 0.0
    return float(row.get("realizado_abs", 0) or 0) / budget


def alert_level(row: pd.Series, thresholds: AlertThresholds) -> str:
    if row.get("tipo") != "custo":
        return "sem_alerta"
    budget = float(row.get("orcado_abs", 0) or 0)
    if budget <= 0:
        return "sem_alerta"

    pct = float(row.get("consumo_pct", 0) or 0)
    if pct >= thresholds.estourado:
        return "estourado"
    if pct >= thresholds.critico:
        return "critico"
    if pct >= thresholds.atencao:
        return "atencao"
    return "sem_alerta"


def aggregate_accounts(view: pd.DataFrame, thresholds: AlertThresholds) -> pd.DataFrame:
    if view.empty:
        return empty_aggregate()

    grouped = (
        view.groupby(["mes", "pec", "contrato", "conta_contabil", "descricao_conta"], dropna=False)
        .agg(
            orcado=("orcado", "sum"),
            realizado=("realizado", "sum"),
            orcado_abs=("orcado_abs", "sum"),
            realizado_abs=("realizado_abs", "sum"),
            fornecedores=("fornecedor", lambda s: ", ".join(sorted({x for x in s if x})[:5])),
        )
        .reset_index()
    )
    grouped["tipo"] = grouped.apply(classify_row_type, axis=1)
    grouped["consumo_pct"] = grouped.apply(consumption_pct, axis=1)
    grouped["saldo_abs"] = grouped["orcado_abs"] - grouped["realizado_abs"]
    grouped["excesso_abs"] = (grouped["realizado_abs"] - grouped["orcado_abs"]).clip(lower=0)
    grouped["nivel_alerta"] = grouped.apply(lambda row: alert_level(row, thresholds), axis=1)
    grouped["alerta_ordem"] = grouped["nivel_alerta"].map(ALERT_ORDER).fillna(0).astype(int)
    return grouped.sort_values(["alerta_ordem", "consumo_pct"], ascending=[False, False])


def empty_aggregate() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "mes",
            "pec",
            "contrato",
            "conta_contabil",
            "descricao_conta",
            "orcado",
            "realizado",
            "orcado_abs",
            "realizado_abs",
            "fornecedores",
            "tipo",
            "consumo_pct",
            "saldo_abs",
            "excesso_abs",
            "nivel_alerta",
            "alerta_ordem",
            "tem_orcamento",
            "cc_sup",
            "fornecedores_qtd",
            "compras_linhas",
        ]
    )


def build_dashboard_accounts(
    compras: pd.DataFrame,
    orcamento: pd.DataFrame,
    thresholds: AlertThresholds,
) -> pd.DataFrame:
    if compras.empty and orcamento.empty:
        return empty_aggregate()

    spent = aggregate_purchases(compras)
    budget = aggregate_budget(orcamento)

    keys = ["mes", "pec_codigo", "conta_codigo"]
    accounts = budget.merge(spent, on=keys, how="outer", suffixes=("_orc", "_compra"))
    accounts["mes"] = accounts["mes"].fillna("")
    accounts["pec"] = accounts["pec_orc"].combine_first(accounts["pec_compra"]).fillna("")
    accounts["conta_contabil"] = accounts["conta_orc"].combine_first(accounts["conta_compra"]).fillna("")
    accounts["descricao_conta"] = accounts["conta_desc_orc"].combine_first(accounts["conta_desc_compra"]).fillna("")
    accounts["cc_sup"] = accounts["cc_sup"].fillna("Sem CC. SUP no orcamento")
    accounts["orcado"] = accounts["valor_or"].fillna(0.0)
    accounts["realizado"] = accounts["compra_realizada"].fillna(0.0)
    accounts["realizado_re_x_or"] = accounts["vl_realizado"].fillna(0.0)
    accounts["re_ajustado"] = accounts["re_ajustado"].fillna(0.0)
    accounts["dif_re_x_or"] = accounts["dif_re_x_or"].fillna(0.0)
    accounts["fornecedores"] = accounts["fornecedores"].fillna("")
    accounts["fornecedores_qtd"] = accounts["fornecedores_qtd"].fillna(0).astype(int)
    accounts["compras_linhas"] = accounts["compras_linhas"].fillna(0).astype(int)
    accounts["contrato"] = accounts["pec"]
    accounts["tem_orcamento"] = accounts["valor_or"].notna()
    accounts["tipo"] = accounts.apply(classify_dashboard_row_type, axis=1)
    accounts["orcado_abs"] = accounts["orcado"].abs()
    accounts["realizado_abs"] = accounts["realizado"].abs()
    accounts["consumo_pct"] = accounts.apply(consumption_pct, axis=1)
    accounts["saldo_abs"] = accounts["orcado_abs"] - accounts["realizado_abs"]
    accounts["excesso_abs"] = (accounts["realizado_abs"] - accounts["orcado_abs"]).clip(lower=0)
    accounts["nivel_alerta"] = accounts.apply(lambda row: dashboard_alert_level(row, thresholds), axis=1)
    accounts["alerta_ordem"] = accounts["nivel_alerta"].map(ALERT_ORDER).fillna(0).astype(int)

    output_columns = [
        "mes",
        "pec",
        "pec_codigo",
        "contrato",
        "cc_sup",
        "conta_contabil",
        "conta_codigo",
        "descricao_conta",
        "orcado",
        "realizado",
        "realizado_re_x_or",
        "re_ajustado",
        "dif_re_x_or",
        "orcado_abs",
        "realizado_abs",
        "fornecedores",
        "fornecedores_qtd",
        "compras_linhas",
        "tipo",
        "consumo_pct",
        "saldo_abs",
        "excesso_abs",
        "tem_orcamento",
        "nivel_alerta",
        "alerta_ordem",
    ]
    return accounts[output_columns].sort_values(["alerta_ordem", "consumo_pct"], ascending=[False, False])


def aggregate_purchases(compras: pd.DataFrame) -> pd.DataFrame:
    if compras.empty:
        return pd.DataFrame(
            columns=[
                "mes",
                "pec_codigo",
                "conta_codigo",
                "pec_compra",
                "conta_compra",
                "conta_desc_compra",
                "compra_realizada",
                "fornecedores",
                "fornecedores_qtd",
                "compras_linhas",
            ]
        )

    return (
        compras.groupby(["mes", "pec_codigo", "conta_codigo"], dropna=False)
        .agg(
            pec_compra=("pec", "first"),
            conta_compra=("conta", "first"),
            conta_desc_compra=("conta_desc", "first"),
            compra_realizada=("valor_compra", "sum"),
            fornecedores=("fornecedor", lambda s: ", ".join(sorted({x for x in s if x})[:8])),
            fornecedores_qtd=("fornecedor", "nunique"),
            compras_linhas=("fornecedor", "size"),
        )
        .reset_index()
    )


def aggregate_budget(orcamento: pd.DataFrame) -> pd.DataFrame:
    if orcamento.empty:
        return pd.DataFrame(
            columns=[
                "mes",
                "pec_codigo",
                "conta_codigo",
                "pec_orc",
                "conta_orc",
                "conta_desc_orc",
                "cc_sup",
                "valor_or",
                "vl_realizado",
                "re_ajustado",
                "dif_re_x_or",
            ]
        )

    return (
        orcamento.groupby(["mes", "pec_codigo", "conta_codigo"], dropna=False)
        .agg(
            pec_orc=("pec", "first"),
            conta_orc=("conta", "first"),
            conta_desc_orc=("conta_desc", "first"),
            cc_sup=("cc_sup", "first"),
            valor_or=("valor_or", "sum"),
            vl_realizado=("vl_realizado", "sum"),
            re_ajustado=("re_ajustado", "sum"),
            dif_re_x_or=("dif_re_x_or", "sum"),
        )
        .reset_index()
    )


def classify_dashboard_row_type(row: pd.Series) -> str:
    text = f"{row.get('cc_sup', '')} {row.get('conta_contabil', '')}".lower()
    code = str(row.get("conta_codigo", ""))
    if code.startswith(("311", "431")) or "receita" in text:
        return "receita"
    return "custo"


def dashboard_alert_level(row: pd.Series, thresholds: AlertThresholds) -> str:
    if row.get("tipo") != "custo":
        return "sem_alerta"
    spent = float(row.get("realizado_abs", 0) or 0)
    budget = float(row.get("orcado_abs", 0) or 0)
    if spent > 0 and (not bool(row.get("tem_orcamento", False)) or budget <= 0):
        return "sem_orcamento"
    return alert_level(row, thresholds)


def summarize_kpis(accounts: pd.DataFrame) -> dict[str, float]:
    costs = accounts[accounts["tipo"] == "custo"] if not accounts.empty else accounts
    revenue = accounts[accounts["tipo"] == "receita"] if not accounts.empty else accounts
    total_budget = abs(float(costs["orcado"].sum())) if not costs.empty else 0.0
    total_realized = float(costs["realizado_abs"].sum()) if not costs.empty else 0.0
    budgeted_revenue = float(revenue["orcado"].clip(lower=0).sum()) if not revenue.empty else 0.0
    realized_revenue = float(revenue["realizado_re_x_or"].sum()) if "realizado_re_x_or" in revenue and not revenue.empty else 0.0
    budgeted_margin = budgeted_revenue - total_budget
    current_budget_margin = budgeted_revenue - total_realized
    return {
        "receita_orcada": budgeted_revenue,
        "orcamento_custos": total_budget,
        "realizado_custos": total_realized,
        "saldo_custos": total_budget - total_realized,
        "excesso_total": float(costs["excesso_abs"].sum()) if not costs.empty else 0.0,
        "alertas_total": float(costs[costs["nivel_alerta"] != "sem_alerta"].shape[0]) if not costs.empty else 0.0,
        "receita_realizada": realized_revenue,
        "margem_orcada": budgeted_margin,
        "margem_atual_orcada": current_budget_margin,
        "lucro_estimado": realized_revenue - total_realized,
    }


def summarize_alert_counts(data: pd.DataFrame, alert_column: str = "nivel_alerta") -> dict[str, int]:
    keys = ("sem_orcamento", "estourado", "critico", "atencao")
    if data.empty or alert_column not in data:
        return {key: 0 for key in keys}
    costs = data[data["tipo"] == "custo"] if "tipo" in data else data
    counts = costs[alert_column].value_counts().to_dict()
    return {key: int(counts.get(key, 0)) for key in keys}


def filter_by_alert_levels(
    data: pd.DataFrame,
    selected_levels: tuple[str, ...] | list[str] | set[str],
    alert_column: str = "nivel_alerta",
) -> pd.DataFrame:
    if data.empty or not selected_levels or alert_column not in data:
        return data
    return data[data[alert_column].isin(selected_levels)]


def top_costs_by_dimension(accounts: pd.DataFrame, dimension: str, limit: int = 10) -> pd.DataFrame:
    if accounts.empty or dimension not in accounts:
        return pd.DataFrame(columns=[dimension, "realizado_abs", "orcado_abs", "consumo_pct", "excesso_abs"])

    costs = accounts[accounts["tipo"] == "custo"]
    if costs.empty:
        return pd.DataFrame(columns=[dimension, "realizado_abs", "orcado_abs", "consumo_pct", "excesso_abs"])

    grouped = (
        costs.groupby(dimension, dropna=False)
        .agg(orcado_abs=("orcado_abs", "sum"), realizado_abs=("realizado_abs", "sum"), excesso_abs=("excesso_abs", "sum"))
        .reset_index()
    )
    grouped["consumo_pct"] = grouped.apply(consumption_pct, axis=1)
    return grouped.sort_values("realizado_abs", ascending=False).head(limit)


def month_variation(accounts: pd.DataFrame) -> pd.DataFrame:
    if accounts.empty:
        return pd.DataFrame(columns=["conta_contabil", "descricao_conta", "mes", "realizado_abs"])

    costs = accounts[accounts["tipo"] == "custo"]
    return (
        costs.groupby(["conta_contabil", "descricao_conta", "mes"], dropna=False)["realizado_abs"]
        .sum()
        .reset_index()
        .sort_values(["conta_contabil", "mes"])
    )


def build_monthly_closing_accounts(
    compras: pd.DataFrame,
    orcamento: pd.DataFrame,
    thresholds: AlertThresholds,
    meses_fechados: tuple[str, ...],
) -> pd.DataFrame:
    closed_months = {str(month).strip() for month in meses_fechados if str(month).strip()}
    if not closed_months:
        return empty_closing_aggregate()

    spent = aggregate_purchases(compras)
    budget = aggregate_budget(orcamento)
    keys = ["mes", "pec_codigo", "conta_codigo"]
    closing = budget.merge(spent, on=keys, how="outer", suffixes=("_orc", "_compra"))
    if closing.empty:
        return empty_closing_aggregate()

    closing = closing[closing["mes"].astype(str).isin(closed_months)].copy()
    if closing.empty:
        return empty_closing_aggregate()

    closing["pec"] = closing["pec_orc"].combine_first(closing["pec_compra"]).fillna("")
    closing["conta_contabil"] = closing["conta_orc"].combine_first(closing["conta_compra"]).fillna("")
    closing["descricao_conta"] = closing["conta_desc_orc"].combine_first(closing["conta_desc_compra"]).fillna("")
    closing["cc_sup"] = closing["cc_sup"].fillna("Sem CC. SUP no orcamento")
    closing["orcado"] = closing["valor_or"].fillna(0.0)
    closing["comprado_ate_agora"] = closing["compra_realizada"].fillna(0.0)
    closing["realizado_fechado"] = closing["vl_realizado"].fillna(0.0)
    closing["orcado_abs"] = closing["orcado"].abs()
    closing["comprado_ate_agora_abs"] = closing["comprado_ate_agora"].abs()
    closing["realizado_fechado_abs"] = closing["realizado_fechado"].abs()
    closing["diferenca_realizado_vs_compras"] = (
        closing["realizado_fechado_abs"] - closing["comprado_ate_agora_abs"]
    )
    closing["diferenca_realizado_vs_compras_abs"] = closing["diferenca_realizado_vs_compras"].abs()
    closing["status_mes"] = "fechado"
    closing["tem_orcamento"] = closing["valor_or"].notna() & (closing["orcado_abs"] > 0)
    closing["tem_compra_produto"] = closing["compra_realizada"].notna() & (closing["comprado_ate_agora_abs"] > 0)
    closing["tem_realizado_re_x_or"] = closing["vl_realizado"].notna() & (closing["realizado_fechado_abs"] > 0)
    closing["tipo"] = closing.apply(classify_dashboard_row_type, axis=1)
    closing["consumo_pct_fechamento"] = closing.apply(closing_consumption_pct, axis=1)
    closing["excesso_fechamento"] = (
        closing["realizado_fechado_abs"] - closing["orcado_abs"]
    ).clip(lower=0)
    closing["nivel_alerta_fechamento"] = closing.apply(lambda row: closing_alert_level(row, thresholds), axis=1)
    closing["alerta_ordem_fechamento"] = closing["nivel_alerta_fechamento"].map(ALERT_ORDER).fillna(0).astype(int)
    closing["origem_observacao"] = closing.apply(closing_origin_observation, axis=1)

    for column in ("tem_orcamento", "tem_compra_produto", "tem_realizado_re_x_or"):
        closing[column] = closing[column].map(bool).astype(object)

    output_columns = [
        "mes",
        "status_mes",
        "pec",
        "pec_codigo",
        "cc_sup",
        "conta_contabil",
        "conta_codigo",
        "descricao_conta",
        "tipo",
        "orcado",
        "orcado_abs",
        "comprado_ate_agora",
        "comprado_ate_agora_abs",
        "realizado_fechado",
        "realizado_fechado_abs",
        "diferenca_realizado_vs_compras",
        "diferenca_realizado_vs_compras_abs",
        "consumo_pct_fechamento",
        "excesso_fechamento",
        "tem_orcamento",
        "tem_compra_produto",
        "tem_realizado_re_x_or",
        "nivel_alerta_fechamento",
        "alerta_ordem_fechamento",
        "origem_observacao",
    ]
    return closing[output_columns].sort_values(
        ["alerta_ordem_fechamento", "excesso_fechamento", "diferenca_realizado_vs_compras_abs"],
        ascending=[False, False, False],
    )


def closing_consumption_pct(row: pd.Series) -> float:
    budget = float(row.get("orcado_abs", 0) or 0)
    if budget <= 0:
        return 0.0
    return float(row.get("realizado_fechado_abs", 0) or 0) / budget


def closing_alert_level(row: pd.Series, thresholds: AlertThresholds) -> str:
    if row.get("tipo") != "custo":
        return "sem_alerta"
    realized = float(row.get("realizado_fechado_abs", 0) or 0)
    budget = float(row.get("orcado_abs", 0) or 0)
    if realized > 0 and (not bool(row.get("tem_orcamento", False)) or budget <= 0):
        return "sem_orcamento"
    pct = float(row.get("consumo_pct_fechamento", 0) or 0)
    if pct >= thresholds.estourado:
        return "estourado"
    if pct >= thresholds.critico:
        return "critico"
    if pct >= thresholds.atencao:
        return "atencao"
    return "sem_alerta"


def closing_origin_observation(row: pd.Series) -> str:
    has_purchase = bool(row.get("tem_compra_produto", False))
    has_realized = bool(row.get("tem_realizado_re_x_or", False))
    has_budget = bool(row.get("tem_orcamento", False))
    if has_purchase and has_realized:
        return "compras_e_realizado_re_x_or"
    if has_realized:
        return "somente_realizado_re_x_or"
    if has_purchase:
        return "somente_compras_produto"
    if has_budget:
        return "somente_orcamento"
    return "sem_movimento"


def empty_closing_aggregate() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "mes",
            "status_mes",
            "pec",
            "pec_codigo",
            "cc_sup",
            "conta_contabil",
            "conta_codigo",
            "descricao_conta",
            "tipo",
            "orcado",
            "orcado_abs",
            "comprado_ate_agora",
            "comprado_ate_agora_abs",
            "realizado_fechado",
            "realizado_fechado_abs",
            "diferenca_realizado_vs_compras",
            "diferenca_realizado_vs_compras_abs",
            "consumo_pct_fechamento",
            "excesso_fechamento",
            "tem_orcamento",
            "tem_compra_produto",
            "tem_realizado_re_x_or",
            "nivel_alerta_fechamento",
            "alerta_ordem_fechamento",
            "origem_observacao",
        ]
    )
