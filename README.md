# 🌱 Calculateur d'Empreinte Carbone des Plans Média

Application Streamlit pour calculer l'empreinte carbone de vos plans média en fonction des supports utilisés.

## 📋 Prérequis

- Python 3.7+
- pandas
- streamlit
- openpyxl

## 🚀 Installation

```bash
pip install streamlit pandas openpyxl
```

## 💻 Lancement de l'application

Dans le dossier du projet, exécutez :

```bash
streamlit run app_calculator.py
```

L'application s'ouvrira automatiquement dans votre navigateur par défaut.

## 📝 Utilisation

### 1. Préparer votre fichier CSV

Créez un fichier CSV avec **deux colonnes obligatoires** :
- `Contact` : Nombre de contacts pour chaque ligne
- `Budget` : Budget alloué (en euros)

Exemple de fichier CSV :
```csv
Contact,Budget
1000000,5000
500000,2500
```

### 2. Charger votre plan

1. Cliquez sur "Browse files" dans la barre latérale
2. Sélectionnez votre fichier CSV
3. Donnez un nom à votre plan (ou gardez le nom du fichier)
4. Sélectionnez le support média correspondant dans le menu déroulant
5. Cliquez sur "✅ Ajouter ce plan"

### 3. Analyser les résultats

L'application affiche :
- **Tableau récapitulatif** : Vue d'ensemble de tous vos plans
- **Métriques globales** : CO2 total, budget total, contacts totaux
- **Graphiques** : Visualisations de la répartition du CO2 et du budget
- **Détails par plan** : Informations détaillées de chaque plan média

### 4. Gérer vos plans

- Ajoutez plusieurs plans pour comparer différents scénarios
- Supprimez un plan avec le bouton 🗑️
- Réinitialisez tous les plans avec le bouton "🔄 Réinitialiser tous les plans"

## 📊 Supports disponibles

L'application utilise les données de référence du fichier `CO2g contact.xlsx` qui contient les facteurs d'émission CO2 pour 69 supports média différents, incluant :

- **OOH** : Affichage extérieur (papier, digital)
- **RADIO** : Radio analogique, DAB, audio digital
- **INTERNET** : Display, social, vidéo, programmatique
- **TELEVISION** : TV classique, replay, VOD, streaming
- **PRESSE** : Presse papier et numérique
- **AUTRES** : Mailing, email, SMS

## 📈 Calculs

Pour chaque plan, l'application calcule :
- **CO2 Total** = Nombre de contacts × CO2g/Contact du support
- **CO2/€** = CO2 Total / Budget
- Conversions en grammes, kilogrammes et tonnes

## 🔧 Structure du projet

```
.
├── app_calculator.py          # Application Streamlit principale
├── CO2g contact.xlsx          # Fichier de référence des facteurs CO2
├── optimizer.py               # Module d'optimisation (optionnel)
└── README.md                  # Ce fichier
```

## ⚠️ Notes importantes

- Le fichier `CO2g contact.xlsx` doit être dans le même dossier que `app_calculator.py`
- Les fichiers CSV doivent impérativement contenir les colonnes `Contact` et `Budget`
- Les calculs sont basés sur les facteurs d'émission fournis dans le fichier de référence

## 🐛 Dépannage

Si vous rencontrez une erreur :
1. Vérifiez que `CO2g contact.xlsx` est bien présent
2. Vérifiez que votre CSV contient les colonnes `Contact` et `Budget`
3. Assurez-vous que les valeurs dans le CSV sont numériques
4. Redémarrez l'application avec `streamlit run app_calculator.py`
