import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from datetime import datetime
from fpdf import FPDF
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Simulador de Investimentos Pro", page_icon="📊", layout="wide")

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: rgba(128, 128, 128, 0.1);
        border: 1px solid rgba(128, 128, 128, 0.3);
        padding: 15px 20px;
        border-radius: 12px;
    }
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE SUPORTE ---

def carregar_dias_uteis(data_inicio, data_fim):
    """Calcula dias úteis usando o arquivo feriados_nacionais.xlsx"""
    try:
        df_feriados = pd.read_excel("feriados_nacionais.xlsx")
        lista_feriados = pd.to_datetime(df_feriados.iloc[:, 0]).dt.date.tolist()
    except Exception as e:
        st.error(f"Erro ao carregar feriados: {e}. Usando dias úteis padrão (seg-sex).")
        lista_feriados = []

    dias_periodo = pd.date_range(start=data_inicio, end=data_fim)
    dias_uteis = [d for d in dias_periodo if d.weekday() < 5 and d.date() not in lista_feriados]
    return dias_uteis

def gerar_pdf(df_anual, df_diario, params):
    """Gera PDF usando Matplotlib para o gráfico (evita erro de dependência Kaleido/Browser)"""
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Relatorio de Simulacao de Investimento", ln=True, align='C')
    
    # 1. Resumo da Análise
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "1. Resumo da Analise", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 8, f"Periodo: {params['inicio']} ate {params['fim']} ({params['dias_uteis']} dias uteis)", ln=True)
    pdf.cell(200, 8, f"Capital Inicial: R$ {params['valor']:,.2f}", ln=True)
    pdf.cell(200, 8, f"Vencedor: {params['vencedor']}", ln=True)
    pdf.cell(200, 8, f"Rentabilidade Adicional: R$ {abs(params['dif_abs']):,.2f} ({params['dif_perc']:.2f}%)", ln=True)
    
    # Gerar gráfico temporário com Matplotlib (seguro para Linux Slim)
    plt.figure(figsize=(10, 5))
    plt.plot(df_diario["Data"], df_diario["Montante CDI"], label="CDI", color='#00d4ff', linewidth=2)
    plt.plot(df_diario["Data"], df_diario["Montante IPCA+"], label="IPCA + Spread", color='#ff4b4b', linewidth=2)
    plt.title("Evolucao Patrimonial ao Longo do Tempo")
    plt.ylabel("Montante (R$)")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.savefig("chart_export.png", dpi=150)
    plt.close()
    
    pdf.ln(5)
    pdf.image("chart_export.png", x=10, w=190)
    pdf.ln(5)
    
    # 2. Tabela Anual
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "2. Evolucao Patrimonial Anual", ln=True)
    pdf.set_font("Arial", '', 10)
    
    # Header Tabela
    pdf.cell(40, 10, "Ano", 1, 0, 'C')
    pdf.cell(75, 10, "Montante CDI", 1, 0, 'C')
    pdf.cell(75, 10, "Montante IPCA+", 1, 1, 'C')
    
    for _, row in df_anual.iterrows():
        pdf.cell(40, 10, str(int(row['Ano'])), 1, 0, 'C')
        pdf.cell(75, 10, f"R$ {row['Montante CDI']:,.2f}", 1, 0, 'C')
        pdf.cell(75, 10, f"R$ {row['Montante IPCA+']:,.2f}", 1, 1, 'C')
    
    # Limpeza
    res = pdf.output(dest='S').encode('latin-1')
    if os.path.exists("chart_export.png"):
        os.remove("chart_export.png")
    return res

# --- SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("⚙️ Parâmetros")
    val_inicial = st.number_input("Capital Inicial (R$)", min_value=0.0, value=100000.0)
    
    c1, c2 = st.columns(2)
    with c1: data_aporte = st.date_input("Data de Aporte", datetime.now())
    with c2: data_vencimento = st.date_input("Vencimento", datetime(2029, 12, 31))
    
    st.subheader("Taxas Esperadas (% a.a.)")
    cdi_aa = st.number_input("CDI Esperado", value=14.75)
    ipca_aa = st.number_input("IPCA Médio", value=4.50)
    spread_aa = st.number_input("Spread", value=6.00)

