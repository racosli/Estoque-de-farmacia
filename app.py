# ============================================================
# DASHBOARD DE ESTOQUE DE FARMÁCIA
# Projeto 2 — Portfólio Farmácia + Ciência de Dados
#
# Para rodar: streamlit run app.py
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

# ── Configuração da página ────────────────────────────────────
st.set_page_config(
    page_title="Estoque Farmácia",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Função de carregamento de dados ──────────────────────────
@st.cache_data
def carregar_dados():
    df = pd.read_csv("dados/estoque.csv", encoding="utf-8")
    df["validade"] = pd.to_datetime(df["validade"])
    hoje = date.today()
    df["dias_para_vencer"] = (df["validade"].dt.date.apply(
        lambda x: (x - hoje).days
    ))

    def classificar_status(dias):
        if dias < 0:
            return "Vencido"
        elif dias <= 30:
            return "Crítico"
        elif dias <= 90:
            return "Alerta"
        else:
            return "OK"

    df["status"] = df["dias_para_vencer"].apply(classificar_status)

    def classificar_estoque(row):
        if row["quantidade"] == 0:
            return "Sem estoque"
        elif row["quantidade"] < row["minimo"]:
            return "Abaixo do mínimo"
        elif row["quantidade"] < row["minimo"] * 1.2:
            return "Estoque baixo"
        else:
            return "OK"

    df["estoque_status"] = df.apply(classificar_estoque, axis=1)
    return df

df = carregar_dados()
hoje = date.today()

# ════════════════════════════════════════════════════════════════
# SIDEBAR — Filtros
# ════════════════════════════════════════════════════════════════
st.sidebar.image(
    "https://img.icons8.com/color/96/pill.png", width=60
)
st.sidebar.title("Filtros")

categorias = ["Todas"] + sorted(df["categoria"].unique().tolist())
categoria_sel = st.sidebar.selectbox("Categoria", categorias)

status_vals = ["Todos", "Vencido", "Crítico", "Alerta", "OK"]
status_sel = st.sidebar.selectbox("Status de validade", status_vals)

estoque_vals = ["Todos", "Sem estoque", "Abaixo do mínimo", "Estoque baixo", "OK"]
estoque_sel = st.sidebar.selectbox("Status de estoque", estoque_vals)

fornecedores = ["Todos"] + sorted(df["fornecedor"].unique().tolist())
fornecedor_sel = st.sidebar.selectbox("Fornecedor", fornecedores)

st.sidebar.markdown("---")
st.sidebar.caption(f"Última atualização: {hoje.strftime('%d/%m/%Y')}")

# Aplicar filtros
df_filtrado = df.copy()
if categoria_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["categoria"] == categoria_sel]
if status_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["status"] == status_sel]
if estoque_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["estoque_status"] == estoque_sel]
if fornecedor_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado["fornecedor"] == fornecedor_sel]

# ════════════════════════════════════════════════════════════════
# CABEÇALHO
# ════════════════════════════════════════════════════════════════
st.title("💊 Dashboard de Estoque de Farmácia")
st.caption("Monitoramento de validade, estoque crítico e consumo por categoria")
st.markdown("---")

# ════════════════════════════════════════════════════════════════
# CARDS DE MÉTRICAS
# ════════════════════════════════════════════════════════════════
col1, col2, col3, col4, col5 = st.columns(5)

vencidos       = len(df[df["status"] == "Vencido"])
criticos_val   = len(df[df["status"] == "Crítico"])
abaixo_min     = len(df[df["estoque_status"] == "Abaixo do mínimo"])
sem_estoque    = len(df[df["estoque_status"] == "Sem estoque"])

col1.metric("📦 Total de itens",       len(df))
col2.metric("❌ Vencidos",             vencidos,     delta=f"-{vencidos}" if vencidos > 0 else None,  delta_color="inverse")
col3.metric("⚠️ Vencem em 30 dias",   criticos_val, delta=f"-{criticos_val}" if criticos_val > 0 else None, delta_color="inverse")
col4.metric("📉 Abaixo do mínimo",    abaixo_min,   delta=f"-{abaixo_min}" if abaixo_min > 0 else None,  delta_color="inverse")
col5.metric("🏷️ Categorias",          df["categoria"].nunique())

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# ALERTAS VISUAIS
# ════════════════════════════════════════════════════════════════
alertas_venc  = df[df["status"].isin(["Vencido", "Crítico"])].sort_values("dias_para_vencer")
alertas_estq  = df[df["estoque_status"].isin(["Sem estoque", "Abaixo do mínimo"])]

