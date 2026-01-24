# Gestion de parc automobile

Application desktop (Tkinter + SQLite) pour gérer le parc automobile d'une entreprise.

Exécution rapide :

1. Installer les dépendances :

```powershell
python -m pip install -r requirements.txt
```

2. Lancer :

```powershell
python -m src.main
```

Fichiers clés :
- `src/db.py` : initialisation de la base SQLite
- `src/models.py` : accès aux données (CRUD)
- `src/ui` : modules d'interface (tableau de bord, véhicules, employés)

Base SQLite : `vehicule_parc.db` (créée automatiquement dans le dossier racine)
