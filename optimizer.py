from scipy.optimize import minimize, LinearConstraint
import numpy as np

def optimisation_media(df, w_carbone=0.5, min_budget_par_canal=1000, max_variation=0.5):
    """
    Optimise la répartition du budget en intégrant les rendements décroissants 
    et des contraintes métier.
    
    Paramètres:
    - df: DataFrame avec les métriques des canaux.
    - w_carbone: Poids de l'objectif carbone (0 à 1).
    - min_budget_par_canal: Budget minimum imposé pour chaque canal (en euros).
    - max_variation: Variation maximale autorisée par rapport au budget initial de CHAQUE canal.
                     Ex: 0.5 = ±50% du budget initial de ce canal
                         1.0 = ±100% du budget initial de ce canal
    """
    
    efficacite_coeffs = df['Contacts_utiles_per_euro'].values
    carbone_coeffs = df['Carbone_per_euro'].values
    budget_total = df['Budget'].sum()
    n_canaux = len(df)
    budgets_initiaux = df['Budget'].values

    mean_carbone = np.mean(carbone_coeffs) * budget_total
    std_carbone = np.std(carbone_coeffs) * budget_total
        
    mean_contacts = np.mean(efficacite_coeffs) * (budget_total)
    std_contacts = np.std(efficacite_coeffs) * (budget_total)
    
    def objectif(x):
        total_carbone = np.dot(x, carbone_coeffs)
        total_contacts_utiles = np.dot(x, efficacite_coeffs)
        # Z-score normalization
        norm_carbone = (total_carbone - mean_carbone) / (std_carbone + 1e-9)
        norm_contacts = (total_contacts_utiles - mean_contacts) / (std_contacts + 1e-9)
        
        return w_carbone * norm_carbone - (1 - w_carbone) * norm_contacts
    
    def gradient(x):
        grad_carbone = carbone_coeffs / std_carbone
        grad_contacts = efficacite_coeffs / std_contacts
        return w_carbone * grad_carbone - (1 - w_carbone) * grad_contacts
    
    # --- Contraintes ---
    # 1. Le budget total de spots doit être respecté
    contrainte_budget = LinearConstraint(np.ones(n_canaux), [budget_total], [budget_total])
    
    # 2. Limites pour chaque canal (min, max budget avec contrainte de variation maximale)
    limites = []
    for i in range(n_canaux):
        # Le minimum est soit le budget minimum imposé, soit le budget initial réduit de max_variation
        min_budget = max(
            min_budget_par_canal,
            budgets_initiaux[i] * (1 - max_variation)
        )
        # Le maximum est le budget initial augmenté de max_variation
        max_budget = budgets_initiaux[i] * (1 + max_variation)
        limites.append((min_budget, max_budget))

    # Point de départ
    x0 = np.clip(budgets_initiaux, min_budget_par_canal, [lim[1] for lim in limites])
    # Si le point de départ ne respecte pas le budget, on le normalise
    if np.sum(x0) != budget_total:
        x0 = x0 / np.sum(x0) * budget_total

    # Optimisation avec gestion d'erreur
    try:
        resultat = minimize(
            objectif, 
            x0, 
            method='trust-constr', 
            bounds=limites, 
            constraints=contrainte_budget,
            options={'maxiter': 10000, 'verbose': 1},


        )
    except Exception as e:
        print(f"Erreur lors de l'optimisation: {e}")
        # Si trust-constr échoue, essayer SLSQP qui est plus robuste
        print("Tentative avec la méthode SLSQP...")
        resultat = minimize(
            objectif,
            x0,
            method='SLSQP',
            jac=gradient,
            bounds=limites,
            constraints={'type': 'eq', 'fun': lambda x: np.sum(x) - budget_total},
            options={'maxiter': 10000}
        )
    
    return resultat
