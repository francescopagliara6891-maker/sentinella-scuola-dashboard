import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Sentinella Scuola - Taranto",
    page_icon="🏫",
    layout="wide"
)

# --- 2. SIDEBAR (FIRMA E LINK BOT) ---
with st.sidebar:
    st.title("ℹ️ Sentinella Scuola")
    st.info(
        """
        **Progetto di Civic Hacking**
        per la trasparenza e la sicurezza scolastica.
        
        Questo strumento permette a cittadini e istituzioni di monitorare 
        lo stato degli edifici e la documentazione di sicurezza.
        
        ---
        **Realizzato da:** Francesco Pagliara
        **Dati:** MIUR Open Data & Rilevazioni Satellitari.
        """
    )
    
    # PULSANTE PER ANDARE AL BOT TELEGRAM
    # ⚠️ SOSTITUISCI IL LINK QUI SOTTO CON QUELLO DEL TUO BOT!
    link_bot = "https://t.me/ScuoleSicureTaranto_bot"
    st.markdown(f"[![Bot Telegram](https://img.shields.io/badge/Apri_Bot_Telegram-blue?style=for-the-badge&logo=telegram)]({link_bot})")
    
    st.divider()
    st.write("© 2025 - Open Source Project")

# --- 3. TITOLO PRINCIPALE ---
st.title("🏫 Monitoraggio Sicurezza Scuole - Taranto")
st.markdown("### Analisi dello stato documentale e sicurezza edifici")
st.markdown("Esplora la mappa, controlla i punteggi e verifica le certificazioni mancanti.")

# --- 4. CARICAMENTO DATI BLINDATO ---
@st.cache_data
def load_data():
    try:
        # Cerca il file nella stessa cartella dello script (per il Cloud)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'Taranto_Safety_Ranking.xlsx')
        
        if not os.path.exists(file_path):
            st.error("❌ Errore: File 'Taranto_Safety_Ranking.xlsx' non trovato.")
            return None
            
        return pd.read_excel(file_path)
    except Exception as e:
        st.error(f"❌ Errore durante il caricamento dati: {e}")
        return None

df = load_data()

# --- 5. LOGICA APPLICAZIONE ---
if df is not None:
    
    # --- FILTRI ---
    # Creiamo una riga per i filtri per non occupare troppo spazio
    st.divider()
    col_filter_1, col_filter_2 = st.columns([1, 3])
    
    with col_filter_1:
        st.markdown("#### 📍 Filtra Area")
    with col_filter_2:
        if 'COMUNE' in df.columns:
            lista_comuni = sorted(df['COMUNE'].unique().tolist())
            scelta_comune = st.selectbox("Seleziona un Comune:", ["TUTTA LA PROVINCIA"] + lista_comuni, label_visibility="collapsed")
        else:
            scelta_comune = "TUTTA LA PROVINCIA"
            
    # Applichiamo il filtro
    if scelta_comune == "TUTTA LA PROVINCIA":
        dati_view = df.copy()
    else:
        dati_view = df[df['COMUNE'] == scelta_comune]

    # --- KPI (INDICATORI CHIAVE) ---
    st.markdown("---")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    kpi1.metric("Scuole Analizzate", len(dati_view))
    
    media_score = dati_view['SAFETY_SCORE'].mean()
    kpi2.metric("Sicurezza Media", f"{media_score:.1f}/100")
    
    # Scuole virtuose (>=80)
    virtuose = len(dati_view[dati_view['SAFETY_SCORE'] >= 80])
    kpi3.metric("Scuole Eccellenti", virtuose, delta="Zona Verde", delta_color="normal")

    # Scuole critiche (<50)
    critiche = len(dati_view[dati_view['SAFETY_SCORE'] < 50])
    kpi4.metric("Scuole Critiche", critiche, delta="-Allerta Rossa", delta_color="inverse")

    # --- MAPPA GEOGRAFICA ---
    st.markdown("### 🗺️ Mappa del Rischio")
    
    if 'lat' in dati_view.columns and 'lon' in dati_view.columns:
        # Rimuoviamo righe senza GPS per evitare errori mappa
        map_data = dati_view.dropna(subset=['lat', 'lon'])
        
        if not map_data.empty:
            fig_map = px.scatter_mapbox(
                map_data,
                lat="lat", 
                lon="lon", 
                color="SAFETY_SCORE",
                hover_name="DENOMINAZIONESCUOLA",
                hover_data={"INDIRIZZOSCUOLA": True, "lat": False, "lon": False},
                color_continuous_scale=['red', 'orange', 'green'],
                range_color=[0, 100],
                zoom=9 if scelta_comune == "TUTTA LA PROVINCIA" else 13,
                height=500
            )
            fig_map.update_layout(mapbox_style="open-street-map")
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("⚠️ Nessuna scuola geolocalizzata trovata per questa selezione.")
    else:
        st.warning("⚠️ Coordinate GPS non disponibili nel dataset.")

    # --- DETTAGLIO E CLASSIFICHE ---
    st.divider()
    c1, c2 = st.columns([1, 1])
    
    # COLONNA SINISTRA: Classifiche
    with c1:
        st.subheader("📊 Top & Flop 10")
        tab_best, tab_worst = st.tabs(["🏆 Le Migliori", "⚠️ Le Peggiori"])
        
        with tab_best:
            st.dataframe(
                dati_view[['DENOMINAZIONESCUOLA', 'SAFETY_SCORE']].sort_values('SAFETY_SCORE', ascending=False).head(10),
                hide_index=True,
                use_container_width=True
            )
            
        with tab_worst:
            st.dataframe(
                dati_view[['DENOMINAZIONESCUOLA', 'SAFETY_SCORE']].sort_values('SAFETY_SCORE', ascending=True).head(10),
                hide_index=True,
                use_container_width=True
            )

    # COLONNA DESTRA: Ispezione Singola
    with c2:
        st.subheader("🔎 Ispezione Puntuale")
        st.info("Seleziona una scuola per vedere i dettagli dei documenti mancanti.")
        
        nomi_scuole = sorted(dati_view['DENOMINAZIONESCUOLA'].unique())
        scuola_sel = st.selectbox("Cerca per nome:", nomi_scuole)
        
        if scuola_sel:
            row = df[df['DENOMINAZIONESCUOLA'] == scuola_sel].iloc[0]
            
            # Box colorato in base al punteggio
            score = row['SAFETY_SCORE']
            if score < 50:
                st.error(f"### Punteggio: {score}/100 (CRITICO)")
            elif score < 80:
                st.warning(f"### Punteggio: {score}/100 (ATTENZIONE)")
            else:
                st.success(f"### Punteggio: {score}/100 (OTTIMO)")
            
            st.write(f"📍 **Indirizzo:** {row['INDIRIZZOSCUOLA']}")
            
            # Mostriamo le mancanze
            with st.expander("📄 Stato Documentale (Clicca per espandere)", expanded=True):
                mancanze = str(row['NOTE_MANCANTI'])
                if mancanze == "nan" or not mancanze.strip():
                    st.markdown("✅ **Tutto in regola.** Nessuna carenza documentale segnalata.")
                else:
                    st.markdown("⚠️ **Documenti Mancanti o Scaduti:**")
                    st.markdown(f"❌ {mancanze}")

else:
    st.stop()