if len(alertas_venc) > 0 or len(alertas_estq) > 0:
    st.subheader("🚨 Alertas")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Validade**")
        for _, row in alertas_venc.iterrows():
            dias = row["dias_para_vencer"]
            if dias < 0:
                st.error(f"❌ **VENCIDO** — {row['medicamento']} ({abs(dias)} dias atrás) | Lote: {row['lote']}")
            else:
                st.warning(f"⚠️ **Vence em {dias} dias** — {row['medicamento']} | Lote: {row['lote']}")

    with col_b:
        st.markdown("**Estoque**")
        for _, row in alertas_estq.iterrows():
            if row["estoque_status"] == "Sem estoque":
                st.error(f"❌ **SEM ESTOQUE** — {row['medicamento']}")
            else:
                st.warning(f"⚠️ **Abaixo do mínimo** — {row['medicamento']} | {row['quantidade']} un. (mín: {row['minimo']})")

    st.markdown("---")

# ════════════════════════════════════════════════════════════════
# GRÁFICOS
# ════════════════════════════════════════════════════════════════
st.subheader("📊 Análise Visual")

tab1, tab2, tab3 = st.tabs(["Estoque vs Mínimo", "Por Categoria", "Status de Validade"])

with tab1:
    df_graf = df_filtrado.sort_values("quantidade")
    fig1 = px.bar(
        df_graf, x="medicamento",
        y=["quantidade", "minimo"],
        barmode="group",
        labels={"value": "Unidades", "medicamento": "Medicamento", "variable": ""},
        color_discrete_map={"quantidade": "#1D9E75", "minimo": "#E53935"},
        title="Quantidade em estoque vs Estoque mínimo",
    )
    fig1.update_layout(xaxis_tickangle=-45, legend_title_text="")
    fig1.for_each_trace(lambda t: t.update(
        name="Quantidade" if t.name == "quantidade" else "Mínimo"
    ))
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    resumo_cat = df_filtrado.groupby("categoria").agg(
        total=("quantidade", "sum"),
        itens=("medicamento", "count")
    ).reset_index()

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig2 = px.pie(
            resumo_cat, values="total", names="categoria",
            title="Distribuição de unidades por categoria",
            hole=0.4,
        )
        st.plotly_chart(fig2, use_container_width=True)
    with col_g2:
        fig3 = px.bar(
            resumo_cat.sort_values("total", ascending=True),
            x="total", y="categoria", orientation="h",
            title="Total de unidades por categoria",
            color="total", color_continuous_scale="Teal",
            labels={"total": "Unidades", "categoria": ""},
        )
        st.plotly_chart(fig3, use_container_width=True)

with tab3:
    status_count = df_filtrado["status"].value_counts().reset_index()
    status_count.columns = ["status", "quantidade"]
    cores_status = {
        "OK":      "#1D9E75",
        "Alerta":  "#FB8C00",
        "Crítico": "#E53935",
        "Vencido": "#B71C1C",
    }
    fig4 = px.bar(
        status_count, x="status", y="quantidade",
        color="status",
        color_discrete_map=cores_status,
        title="Medicamentos por status de validade",
        labels={"quantidade": "Quantidade", "status": "Status"},
    )
    fig4.update_layout(showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ════════════════════════════════════════════════════════════════
# TABELA INTERATIVA
# ════════════════════════════════════════════════════════════════
st.subheader("📋 Tabela de Estoque")

def colorir_linha(row):
    if row["Status Validade"] == "Vencido":
        return ["background-color: #FFCDD2"] * len(row)
    elif row["Status Validade"] == "Crítico":
        return ["background-color: #FFE0B2"] * len(row)
    elif row["Status Estoque"] == "Abaixo do mínimo":
        return ["background-color: #FFF9C4"] * len(row)
    else:
        return [""] * len(row)

colunas_exibir = [
    "medicamento", "categoria", "lote", "validade",
    "quantidade", "minimo", "status", "estoque_status", "fornecedor"
]
df_exibir = df_filtrado[colunas_exibir].copy()
df_exibir["validade"] = df_exibir["validade"].dt.strftime("%d/%m/%Y")
df_exibir.columns = [
    "Medicamento", "Categoria", "Lote", "Validade",
    "Quantidade", "Mínimo", "Status Validade", "Status Estoque", "Fornecedor"
]

st.dataframe(
    df_exibir.style.apply(colorir_linha, axis=1),
    use_container_width=True,
    height=400,
)

st.caption(f"Exibindo {len(df_filtrado)} de {len(df)} medicamentos")

# ── Botão de download ─────────────────────────────────────────
csv_download = df_filtrado.to_csv(index=False, encoding="utf-8-sig")
st.download_button(
    label="⬇️ Baixar tabela filtrada (.csv)",
    data=csv_download,
    file_name=f"estoque_filtrado_{hoje}.csv",
    mime="text/csv",
)
