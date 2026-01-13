import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
from datetime import date
import os 
import sys
import math # Ajout pour la fonction math.ceil

# --- Configuration de la page Streamlit ---
st.set_page_config(page_title="Dimensionnement Solaire", page_icon="☀️", layout="wide")


# --- FONCTION CRUCIALE DE RECHERCHE DE FICHIERS DANS L'EXE ---
def find_data_file(filename):
    """Trouve les fichiers intégrés (mode .exe) ou locaux (mode dev)."""
    if getattr(sys, "frozen", False):
        basepath = sys._MEIPASS
    else:
        basepath = os.path.dirname(__file__)
    return os.path.join(basepath, filename)

# Définition des chemins des logos
LOGO_PATH_APP = find_data_file("logo_entreprise.png")
LOGO_PATH_PDF = find_data_file("logo_entreprise_pdf.png")
# --- STYLE CSS ---
st.markdown("""
<style>
/* On ne force plus le background de .stApp pour laisser le thème s'adapter */

/* On personnalise les titres pour qu'ils restent bleus dans les deux modes */
h1, h2 {
    color: #1f77b4 !important; 
}

/* On personnalise les blocs de métriques pour qu'ils s'adaptent au thème */
div[data-testid="stMetric"] {
    background-color: var(--secondary-background-color); /* Utilise le gris auto de Streamlit */
    border-radius: 10px;
    padding: 15px;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
}

/* Optionnel : si tu veux vraiment garder un fond bleuté uniquement en mode clair */
@media (prefers-color-scheme: light) {
    .stApp {
        background-color: #f7f9fc; 
    }
}
</style>
""", unsafe_allow_html=True)


# --- CLASSE DE RAPPORT PDF ---
class PDFRapport(FPDF):
    def header(self):
        try:
            self.image(LOGO_PATH_PDF, 170, 10, 30) 
        except:
            pass
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'Note de Calcul Solaire', 0, 0, 'C')
        self.ln(20) 

    def footer(self):
        self.set_y(-15) 
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb} - Document généré automatiquement le ' + str(date.today()), 0, 0, 'C')


# --- Initialisation de la session ---
if 'equipements' not in st.session_state:
    st.session_state.equipements = []
    
# Variables initialisées au niveau supérieur
energie_totale_journaliere = 0
pdf_data = {} 
puissance_max_instantanee = 0 # NOUVELLE VARIABLE
nom_projet = "Projet Sans Nom" # Initialisation

# --- Partie 1 : En-tête (Logo + Titre) ---

col_gauche, col_milieu, col_droite = st.columns([3, 2, 3]) 
with col_milieu:
    try:
        st.image(LOGO_PATH_APP, use_container_width=True)
    except:
        st.header("")

st.markdown("<h1 style='text-align: center;'>Logiciel de Dimensionnement Solaire</h1>", unsafe_allow_html=True)
st.markdown("---")


# ----------------------------------------------------
# 1. INFORMATIONS PROJET 
# ----------------------------------------------------
with st.container(border=True):
    st.header("🏠 Informations du Projet")
    col_info_client, col_info_date = st.columns([3, 1])
    with col_info_client:
        nom_projet = st.text_input("Nom de l'entreprise/client pour le dimensionnement", value="Projet Sans Nom")
    with col_info_date:
        st.markdown(f"**Date du Calcul**\n\n{date.today()}")

st.markdown("---")


# ----------------------------------------------------
# 2. BILAN DE PUISSANCE
# ----------------------------------------------------
st.header("1️⃣ Bilan de Puissance")
st.markdown("Ajoutez tous les équipements et estimez leur temps de fonctionnement quotidien.")

# Formulaire pour ajouter un équipement
with st.expander("➕ Ajouter un nouvel équipement", expanded=False):
    with st.form("ajout_equipement_form"):
        col_nom, col_p, col_q, col_h, col_simult = st.columns(5)
        with col_nom:
            nom_eq = st.text_input("Nom de l'équipement")
        with col_p:
            puissance_eq = st.number_input("Puissance (W)", min_value=0, value=0, help="Puissance nominale de l'appareil.")
        with col_q:
            quantite_eq = st.number_input("Quantité", min_value=1, value=1)
        with col_h:
            heures_eq = st.number_input("Heures/jour", min_value=0.0, max_value=24.0, value=0.0, step=0.5, format="%.1f")
        with col_simult:
            # Champ pour le dimensionnement de l'onduleur
            simultane = st.checkbox("Fonctionne simultanément ?", value=True, help="Cochez si cet appareil peut fonctionner en même temps que d'autres (pour dimensionner l'onduleur).")

        bouton_ajouter = st.form_submit_button("Ajouter l'équipement")

        if bouton_ajouter and nom_eq and puissance_eq > 0:
            energie_journaliere = puissance_eq * quantite_eq * heures_eq
            st.session_state.equipements.append({
                "Équipement": nom_eq,
                "Puissance (W)": puissance_eq,
                "Qté": quantite_eq,
                "H/j": heures_eq,
                "Énergie (Wh/j)": energie_journaliere,
                "Simultané": simultane 
            })
            st.success(f"{nom_eq} ajouté !")

