import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from ..models import find_vehicles, find_employees, get_connection
from ..db import get_connection as db_connection

MOTIFS = [
    'Déplacement professionnel',
    'Rendez-vous client',
    'Livraison',
    'Visite site',
    'Formation',
    'Conférence',
    'Réunion interne',
    'Autre'
]

class ReservationWindow:
    """Window for vehicle reservation/checkout"""
    def __init__(self, parent=None):
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title('Nouvelle Réservation - Sortie de Véhicule')
        self.window.geometry('700x650')
        self.build_ui()

    def build_ui(self):
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.pack(fill='both', expand=True)

        # Title
        title = ttk.Label(main_frame, text='Réservation et Sortie de Véhicule', 
                         font=('Arial', 14, 'bold'))
        title.pack(pady=10)

        # Separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=5)

        # Vehicle selection
        vehicle_frame = ttk.LabelFrame(main_frame, text='Sélection du Véhicule', padding=10)
        vehicle_frame.pack(fill='x', pady=10)

        ttk.Label(vehicle_frame, text='Véhicule disponible *').pack(anchor='w', pady=5)
        self.vehicle_var = tk.StringVar()
        self.vehicle_combo = ttk.Combobox(vehicle_frame, textvariable=self.vehicle_var, 
                                          state='readonly', width=70)
        self.vehicle_combo.pack(fill='x', pady=5)
        self.vehicle_combo.bind('<<ComboboxSelected>>', self.on_vehicle_selected)
        self.load_available_vehicles()

        # Vehicle details
        ttk.Label(vehicle_frame, text='Détails:').pack(anchor='w', pady=5)
        self.vehicle_details = ttk.Label(vehicle_frame, text='', foreground='blue')
        self.vehicle_details.pack(anchor='w', padx=20)

        # Employee selection
        employee_frame = ttk.LabelFrame(main_frame, text='Employé Conducteur', padding=10)
        employee_frame.pack(fill='x', pady=10)

        ttk.Label(employee_frame, text='Employé autorisé *').pack(anchor='w', pady=5)
        self.employee_var = tk.StringVar()
        self.employee_combo = ttk.Combobox(employee_frame, textvariable=self.employee_var, 
                                           state='readonly', width=70)
        self.employee_combo.pack(fill='x', pady=5)
        self.load_authorized_employees()

        # Trip details
        trip_frame = ttk.LabelFrame(main_frame, text='Détails du Déplacement', padding=10)
        trip_frame.pack(fill='both', expand=True, pady=10)

        # Motif
        ttk.Label(trip_frame, text='Motif *').grid(row=0, column=0, sticky='w', pady=5)
        self.motif_var = tk.StringVar()
        motif_combo = ttk.Combobox(trip_frame, textvariable=self.motif_var, 
                                   values=MOTIFS, state='readonly', width=50)
        motif_combo.grid(row=0, column=1, sticky='ew', pady=5)

        # Destination
        ttk.Label(trip_frame, text='Destination *').grid(row=1, column=0, sticky='w', pady=5)
        self.destination_var = tk.StringVar()
        ttk.Entry(trip_frame, textvariable=self.destination_var, width=53).grid(row=1, column=1, sticky='ew', pady=5)

        # Expected departure date and time
        ttk.Label(trip_frame, text='Date départ prévue *').grid(row=2, column=0, sticky='w', pady=5)
        date_time_frame = ttk.Frame(trip_frame)
        date_time_frame.grid(row=2, column=1, sticky='ew', pady=5)
        self.date_sortie_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(date_time_frame, textvariable=self.date_sortie_var, width=15).pack(side='left', padx=5)
        ttk.Label(date_time_frame, text='Heure:').pack(side='left', padx=5)
        self.time_sortie_var = tk.StringVar(value=datetime.now().strftime('%H:%M'))
        ttk.Entry(date_time_frame, textvariable=self.time_sortie_var, width=10).pack(side='left', padx=5)

        # Expected return date and time
        ttk.Label(trip_frame, text='Date retour prévue *').grid(row=3, column=0, sticky='w', pady=5)
        date_time_frame2 = ttk.Frame(trip_frame)
        date_time_frame2.grid(row=3, column=1, sticky='ew', pady=5)
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        self.date_retour_var = tk.StringVar(value=tomorrow)
        ttk.Entry(date_time_frame2, textvariable=self.date_retour_var, width=15).pack(side='left', padx=5)
        ttk.Label(date_time_frame2, text='Heure:').pack(side='left', padx=5)
        self.time_retour_var = tk.StringVar(value='18:00')
        ttk.Entry(date_time_frame2, textvariable=self.time_retour_var, width=10).pack(side='left', padx=5)

        # Initial mileage
        ttk.Label(trip_frame, text='Kilométrage au départ *').grid(row=4, column=0, sticky='w', pady=5)
        self.km_depart_var = tk.StringVar()
        ttk.Entry(trip_frame, textvariable=self.km_depart_var, width=53).grid(row=4, column=1, sticky='ew', pady=5)

        # Notes
        ttk.Label(trip_frame, text='Remarques').grid(row=5, column=0, sticky='nw', pady=5)
        self.remarks_text = tk.Text(trip_frame, height=4, width=50)
        self.remarks_text.grid(row=5, column=1, sticky='ew', pady=5)

        trip_frame.columnconfigure(1, weight=1)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=15)
        ttk.Button(button_frame, text='Réserver et Sortir', command=self.save_reservation).pack(side='left', padx=5)
        ttk.Button(button_frame, text='Annuler', command=self.window.destroy).pack(side='left', padx=5)

    def load_available_vehicles(self):
        """Load only available vehicles"""
        vehicles = find_vehicles()
        available = [v for v in vehicles if v.get('statut') == 'disponible']
        
        display_list = []
        self.vehicle_map = {}
        
        for v in available:
            display = f"{v.get('immatriculation')} - {v.get('marque')} {v.get('modele')} ({v.get('annee')})"
            display_list.append(display)
            self.vehicle_map[display] = v
        
        self.vehicle_combo['values'] = display_list
        
        if not display_list:
            messagebox.showwarning('Aucun véhicule', 'Aucun véhicule disponible actuellement')

    def load_authorized_employees(self):
        """Load only authorized employees"""
        employees = find_employees()
        authorized = [e for e in employees if e.get('autorise_conduire')]
        
        display_list = []
        self.employee_map = {}
        
        for e in authorized:
            display = f"{e.get('matricule')} - {e.get('nom')} {e.get('prenom')}"
            display_list.append(display)
            self.employee_map[display] = e
        
        self.employee_combo['values'] = display_list

    def on_vehicle_selected(self, event=None):
        """Display vehicle details when selected"""
        if self.vehicle_var.get() in self.vehicle_map:
            vehicle = self.vehicle_map[self.vehicle_var.get()]
            details = f"Marque: {vehicle.get('marque')}, Modèle: {vehicle.get('modele')}, Type: {vehicle.get('type_vehicule')}, Carburant: {vehicle.get('carburant')}"
            self.vehicle_details.config(text=details)
            # Auto-fill mileage from vehicle's current mileage
            self.km_depart_var.set(str(vehicle.get('kilometrage_actuel', 0)))

    def validate_inputs(self):
        """Validate all required fields"""
        if not self.vehicle_var.get():
            messagebox.showerror('Erreur', 'Veuillez sélectionner un véhicule')
            return False
        
        if not self.employee_var.get():
            messagebox.showerror('Erreur', 'Veuillez sélectionner un employé')
            return False
        
        if not self.motif_var.get():
            messagebox.showerror('Erreur', 'Veuillez sélectionner un motif')
            return False
        
        if not self.destination_var.get():
            messagebox.showerror('Erreur', 'Veuillez entrer une destination')
            return False
        
        if not self.km_depart_var.get():
            messagebox.showerror('Erreur', 'Veuillez entrer le kilométrage au départ')
            return False
        
        # Validate dates
        try:
            datetime.strptime(self.date_sortie_var.get(), '%Y-%m-%d')
            datetime.strptime(self.date_retour_var.get(), '%Y-%m-%d')
            datetime.strptime(self.time_sortie_var.get(), '%H:%M')
            datetime.strptime(self.time_retour_var.get(), '%H:%M')
        except ValueError:
            messagebox.showerror('Erreur', 'Format de date/heure invalide (YYYY-MM-DD et HH:MM)')
            return False
        
        # Validate mileage is numeric
        try:
            int(self.km_depart_var.get())
        except ValueError:
            messagebox.showerror('Erreur', 'Le kilométrage doit être un nombre')
            return False
        
        return True

    def save_reservation(self):
        """Save reservation and update vehicle status"""
        if not self.validate_inputs():
            return
        
        try:
            vehicle = self.vehicle_map[self.vehicle_var.get()]
            employee = self.employee_map[self.employee_var.get()]
            
            conn = db_connection()
            c = conn.cursor()
            
            # Insert reservation
            date_sortie_prevue = f"{self.date_sortie_var.get()} {self.time_sortie_var.get()}:00"
            date_retour_prevue = f"{self.date_retour_var.get()} {self.time_retour_var.get()}:00"
            
            c.execute('''INSERT INTO sorties_reservations (
                vehicule_id, employe_id, date_sortie_prevue, heure_sortie_prevue,
                date_retour_prevue, heure_retour_prevue, km_depart, motif, destination,
                statut
            ) VALUES (?,?,?,?,?,?,?,?,?,?)''', (
                vehicle.get('id'),
                employee.get('id'),
                self.date_sortie_var.get(),
                self.time_sortie_var.get(),
                self.date_retour_var.get(),
                self.time_retour_var.get(),
                int(self.km_depart_var.get()),
                self.motif_var.get(),
                self.destination_var.get(),
                'réservée'
            ))
            
            # Update vehicle status to 'en sortie'
            c.execute('UPDATE vehicules SET statut = ? WHERE id = ?', 
                     ('en sortie', vehicle.get('id')))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo('Succès', 
                f'Réservation créée!\nVéhicule {vehicle.get("immatriculation")} réservé pour {employee.get("nom")} {employee.get("prenom")}')
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror('Erreur', f'Erreur lors de la réservation: {str(e)}')
