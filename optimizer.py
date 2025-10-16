import pandas as pd
from scipy.optimize import minimize, LinearConstraint
import numpy as np
import matplotlib.pyplot as plt

def optimisation_media(df, w_carbone=0.5, alpha=0.6,min_budget_par_canal=1000, max_variation=1.0):
    """
    Optimise la répartition des spots en intégrant les rendements décroissants 
    et des contraintes métier.
    
    Paramètres:
    - df: DataFrame avec les métriques des canaux.
    - w_carbone: Poids de l'objectif carbone (0 à 1).
    - alpha: Exposant des rendements décroissants (typiquement entre 0.4 et 0.8). 
             Plus il est bas, plus les rendements diminuent vite.
    - min_spots_par_canal: Nombre de spots minimum imposé pour chaque canal.
    - max_variation: Variation maximale autorisée par rapport au nombre initial (ex: 1.0 = +100%).
    """
    
    efficacite_coeffs = df['Contacts_utiles_per_euro'].values
    carbone_coeffs = df['Carbone_per_euro'].values
    budget_total = df['Budget'].sum()
    n_canaux = len(df)
    budgets_initiaux = df['Budget'].values
    
    def objectif(x):
        total_carbone = np.sum(x * carbone_coeffs)
        total_contacts_utiles = np.sum(efficacite_coeffs * (x ** alpha))
        
        # Calculer moyenne et écart-type pour chaque métrique sur plusieurs scénarios
        # (à pré-calculer ou estimer)
        mean_carbone = np.mean(carbone_coeffs) * budget_total
        std_carbone = np.std(carbone_coeffs) * budget_total
        
        mean_contacts = np.mean(efficacite_coeffs) * (budget_total ** alpha)
        std_contacts = np.std(efficacite_coeffs) * (budget_total ** alpha)
        
        # Z-score normalization
        norm_carbone = (total_carbone - mean_carbone) / (std_carbone + 1e-9)
        norm_contacts = (total_contacts_utiles - mean_contacts) / (std_contacts + 1e-9)
        
        return w_carbone * norm_carbone - (1 - w_carbone) * norm_contacts
    # --- Contraintes ---
    # 1. Le budget total de spots doit être respecté
    contrainte_budget = LinearConstraint(np.ones(n_canaux), [budget_total], [budget_total])
    
    # 2. Limites pour chaque canal (min, max spots avec contrainte de variation maximale)
    limites = []
    for i in range(n_canaux):
        min_budget = min_budget_par_canal
        max_budget = min(
            budgets_initiaux[i] * (1 + max_variation),
            budget_total
        )
        limites.append((min_budget, max_budget))
    print("Limites par canal (min, max):", limites)
    # Point de départ
    x0 = np.clip(budgets_initiaux, min_budget_par_canal, [lim[1] for lim in limites])
    # Si le point de départ ne respecte pas le budget, on le normalise
    if np.sum(x0) != budget_total:
        x0 = x0 / np.sum(x0) * budget_total

    # Optimisation
    resultat = minimize(objectif, x0, method='trust-constr', bounds=limites, constraints=contrainte_budget)
    
    return resultat
