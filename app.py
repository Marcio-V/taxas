import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Simulador de Investimentos: CDI vs IPCA+",
    page_icon="📊",
    layout="wide"
)

# --- ESTILIZAÇÃO CSS CUSTOMIZADA (CORREÇÃO DE VISIBILIDADE) ---
st.markdown("""
    <style>
    /* Estilização dos cards de métricas para garantir legibilidade */
    div[data-testid="metric-container"] {
        background-color: rgba(128, 128, 128, 0.1); 
        border: 1px solid rgba(128, 128, 128, 0.3);
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Garantir que o valor da métrica tenha destaque */
    [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
    }

    /* Ajuste de espaçamento dos gráficos */
    .block-container {
        padding-top: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- TÍTULO E DESCRIÇÃO ---
st.title("📊 Simulador de Ativos Renda Fixa")
st.markdown("Compare a rentabilidade projetada entre o **CDI** e a estratégia de **IPCA + Spread**.")
st.divider()

# --- SIDEBAR: INPUTS DO USUÁRIO ---
with st.sidebar:
    st.header("⚙️ Parâmetros da Simulação")
    
    val_inicial = st.number_input(
        "Capital Inicial (R$)", 
        min_value=0.0, 
        value=100000.0, 
        step=5000.0,
        help="Valor que você pretende investir hoje."
    )
    
    anos = st.slider(
        "Horizonte de Tempo (Anos)", 
        1, 30, 5,
        help="Período total do investimento."
    )
    
    st.subheader("Taxas Esperadas (% a.a.)")
    cdi_aa = st.number_input("CDI Esperado", value=14.75, step=0.25)
    ipca_aa = st.number_input("IPCA Médio", value=4.50, step=0.1)
    spread_aa = st.number_input("Spread (Custo/Prêmio)", value=6.00, step=0.1)

    if st.button("🔄 Resetar Simulação"):
        st.rerun()

# --- LÓGICA DE CÁLCULO ---
def calcular_simulacao(valor, anos, cdi, ipca, spread):
    taxa_cdi = cdi / 100
    # Cálculo simplificado de IPCA + Spread (Soma das taxas)
    taxa_ipca_spread = (ipca + spread) / 100
    
    dados = []
    for ano in range(anos + 1):
        montante_cdi = valor * (1 + taxa_cdi) ** ano
        montante_ipca = valor * (1 + taxa_ipca_spread) ** ano
        
        dados.append({
            "Ano": ano,
            "Montante CDI": montante_cdi,
            "Montante IPCA+": montante_ipca,
            "Taxa Acum. CDI (%)": ((1 + taxa_cdi) ** ano - 1) * 100,
            "Taxa Acum. IPCA+ (%)": ((1 + taxa_ipca_spread) ** ano - 1) * 100
        })
    
    return pd.DataFrame(dados)

df_evolucao = calcular_simulacao(val_inicial, anos, cdi_aa, ipca_aa, spread_aa)

# Resultados Finais
res_cdi = df_evolucao["Montante CDI"].iloc[-1]
res_ipca = df_evolucao["Montante IPCA+"].iloc[-1]
dif_abs = res_ipca - res_cdi
dif_perc = (res_ipca / res_cdi - 1) * 100
vencedor = "IPCA + Spread" if res_ipca > res_cdi else "CDI"

# --- INTERFACE DE RESULTADOS ---

# Colunas de métricas
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Final CDI", f"R$ {res_cdi:,.2f}")
with c2:
    st.metric("Final IPCA+", f"R$ {res_ipca:,.2f}")
with c3:
    # Delta positivo se IPCA+ ganha, negativo se perde
    st.metric("Diferença Absoluta", f"R$ {abs(dif_abs):,.2f}", delta=f"{dif_abs:,.2f}")
with c4:
    st.metric("Diferença Relativa", f"{dif_perc:.2f}%", delta=f"{dif_perc:.2f}%")

# Insight Dinâmico
st.info(f"💡 **Insight:** O cenário **{vencedor}** superou o concorrente em **{abs(dif_perc):.2f}%** no período de **{anos} anos**, "
        f"gerando uma diferença de **R$ {abs(dif_abs):,.2f}** no montante final.")

# --- GRÁFICOS ---
t1, t2 = st.tabs(["📈 Evolução do Patrimônio", "📊 Taxas Acumuladas"])

with t1:
    fig_patrimonio = go.Figure()
    fig_patrimonio.add_trace(go.Scatter(x=df_evolucao["Ano"], y=df_evolucao["Montante CDI"], 
                                        name="CDI", line=dict(color='#00d4ff', width=3)))
    fig_patrimonio.add_trace(go.Scatter(x=df_evolucao["Ano"], y=df_evolucao["Montante IPCA+"], 
                                        name="IPCA + Spread", line=dict(color='#ff4b4b', width=3)))
    
    fig_patrimonio.update_layout(
        title="Crescimento Nominal do Capital (R$)",
        hovermode="x unified",
        template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_patrimonio, use_container_width=True)

with t2:
    fig_taxas = go.Figure()
    fig_taxas.add_trace(go.Scatter(x=df_evolucao["Ano"], y=df_evolucao["Taxa Acum. CDI (%)"], 
                                   name="Rentabilidade CDI (%)", line=dict(dash='dot', color='#00d4ff')))
    fig_taxas.add_trace(go.Scatter(x=df_evolucao["Ano"], y=df_evolucao["Taxa Acum. IPCA+ (%)"], 
                                   name="Rentabilidade IPCA+ (%)", line=dict(dash='dot', color='#ff4b4b')))
    
    fig_taxas.update_layout(
        title="Rentabilidade Acumulada (%)",
        hovermode="x unified",
        template="plotly_dark" if st.get_option("theme.base") == "dark" else "plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_taxas, use_container_width=True)

# --- TABELA DETALHADA ---
with st.expander("📄 Ver tabela de evolução anual"):
    df_show = df_evolucao.copy()
    # Formatação para exibição
    for col in ["Montante CDI", "Montante IPCA+"]:
        df_show[col] = df_show[col].apply(lambda x: f"R$ {x:,.2f}")
    for col in ["Taxa Acum. CDI (%)", "Taxa Acum. IPCA+ (%)"]:
        df_show[col] = df_show[col].apply(lambda x: f"{x:.2f}%")
    
    st.dataframe(df_show, use_container_width=True)

st.caption("Nota: Cálculos baseados em juros compostos anuais. Não considera impostos ou taxas operacionais.")