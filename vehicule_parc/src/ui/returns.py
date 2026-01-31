import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from ..models import find_vehicles, find_employees, get_connection
from ..db import get_connection as db_connection

FUEL_LEVELS = ['Réserve', 'Faible (1/4)', 'Moyen (1/2)', 'Bon (3/4)', 'Plein']
VEHICLE_CONDITIONS = ['Propre', 'Légèrement sale', 'Très sale']
VEHICLE_STATUS = ['disponible', 'à nettoyer', 'en maintenance']

class ReturnWindow:
    """Window for vehicle return/check-in"""
    def __init__(self, parent=None):
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title('Retour de Véhicule')
        self.window.geometry('900x750')
        self.selected_return = None
        self.build_ui()
        self.load_active_rentals()

    def build_ui(self):
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.pack(fill='both', expand=True)

        # Title
        title = ttk.Label(main_frame, text='Retour et Clôture de Sortie', 
                         font=('Arial', 14, 'bold'))
        title.pack(pady=10)

        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=5)

        # Filter frame
        filter_frame = ttk.LabelFrame(main_frame, text='Filtres', padding=10)
        filter_frame.pack(fill='x', pady=10)

        ttk.Label(filter_frame, text='Employé:').grid(row=0, column=0, sticky='w', padx=5)
        self.employee_filter_var = tk.StringVar(value='')
        self.employee_filter_combo = ttk.Combobox(filter_frame, textvariable=self.employee_filter_var, 
                                                   state='readonly', width=30)
        self.employee_filter_combo.grid(row=0, column=1, padx=5)
        self.employee_filter_combo.bind('<<ComboboxSelected>>', lambda e: self.load_active_rentals())

        ttk.Label(filter_frame, text='Véhicule:').grid(row=0, column=2, sticky='w', padx=5)
        self.vehicle_filter_var = tk.StringVar(value='')
        self.vehicle_filter_combo = ttk.Combobox(filter_frame, textvariable=self.vehicle_filter_var, 
                                                  state='readonly', width=30)
        self.vehicle_filter_combo.grid(row=0, column=3, padx=5)
        self.vehicle_filter_combo.bind('<<ComboboxSelected>>', lambda e: self.load_active_rentals())

        ttk.Button(filter_frame, text='Réinitialiser', command=self.reset_filters).grid(row=0, column=4, padx=5)

        self.load_filter_options()

        # Active rentals list
        list_frame = ttk.LabelFrame(main_frame, text='Sorties en Cours', padding=10)
        list_frame.pack(fill='both', expand=True, pady=10)

        columns = ('Immatriculation', 'Employé', 'Motif', 'Date Départ', 'Destination')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == 'Immatriculation':
                self.tree.column(col, width=100)
            elif col == 'Employé':
                self.tree.column(col, width=120)
            else:
                self.tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.tree.bind('<<TreeviewSelect>>', self.on_rental_selected)

        # Return details frame
        return_frame = ttk.LabelFrame(main_frame, text='Saisie du Retour', padding=10)
        return_frame.pack(fill='both', expand=True, pady=10)

        # Rental info (read-only)
        info_frame = ttk.LabelFrame(return_frame, text='Informations de la Sortie', padding=8)
        info_frame.pack(fill='x', pady=5)

        self.info_labels = {}
        info_fields = [
            ('Véhicule', 'vehicle_info'),
            ('Employé', 'employee_info'),
            ('Motif', 'motif_info'),
            ('Départ', 'departure_info'),
            ('KM Départ', 'km_depart_info'),
        ]

        for i, (label, key) in enumerate(info_fields):
            ttk.Label(info_frame, text=label + ':').grid(row=0, column=i*2, sticky='w', padx=5)
            self.info_labels[key] = ttk.Label(info_frame, text='', foreground='blue', font=('Arial', 9))
            self.info_labels[key].grid(row=0, column=i*2+1, sticky='w', padx=5)

        # Return data entry
        entry_frame = ttk.LabelFrame(return_frame, text='Données de Retour', padding=8)
        entry_frame.pack(fill='both', expand=True, pady=5)

        # Return mileage
        ttk.Label(entry_frame, text='Kilométrage au retour *').grid(row=0, column=0, sticky='w', pady=5)
        self.km_retour_var = tk.StringVar()
        self.km_retour_entry = ttk.Entry(entry_frame, textvariable=self.km_retour_var, width=15)
        self.km_retour_entry.grid(row=0, column=1, sticky='w', pady=5)
        self.km_retour_var.trace('w', self.calculate_distance)

        # Auto-calculated distance
        ttk.Label(entry_frame, text='Distance parcourue').grid(row=0, column=2, sticky='w', padx=20)
        self.distance_label = ttk.Label(entry_frame, text='0 km', foreground='green', font=('Arial', 10, 'bold'))
        self.distance_label.grid(row=0, column=3, sticky='w')

        # Duration (auto-calculated)
        ttk.Label(entry_frame, text='Durée de la sortie').grid(row=0, column=4, sticky='w', padx=20)
        self.duration_label = ttk.Label(entry_frame, text='N/A', foreground='green', font=('Arial', 10, 'bold'))
        self.duration_label.grid(row=0, column=5, sticky='w')

        # Vehicle condition
        ttk.Label(entry_frame, text='État du véhicule *').grid(row=1, column=0, sticky='w', pady=5)
        self.condition_var = tk.StringVar()
        condition_combo = ttk.Combobox(entry_frame, textvariable=self.condition_var, 
                                       values=VEHICLE_CONDITIONS, state='readonly', width=18)
        condition_combo.grid(row=1, column=1, sticky='ew', pady=5)

        # Fuel level
        ttk.Label(entry_frame, text='Niveau carburant *').grid(row=1, column=2, sticky='w', padx=20)
        self.fuel_var = tk.StringVar()
        fuel_combo = ttk.Combobox(entry_frame, textvariable=self.fuel_var, 
                                  values=FUEL_LEVELS, state='readonly', width=18)
        fuel_combo.grid(row=1, column=3, sticky='ew', pady=5)

        # New status
        ttk.Label(entry_frame, text='Nouveau statut *').grid(row=1, column=4, sticky='w', padx=20)
        self.new_status_var = tk.StringVar(value='disponible')
        status_combo = ttk.Combobox(entry_frame, textvariable=self.new_status_var, 
                                    values=VEHICLE_STATUS, state='readonly', width=15)
        status_combo.grid(row=1, column=5, sticky='ew', pady=5)

        # Damage report
        ttk.Label(entry_frame, text='Dommages observés').grid(row=2, column=0, sticky='nw', pady=5)
        self.damage_text = tk.Text(entry_frame, height=5, width=80)
        self.damage_text.grid(row=2, column=0, columnspan=6, sticky='ew', pady=5)

        entry_frame.columnconfigure(1, weight=1)
        entry_frame.columnconfigure(3, weight=1)
        entry_frame.columnconfigure(5, weight=1)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=15)
        ttk.Button(button_frame, text='Clôturer le Retour', command=self.save_return).pack(side='left', padx=5)
        ttk.Button(button_frame, text='Annuler', command=self.window.destroy).pack(side='left', padx=5)

    def load_filter_options(self):
        """Load employee and vehicle options for filters"""
        # Load employees
        employees = find_employees()
        employee_list = [''] + [f"{e.get('matricule')} - {e.get('nom')} {e.get('prenom')}" for e in employees]
        self.employee_filter_combo['values'] = employee_list

        # Load vehicles
        vehicles = find_vehicles()
        vehicle_list = [''] + [f"{v.get('immatriculation')} - {v.get('marque')} {v.get('modele')}" for v in vehicles]
        self.vehicle_filter_combo['values'] = vehicle_list

    def load_active_rentals(self):
        """Load active rentals (status 'en sortie' or 'réservée')"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = db_connection()
        c = conn.cursor()

        # Get active rentals
        c.execute('''SELECT sr.id, sr.vehicule_id, sr.employe_id, sr.motif, sr.destination,
                            sr.date_sortie_reelle, sr.heure_sortie_reelle, sr.km_depart,
                            v.immatriculation, v.marque, v.modele, e.nom, e.prenom
                     FROM sorties_reservations sr
                     JOIN vehicules v ON sr.vehicule_id = v.id
                     JOIN employes e ON sr.employe_id = e.id
                     WHERE sr.statut IN ('en sortie', 'réservée')
                     ORDER BY sr.date_sortie_reelle DESC''')

        rentals = c.fetchall()
        
        # Apply filters
        employee_filter = self.employee_filter_var.get()
        vehicle_filter = self.vehicle_filter_var.get()

        for rental in rentals:
            rental_id, veh_id, emp_id, motif, destination, date_out, time_out, km_out, immat, marque, modele, nom, prenom = rental

            # Apply employee filter
            if employee_filter and f"{emp_id}" not in str(emp_id):
                if f"{nom} {prenom}" not in employee_filter:
                    continue

            # Apply vehicle filter
            if vehicle_filter and immat not in vehicle_filter:
                continue

            date_str = date_out if date_out else 'N/A'
            self.tree.insert('', 'end', values=(immat, f"{nom} {prenom}", motif, date_str, destination))

        conn.close()

    def on_rental_selected(self, event=None):
        """Load selected rental details"""
        selection = self.tree.selection()
        if not selection:
            return

        # Get selected item values
        item = self.tree.item(selection[0])
        immat = item['values'][0]

        conn = db_connection()
        c = conn.cursor()

        # Get full rental details
        c.execute('''SELECT sr.id, sr.vehicule_id, sr.employe_id, sr.motif, 
                            COALESCE(sr.date_sortie_reelle, sr.date_sortie_prevue) as date_out,
                            COALESCE(sr.heure_sortie_reelle, sr.heure_sortie_prevue) as time_out,
                            sr.km_depart, sr.destination,
                            v.immatriculation, v.marque, v.modele, e.nom, e.prenom
                     FROM sorties_reservations sr
                     JOIN vehicules v ON sr.vehicule_id = v.id
                     JOIN employes e ON sr.employe_id = e.id
                     WHERE v.immatriculation = ? AND sr.statut IN ('en sortie', 'réservée')
                     ORDER BY sr.date_sortie_prevue DESC LIMIT 1''', (immat,))

        rental = c.fetchone()
        conn.close()

        if rental:
            rental_id, veh_id, emp_id, motif, date_out, time_out, km_out, destination, immat, marque, modele, nom, prenom = rental
            self.selected_return = {
                'id': rental_id,
                'vehicle_id': veh_id,
                'employee_id': emp_id,
                'immatriculation': immat,
                'marque': marque,
                'modele': modele,
                'employee_name': f"{nom} {prenom}",
                'motif': motif,
                'date_sortie': date_out,
                'time_sortie': time_out,
                'km_depart': km_out,
                'destination': destination
            }

            # Display rental info
            self.info_labels['vehicle_info'].config(text=f"{immat} - {marque} {modele}")
            self.info_labels['employee_info'].config(text=f"{nom} {prenom}")
            self.info_labels['motif_info'].config(text=motif)
            self.info_labels['departure_info'].config(text=f"{date_out} {time_out if time_out else ''}")
            self.info_labels['km_depart_info'].config(text=f"{km_out} km")

            # Clear return fields
            self.km_retour_var.set('')
            self.condition_var.set('')
            self.fuel_var.set('')
            self.new_status_var.set('disponible')
            self.damage_text.delete('1.0', tk.END)
            self.distance_label.config(text='0 km')
            self.duration_label.config(text='N/A')

    def calculate_distance(self, *args):
        """Calculate distance and duration automatically"""
        if not self.selected_return or not self.km_retour_var.get():
            return

        try:
            km_retour = int(self.km_retour_var.get())
            km_depart = self.selected_return['km_depart']
            distance = km_retour - km_depart
            self.distance_label.config(text=f"{distance} km")

            # Calculate duration
            date_out = self.selected_return['date_sortie']
            time_out = self.selected_return['time_sortie']
            
            if date_out and time_out:
                try:
                    departure = datetime.strptime(f"{date_out} {time_out}", '%Y-%m-%d %H:%M')
                    now = datetime.now()
                    delta = now - departure
                    
                    hours = delta.total_seconds() / 3600
                    days = delta.days
                    
                    if days > 0:
                        duration_str = f"{days}j {int(hours % 24)}h"
                    else:
                        duration_str = f"{int(hours)}h {int((hours % 1) * 60)}min"
                    
                    self.duration_label.config(text=duration_str)
                except:
                    pass
        except ValueError:
            self.distance_label.config(text='Km invalide')

    def reset_filters(self):
        """Reset all filters"""
        self.employee_filter_var.set('')
        self.vehicle_filter_var.set('')
        self.load_active_rentals()

    def validate_inputs(self):
        """Validate return data"""
        if not self.selected_return:
            messagebox.showerror('Erreur', 'Veuillez sélectionner une sortie')
            return False

        if not self.km_retour_var.get():
            messagebox.showerror('Erreur', 'Veuillez entrer le kilométrage au retour')
            return False

        if not self.condition_var.get():
            messagebox.showerror('Erreur', 'Veuillez sélectionner l\'état du véhicule')
            return False

        if not self.fuel_var.get():
            messagebox.showerror('Erreur', 'Veuillez sélectionner le niveau carburant')
            return False

        if not self.new_status_var.get():
            messagebox.showerror('Erreur', 'Veuillez sélectionner un nouveau statut')
            return False

        try:
            km_retour = int(self.km_retour_var.get())
            if km_retour < self.selected_return['km_depart']:
                messagebox.showerror('Erreur', 'Le kilométrage au retour ne peut pas être inférieur à celui au départ')
                return False
        except ValueError:
            messagebox.showerror('Erreur', 'Kilométrage invalide')
            return False

        return True

    def save_return(self):
        """Save vehicle return and update status"""
        if not self.validate_inputs():
            return

        try:
            conn = db_connection()
            c = conn.cursor()

            # Update rental record
            now = datetime.now()
            km_retour = int(self.km_retour_var.get())
            
            print(f"DEBUG: Updating rental {self.selected_return['id']}")
            c.execute('''UPDATE sorties_reservations 
                        SET date_retour_reelle = ?,
                            heure_retour_reelle = ?,
                            km_retour = ?,
                            etat_retour = ?,
                            niveau_carburant_retour = ?,
                            statut = ?
                        WHERE id = ?''', (
                now.strftime('%Y-%m-%d'),
                now.strftime('%H:%M:%S'),
                km_retour,
                self.condition_var.get(),
                self.fuel_var.get(),
                'clôturée',
                self.selected_return['id']
            ))

            print(f"DEBUG: Updating vehicle {self.selected_return['vehicle_id']}")
            # Update vehicle mileage and status
            c.execute('''UPDATE vehicules 
                        SET kilometrage_actuel = ?,
                            statut = ?
                        WHERE id = ?''', (
                km_retour,
                self.new_status_var.get(),
                self.selected_return['vehicle_id']
            ))

            conn.commit()
            print(f"DEBUG: Commit successful")
            conn.close()

            messagebox.showinfo('Succès', 
                f'Retour clôturé!\nVéhicule {self.selected_return["immatriculation"]} - Nouveau statut: {self.new_status_var.get()}')
            
            # Refresh list
            self.load_active_rentals()
            self.selected_return = None
            
        except Exception as e:
            print(f"DEBUG: Exception caught: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            messagebox.showerror('Erreur', f'Erreur lors de la clôture: {str(e)}')