# Affichage du tableau des équipements
if st.session_state.equipements:
    df_equipements = pd.DataFrame(st.session_state.equipements)
    
    # Calcul de l'énergie totale journalière
    energie_totale_journaliere = df_equipements["Énergie (Wh/j)"].sum()
    
    # Calcul de la puissance maximale instantanée pour l'onduleur
    puissance_max_instantanee = df_equipements[df_equipements["Simultané"] == True]["Puissance (W)"].sum()
    
    st.dataframe(df_equipements.drop(columns=['Simultané']), use_container_width=True)
    
    col_e, col_p_inst = st.columns(2)
    with col_e:
        st.metric(label="ÉNERGIE TOTALE JOURNALIÈRE (E_conso)", value=f"{energie_totale_journaliere:.0f} Wh/jour")
    with col_p_inst:
        st.metric(label="PUISSANCE MAX. INSTANTANÉE (P_max)", value=f"{puissance_max_instantanee:.0f} W")


st.markdown("---")


# ----------------------------------------------------
# 3. PARAMÈTRES & DIMENSIONNEMENT SOLAIRE
# ----------------------------------------------------
st.header("2️⃣ Paramètres & Dimensionnement Solaire")

# Variables initialisées (pour le scope)
psh, rendement_global, tension_systeme, autonomie_jours, prof_decharge = 0, 0, 0, 0, 0
puissance_crete_necessaire, energie_stockee_necessaire_wh, capacite_batterie_ah = 0, 0, 0
puissance_panneau_standard, icc_panneau, nombre_panneaux_reel, courant_regul_min = 0, 0, 0, 0
facteur_securite_onduleur = 0

