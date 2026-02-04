import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Monitoraggio Scuole Taranto", page_icon="🏫", layout="wide")

# --- TITOLO E INTRO ---
st.title("🏫 Monitoraggio Sicurezza Scuole - Prov. di Taranto")
st.markdown("""
Questa dashboard visualizza lo stato di sicurezza e la documentazione degli istituti scolastici.
**Dati:** Open Data MIUR & Geocoding proprietario.
""")

# --- FUNZIONE CARICAMENTO DATI (Blindata per il Cloud) ---
@st.cache_data
def load_data():
    # Cerca il file nella stessa directory dello script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'Taranto_Safety_Ranking.xlsx')
    
    try:
        df = pd.read_excel(file_path)
        return df
    except FileNotFoundError:
        st.error(f"❌ Errore critico: File '{file_path}' non trovato.")
        return None
    except Exception as e:
        st.error(f"❌ Errore caricamento dati: {e}")
        return None

df_totale = load_data()

# --- BLOCCO PRINCIPALE ---
if df_totale is not None:
    # --- SIDEBAR (FILTRI) ---
    st.sidebar.header("🔍 Filtri Ricerca")
    
    if 'COMUNE' in df_totale.columns:
        lista_comuni = sorted(df_totale['COMUNE'].unique().tolist())
        opzione_comune = st.sidebar.selectbox("Seleziona Comune:", ["TUTTA LA PROVINCIA"] + lista_comuni)
        
        if opzione_comune == "TUTTA LA PROVINCIA":
            df = df_totale.copy()
            st.subheader("Visualizzazione: Intera Provincia")
        else:
            df = df_totale[df_totale['COMUNE'] == opzione_comune].copy()
            st.subheader(f"Visualizzazione: Comune di {opzione_comune}")
    else:
        st.error("Colonna 'COMUNE' mancante nel dataset.")
        df = df_totale.copy()

    # --- KPI (INDICATORI) ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Scuole Analizzate", len(df))
    media_score = df['SAFETY_SCORE'].mean()
    col2.metric("Punteggio Medio Sicurezza", f"{media_score:.1f}/100")
    
    # Scuole critiche (<50 punti)
    critiche = len(df[df['SAFETY_SCORE'] < 50])
    col3.metric("Scuole in Stato Critico", critiche, delta="-Attenzione", delta_color="inverse")
    
    st.divider()

    # --- MAPPA GEOGRAFICA ---
    st.markdown("### 🗺️ Mappa del Rischio")
    
    if 'lat' in df.columns and 'lon' in df.columns:
        # Pulizia dati mappa (rimuoviamo chi non ha coordinate)
        df_map = df.dropna(subset=['lat', 'lon'])
        
        fig_map = px.scatter_mapbox(
            df_map,
            lat="lat", 
            lon="lon", 
            color="SAFETY_SCORE",
            hover_name="DENOMINAZIONESCUOLA",
            # Personalizziamo il tooltip quando passi col mouse
            hover_data={
                "lat": False, "lon": False, 
                "INDIRIZZOSCUOLA": True, 
                "NOTE_MANCANTI": True
            },
            color_continuous_scale=['red', 'orange', 'green'],
            range_color=[0, 100],
            zoom=9 if opzione_comune == "TUTTA LA PROVINCIA" else 13,
            height=500
        )
        fig_map.update_layout(mapbox_style="open-street-map")
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("⚠️ Coordinate GPS non disponibili nel file caricato.")

    st.divider()

    # --- DETTAGLIO SCUOLA ---
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("### 📊 Classifica (Top & Flop)")
        # Mostriamo le 10 peggiori e le 5 migliori se ci sono abbastanza dati
        if len(df) > 0:
            tab1, tab2 = st.tabs(["⚠️ Le più Critiche", "🏆 Le più Virtuose"])
            
            with tab1:
                df_worst = df.sort_values('SAFETY_SCORE', ascending=True).head(10)
                st.dataframe(
                    df_worst[['DENOMINAZIONESCUOLA', 'SAFETY_SCORE', 'NOTE_MANCANTI']], 
                    hide_index=True,
                    use_container_width=True
                )
                
            with tab2:
                df_best = df.sort_values('SAFETY_SCORE', ascending=False).head(10)
                st.dataframe(
                    df_best[['DENOMINAZIONESCUOLA', 'SAFETY_SCORE']], 
                    hide_index=True,
                    use_container_width=True
                )

    with c2:
        st.markdown("### 🔎 Ispezione Singola")
        nomi_scuole = sorted(df['DENOMINAZIONESCUOLA'].unique().tolist())
        scuola_sel = st.selectbox("Cerca Istituto:", nomi_scuole)
        
        if scuola_sel:
            row = df[df['DENOMINAZIONESCUOLA'] == scuola_sel].iloc[0]
            
            punteggio = row['SAFETY_SCORE']
            if punteggio < 50:
                st.error(f"Punteggio: {punteggio}/100 🛑")
            elif punteggio < 80:
                st.warning(f"Punteggio: {punteggio}/100 ⚠️")
            else:
                st.success(f"Punteggio: {punteggio}/100 ✅")
            
            st.write(f"📍 **Indirizzo:** {row['INDIRIZZOSCUOLA']}")
            
            with st.expander("📄 Vedi Documenti Mancanti", expanded=True):
                if pd.isna(row['NOTE_MANCANTI']) or str(row['NOTE_MANCANTI']).strip() == "":
                    st.write("Nessuna mancanza segnalata.")
                else:
                    st.write(row['NOTE_MANCANTI'])

else:
    st.stop()