from src.db import get_connection

def add_vehicle(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO vehicules (
        immatriculation, marque, modele, type_vehicule, annee, date_acquisition,
        kilometrage_actuel, carburant, puissance_fiscale, numero_chassis, photo_path,
        type_affectation, statut, service_principal, seuil_revision_km
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', (
        data.get('immatriculation'), data.get('marque'), data.get('modele'), data.get('type_vehicule'),
        data.get('annee'), data.get('date_acquisition'), data.get('kilometrage_actuel',0), data.get('carburant'),
        data.get('puissance_fiscale'), data.get('numero_chassis'), data.get('photo_path'), data.get('type_affectation'),
        data.get('statut','disponible'), data.get('service_principal'), data.get('seuil_revision_km')
    ))
    conn.commit()
    conn.close()

def find_vehicles(filter_text=None, filters=None):
    conn = get_connection()
    c = conn.cursor()
    query = 'SELECT * FROM vehicules'
    clauses = []
    params = []
    if filter_text:
        clauses.append('(immatriculation LIKE ? OR marque LIKE ? OR modele LIKE ? OR service_principal LIKE ?)')
        like = f'%{filter_text}%'
        params.extend([like, like, like, like])
    if filters:
        if 'type_vehicule' in filters:
            clauses.append('type_vehicule = ?')
            params.append(filters['type_vehicule'])
        if 'statut' in filters:
            clauses.append('statut = ?')
            params.append(filters['statut'])
    if clauses:
        query += ' WHERE ' + ' AND '.join(clauses)
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_employee(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO employes (
        matricule, nom, prenom, service, telephone, email, num_permis,
        date_validite_permis, autorise_conduire, photo_path
    ) VALUES (?,?,?,?,?,?,?,?,?,?)''', (
        data.get('matricule'), data.get('nom'), data.get('prenom'), data.get('service'),
        data.get('telephone'), data.get('email'), data.get('num_permis'), data.get('date_validite_permis'),
        1 if data.get('autorise_conduire') else 0, data.get('photo_path')
    ))
    conn.commit()
    conn.close()

def find_employees(filter_text=None):
    conn = get_connection()
    c = conn.cursor()
    query = 'SELECT * FROM employes'
    params = []
    if filter_text:
        query += ' WHERE matricule LIKE ? OR nom LIKE ? OR prenom LIKE ? OR service LIKE ?'
        like = f'%{filter_text}%'
        params = [like, like, like, like]
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_dashboard_counts():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM vehicules")
    total = c.fetchone()['total']
    c.execute("SELECT COUNT(*) as available FROM vehicules WHERE statut = 'disponible'")
    available = c.fetchone()['available']
    c.execute("SELECT COUNT(*) as in_use FROM vehicules WHERE statut = 'en sortie'")
    in_use = c.fetchone()['in_use']
    c.execute("SELECT COUNT(*) as maintenance FROM vehicules WHERE statut = 'en maintenance'")
    maintenance = c.fetchone()['maintenance']
    conn.close()
    return {'total': total, 'available': available, 'in_use': in_use, 'maintenance': maintenance}
