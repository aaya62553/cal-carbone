import numpy as np
from scipy.optimize import minimize, LinearConstraint
import warnings

def optimisation_media(
    df,
    w_carbone=0.5,
    min_budget_par_canal=1000,
    max_variation=0.5,
    lambda_reg=1e-7,
):
    """
    Paramètres:
      - df: contient les colonnes 'Contacts_utiles_per_euro', 'Carbone_per_euro', 'Budget'
      - w_carbone: poids du carbone dans [0,1]
      - min_budget_par_canal: budget minimum par canal
      - max_variation: variation max autorisée autour du budget initial pour chaque canal (ex: 0.5 => ±50%)
      - lambda_reg: intensité L2; plus grand => allocations plus proches de x_center
    """
    efficacite = df['Contacts_utiles_per_euro'].values.astype(float)
    carbone = df['Carbone_per_euro'].values.astype(float)
    budgets_initiaux = df['Budget'].values.astype(float)
    budget_total = float(budgets_initiaux.sum())
    n = len(df)

    # Normalisation: utiliser les écarts types des coefficients "par euro" (sans * budget_total)
    eps = 1e-12
    std_contacts = float(np.std(efficacite))
    std_carbone = float(np.std(carbone))
    if std_contacts == 0:
        warnings.warn("std_contacts == 0: normalisation des contacts désactivée (eps utilisé).")
        std_contacts = eps
    if std_carbone == 0:
        warnings.warn("std_carbone == 0: normalisation du carbone désactivée (eps utilisé).")
        std_carbone = eps

    # Vecteur coût (linéaire)
    # Minimiser c^T x favorise efficacité (terme négatif) et pénalise carbone (terme positif)
    c = w_carbone * (carbone / std_carbone) - (1.0 - w_carbone) * (efficacite / std_contacts)

    # Bornes individuelles [min_i, max_i] avec variation max autour de l'initial + plancher commun
    lower_bounds = np.empty(n)
    upper_bounds = np.empty(n)
    for i in range(n):
        lb = max(min_budget_par_canal, budgets_initiaux[i] * (1 - max_variation))
        ub = budgets_initiaux[i] * (1 + max_variation)
        lower_bounds[i] = float(lb)
        upper_bounds[i] = float(ub)

    # Vérifier faisabilité simple
    sum_low = float(lower_bounds.sum())
    sum_up = float(upper_bounds.sum())
    if sum_low > budget_total + 1e-9:
        raise ValueError(
            f"Problème infaisable: somme des bornes basses {sum_low:.2f} > budget_total {budget_total:.2f}"
        )
    if sum_up < budget_total - 1e-9:
        raise ValueError(
            f"Problème infaisable: somme des bornes hautes {sum_up:.2f} < budget_total {budget_total:.2f}"
        )

    # Point de départ et centre de régularisation x_center (rend la régularisation pertinente et faisable)
    x0 = np.clip(budgets_initiaux, lower_bounds, upper_bounds)

    x_center = x0.copy()  # centre de régularisation

    w_diag = np.ones(n, dtype=float)

    # Définir objectif, gradient, Hessienne
    # f(x) = c^T x + (lambda/2) * sum_i w2_i * (x_i - x_center_i)^2
    def fun(x):
        dx = x - x_center
        return float(np.dot(c, x) + 0.5 * lambda_reg * np.dot(w_diag * dx, dx))

    def jac(x):
        dx = x - x_center
        return c + lambda_reg * (w_diag * dx)

    def hess(_x):
        # Hessienne constante (diagonale)
        return np.diag(lambda_reg * w_diag)
    

    # Contrainte somme(x) == budget_total
    constraint = LinearConstraint(np.ones((1, n)), [budget_total], [budget_total])

    res = minimize(
        fun,
        x0,
        method="trust-constr",
        jac=jac,
        hess=hess,
        bounds=list(zip(lower_bounds, upper_bounds)),
        constraints=[constraint],
        options={
            "maxiter": 2000,
            "gtol": 1e-12,
            "xtol": 1e-12,
            "barrier_tol": 1e-12,
            "verbose": 0,
        },
    )

    # Fallback SLSQP si jamais nécessaire
    if not res.success:
        res = minimize(
            fun,
            x0,
            method="SLSQP",
            jac=jac,
            bounds=list(zip(lower_bounds, upper_bounds)),
            constraints={"type": "eq", "fun": lambda x: np.sum(x) - budget_total, "jac": lambda x: np.ones_like(x)},
            options={"maxiter": 2000, "ftol": 1e-9, "disp": False},
        )

    return res