import tkinter as tk
from tkinter import ttk, messagebox
from ..db import get_connection
from ..models import find_vehicles, find_employees


class FuelWindow:
    def __init__(self, parent):
        self.root = tk.Toplevel(parent)
        self.root.title('Ravitaillement Carburant')
        self.root.geometry('640x380')
        self.build_ui()

    def build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text='Véhicule').grid(row=0, column=0, sticky='w')
        self.cmb_vehicle = ttk.Combobox(frame, state='readonly')
        self.cmb_vehicle.grid(row=0, column=1, sticky='ew')

        ttk.Label(frame, text='Employé').grid(row=1, column=0, sticky='w')
        self.cmb_employee = ttk.Combobox(frame, state='readonly')
        self.cmb_employee.grid(row=1, column=1, sticky='ew')

        ttk.Label(frame, text='Date (YYYY-MM-DD)').grid(row=2, column=0, sticky='w')
        self.entry_date = ttk.Entry(frame)
        self.entry_date.grid(row=2, column=1, sticky='ew')

        ttk.Label(frame, text='Quantité (L)').grid(row=3, column=0, sticky='w')
        self.entry_qty = ttk.Entry(frame)
        self.entry_qty.grid(row=3, column=1, sticky='ew')

        ttk.Label(frame, text='Coût total').grid(row=4, column=0, sticky='w')
        self.entry_cost = ttk.Entry(frame)
        self.entry_cost.grid(row=4, column=1, sticky='ew')

        ttk.Label(frame, text='Station').grid(row=5, column=0, sticky='w')
        self.entry_station = ttk.Entry(frame)
        self.entry_station.grid(row=5, column=1, sticky='ew')

        ttk.Label(frame, text='Kilométrage au plein').grid(row=6, column=0, sticky='w')
        self.entry_km = ttk.Entry(frame)
        self.entry_km.grid(row=6, column=1, sticky='ew')

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text='Enregistrer', command=self.save_fuel).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Annuler', command=self.root.destroy).pack(side='left', padx=5)

        frame.columnconfigure(1, weight=1)
        self.load_data()

    def load_data(self):
        vehicles = find_vehicles()
        self.veh_map = {f"{r['immatriculation']} - {r.get('marque','')} {r.get('modele','')}": r['id'] for r in vehicles}
        self.cmb_vehicle['values'] = list(self.veh_map.keys())

        employees = find_employees()
        self.emp_map = {f"{e['matricule']} - {e['nom']} {e['prenom']}": e['id'] for e in employees}
        self.cmb_employee['values'] = list(self.emp_map.keys())

    def save_fuel(self):
        veh_sel = self.cmb_vehicle.get()
        emp_sel = self.cmb_employee.get()
        if not veh_sel:
            messagebox.showerror('Erreur', 'Sélectionner un véhicule')
            return
        veh_id = self.veh_map[veh_sel]
        emp_id = self.emp_map.get(emp_sel)
        date = self.entry_date.get().strip()
        try:
            qty = float(self.entry_qty.get().strip() or 0.0)
        except ValueError:
            messagebox.showerror('Erreur', 'Quantité invalide')
            return
        try:
            cost = float(self.entry_cost.get().strip() or 0.0)
        except ValueError:
            messagebox.showerror('Erreur', 'Coût invalide')
            return
        station = self.entry_station.get().strip()
        try:
            km = int(self.entry_km.get().strip() or 0)
        except ValueError:
            messagebox.showerror('Erreur', 'Kilométrage invalide')
            return

        conn = get_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO ravitaillements (vehicule_id, employe_id, date, quantite_litres, cout, station, kilometrage)
                     VALUES (?,?,?,?,?,?,?)''', (veh_id, emp_id, date, qty, cost, station, km))

        # compute consumption average since last refill if possible
        c.execute('SELECT kilometrage FROM ravitaillements WHERE vehicule_id = ? ORDER BY id DESC LIMIT 2', (veh_id,))
        rows = c.fetchall()
        avg_msg = ''
        if len(rows) >= 2:
            try:
                last_km = rows[1][0]
                distance = km - last_km
                if distance > 0:
                    cons = (qty / distance) * 100
                    avg_msg = f'Consommation moyenne calculée: {cons:.2f} L/100 km'
            except Exception:
                avg_msg = ''

        # update vehicle kilometrage if greater
        c.execute('SELECT kilometrage_actuel FROM vehicules WHERE id = ?', (veh_id,))
        r = c.fetchone()
        if r and km > (r['kilometrage_actuel'] or 0):
            c.execute('UPDATE vehicules SET kilometrage_actuel = ? WHERE id = ?', (km, veh_id))

        conn.commit()
        conn.close()
        messagebox.showinfo('Succès', 'Ravitaillement enregistré' + ('\n' + avg_msg if avg_msg else ''))
        self.root.destroy()
