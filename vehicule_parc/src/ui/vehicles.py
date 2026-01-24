import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from ..models import add_vehicle, find_vehicles, get_connection
from ..db import get_connection as db_connection

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

class VehicleListWindow:
    """Main window for vehicle list, search, and management"""
    def __init__(self, parent=None):
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title('Gestion des Véhicules')
        self.root.geometry('1000x600')
        self.build_ui()
        self.load_vehicles()

    def build_ui(self):
        # Top search and filter frame
        search_frame = ttk.LabelFrame(self.root, text='Recherche et Filtres', padding=10)
        search_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(search_frame, text='Recherche:').grid(row=0, column=0, sticky='w', padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.load_vehicles())
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).grid(row=0, column=1, padx=5)

        ttk.Label(search_frame, text='Type:').grid(row=0, column=2, sticky='w', padx=5)
        self.type_var = tk.StringVar(value='')
        type_combo = ttk.Combobox(search_frame, textvariable=self.type_var, 
                                   values=[''] + VEHICLE_TYPES, state='readonly', width=15)
        type_combo.grid(row=0, column=3, padx=5)
        type_combo.bind('<<ComboboxSelected>>', lambda *args: self.load_vehicles())

        ttk.Label(search_frame, text='Statut:').grid(row=0, column=4, sticky='w', padx=5)
        self.status_var = tk.StringVar(value='')
        status_combo = ttk.Combobox(search_frame, textvariable=self.status_var, 
                                     values=[''] + list(STATUS_COLORS.keys()), state='readonly', width=15)
        status_combo.grid(row=0, column=5, padx=5)
        status_combo.bind('<<ComboboxSelected>>', lambda *args: self.load_vehicles())

        # Action buttons
        button_frame = ttk.Frame(search_frame)
        button_frame.grid(row=0, column=6, columnspan=2, padx=10)
        ttk.Button(button_frame, text='Ajouter', command=self.open_add_vehicle).pack(side='left', padx=2)
        ttk.Button(button_frame, text='Modifier', command=self.open_edit_vehicle).pack(side='left', padx=2)
        ttk.Button(button_frame, text='Détails', command=self.open_vehicle_detail).pack(side='left', padx=2)
        ttk.Button(button_frame, text='Supprimer', command=self.delete_vehicle).pack(side='left', padx=2)

        # Full fleet status alert
        self.alert_label = ttk.Label(self.root, text='', foreground='red', font=('Arial', 12, 'bold'))
        self.alert_label.pack(fill='x', padx=10, pady=5)

        # Tree view for vehicles
        tree_frame = ttk.Frame(self.root, padding=10)
        tree_frame.pack(fill='both', expand=True)

        columns = ('Immatriculation', 'Marque', 'Modèle', 'Type', 'Année', 'Statut', 'Service')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == 'Immatriculation':
                self.tree.column(col, width=100)
            elif col == 'Statut':
                self.tree.column(col, width=120)
            else:
                self.tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Status bar
        self.status_bar = ttk.Label(self.root, text='', relief='sunken')
        self.status_bar.pack(fill='x', side='bottom')

    def load_vehicles(self):
        """Load vehicles with current filters"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Configure tag styles
        style = ttk.Style()
        for status, color in STATUS_COLORS.items():
            style.configure(f'{status}.Treeview.Item', background=color)

        # Build filters
        filters = {}
        if self.type_var.get():
            filters['type_vehicule'] = self.type_var.get()
        if self.status_var.get():
            filters['statut'] = self.status_var.get()

        # Get vehicles
        search_text = self.search_var.get()
        vehicles = find_vehicles(filter_text=search_text if search_text else None, filters=filters if filters else None)

        # Check fleet status
        total = len(vehicles)
        available = sum(1 for v in vehicles if v.get('statut') == 'disponible')
        
        if total > 0 and available == 0:
            self.alert_label.config(text='Parc complet – Aucun véhicule de l\'entreprise disponible actuellement')
        else:
            self.alert_label.config(text='')

        # Insert vehicles
        for vehicle in vehicles:
            status = vehicle.get('statut', 'disponible')
            tag = status
            self.tree.insert('', 'end', 
                           values=(
                               vehicle.get('immatriculation'),
                               vehicle.get('marque'),
                               vehicle.get('modele'),
                               vehicle.get('type_vehicule'),
                               vehicle.get('annee'),
                               status,
                               vehicle.get('service_principal')
                           ),
                           tags=(tag,))

        self.status_bar.config(text=f'Total: {total} | Disponibles: {available}')

    def get_selected_vehicle(self):
        """Get the selected vehicle from the tree"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning('Sélection', 'Veuillez sélectionner un véhicule')
            return None
        immatriculation = self.tree.item(selection[0])['values'][0]
        vehicles = find_vehicles()
        for v in vehicles:
            if v.get('immatriculation') == immatriculation:
                return v
        return None

    def open_add_vehicle(self):
        """Open add vehicle form"""
        AddEditVehicleWindow(self.root, callback=self.load_vehicles)

    def open_edit_vehicle(self):
        """Open edit vehicle form"""
        vehicle = self.get_selected_vehicle()
        if vehicle:
            AddEditVehicleWindow(self.root, vehicle=vehicle, callback=self.load_vehicles)

    def open_vehicle_detail(self):
        """Open vehicle detail window"""
        vehicle = self.get_selected_vehicle()
        if vehicle:
            VehicleDetailWindow(self.root, vehicle)

    def delete_vehicle(self):
        """Delete selected vehicle"""
        vehicle = self.get_selected_vehicle()
        if not vehicle:
            return
        
        # Check for dependent records
        conn = db_connection()
        c = conn.cursor()
        
        vehicle_id = vehicle.get('id')
        
        # Check for sorties/réservations
        c.execute('SELECT COUNT(*) as count FROM sorties_reservations WHERE vehicule_id = ?', (vehicle_id,))
        sorties_count = c.fetchone()['count']
        
        # Check for maintenances
        c.execute('SELECT COUNT(*) as count FROM maintenances WHERE vehicule_id = ?', (vehicle_id,))
        maintenance_count = c.fetchone()['count']
        
        # Check for ravitaillements
        c.execute('SELECT COUNT(*) as count FROM ravitaillements WHERE vehicule_id = ?', (vehicle_id,))
        fuel_count = c.fetchone()['count']
        
        # Check for documents
        c.execute('SELECT COUNT(*) as count FROM documents WHERE vehicule_id = ?', (vehicle_id,))
        doc_count = c.fetchone()['count']
        
        # Check for permanent assignments
        c.execute('SELECT COUNT(*) as count FROM affectations_permanentes WHERE vehicule_id = ? AND date_fin IS NULL', (vehicle_id,))
        assign_count = c.fetchone()['count']
        
        conn.close()
        
        # Display warning if dependencies exist
        if sorties_count > 0 or maintenance_count > 0 or fuel_count > 0 or doc_count > 0 or assign_count > 0:
            msg = f"Impossible de supprimer {vehicle.get('immatriculation')} - Des éléments dépendants existent:\n\n"
            if sorties_count > 0:
                msg += f"• {sorties_count} sortie(s)/réservation(s)\n"
            if maintenance_count > 0:
                msg += f"• {maintenance_count} maintenance(s)\n"
            if fuel_count > 0:
                msg += f"• {fuel_count} ravitaillement(s)\n"
            if doc_count > 0:
                msg += f"• {doc_count} document(s)\n"
            if assign_count > 0:
                msg += f"• 1 affectation permanente active\n"
            
            msg += "\nSupprimez ces éléments d'abord."
            messagebox.showwarning('Impossible de supprimer', msg)
            return
        
        # Confirm deletion
        if messagebox.askyesno('Confirmer', f'Supprimer définitivement {vehicle.get("immatriculation")}?'):
            try:
                conn = db_connection()
                c = conn.cursor()
                c.execute('DELETE FROM vehicules WHERE id = ?', (vehicle_id,))
                conn.commit()
                conn.close()
                self.load_vehicles()
                messagebox.showinfo('Succès', f'Véhicule {vehicle.get("immatriculation")} supprimé')
            except Exception as e:
                messagebox.showerror('Erreur', f'Erreur lors de la suppression: {str(e)}')