if energie_totale_journaliere > 0:
    
    # ----------------------------------------------------
    # LIGNE 1 : Panneaux et Rendement
    col_panneau_p, col_panneau_icc, col_site_psh, col_site_rendement = st.columns(4)
    with col_panneau_p:
        puissance_panneau_standard = st.number_input("Puissance d'un panneau (Wc)", min_value=100, value=400, step=50)
    with col_panneau_icc:
        icc_panneau = st.number_input("Courant de Court-Circuit (Icc) d'un panneau (A)", min_value=1.0, value=10.0, step=0.1, format="%.1f")
    with col_site_psh:
        psh = st.number_input("Irradiation Journalière (PSH - h)", min_value=1.0, value=4.5, step=0.1, help="Nombre d'heures d'ensoleillement maximal équivalent.")
    with col_site_rendement:
        rendement_global = st.slider("Rendement global du système (PR)", min_value=0.5, max_value=0.9, value=0.70, help="Pertes (câbles, onduleur, poussière...).")


    # ----------------------------------------------------
    # LIGNE 2 : Batterie et Onduleur
    col_tension, col_autonomie, col_dod, col_facteur_inv = st.columns(4)
    with col_tension:
        tension_systeme = st.selectbox("Tension du système (V)", options=[12, 24, 48], index=1)
    with col_autonomie:
        autonomie_jours = st.number_input("Jours d'autonomie souhaités", min_value=1, value=2)
    with col_dod:
        prof_decharge = st.slider("Profondeur de décharge max (DoD)", min_value=0.2, max_value=1.0, value=0.8, help="DoD recommandé pour Lithium/Gel.")
    with col_facteur_inv:
        facteur_securite_onduleur = st.number_input("Facteur Sécurité Onduleur", min_value=1.0, value=1.25, step=0.05, format="%.2f", help="Marge appliquée à la puissance max. (1.25 = 25% de marge).")


    # --- CALCULS DU DIMENSIONNEMENT ---
    
    # 1. Puissance Crête des Panneaux (Wc)
    facteur_securite_pv = 1.25 # Maintenu à 1.25 (25% de marge)
    puissance_crete_necessaire = (energie_totale_journaliere * facteur_securite_pv) / (psh * rendement_global)

    # 2. Capacité Batterie (Ah et Wh)
    energie_stockee_necessaire_wh = (energie_totale_journaliere * autonomie_jours) / prof_decharge
    capacite_batterie_ah = energie_stockee_necessaire_wh / tension_systeme
    
    # 3. Dimensionnement du Régulateur
    nombre_panneaux_min = (puissance_crete_necessaire / puissance_panneau_standard)
    nombre_panneaux_reel = int(math.ceil(nombre_panneaux_min)) # Correction : Arrondi supérieur
    nombre_panneaux_reel = max(1, nombre_panneaux_reel)

    courant_icc_total_parallel = nombre_panneaux_reel * icc_panneau
    courant_regul_min = courant_icc_total_parallel * 1.25 

    # 4. Dimensionnement de l'Onduleur
    puissance_onduleur_requise = puissance_max_instantanee * facteur_securite_onduleur
    

    # ----------------------------------------------------
    # AFFICHAGE DES RESULTATS
    # ----------------------------------------------------
    st.subheader("📊 Résultats du Dimensionnement")
    
    col_res1, col_res2, col_res3, col_res4 = st.columns(4)
    
    with col_res1:
        st.success(f"**⚡ CHAMP PHOTOVOLTAÏQUE**\n\nPuissance Crête minimale : **{puissance_crete_necessaire:.0f} Wc**\nNombre de panneaux ({puissance_panneau_standard}Wc) : **{nombre_panneaux_reel}**")
        
    with col_res2:
        st.success(f"**🔋 PARC BATTERIE ({tension_systeme}V)**\n\nCapacité min. (C10) : **{capacite_batterie_ah:.0f} Ah**\nÉnergie brute : **{energie_stockee_necessaire_wh:.0f} Wh**")
        
    with col_res3:
        st.info(f"**🔌 RÉGULATEUR DE CHARGE**\n\nCourant minimum requis : **{courant_regul_min:.0f} A**\n**Système :** {tension_systeme}V")

    with col_res4:
        st.info(f"**📈 ONDULEUR/CONVERTISSEUR**\n\nPuissance requise : **{puissance_onduleur_requise:.0f} VA**\n**Facteur Sécurité :** {facteur_securite_onduleur:.2f}")


    # CORRECTION CRUCIALE : Stockage des résultats dans pdf_data
    pdf_data = {
        'nom_projet': nom_projet,
        'equipements': st.session_state.equipements,
        'energie_totale_journaliere': energie_totale_journaliere,
        'puissance_max_instantanee': puissance_max_instantanee, # Ajout
        'psh': psh,
        'rendement_global': rendement_global,
        'tension_systeme': tension_systeme,
        'autonomie_jours': autonomie_jours,
        'prof_decharge': prof_decharge,
        'puissance_crete_necessaire': puissance_crete_necessaire,
        'energie_stockee_necessaire_wh': energie_stockee_necessaire_wh,
        'capacite_batterie_ah': capacite_batterie_ah,
        'puissance_panneau_standard': puissance_panneau_standard,
        'nombre_panneaux_reel': nombre_panneaux_reel,
        'courant_regul_min': courant_regul_min,
        'puissance_onduleur_requise': puissance_onduleur_requise, # Ajout
        'facteur_securite_onduleur': facteur_securite_onduleur # Ajout
    }
else:
    st.warning("Veuillez ajouter des équipements pour lancer le dimensionnement.")

st.markdown("---")

# ----------------------------------------------------
# 4. GÉNÉRATION DU PDF 
# ----------------------------------------------------
st.header("3️⃣ Imprimer le Rapport")


