import streamlit as st
import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurazione pagina
st.set_page_config(page_title="E-commerce Search", layout="wide")

# Funzione per caricare i dati
@st.cache_data
def load_data():
    try:
        df = pd.read_excel('NOME_FILE-EXCEL.xlsx')
        df = df.fillna('')
        logger.info(f"Loaded DataFrame with {len(df)} rows")
        return df
    except Exception as e:
        st.error(f"Errore nel caricamento del file: {e}")
        logger.error(f"Error loading data: {e}")
        return None

def calculate_relevance_score(row, search_terms):
    score = 0
    
    name = str(row['item_name']).lower()
    category = str(row['category']).lower()
    brand = str(row['brand']).lower()
    keywords = str(row['generic_keywords']).lower()
    
    # Dividi il nome in parole per match esatti
    name_words = set(name.split())
    
    match_details = []  # Per debug
    
    for term in search_terms:
        # Match nella categoria (peso x5)
        if term in category:
            score += 5
            match_details.append(f"{term} in category: +5")
        # Match nel brand (peso x3)
        if term in brand:
            score += 3
            match_details.append(f"{term} in brand: +3")
        # Match nel nome (peso x2)
        if term in name:
            score += 2
            match_details.append(f"{term} in name: +2")
            # Bonus per match esatto della parola nel nome (x2)
            if term in name_words:
                score += 2
                match_details.append(f"{term} exact match in name: +2")
            # Bonus se il termine è all'inizio del nome (x1)
            if name.startswith(term):
                score += 1
                match_details.append(f"{term} at start of name: +1")
        # Match nelle keywords (peso x1)
        if term in keywords:
            score += 1
            match_details.append(f"{term} in keywords: +1")
    
    # Bonus se tutti i termini di ricerca sono nel nome (x3)
    if all(term in name for term in search_terms):
        score += 3
        match_details.append("all terms in name: +3")
    
    logger.debug(f"Score details for {row['item_name']}: {', '.join(match_details)}")
    return score

# Stile CSS
st.markdown("""
<style>
.search-result {
    padding: 1rem;
    border: 1px solid #eee;
    border-radius: 5px;
    margin: 0.5rem 0;
    background-color: white;
}
.search-result:hover {
    background-color: #f8f9fa;
    border-color: #ddd;
}
.price {
    font-size: 1.2rem;
    font-weight: bold;
    color: #1e88e5;
}
.category {
    color: #666;
    font-size: 0.9rem;
}
.brand {
    color: #2196f3;
    font-weight: 500;
}
.debug-info {
    margin-top: 2rem;
    padding: 1rem;
    background-color: #f8f9fa;
    border-radius: 5px;
}
</style>
""", unsafe_allow_html=True)

# Sidebar per Debug
with st.sidebar:
    st.title("Debug Options")
    show_debug = st.checkbox("Show Debug Info")
    show_scores = st.checkbox("Show Relevance Scores")
    show_dataframe = st.checkbox("Show Raw DataFrame")

# Titolo
st.title("🔍 E-commerce Search")

# Carica i dati
df = load_data()

if df is not None:
    # Debug info - Raw DataFrame
    if show_dataframe:
        st.subheader("Raw DataFrame")
        st.dataframe(df)

    # Barra di ricerca
    search_query = st.text_input(
        "Cerca prodotti",
        placeholder="Es: lenzuola, piumini...",
    )

    # Logica di ricerca
    if search_query:
        search_terms = search_query.lower().split()
        filtered_df = df.copy()
        
        # Debug info - Search terms
        if show_debug:
            st.write("Debug Info:")
            st.write(f"Search terms: {search_terms}")
        
        # Applica i filtri di ricerca
        for term in search_terms:
            mask = (
                filtered_df['item_name'].str.lower().str.contains(term, na=False) |
                filtered_df['category'].str.lower().str.contains(term, na=False) |
                filtered_df['brand'].str.lower().str.contains(term, na=False) |
                filtered_df['generic_keywords'].str.lower().str.contains(term, na=False)
            )
            filtered_df = filtered_df[mask]
        
        if not filtered_df.empty:
            # Calcola i punteggi di rilevanza
            filtered_df['relevance_score'] = filtered_df.apply(
                lambda row: calculate_relevance_score(row, search_terms), 
                axis=1
            )
            
            # Ordina per punteggio di rilevanza
            filtered_df = filtered_df.sort_values('relevance_score', ascending=False)
            
            st.subheader(f"Risultati ({len(filtered_df)} prodotti)")
            
            # Debug info - Relevance scores
            if show_scores:
                st.write("Relevance Scores:")
                score_df = filtered_df[['item_name', 'relevance_score']].copy()
                st.dataframe(score_df)
            
            # Mostra i risultati
            for _, product in filtered_df.iterrows():
                # Gestiamo il prezzo in modo sicuro
                try:
                    price = f"€{float(product['sale_price']):.2f}"
                except:
                    price = f"€{product['sale_price']}"
                
                st.markdown(f"""
                <div class="search-result">
                    <h3>{product['item_name']}</h3>
                    <div class="category">
                        {product['category']} • <span class="brand">{product['brand']}</span>
                    </div>
                    <div class="price">{price}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Debug info - Per product details
                if show_debug:
                    st.write(f"Debug for: {product['item_name']}")
                    st.json({
                        'relevance_score': product['relevance_score'],
                        'category': product['category'],
                        'brand': product['brand'],
                        'keywords': product['generic_keywords']
                    })
        else:
            st.info("Nessun prodotto trovato")
            if show_debug:
                st.write("Debug: No results found for query:", search_query)
    else:
        st.info("Inserisci un termine di ricerca per iniziare")

logger.info("App completed execution")