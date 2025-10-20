import streamlit as st
import pandas as pd

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
        # Nettoyer les données - garder Alpha même avec NaN
        df = df[['Support', 'CO2g/Contact', 'Alpha']]
        df = df[df['Support'].notna() & df['CO2g/Contact'].notna()]
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
                    if "contact" in col_plan.lower() or "impression" in col_plan.lower():
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
    st.sidebar.subheader("Plans actuels")
    
    if len(st.session_state.plans) > 0:
        for idx, plan in enumerate(st.session_state.plans):
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                st.sidebar.text(f"{idx+1}. {plan['nom']} - {plan['support']}")
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
        st.dataframe(df_summary, width=1200)
        
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
        st.dataframe(df_support_summary, width=1200)
        
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
                
                st.dataframe(plan['data'], width=1200)
        
        # Section Optimisation
        st.markdown("---")
        st.header("Optimisation Budget / Carbone")
        
        st.markdown("""
        L'optimiseur permet de trouver la meilleure répartition budgétaire entre les supports pour :
        - **Minimiser l'empreinte carbone**
        - **Maximiser les contacts utiles**
        - Respecter les contraintes budgétaires
        """)
        
        # Préparer les données pour l'optimisation
        can_optimize = True
        optimization_data = []
        
        for support, data in support_summary.items():
            # Récupérer l'alpha du support
            alpha_value = co2_ref[co2_ref['Support'] == support]['Alpha'].values
            if len(alpha_value) == 0 or pd.isna(alpha_value[0]):
                st.warning(f"⚠️ Le support '{support}' n'a pas de valeur Alpha définie. Optimisation impossible.")
                can_optimize = False
                break
            
            alpha = alpha_value[0]
            co2_factor = data['CO2_factor']
            budget = data['Budget']
            contacts = data['Contacts']
            
            # Calculer les métriques nécessaires
            # Alpha est un multiplicateur (pas une puissance) : Contacts_utiles = Contacts × (Alpha/100)
            contacts_utiles = contacts * (alpha / 100)
            contacts_utiles_per_euro = contacts_utiles / budget if budget > 0 else 0
            carbone_per_euro = (contacts / budget) * co2_factor if budget > 0 else 0
            
            optimization_data.append({
                'Support': support,
                'Budget': budget,
                'Contacts': contacts,
                'Alpha': alpha,
                'Contacts_utiles': contacts_utiles,
                'Contacts_utiles_per_euro': contacts_utiles_per_euro,
                'Carbone_per_euro': carbone_per_euro,
                'CO2_factor': co2_factor
            })
        
        if can_optimize and len(optimization_data) > 0:
            df_optim = pd.DataFrame(optimization_data)
            
            # Paramètres d'optimisation
            col1, col2, col3 = st.columns(3)
            
            with col1:
                w_carbone = st.slider(
                    "Poids Carbone",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    step=0.05,
                    help="0 = Focus contacts utiles, 1 = Focus réduction carbone"
                )
            
            with col2:
                max_variation = st.slider(
                    "Variation max par support (%)",
                    min_value=0.0,
                    max_value=2.0,
                    value=0.5,
                    step=0.1,
                    help="Variation autorisée PAR SUPPORT par rapport à son budget initial. Ex: 0.5 = ±50% du budget de ce support"
                )

            with col3:
                min_budget_par_canal = st.number_input(
                    "Budget minimum par support (€)",
                    min_value=0,
                    max_value=int(total_budget / len(optimization_data)),
                    value=1000,
                    step=100
                )
            
            if st.button("Lancer l'optimisation", type="primary"):
                try:
                    # Forcer le rechargement du module optimizer pour éviter les problèmes de cache
                    import importlib
                    import sys
                    if 'optimizer' in sys.modules:
                        importlib.reload(sys.modules['optimizer'])
                    from optimizer import optimisation_media                    
                    
                    with st.spinner("Optimisation en cours..."):
                        resultat = optimisation_media(
                            df_optim,
                            w_carbone=w_carbone,
                            min_budget_par_canal=min_budget_par_canal,
                            max_variation=max_variation
                        )
                    
                    if resultat.success:
                        st.success("✅ Optimisation réussie !")
                        
                        # Préparer les résultats
                        budgets_optimises = resultat.x
                        df_optim['Budget_Optimise'] = budgets_optimises
                        df_optim['Variation_%'] = ((budgets_optimises - df_optim['Budget']) / df_optim['Budget'] * 100)
                        df_optim['Variation_€'] = budgets_optimises - df_optim['Budget']
                        
                        # Calculer les métriques optimisées
                        total_contacts_utiles_avant = sum(df_optim['Contacts_utiles'])
                        total_carbone_avant = sum(df_optim['Budget'] * df_optim['Carbone_per_euro'])
                        
                        # Recalculer avec les nouveaux budgets
                        contacts_utiles_apres = []
                        carbone_apres = []
                        for i, row in df_optim.iterrows():
                            nouveau_budget = budgets_optimises[i]
                            # Estimer les nouveaux contacts proportionnellement au budget
                            ratio_budget = nouveau_budget / row['Budget'] if row['Budget'] > 0 else 1
                            nouveaux_contacts = row['Contacts'] * ratio_budget
                            contacts_utiles_apres.append(nouveaux_contacts * (row['Alpha'] / 100))
                            carbone_apres.append(nouveaux_contacts * row['CO2_factor'])
                        
                        total_contacts_utiles_apres = sum(contacts_utiles_apres)
                        total_carbone_apres = sum(carbone_apres)
                        
                        # Afficher les métriques de comparaison
                        st.subheader("Comparaison Avant / Après Optimisation")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric(
                                "Budget Total",
                                f"{sum(budgets_optimises):,.0f} €",
                            )
                        
                        with col2:
                            gain_contacts = ((total_contacts_utiles_apres - total_contacts_utiles_avant) / total_contacts_utiles_avant * 100)
                            st.metric(
                                "Contacts Utiles",
                                f"{total_contacts_utiles_apres:,.0f}",
                                delta=f"{gain_contacts:+.1f}%"
                            )
                        
                        with col3:
                            gain_carbone = ((total_carbone_apres - total_carbone_avant) / total_carbone_avant * 100)
                            st.metric(
                                "CO2 Total (g)",
                                f"{total_carbone_apres:,.0f}",
                                delta=f"{gain_carbone:+.1f}%",
                                delta_color="inverse"  # Rouge = augmentation = mauvais
                            )
                        
                        # Tableau de répartition optimisée
                        st.subheader("Répartition Budgétaire Optimisée")
                        
                        df_display = df_optim[['Support', 'Budget', 'Budget_Optimise', 'Variation_€', 'Variation_%']].copy()
                        df_display['Budget'] = df_display['Budget'].apply(lambda x: f"{x:,.0f} €")
                        df_display['Budget_Optimise'] = df_display['Budget_Optimise'].apply(lambda x: f"{x:,.0f} €")
                        df_display['Variation_€'] = df_display['Variation_€'].apply(lambda x: f"{x:+,.0f} €")
                        df_display['Variation_%'] = df_display['Variation_%'].apply(lambda x: f"{x:+.1f}%")
                        
                        df_display.columns = ['Support', 'Budget Initial', 'Budget Optimisé', 'Variation (€)', 'Variation (%)']
                        st.dataframe(df_display, width=1200)
                        
                        # Graphique de comparaison
                        st.subheader("Comparaison Visuelle")
                        
                        comparison_data = pd.DataFrame({
                            'Support': df_optim['Support'].tolist() + df_optim['Support'].tolist(),
                            'Budget': df_optim['Budget'].tolist() + budgets_optimises.tolist(),
                            'Type': ['Initial'] * len(df_optim) + ['Optimisé'] * len(df_optim)
                        })
                        
                        import plotly.express as px
                        fig = px.bar(
                            comparison_data,
                            x='Support',
                            y='Budget',
                            color='Type',
                            barmode='group',
                            title='Comparaison Budget Initial vs Optimisé par Support',
                            labels={'Budget': 'Budget (€)'},
                            color_discrete_map={'Initial': '#1f77b4', 'Optimisé': '#2ca02c'}
                        )
                        st.plotly_chart(fig, config={'responsive': True})
                        
                    else:
                        st.error(f"❌ L'optimisation a échoué : {resultat.message}")
                        
                        # Afficher plus de détails pour debug
                        with st.expander("📋 Détails de l'échec"):
                            st.write("**Statut:**", resultat.status)
                            st.write("**Message:**", resultat.message)
                            st.write("**Nombre d'itérations:**", resultat.nit if hasattr(resultat, 'nit') else 'N/A')
                            st.write("**Nombre d'évaluations:**", resultat.nfev if hasattr(resultat, 'nfev') else 'N/A')
                            st.write("**Solution partielle (x):**", resultat.x if hasattr(resultat, 'x') else 'N/A')
                        
                        st.info("💡 Essayez de : 1) Augmenter la variation max, 2) Réduire le budget minimum, ou 3) Relancer l'optimisation")
                
                except ImportError as e:
                    st.error(f"❌ Le module optimizer.py est introuvable : {e}")
                    st.info("Assurez-vous qu'optimizer.py est présent dans le même dossier que l'application.")
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'optimisation : {e}")
                    with st.expander("📋 Traceback complet"):
                        import traceback
                        st.code(traceback.format_exc())
        
        # Courbe de Pareto
        st.markdown("---")
        st.header("Analyse de Pareto : Contacts Utiles vs Carbone")
        
        st.markdown("""
        La courbe de Pareto explore différents compromis entre **maximiser les contacts utiles** 
        et **minimiser l'empreinte carbone** en variant le poids carbone de 0 à 1.
        """)
        
        if st.button("🔬 Générer la Courbe de Pareto", type="primary"):
            if can_optimize and len(optimization_data) > 0:
                try:
                    from optimizer import optimisation_media
                    import importlib
                    import sys
                    if 'optimizer' in sys.modules:
                        importlib.reload(sys.modules['optimizer'])
                    
                    # Tester différents poids carbone
                    poids_carbone_range = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
                    pareto_results = []
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, w in enumerate(poids_carbone_range):
                        status_text.text(f"Optimisation pour poids carbone = {w:.1f}...")
                        
                        resultat = optimisation_media(
                            df_optim,
                            w_carbone=w,
                            min_budget_par_canal=min_budget_par_canal,
                            max_variation=max_variation
                        )
                        
                        if resultat.success:
                            # Calculer les métriques pour cette solution
                            contacts_utiles_total = 0
                            carbone_total = 0
                            
                            for j, row in df_optim.iterrows():
                                nouveau_budget = resultat.x[j]
                                ratio_budget = nouveau_budget / row['Budget'] if row['Budget'] > 0 else 1
                                nouveaux_contacts = row['Contacts'] * ratio_budget
                                contacts_utiles_total += nouveaux_contacts * (row['Alpha'] / 100)
                                carbone_total += nouveaux_contacts * row['CO2_factor']
                            
                            pareto_results.append({
                                'w_carbone': w,
                                'contacts_utiles': contacts_utiles_total,
                                'carbone_g': carbone_total,
                                'carbone_kg': carbone_total / 1000,
                                'budgets': resultat.x.copy()
                            })
                        
                        progress_bar.progress((i + 1) / len(poids_carbone_range))
                    
                    status_text.empty()
                    progress_bar.empty()
                    
                    if len(pareto_results) > 0:
                        st.success(f"✅ {len(pareto_results)} optimisations réussies sur {len(poids_carbone_range)}")
                        
                        # Créer le DataFrame pour Pareto
                        df_pareto = pd.DataFrame([{
                            'Poids Carbone': r['w_carbone'],
                            'Contacts Utiles': r['contacts_utiles'],
                            'Carbone (kg)': r['carbone_kg']
                        } for r in pareto_results])
                        df_pareto["Derive_Contacts"] = df_pareto["Contacts Utiles"].diff() / df_pareto["Carbone (kg)"].diff()
                        df_pareto["Derive_Contacts"].fillna(0, inplace=True)
                        
                        for i in range(3, len(df_pareto)):
                            if df_pareto.loc[10-i, "Derive_Contacts"] < df_pareto.loc[10-i+1, "Derive_Contacts"]*0.7 and df_pareto.loc[10-i+1, "Derive_Contacts"] >= 0:
                                optimal_idx = 10-i
                                break
                        # Graphique Pareto interactif
                        import plotly.graph_objects as go
                        
                        fig = go.Figure()
                        
                        # Ajouter la courbe Pareto
                        fig.add_trace(go.Scatter(
                            x=df_pareto['Carbone (kg)'],
                            y=df_pareto['Contacts Utiles'],
                            mode='lines+markers',
                            marker=dict(
                                size=12,
                                color=df_pareto['Poids Carbone'],
                                colorscale='RdYlGn',
                                showscale=True,
                                colorbar=dict(title="Poids<br>Carbone"),
                                line=dict(width=1, color='white')
                            ),
                            line=dict(width=2, color='rgba(100, 100, 100, 0.3)'),
                            text=[f"w={w:.1f}" for w in df_pareto['Poids Carbone']],
                            hovertemplate='<b>Poids Carbone: %{text}</b><br>' +
                                         'Carbone: %{x:,.0f} kg<br>' +
                                         'Contacts Utiles: %{y:,.0f}<br>' +
                                         '<extra></extra>'
                        ))
                        
                        # Ajouter le point initial (avant optimisation)
                        contacts_init = sum(df_optim['Contacts_utiles'])
                        carbone_init = sum(df_optim['Budget'] * df_optim['Carbone_per_euro']) / 1000
                        
                        fig.add_trace(go.Scatter(
                            x=[carbone_init],
                            y=[contacts_init],
                            mode='markers',
                            marker=dict(size=15, color='red', symbol='star', line=dict(width=2, color='white')),
                            name='Budget Initial',
                            hovertemplate='<b>Budget Initial</b><br>' +
                                         'Carbone: %{x:,.0f} kg<br>' +
                                         'Contacts Utiles: %{y:,.0f}<br>' +
                                         '<extra></extra>'
                        ))

                        fig.add_trace(go.Scatter(
                            x=[df_pareto['Carbone (kg)'][optimal_idx]],
                            y=[df_pareto['Contacts Utiles'][optimal_idx]],
                            mode='markers+text',
                            marker=dict(color='green', size=15, symbol='circle'),
                            text=['Poids optimal'],
                            textposition='top center',
                            hoverinfo='skip',
                            showlegend=False
                            
                        ))
                        
                        fig.update_layout(
                            title='Courbe de Pareto : Efficacité vs Empreinte Carbone',
                            xaxis_title='Empreinte Carbone (kg)',
                            yaxis_title='Contacts Utiles',
                            hovermode='closest',
                            height=600,
                        )
                        
                        st.plotly_chart(fig)
                        
                        # Tableau récapitulatif
                        st.subheader("📋 Détails des Solutions Pareto")
                        
                        df_pareto_display = df_pareto.copy()
                        df_pareto_display['Contacts Utiles'] = df_pareto_display['Contacts Utiles'].apply(lambda x: f"{x:,.0f}")
                        df_pareto_display['Carbone (kg)'] = df_pareto_display['Carbone (kg)'].apply(lambda x: f"{x:,.2f}")
                        
                        # Calculer les variations par rapport à l'initial
                        variations = []
                        for r in pareto_results:
                            var_contacts = (r['contacts_utiles'] - contacts_init) / contacts_init * 100
                            var_carbone = (r['carbone_kg'] - carbone_init) / carbone_init * 100
                            variations.append({
                                'Δ Contacts (%)': f"{var_contacts:+.1f}%",
                                'Δ Carbone (%)': f"{var_carbone:+.1f}%"
                            })
                        
                        df_variations = pd.DataFrame(variations)
                        df_pareto_final = pd.concat([df_pareto_display, df_variations], axis=1)
                        st.session_state.df_pareto_final = df_pareto_final
                        st.dataframe(df_pareto_final, width=1200)
                        
                        # Recommandations
                        st.subheader("Recommandations")
                        
                        # Trouver les meilleurs compromis
                        best_contacts_idx = df_pareto['Contacts Utiles'].idxmax()
                        best_carbone_idx = df_pareto['Carbone (kg)'].idxmin()

                        

                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.markdown("**Meilleure Performance**")
                            st.metric("Poids Carbone", f"{pareto_results[best_contacts_idx]['w_carbone']:.1f}")
                            st.metric("Contacts Utiles", f"{pareto_results[best_contacts_idx]['contacts_utiles']:,.0f}")
                            st.metric("Carbone", f"{pareto_results[best_contacts_idx]['carbone_kg']:,.1f} kg")
                        
                        with col2:
                            st.markdown("**Meilleure Empreinte Carbone**")
                            st.metric("Poids Carbone", f"{pareto_results[best_carbone_idx]['w_carbone']:.1f}")
                            st.metric("Contacts Utiles", f"{pareto_results[best_carbone_idx]['contacts_utiles']:,.0f}")
                            st.metric("Carbone", f"{pareto_results[best_carbone_idx]['carbone_kg']:,.1f} kg")
                        
                        with col3:
                            st.markdown("**Compromis Optimal**")
                            st.metric("Poids Carbone", f"{pareto_results[optimal_idx]['w_carbone']:.1f}")
                            st.metric("Contacts Utiles", f"{pareto_results[optimal_idx]['contacts_utiles']:,.0f}")
                            st.metric("Carbone", f"{pareto_results[optimal_idx]['carbone_kg']:,.1f} kg")
                        
                        # Option d'export
                        st.markdown("---")
                        if st.button("Exporter les résultats Pareto (CSV)"):
                            print(st.session_state.df_pareto_final)
                            csv = st.session_state.df_pareto_final.to_csv(index=False)
                            st.download_button(
                                label="Télécharger CSV",
                                data=csv,
                                file_name="pareto_analysis.csv",
                                mime="text/csv"
                            )
                    else:
                        st.error("❌ Aucune optimisation n'a réussi")
                
                except Exception as e:
                    st.error(f"❌ Erreur lors de la génération de la courbe de Pareto : {e}")
                    import traceback
                    st.code(traceback.format_exc())
            else:
                st.warning("⚠️ Impossible de générer la courbe de Pareto : certains supports n'ont pas de valeur Alpha")
        
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
        st.dataframe(co2_ref, width=1200)

else:
    st.error("⚠️ Impossible de charger le fichier de référence CO2g contact.xlsx")
    st.info("Assurez-vous que le fichier 'CO2g contact.xlsx' est présent dans le même dossier que cette application.")
