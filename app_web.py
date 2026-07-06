import streamlit as st
import os
import tempfile
import urllib3

# Configuração global da página (Sem barra lateral)
st.set_page_config(page_title="C.C.P - Contagem Rápida", page_icon="", layout="wide", initial_sidebar_state="collapsed")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Importação do motor Back-end (O cérebro da contagem)
from app_ccp import executar_automacao_ccp_backend, salvar_e_formatar_excel

# =========================================================
#  ESTILO VISUAL CORPORATIVO
# =========================================================
ESTILO_CUSTOMIZADO = """
<style>
    /* Oculta o botão de recolher a barra lateral para travar em página única */
    [data-testid="collapsedControl"] { display: none !important; }
    
    .stApp { background-color: #F4F7F6 !important; }
    
    .block-container .element-container div.stAlert, 
    .block-container .stMarkdown, 
    div.stContainer {
        background-color: #FFFFFF !important;
        border: 1px solid #EAEAEA !important;
        border-radius: 12px !important;
    }
    
    button[kind="primary"] {
        background-color: #2A7B76 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        border: none !important;
        padding: 12px !important;
    }
    button[kind="primary"]:hover {
        background-color: #226460 !important;
        color: #FFFFFF !important;
    }
    
    .titulo-decorativo::after {
        content: "";
        display: block;
        width: 40px;
        height: 3px;
        background-color: #2A7B76;
        border-radius: 1px;
        margin-top: 8px;
        margin-bottom: 20px;
    }
</style>
"""
st.markdown(ESTILO_CUSTOMIZADO, unsafe_allow_html=True)

# =========================================================
# FUNÇÃO AUXILIAR
# =========================================================
def salvar_arquivo_temporario(uploaded_file):
    if uploaded_file is not None:
        caminho_temp = os.path.join(tempfile.gettempdir(), uploaded_file.name)
        with open(caminho_temp, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return caminho_temp
    return None

# =========================================================
# TELA ÚNICA DE PROCESSAMENTO
# =========================================================
st.write("") # Espaçamento no topo
st.markdown("<h1 class='titulo-decorativo'>CONTAGEM DE CLIENTES POR POLÍGONOS (C.C.P)</h1>", unsafe_allow_html=True)
st.markdown("Cruze a base de clientes georreferenciados com os polígonos das áreas operacionais de forma rápida.")
st.write("")

col_form, col_resultado = st.columns([3, 2])

# LADO ESQUERDO: UPLOAD DOS ARQUIVOS
with col_form:
    with st.container(border=True):
        st.markdown("##### Envie os arquivos Geográficos")
        st.info("Insira os arquivos e clique em processar. Não feche a página até a conclusão.")
        
        arquivo_clientes = st.file_uploader("1. Selecione o arquivo de Clientes (KML/KMZ)", type=["kml", "kmz"])
        arquivo_poligonos = st.file_uploader("2. Selecione o arquivo de Polígonos (KML/KMZ)", type=["kml", "kmz"])
        
        if st.button("▶ INICIAR PROCESSAMENTO", type="primary", use_container_width=True):
            if not arquivo_clientes or not arquivo_poligonos:
                st.warning("Por favor, faça o upload dos dois arquivos antes de iniciar.")
            else:
                cam_cli = salvar_arquivo_temporario(arquivo_clientes)
                cam_pol = salvar_arquivo_temporario(arquivo_poligonos)
                
                barra_progresso = st.progress(0)
                status_texto = st.empty()
                
                def atualizar_progresso_web(valor, texto):
                    barra_progresso.progress(valor)
                    status_texto.text(texto)

                try:
                    mensagem, dados_tabela, df_resumo = executar_automacao_ccp_backend(cam_pol, cam_cli, atualizar_progresso_web)
                    st.success(" Análise concluída com sucesso!")
                    st.session_state["ccp_dados"] = dados_tabela
                    st.session_state["ccp_df"] = df_resumo
                except Exception as e:
                    st.error(f"❌ Ocorreu um erro no processamento: {e}")

# LADO DIREITO: RESULTADO E DOWNLOAD
with col_resultado:
    with st.container(border=True):
        st.markdown("##### Resultados da Análise")
        
        if "ccp_dados" in st.session_state:
            import pandas as pd
            df_exibicao = pd.DataFrame(st.session_state["ccp_dados"])
            df_exibicao.columns = ["Localidade", "Quantidade de Clientes"]
            
            # Mostra a tabela diretamente na tela
            st.dataframe(df_exibicao, use_container_width=True, hide_index=True)
            
            # Prepara o Excel
            caminho_excel_temp = os.path.join(tempfile.gettempdir(), "Resumo_Clientes_por_Poligono.xlsx")
            salvar_e_formatar_excel(st.session_state["ccp_df"], caminho_excel_temp, "Resumo")
            
            with open(caminho_excel_temp, "rb") as f:
                bytes_excel = f.read()
                
            st.download_button(
                label="EXPORTAR RELATÓRIO EXCEL",
                data=bytes_excel,
                file_name="Resumo_Clientes_por_Poligono.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
        else:
            st.markdown("<p style='color: #7A8B8B; font-size: 14px; text-align: center; margin-top: 50px;'>Aguardando o envio dos arquivos...</p>", unsafe_allow_html=True)