def create_pdf_report(data): 
    pdf = PDFRapport()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    
    # NOM DU PROJET
    pdf.set_font('Arial', 'U', 16)
    pdf.cell(0, 15, f"Projet : {data['nom_projet']}", 0, 1)
    pdf.ln(5)
    
    # Section 1 : Bilan
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '1. Bilan de Puissance', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    line_height = pdf.font_size * 2.5
    effective_width = pdf.w - pdf.l_margin - pdf.r_margin
    col_width_eq = effective_width / 3
    col_width_num = effective_width / 6

    # En-têtes du tableau
    pdf.set_font('Arial', 'B', 10)
    for header in ['Équipement', 'Qté', 'Puis. (W)', 'H/j', 'Éner. (Wh/j)']:
        if header == 'Équipement':
            pdf.cell(col_width_eq, line_height, header, border=1)
        else:
            pdf.cell(col_width_num, line_height, header, border=1)
    pdf.ln(line_height)
    
    # Données du tableau 
    pdf.set_font('Arial', '', 10)
    if 'equipements' in data and data['equipements']:
        for item in data['equipements']:
            pdf.cell(col_width_eq, line_height, str(item["Équipement"]), border=1)
            pdf.cell(col_width_num, line_height, str(item["Qté"]), border=1)
            pdf.cell(col_width_num, line_height, str(item["Puissance (W)"]), border=1)
            pdf.cell(col_width_num, line_height, str(item["H/j"]), border=1)
            pdf.cell(col_width_num, line_height, str(item["Énergie (Wh/j)"]), border=1)
            pdf.ln(line_height)
            
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 7, f"TOTAL ÉNERGIE JOURNALIÈRE : {data['energie_totale_journaliere']:.0f} Wh/jour", 0, 1)
    pdf.cell(0, 7, f"PUISSANCE MAX. INSTANTANÉE (P_max) : {data['puissance_max_instantanee']:.0f} W", 0, 1)

    # Section 2 : Hypothèses
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '2. Hypothèses de Dimensionnement', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"- Irradiation (PSH) : {data['psh']} h/j", 0, 1)
    pdf.cell(0, 8, f"- Rendement Global (PR) : {data['rendement_global']}", 0, 1)
    pdf.cell(0, 8, f"- Tension système : {data['tension_systeme']} V", 0, 1)
    pdf.cell(0, 8, f"- Autonomie : {data['autonomie_jours']} jours", 0, 1)
    pdf.cell(0, 8, f"- Profondeur de décharge (DoD) : {data['prof_decharge']*100:.0f}%", 0, 1)

    # Section 3 : Résultats
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '3. Résultats et Recommandations', 0, 1)
    
    # 3.1 PV
    pdf.set_fill_color(200, 220, 255) 
    pdf.cell(0, 10, 'CHAMP PHOTOVOLTAÏQUE', 0, 1, 'L', True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"Puissance crête totale à installer : {data['puissance_crete_necessaire']:.0f} Wc", 0, 1)
    pdf.cell(0, 8, f"Nombre de panneaux ({data['puissance_panneau_standard']}Wc) : {data['nombre_panneaux_reel']} unités", 0, 1)
    
    # 3.2 REGULATEUR 
    pdf.ln(5)
    pdf.set_fill_color(255, 240, 200) 
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'RÉGULATEUR DE CHARGE', 0, 1, 'L', True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"Courant de charge minimum requis : {data['courant_regul_min']:.0f} A", 0, 1)
    pdf.cell(0, 8, "Recommandation : Choisir un régulateur MPPT d'un courant nominal supérieur à cette valeur.", 0, 1)

    # 3.3 BATTERIE
    pdf.ln(5)
    pdf.set_fill_color(220, 255, 220) 
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'PARC BATTERIE', 0, 1, 'L', True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"Capacité totale nécessaire (C10) en {data['tension_systeme']}V : {data['capacite_batterie_ah']:.0f} Ah", 0, 1)
    pdf.cell(0, 8, f"Soit une énergie stockée brute de : {data['energie_stockee_necessaire_wh']:.0f} Wh", 0, 1)

    # 3.4 ONDULEUR (NOUVEAU)
    pdf.ln(5)
    pdf.set_fill_color(255, 200, 200) 
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'ONDEULEUR/CONVERTISSEUR', 0, 1, 'L', True)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"Puissance maximale instantanée à couvrir : {data['puissance_max_instantanee']:.0f} W", 0, 1)
    pdf.cell(0, 8, f"Puissance nominale requise (avec marge de {data['facteur_securite_onduleur']:.2f}) : {data['puissance_onduleur_requise']:.0f} VA", 0, 1)
    pdf.cell(0, 8, "Recommandation : Choisir un onduleur de puissance nominale supérieure à cette valeur.", 0, 1)

    return pdf.output(dest='S').encode('latin-1')

if energie_totale_journaliere > 0:
    if st.button("Générer le rapport PDF", type="primary"):
        with st.spinner('Génération du PDF en cours...'):
            pdf_bytes = create_pdf_report(pdf_data) 
            st.success("PDF généré avec succès !")
            
            st.download_button(
                label="📥 Télécharger le Rapport PDF",
                data=pdf_bytes,
                file_name=f"Note_Calcul_Solaire_{date.today()}_{nom_projet.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
else:
    if not st.session_state.equipements:

        st.warning("Veuillez ajouter des équipements pour commencer le bilan.")

