import streamlit as st
import pandas as pd
import numpy as np

# Configuration de la page
st.set_page_config(
    page_title="Calculateur Carbone Média",
    page_icon="🌱",
    layout="wide"
)

# Titre de l'application
st.title("Calculateur d'Empreinte Carbone des Plans Média")
st.markdown("---")

# Chargement du fichier de référence CO2
@st.cache_data
def load_co2_reference():
    """Charge le fichier de référence CO2g contact.xlsx"""
    try:
        df = pd.read_excel('CO2g contact.xlsx')
        # Nettoyer les données
        df = df[['Support', 'CO2g/Contact']].dropna()
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier CO2g contact.xlsx : {e}")
        return None

# Chargement des données de référence
co2_ref = load_co2_reference()

if co2_ref is not None:
    # Sidebar pour la configuration
    st.sidebar.header("Gestion des Plans")
    
    # Initialiser la session state pour stocker les plans
    if 'plans' not in st.session_state:
        st.session_state.plans = []
    
    # Section d'ajout de plan
    st.sidebar.subheader("Ajouter un nouveau plan")
    
    # Upload du fichier CSV
    uploaded_file = st.sidebar.file_uploader(
        "Charger un plan média (CSV)",
        type=['csv'],
        help="Le fichier doit contenir les colonnes : Contact, Budget"
    )
    
    if uploaded_file is not None:
        # Nom du plan
        plan_name = st.sidebar.text_input(
            "Nom du plan",
            value=uploaded_file.name.replace('.csv', '')
        )
        
        # Sélection du support
        support_choisi = st.sidebar.selectbox(
            "Sélectionner le support média",
            options=sorted(co2_ref['Support'].unique()),
            key='support_select'
        )
        
        # Bouton pour ajouter le plan
        if st.sidebar.button("✅ Ajouter ce plan", key='add_plan'):
            try:
                # Lire le fichier CSV
                from detect_delimiter import detect
                
                # Reset the file pointer to the beginning
                uploaded_file.seek(0)
                firstline = uploaded_file.readline().decode('utf-8')
                uploaded_file.seek(0)
                delimiter = detect(firstline)
                df_plan = pd.read_csv(uploaded_file, delimiter=delimiter)
                
                # Vérifier les colonnes requises
                cont,bud=False,False
                for col_plan in df_plan.columns:
                    if "contact" in col_plan.lower() or "contacts" in col_plan.lower():
                        df_plan.rename(columns={col_plan: "Contact"}, inplace=True)
                        cont=True
                    if "budget" in col_plan.lower() or "tarif" in col_plan.lower():
                        df_plan.rename(columns={col_plan: "Budget"}, inplace=True)
                        bud=True
                    if cont and bud:
                        break
                if 'Contact' not in df_plan.columns or 'Budget' not in df_plan.columns:
                    st.sidebar.error("❌ Le fichier doit contenir les colonnes 'Contact' et 'Budget'")
                else:
                    print(df_plan.columns)
                    # Obtenir le facteur CO2
                    co2_factor = co2_ref[co2_ref['Support'] == support_choisi]['CO2g/Contact'].values[0]
                    
                    # Calculer le CO2 total

                    df_plan['Contact'] = df_plan['Contact'].astype(str).str.replace(" ", "").str.replace(",",".").astype(float)
                    df_plan['Budget'] = df_plan['Budget'].astype(str).str.replace(" ", "").str.replace(",",".").astype(float)
                    total_contacts = df_plan['Contact'].sum()
                    total_budget = df_plan['Budget'].sum()
                    total_co2 = total_contacts * co2_factor
                    
                    # Ajouter le plan à la session
                    st.session_state.plans.append({
                        'nom': plan_name,
                        'support': support_choisi,
                        'data': df_plan,
                        'contacts': total_contacts,
                        'budget': total_budget,
                        'co2_factor': co2_factor,
                        'co2_total': total_co2
                    })
                    
                    st.sidebar.success(f"✅ Plan '{plan_name}' ajouté avec succès !")
                    st.rerun()
                    
            except Exception as e:
                st.sidebar.error(f"❌ Erreur lors du traitement du fichier : {e}")
    
    # Affichage des plans ajoutés
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Plans actuels")
    
    if len(st.session_state.plans) > 0:
        for idx, plan in enumerate(st.session_state.plans):
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                st.sidebar.text(f"{idx+1}. {plan['nom']}")
            with col2:
                if st.sidebar.button("🗑️", key=f"delete_{idx}"):
                    st.session_state.plans.pop(idx)
                    st.rerun()
    else:
        st.sidebar.info("Aucun plan ajouté pour le moment")
    
    # Zone principale - Affichage des résultats
    if len(st.session_state.plans) > 0:
        st.header("Résumé des Plans Média")
        
        # Créer un DataFrame récapitulatif
        summary_data = []
        for plan in st.session_state.plans:
            summary_data.append({
                'Nom du Plan': plan['nom'],
                'Support': plan['support'],
                'Contacts': f"{plan['contacts']:,.0f}",
                'Budget (€)': f"{plan['budget']:,.2f}",
                'CO2g/Contact': f"{plan['co2_factor']:.3f}",
                'CO2 Total (g)': f"{plan['co2_total']:,.2f}",
                'CO2 Total (kg)': f"{plan['co2_total']/1000:.2f}"
            })
        
        df_summary = pd.DataFrame(summary_data)
        
        # Afficher le tableau récapitulatif par plan
        st.subheader("Par Plan")
        st.dataframe(df_summary, use_container_width=True)
        
        # Tableau récapitulatif par support
        st.markdown("---")
        st.subheader("Récapitulatif par Support")
        
        support_summary = {}
        for plan in st.session_state.plans:
            support = plan['support']
            if support not in support_summary:
                support_summary[support] = {
                    'Nombre de Plans': 0,
                    'Contacts': 0,
                    'Budget': 0,
                    'CO2_factor': plan['co2_factor'],
                    'CO2_total': 0
                }
            support_summary[support]['Nombre de Plans'] += 1
            support_summary[support]['Contacts'] += plan['contacts']
            support_summary[support]['Budget'] += plan['budget']
            support_summary[support]['CO2_total'] += plan['co2_total']
        
        support_data = []
        for support, data in support_summary.items():
            support_data.append({
                'Support': support,
                'Nombre de Plans': data['Nombre de Plans'],
                'Contacts': f"{data['Contacts']:,.0f}",
                'Budget (€)': f"{data['Budget']:,.2f}",
                'CO2g/Contact': f"{data['CO2_factor']:.3f}",
                'CO2 Total (g)': f"{data['CO2_total']:,.2f}",
                'CO2 Total (kg)': f"{data['CO2_total']/1000:.2f}",
                '% du CO2 total': f"{(data['CO2_total']/sum([s['CO2_total'] for s in support_summary.values()])*100):.1f}%"
            })
        
        df_support_summary = pd.DataFrame(support_data)
        st.dataframe(df_support_summary, use_container_width=True)
        
        # Calculs globaux
        st.markdown("---")
        st.header("Empreinte Carbone Globale")
        
        total_co2_g = sum([plan['co2_total'] for plan in st.session_state.plans])
        total_co2_kg = total_co2_g / 1000
        total_co2_tonnes = total_co2_kg / 1000
        total_budget = sum([plan['budget'] for plan in st.session_state.plans])
        total_contacts = sum([plan['contacts'] for plan in st.session_state.plans])
        
        # Afficher les métriques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="CO2 Total",
                value=f"{total_co2_kg:,.2f} kg",
                delta=f"{total_co2_tonnes:.3f} tonnes"
            )
        
        with col2:
            st.metric(
                label="Budget Total",
                value=f"{total_budget:,.2f} €"
            )
        
        with col3:
            st.metric(
                label="Contacts Total",
                value=f"{total_contacts:,.0f}"
            )
        
        with col4:
            co2_per_euro = total_co2_g / total_budget if total_budget > 0 else 0
            st.metric(
                label="CO2/€",
                value=f"{co2_per_euro:.2f} g"
            )
        
        # Graphiques
        st.markdown("---")
        st.header("Visualisations")
        
        # Agréger les données par support
        support_aggregation = {}
        for plan in st.session_state.plans:
            support = plan['support']
            if support not in support_aggregation:
                support_aggregation[support] = {
                    'co2': 0,
                    'budget': 0,
                    'contacts': 0,
                    'nb_plans': 0
                }
            support_aggregation[support]['co2'] += plan['co2_total']
            support_aggregation[support]['budget'] += plan['budget']
            support_aggregation[support]['contacts'] += plan['contacts']
            support_aggregation[support]['nb_plans'] += 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Répartition du CO2 par Support")
            chart_data = pd.DataFrame({
                'Support': list(support_aggregation.keys()),
                'CO2 (kg)': [data['co2']/1000 for data in support_aggregation.values()]
            })
            st.bar_chart(chart_data.set_index('Support'))
        
        with col2:
            st.subheader("Répartition du Budget par Support")
            chart_data = pd.DataFrame({
                'Support': list(support_aggregation.keys()),
                'Budget (€)': [data['budget'] for data in support_aggregation.values()]
            })
            st.bar_chart(chart_data.set_index('Support'))
        
        # Détails par plan
        st.markdown("---")
        st.header("Détails par Plan")
        
        for idx, plan in enumerate(st.session_state.plans):
            with st.expander(f"{plan['nom']} - {plan['support']}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Contacts", f"{plan['contacts']:,.0f}")
                with col2:
                    st.metric("Budget", f"{plan['budget']:,.2f} €")
                with col3:
                    st.metric("CO2 Total", f"{plan['co2_total']/1000:.2f} kg")
                
                st.dataframe(plan['data'], use_container_width=True)
        
        # Bouton pour tout réinitialiser
        st.markdown("---")
        if st.button("🔄 Réinitialiser tous les plans", type="secondary"):
            st.session_state.plans = []
            st.rerun()
    
    else:
        # Message d'accueil
        st.info("👈 Ajoutez un plan média via le menu latéral pour commencer")
        
        st.markdown("""
        ### Instructions
        
        1. **Préparez votre fichier CSV** avec les colonnes suivantes :
           - `Contact` : Nombre de contacts
           - `Budget` : Budget alloué (en €)
        
        2. **Chargez le fichier** via le menu latéral

        3. **Sélectionnez le support média correspondant** dans la liste déroulante

        4. **Ajoutez le plan** pour voir les calculs d'empreinte carbone
        
        5. **Répétez** pour ajouter plusieurs plans et comparer leurs impacts

        ### Supports disponibles
        """)
        
        # Afficher la table de référence CO2
        st.dataframe(co2_ref.sort_values('Support'), use_container_width=True)

else:
    st.error("⚠️ Impossible de charger le fichier de référence CO2g contact.xlsx")
    st.info("Assurez-vous que le fichier 'CO2g contact.xlsx' est présent dans le même dossier que cette application.")