class AddEditVehicleWindow:
    """Form for adding/editing vehicles"""
    def __init__(self, parent, vehicle=None, callback=None):
        self.window = tk.Toplevel(parent)
        self.window.title('Ajouter un véhicule' if not vehicle else 'Modifier un véhicule')
        self.window.geometry('600x700')
        self.vehicle = vehicle
        self.callback = callback
        self.build_ui()
        if vehicle:
            self.populate_fields()

    def build_ui(self):
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.pack(fill='both', expand=True)

        fields = [
            ('Immatriculation *', 'immatriculation', 'entry'),
            ('Marque *', 'marque', 'entry'),
            ('Modèle *', 'modele', 'entry'),
            ('Type *', 'type_vehicule', 'combobox', VEHICLE_TYPES),
            ('Année', 'annee', 'entry'),
            ('Date acquisition', 'date_acquisition', 'entry'),
            ('Kilométrage initial', 'kilometrage_actuel', 'entry'),
            ('Type carburant', 'carburant', 'combobox', FUEL_TYPES),
            ('Puissance fiscale', 'puissance_fiscale', 'entry'),
            ('Numéro châssis', 'numero_chassis', 'entry'),
            ('Service principal', 'service_principal', 'entry'),
            ('Type affectation', 'type_affectation', 'combobox', AFFECTATION_TYPES),
            ('Statut', 'statut', 'combobox', list(STATUS_COLORS.keys())),
            ('Seuil révision (km)', 'seuil_revision_km', 'entry'),
        ]

        self.entries = {}
        row = 0
        for field_info in fields:
            label = ttk.Label(main_frame, text=field_info[0])
            label.grid(row=row, column=0, sticky='w', pady=5)

            if field_info[2] == 'entry':
                entry = ttk.Entry(main_frame, width=40)
                entry.grid(row=row, column=1, sticky='ew', pady=5)
                self.entries[field_info[1]] = entry
            elif field_info[2] == 'combobox':
                combo = ttk.Combobox(main_frame, values=field_info[3], state='readonly', width=37)
                combo.grid(row=row, column=1, sticky='ew', pady=5)
                self.entries[field_info[1]] = combo

            row += 1

        # Photo path
        ttk.Label(main_frame, text='Photo du véhicule').grid(row=row, column=0, sticky='w', pady=5)
        photo_frame = ttk.Frame(main_frame)
        photo_frame.grid(row=row, column=1, sticky='ew', pady=5)
        self.photo_var = tk.StringVar()
        ttk.Entry(photo_frame, textvariable=self.photo_var, width=30).pack(side='left', fill='x', expand=True)
        ttk.Button(photo_frame, text='Parcourir', command=self.browse_photo, width=10).pack(side='left', padx=5)

        row += 1

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text='Enregistrer', command=self.save).pack(side='left', padx=5)
        ttk.Button(button_frame, text='Annuler', command=self.window.destroy).pack(side='left', padx=5)

        main_frame.columnconfigure(1, weight=1)

    def browse_photo(self):
        """Browse for photo file"""
        filename = filedialog.askopenfilename(filetypes=[('Images', '*.png *.jpg *.jpeg *.gif')])
        if filename:
            self.photo_var.set(filename)

    def populate_fields(self):
        """Populate fields with existing vehicle data"""
        for key, entry in self.entries.items():
            value = self.vehicle.get(key)
            if value:
                entry.delete(0, tk.END)
                entry.insert(0, str(value))
        
        if self.vehicle.get('photo_path'):
            self.photo_var.set(self.vehicle.get('photo_path'))

    def save(self):
        """Save vehicle data"""
        # Validate required fields
        required = ['immatriculation', 'marque', 'modele', 'type_vehicule']
        for field in required:
            if not self.entries[field].get():
                messagebox.showerror('Erreur', f'{field} est obligatoire')
                return

        data = {}
        for key, entry in self.entries.items():
            value = entry.get()
            data[key] = value if value else None

        data['photo_path'] = self.photo_var.get()

        try:
            if self.vehicle:
                # Update existing
                conn = db_connection()
                c = conn.cursor()
                update_fields = ', '.join([f'{k} = ?' for k in data.keys()])
                values = list(data.values()) + [self.vehicle.get('id')]
                c.execute(f'UPDATE vehicules SET {update_fields} WHERE id = ?', values)
                conn.commit()
                conn.close()
                messagebox.showinfo('Succès', 'Véhicule modifié')
            else:
                # Add new
                add_vehicle(data)
                messagebox.showinfo('Succès', 'Véhicule ajouté')

            if self.callback:
                self.callback()
            self.window.destroy()
        except Exception as e:
            messagebox.showerror('Erreur', f'Erreur lors de l\'enregistrement: {str(e)}')


