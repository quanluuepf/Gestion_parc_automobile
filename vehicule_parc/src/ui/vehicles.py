import tkinter as tk
from tkinter import ttk, messagebox
from ..models import add_vehicle, find_vehicles
from ..db import get_connection as db_connection


# ==========================================================
# CONSTANTES
# ==========================================================
STATUS_COLORS = {
    'disponible': '#90EE90',
    'en sortie': '#FFD700',
    'en maintenance': '#FFA500',
    'immobilisé': '#FF6347',
    'panne': '#DC143C',
    'à nettoyer': '#87CEEB'
}

VEHICLE_TYPES = ['Voiture', 'Utilitaire', 'Camionnette', 'Fourgon', 'Bus']
FUEL_TYPES = ['Essence', 'Diesel', 'Électrique', 'Hybride']
AFFECTATION_TYPES = ['Mutualisé', 'Voiture de fonction']


# ==========================================================
# LISTE DES VEHICULES (DASHBOARD)
# ==========================================================
class VehicleListWindow:
    def __init__(self, parent=None):
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title('Gestion des Véhicules')
        self.root.geometry('1000x600')
        self.build_ui()
        self.load_vehicles()

    def build_ui(self):
        search = ttk.LabelFrame(self.root, text='Recherche & Filtres', padding=10)
        search.pack(fill='x', padx=10, pady=5)

        ttk.Label(search, text='Recherche').grid(row=0, column=0)
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *_: self.load_vehicles())
        ttk.Entry(search, textvariable=self.search_var, width=25).grid(row=0, column=1)

        ttk.Label(search, text='Type').grid(row=0, column=2)
        self.type_var = tk.StringVar()
        ttk.Combobox(
            search,
            textvariable=self.type_var,
            values=[''] + VEHICLE_TYPES,
            state='readonly',
            width=15
        ).grid(row=0, column=3)

        ttk.Label(search, text='Statut').grid(row=0, column=4)
        self.status_var = tk.StringVar()
        ttk.Combobox(
            search,
            textvariable=self.status_var,
            values=[''] + list(STATUS_COLORS.keys()),
            state='readonly',
            width=15
        ).grid(row=0, column=5)

        ttk.Button(search, text='Ajouter', command=self.open_add_vehicle).grid(row=0, column=6, padx=5)
        ttk.Button(search, text='Modifier', command=self.open_edit_vehicle).grid(row=0, column=7, padx=5)
        ttk.Button(search, text='Supprimer', command=self.delete_vehicle).grid(row=0, column=8, padx=5)

        self.alert_label = ttk.Label(self.root, foreground='red', font=('Arial', 11, 'bold'))
        self.alert_label.pack(fill='x', padx=10)

        columns = ('Immatriculation', 'Marque', 'Modèle', 'Type', 'Année', 'Statut', 'Service')
        self.tree = ttk.Treeview(self.root, columns=columns, show='headings')

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)

        self.tree.pack(fill='both', expand=True, padx=10, pady=5)

        self.status_bar = ttk.Label(self.root, relief='sunken')
        self.status_bar.pack(fill='x')

    # ======================================================
    # CHARGEMENT
    # ======================================================
    def load_vehicles(self):
        self.tree.delete(*self.tree.get_children())

        filters = {}
        if self.type_var.get():
            filters['type_vehicule'] = self.type_var.get()
        if self.status_var.get():
            filters['statut'] = self.status_var.get()

        vehicles = find_vehicles(
            filter_text=self.search_var.get() or None,
            filters=filters or None
        )

        total = len(vehicles)
        available = sum(1 for v in vehicles if v['statut'] == 'disponible')

        self.alert_label.config(
            text="Aucun véhicule disponible" if total and not available else ''
        )

        for v in vehicles:
            self.tree.insert(
                '',
                'end',
                iid=str(v['id']),   # 🔑 ID BDD = clé unique
                values=(
                    v['immatriculation'],
                    v['marque'],
                    v['modele'],
                    v['type_vehicule'],
                    v['annee'],
                    v['statut'],
                    v['service_principal']
                ),
                tags=(v['statut'],)
            )

        for status, color in STATUS_COLORS.items():
            self.tree.tag_configure(status, background=color)

        self.status_bar.config(text=f"Total : {total} | Disponibles : {available}")

    # ======================================================
    # SELECTION
    # ======================================================
    def get_selected_vehicle(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning('Sélection', 'Veuillez sélectionner un véhicule')
            return None

        vehicle_id = int(selection[0])

        conn = db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM vehicules WHERE id = ?', (vehicle_id,))
        row = c.fetchone()
        columns = [d[0] for d in c.description]
        conn.close()

        return dict(zip(columns, row)) if row else None

    # ======================================================
    # ACTIONS
    # ======================================================
    def open_add_vehicle(self):
        AddEditVehicleWindow(self.root, callback=self.load_vehicles)

    def open_edit_vehicle(self):
        v = self.get_selected_vehicle()
        if v:
            AddEditVehicleWindow(self.root, vehicle=v, callback=self.load_vehicles)

    def delete_vehicle(self):
        v = self.get_selected_vehicle()
        if not v:
            return

        if not messagebox.askyesno(
            'Confirmation',
            f"Supprimer définitivement {v['immatriculation']} ?"
        ):
            return

        conn = db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM vehicules WHERE id = ?', (v['id'],))
        conn.commit()
        conn.close()

        self.load_vehicles()
        messagebox.showinfo('Succès', 'Véhicule supprimé')


# ==========================================================
# AJOUT / MODIFICATION VEHICULE
# ==========================================================
class AddEditVehicleWindow:
    def __init__(self, parent, vehicle=None, callback=None):
        self.vehicle = vehicle
        self.callback = callback

        self.window = tk.Toplevel(parent)
        self.window.title('Modifier un véhicule' if vehicle else 'Ajouter un véhicule')
        self.window.geometry('600x850')

        self.entries = {}
        self.build_ui()
        if vehicle:
            self.populate()

    def build_ui(self):
        frame = ttk.Frame(self.window, padding=15)
        frame.pack(fill='both', expand=True)

        fields = [
            ('Immatriculation', 'immatriculation', 'entry'),
            ('Marque', 'marque', 'entry'),
            ('Modèle', 'modele', 'entry'),
            ('Type', 'type_vehicule', 'combo', VEHICLE_TYPES),
            ('Année', 'annee', 'entry'),
            ('Carburant', 'carburant', 'combo', FUEL_TYPES),
            ('Statut', 'statut', 'combo', list(STATUS_COLORS.keys())),
            ('Service', 'service_principal', 'entry'),
            ('Affectation', 'type_affectation', 'combo', AFFECTATION_TYPES),
            ('Date d\'acquisition', 'date_acquisition', 'entry'),
            ('Numéro de châssis', 'numero_chassis', 'entry'),
            ('Photo (chemin)', 'photo_path', 'entry'),
            ('Kilométrage Initial (km)', 'kilometrage_initial', 'entry'),
            ('Kilométrage Actuel (km)', 'kilometrage_actuel', 'entry'),
            ('Seuil Révision (km)', 'seuil_revision_km', 'entry'),
        ]

        for i, field in enumerate(fields):
            label, key, kind, *values = field
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky='w', pady=4)

            if kind == 'entry':
                widget = ttk.Entry(frame, width=40)
            else:
                widget = ttk.Combobox(
                    frame,
                    values=values[0],
                    state='readonly',
                    width=38
                )

            widget.grid(row=i, column=1, sticky='w')
            self.entries[key] = widget

        ttk.Button(
            frame,
            text='Enregistrer',
            command=self.save
        ).grid(row=len(fields) + 1, column=1, pady=20, sticky='e')

    def populate(self):
        for k, w in self.entries.items():
            if self.vehicle.get(k) is not None:
                if isinstance(w, ttk.Combobox):
                    w.set(self.vehicle[k])
                else:
                    w.insert(0, self.vehicle[k])

    def save(self):
        data = {k: w.get() or None for k, w in self.entries.items()}

        conn = db_connection()
        c = conn.cursor()

        if self.vehicle:
            fields = ', '.join(f'{k}=?' for k in data)
            c.execute(
                f'UPDATE vehicules SET {fields} WHERE id=?',
                list(data.values()) + [self.vehicle['id']]
            )
        else:
            add_vehicle(data)

        conn.commit()
        conn.close()

        if self.callback:
            self.callback()
        self.window.destroy()
