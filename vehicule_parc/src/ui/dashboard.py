import tkinter as tk
from tkinter import ttk, messagebox
from ..models import get_dashboard_counts, find_vehicles
from .vehicles import VehicleListWindow
from .employees import EmployeeListWindow
from .reservations import ReservationWindow
from .returns import ReturnWindow
from .maintenance import MaintenanceWindow
from .fuel import FuelWindow
from .alerts import AlertsWindow
from .statistics import StatisticsWindow


STATUS_COLORS = {
    'disponible': '#d4f8d4',
    'en sortie': '#ffe7c6',
    'en maintenance': '#ffd6d6',
    'immobilisé': '#ffb3b3',
    'panne': '#ff9999',
    'à nettoyer': '#d6ecff'
}


class DashboardApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Tableau de bord - Gestion parc automobile')
        self.root.geometry('1000x600')
        self.build_ui()
        self.refresh_dashboard()

    # ======================================================
    # UI
    # ======================================================
    def build_ui(self):
        # ================= MENU =================
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Fichier', menu=file_menu)
        file_menu.add_command(label='Quitter', command=self.root.quit)

        mgmt_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Gestion', menu=mgmt_menu)
        mgmt_menu.add_command(label='Gestion des Véhicules', command=self.open_vehicles)
        mgmt_menu.add_command(label='Gestion des Employés', command=self.open_employees)
        mgmt_menu.add_separator()
        mgmt_menu.add_command(label='Réservations', command=self.open_reservations)
        mgmt_menu.add_command(label='Retours', command=self.open_returns)

        # ================= TOP SUMMARY =================
        self.top = ttk.LabelFrame(self.root, text='Résumé du parc', padding=10)
        self.top.pack(fill='x', padx=10, pady=5)

        self.lbl_total = ttk.Label(self.top, font=('Arial', 11, 'bold'))
        self.lbl_available = ttk.Label(self.top, font=('Arial', 11, 'bold'))
        self.lbl_in_use = ttk.Label(self.top, font=('Arial', 11, 'bold'))
        self.lbl_maintenance = ttk.Label(self.top, font=('Arial', 11, 'bold'))

        self.lbl_total.pack(side='left', padx=15)
        self.lbl_available.pack(side='left', padx=15)
        self.lbl_in_use.pack(side='left', padx=15)
        self.lbl_maintenance.pack(side='left', padx=15)

        ttk.Button(
            self.top,
            text='🔄 Rafraîchir',
            command=self.refresh_dashboard
        ).pack(side='right', padx=10)

        self.alert_label = ttk.Label(
            self.root,
            foreground='red',
            font=('Arial', 12, 'bold')
        )
        self.alert_label.pack(fill='x', padx=10)

        # ================= QUICK ACTIONS =================
        actions = ttk.LabelFrame(self.root, text='Actions rapides', padding=10)
        actions.pack(fill='x', padx=10, pady=5)

        ttk.Button(actions, text='Gestion Véhicules', width=20, command=self.open_vehicles).pack(side='left', padx=5)
        ttk.Button(actions, text='Gestion Employés', width=20, command=self.open_employees).pack(side='left', padx=5)
        ttk.Button(actions, text='Nouvelle Réservation', width=20, command=self.open_reservations).pack(side='left', padx=5)
        ttk.Button(actions, text='Retour Véhicule', width=20, command=self.open_returns).pack(side='left', padx=5)
        ttk.Button(actions, text='Enregistrement Maintenance', width=22, command=self.open_maintenance).pack(side='left', padx=5)
        ttk.Button(actions, text='Ravitaillement Carburant', width=22, command=self.open_fuel).pack(side='left', padx=5)
        ttk.Button(actions, text='Alertes / Échéances', width=20, command=self.open_alerts).pack(side='left', padx=5)
        ttk.Button(actions, text='Statistiques & Rapports', width=22, command=self.open_statistics).pack(side='left', padx=5)

        # ================= VEHICLE LIST =================
        tree_frame = ttk.LabelFrame(self.root, text='Véhicules', padding=10)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        columns = ('immatriculation', 'marque', 'modele', 'statut', 'service')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)

        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=160)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    # ======================================================
    # REFRESH GLOBAL
    # ======================================================
    def refresh_dashboard(self):
        """Recharge TOUT le dashboard"""
        self.refresh_counts()
        self.load_vehicles()

    def refresh_counts(self):
        counts = get_dashboard_counts()

        self.lbl_total.config(text=f"Total véhicules : {counts['total']}")
        self.lbl_available.config(text=f"Disponibles : {counts['available']}")
        self.lbl_in_use.config(text=f"En sortie : {counts['in_use']}")
        self.lbl_maintenance.config(text=f"En maintenance : {counts['maintenance']}")

        if counts['total'] > 0 and counts['available'] == 0:
            self.alert_label.config(
                text="Parc complet – Aucun véhicule de l'entreprise disponible actuellement"
            )
        else:
            self.alert_label.config(text='')

    # ======================================================
    # VEHICLES LIST
    # ======================================================
    def load_vehicles(self):
        self.tree.delete(*self.tree.get_children())

        for row in find_vehicles():
            status = row.get('statut') or 'disponible'
            self.tree.insert(
                '',
                'end',
                values=(
                    row.get('immatriculation'),
                    row.get('marque'),
                    row.get('modele'),
                    status,
                    row.get('service_principal')
                ),
                tags=(status,)
            )

        for status, color in STATUS_COLORS.items():
            self.tree.tag_configure(status, background=color)

    # ======================================================
    # NAVIGATION
    # ======================================================
    def open_vehicles(self):
        VehicleListWindow(self.root)

    def open_employees(self):
        EmployeeListWindow(self.root)

    def open_reservations(self):
        ReservationWindow(self.root)

    def open_returns(self):
        ReturnWindow(self.root)

    def open_maintenance(self):
        MaintenanceWindow(self.root)

    def open_fuel(self):
        FuelWindow(self.root)

    def open_alerts(self):
        AlertsWindow(self.root)

    def open_statistics(self):
        StatisticsWindow(self.root)

    # ======================================================
    # RUN
    # ======================================================
    def run(self):
        self.root.mainloop()