class VehicleDetailWindow:
    """Detailed view of a vehicle with history"""
    def __init__(self, parent, vehicle):
        self.window = tk.Toplevel(parent)
        self.window.title(f'Détails - {vehicle.get("immatriculation")}')
        self.window.geometry('800x600')
        self.vehicle = vehicle
        self.build_ui()
        self.load_history()

    def build_ui(self):
        # Notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # General info tab
        general_frame = ttk.Frame(notebook, padding=10)
        notebook.add(general_frame, text='Informations générales')

        fields = [
            ('Immatriculation', 'immatriculation'),
            ('Marque', 'marque'),
            ('Modèle', 'modele'),
            ('Type', 'type_vehicule'),
            ('Année', 'annee'),
            ('Date acquisition', 'date_acquisition'),
            ('Kilométrage actuel', 'kilometrage_actuel'),
            ('Carburant', 'carburant'),
            ('Puissance fiscale', 'puissance_fiscale'),
            ('Numéro châssis', 'numero_chassis'),
            ('Service principal', 'service_principal'),
            ('Type affectation', 'type_affectation'),
            ('Statut', 'statut'),
            ('Seuil révision', 'seuil_revision_km'),
        ]

        for i, (label, key) in enumerate(fields):
            ttk.Label(general_frame, text=label + ':').grid(row=i, column=0, sticky='w', pady=5)
            ttk.Label(general_frame, text=str(self.vehicle.get(key, ''))).grid(row=i, column=1, sticky='w', pady=5)

        # History tab
        history_frame = ttk.Frame(notebook, padding=10)
        notebook.add(history_frame, text='Historique')

        ttk.Label(history_frame, text='Sorties et réservations').pack()
        self.history_tree = ttk.Treeview(history_frame, columns=('Date Sortie', 'Employé', 'Motif', 'KM Départ', 'KM Retour', 'Statut'), 
                                        show='headings', height=15)
        for col in self.history_tree['columns']:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(history_frame, orient='vertical', command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        self.history_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def load_history(self):
        """Load vehicle history"""
        conn = db_connection()
        c = conn.cursor()
        c.execute('''SELECT sr.date_sortie_reelle, e.nom, sr.motif, sr.km_depart, sr.km_retour, sr.statut
                     FROM sorties_reservations sr
                     LEFT JOIN employes e ON sr.employe_id = e.id
                     WHERE sr.vehicule_id = ?
                     ORDER BY sr.date_sortie_reelle DESC''', (self.vehicle.get('id'),))
        
        for row in c.fetchall():
            self.history_tree.insert('', 'end', values=(row[0], row[1], row[2], row[3], row[4], row[5]))
        
        conn.close()
