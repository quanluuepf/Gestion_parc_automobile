import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vehicule_parc.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.executescript('''
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        nom TEXT,
        prenom TEXT,
        email TEXT,
        actif INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS employes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricule TEXT UNIQUE NOT NULL,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        service TEXT,
        telephone TEXT,
        email TEXT,
        num_permis TEXT,
        date_validite_permis TEXT,
        autorise_conduire INTEGER DEFAULT 0,
        photo_path TEXT
    );

    CREATE TABLE IF NOT EXISTS vehicules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        immatriculation TEXT UNIQUE NOT NULL,
        marque TEXT,
        modele TEXT,
        type_vehicule TEXT,
        annee INTEGER,
        date_acquisition TEXT,
        kilometrage_initial INTEGER DEFAULT 0,
        kilometrage_actuel INTEGER DEFAULT 0,
        carburant TEXT,
        puissance_fiscale TEXT,
        numero_chassis TEXT,
        photo_path TEXT,
        type_affectation TEXT,
        statut TEXT,
        service_principal TEXT,
        seuil_revision_km INTEGER
    );

    CREATE TABLE IF NOT EXISTS affectations_permanentes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicule_id INTEGER,
        employe_id INTEGER,
        date_debut TEXT,
        date_fin TEXT,
        FOREIGN KEY (vehicule_id) REFERENCES vehicules(id),
        FOREIGN KEY (employe_id) REFERENCES employes(id)
    );

    CREATE TABLE IF NOT EXISTS sorties_reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicule_id INTEGER,
        employe_id INTEGER,
        date_sortie_prevue TEXT,
        heure_sortie_prevue TEXT,
        date_retour_prevue TEXT,
        heure_retour_prevue TEXT,
        date_sortie_reelle TEXT,
        heure_sortie_reelle TEXT,
        km_depart INTEGER,
        date_retour_reelle TEXT,
        heure_retour_reelle TEXT,
        km_retour INTEGER,
        motif TEXT,
        destination TEXT,
        etat_retour TEXT,
        niveau_carburant_retour TEXT,
        statut TEXT,
        FOREIGN KEY (vehicule_id) REFERENCES vehicules(id),
        FOREIGN KEY (employe_id) REFERENCES employes(id)
    );

    CREATE TABLE IF NOT EXISTS maintenances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicule_id INTEGER,
        date TEXT,
        type_intervention TEXT,
        kilometrage INTEGER,
        cout REAL,
        prestataire TEXT,
        remarques TEXT,
        date_prochaine_echeance TEXT,
        FOREIGN KEY (vehicule_id) REFERENCES vehicules(id)
    );

    CREATE TABLE IF NOT EXISTS ravitaillements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicule_id INTEGER,
        employe_id INTEGER,
        date TEXT,
        quantite_litres REAL,
        cout REAL,
        station TEXT,
        kilometrage INTEGER,
        FOREIGN KEY (vehicule_id) REFERENCES vehicules(id),
        FOREIGN KEY (employe_id) REFERENCES employes(id)
    );

    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicule_id INTEGER,
        type_document TEXT,
        date_emission TEXT,
        date_echeance TEXT,
        chemin_fichier TEXT,
        description TEXT,
        FOREIGN KEY (vehicule_id) REFERENCES vehicules(id)
    );

    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        date_action TEXT,
        details TEXT
    );
    ''')
    conn.commit()
    conn.close()