# --- LÓGICA DE CÁLCULO ---
if data_vencimento <= data_aporte:
    st.error("A data de vencimento deve ser posterior à data de aporte.")
else:
    # 1. Dias Úteis
    dias_uteis_datas = carregar_dias_uteis(data_aporte, data_vencimento)
    total_dias_uteis = len(dias_uteis_datas)
    total_dias_corridos = (data_vencimento - data_aporte).days

    # 2. Taxas Diárias (Base 252)
    t_diaria_cdi = (1 + cdi_aa/100)**(1/252) - 1
    ipca_comp_aa = (1 + ipca_aa/100) * (1 + spread_aa/100) - 1
    t_diaria_ipca = (1 + ipca_comp_aa)**(1/252) - 1

    # 3. Evolução Diária
    evolucao_diaria = []
    s_cdi, s_ipca = val_inicial, val_inicial
    
    for data in dias_uteis_datas:
        s_cdi *= (1 + t_diaria_cdi)
        s_ipca *= (1 + t_diaria_ipca)
        evolucao_diaria.append({
            "Data": data, 
            "Ano": data.year, 
            "Montante CDI": s_cdi, 
            "Montante IPCA+": s_ipca
        })

    df_diario = pd.DataFrame(evolucao_diaria)
    df_anual = df_diario.groupby('Ano').last().reset_index()

    # KPIs Finais
    res_cdi = s_cdi
    res_ipca = s_ipca
    dif_abs = res_ipca - res_cdi
    dif_perc = (res_ipca / res_cdi - 1) * 100
    vencedor = "IPCA + Spread" if res_ipca > res_cdi else "CDI"

    # --- INTERFACE DE RESULTADOS ---
    st.title("📊 Simulador de Ativos Renda Fixa")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Final CDI", f"R$ {res_cdi:,.2f}")
    k2.metric("Final IPCA+", f"R$ {res_ipca:,.2f}")
    k3.metric("Diferença Absoluta", f"R$ {abs(dif_abs):,.2f}", delta=f"{dif_abs:,.2f}")
    k4.metric("Diferença Relativa", f"{dif_perc:.2f}%", delta=f"{dif_perc:.2f}%")

    st.info(f"💡 **Insight:** O cenário **{vencedor}** superou o concorrente em **{abs(dif_perc):.2f}%** no período.")

    # Gráfico Plotly (Para visualização no Browser)
    fig_plotly = go.Figure()
    fig_plotly.add_trace(go.Scatter(x=df_diario["Data"], y=df_diario["Montante CDI"], name="CDI", line=dict(color='#00d4ff')))
    fig_plotly.add_trace(go.Scatter(x=df_diario["Data"], y=df_diario["Montante IPCA+"], name="IPCA+", line=dict(color='#ff4b4b')))
    fig_plotly.update_layout(title="Evolução Patrimonial Diária", template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig_plotly, use_container_width=True)

    # Botão de Exportação
    params_pdf = {
        "valor": val_inicial, "inicio": data_aporte, "fim": data_vencimento,
        "dias_uteis": total_dias_uteis, "vencedor": vencedor,
        "dif_abs": dif_abs, "dif_perc": dif_perc
    }

    if st.button("📄 Gerar Relatório PDF Completo"):
        with st.spinner("Gerando PDF..."):
            pdf_bytes = gerar_pdf(df_anual, df_diario, params_pdf)
            st.download_button(
                label="📥 Clique aqui para baixar o PDF",
                data=pdf_bytes,
                file_name=f"Relatorio_Investimento_{vencedor}.pdf",
                mime="application/pdf"
            )

    with st.expander("📄 Ver Tabela de Evolução Anual"):
        st.table(df_anual.style.format({
            "Montante CDI": "R$ {:,.2f}",
            "Montante IPCA+": "R$ {:,.2f}"
        }))