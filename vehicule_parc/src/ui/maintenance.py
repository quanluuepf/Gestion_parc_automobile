import tkinter as tk
from tkinter import ttk, messagebox
from ..db import get_connection
from ..models import find_vehicles

INTERVENTION_TYPES = ['Vidange', 'Pneus', 'Freins', 'Réparation', 'Contrôle technique', 'Autre']


class MaintenanceWindow:
    def __init__(self, parent):
        self.root = tk.Toplevel(parent)
        self.root.title('Enregistrement Maintenance')
        self.root.geometry('600x420')
        self.build_ui()

    def build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text='Véhicule').grid(row=0, column=0, sticky='w')
        self.cmb_vehicle = ttk.Combobox(frame, state='readonly')
        self.cmb_vehicle.grid(row=0, column=1, sticky='ew')

        ttk.Label(frame, text='Type intervention').grid(row=1, column=0, sticky='w')
        self.cmb_type = ttk.Combobox(frame, values=INTERVENTION_TYPES, state='readonly')
        self.cmb_type.grid(row=1, column=1, sticky='ew')

        ttk.Label(frame, text='Date (YYYY-MM-DD)').grid(row=2, column=0, sticky='w')
        self.entry_date = ttk.Entry(frame)
        self.entry_date.grid(row=2, column=1, sticky='ew')

        ttk.Label(frame, text='Kilométrage').grid(row=3, column=0, sticky='w')
        self.entry_km = ttk.Entry(frame)
        self.entry_km.grid(row=3, column=1, sticky='ew')

        ttk.Label(frame, text='Coût TTC').grid(row=4, column=0, sticky='w')
        self.entry_cost = ttk.Entry(frame)
        self.entry_cost.grid(row=4, column=1, sticky='ew')

        ttk.Label(frame, text='Prestataire').grid(row=5, column=0, sticky='w')
        self.entry_prest = ttk.Entry(frame)
        self.entry_prest.grid(row=5, column=1, sticky='ew')

        ttk.Label(frame, text='Remarques').grid(row=6, column=0, sticky='nw')
        self.txt_rem = tk.Text(frame, height=5)
        self.txt_rem.grid(row=6, column=1, sticky='ew')

        # Next due: manual or automatic
        ttk.Label(frame, text='Prochaine échéance (manuelle)').grid(row=7, column=0, sticky='w')
        self.entry_next = ttk.Entry(frame)
        self.entry_next.grid(row=7, column=1, sticky='ew')

        self.mark_maintenance_var = tk.IntVar()
        ttk.Checkbutton(frame, text='Marquer véhicule en maintenance', variable=self.mark_maintenance_var).grid(row=8, column=1, sticky='w')

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text='Enregistrer', command=self.save_maintenance).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Annuler', command=self.root.destroy).pack(side='left', padx=5)

        frame.columnconfigure(1, weight=1)
        self.load_vehicles()

    def load_vehicles(self):
        rows = find_vehicles()
        self.vehicles = {f"{r['immatriculation']} - {r.get('marque','')} {r.get('modele','')}": r['id'] for r in rows}
        self.cmb_vehicle['values'] = list(self.vehicles.keys())

    def save_maintenance(self):
        sel = self.cmb_vehicle.get()
        if not sel:
            messagebox.showerror('Erreur', 'Sélectionner un véhicule')
            return
        veh_id = self.vehicles[sel]
        type_int = self.cmb_type.get() or 'Autre'
        date = self.entry_date.get().strip()
        try:
            km = int(self.entry_km.get().strip() or 0)
        except ValueError:
            messagebox.showerror('Erreur', 'Kilométrage invalide')
            return
        try:
            cost = float(self.entry_cost.get().strip() or 0.0)
        except ValueError:
            messagebox.showerror('Erreur', 'Coût invalide')
            return
        prest = self.entry_prest.get().strip()
        remarques = self.txt_rem.get('1.0', 'end').strip()
        next_due = self.entry_next.get().strip() or None

        conn = get_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO maintenances (vehicule_id, date, type_intervention, kilometrage, cout, prestataire, remarques, date_prochaine_echeance)
                     VALUES (?,?,?,?,?,?,?,?)''', (veh_id, date, type_int, km, cost, prest, remarques, next_due))
        if self.mark_maintenance_var.get():
            c.execute('UPDATE vehicules SET statut = ? WHERE id = ?', ('en maintenance', veh_id))
        conn.commit()
        conn.close()
        messagebox.showinfo('Succès', 'Maintenance enregistrée')
        self.root.destroy()
