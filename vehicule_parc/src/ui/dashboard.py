import tkinter as tk
from tkinter import ttk
from ..models import get_dashboard_counts, find_vehicles
from .vehicles import VehicleListWindow
from .employees import EmployeeListWindow
from .reservations import ReservationWindow
from .returns import ReturnWindow

STATUS_COLORS = {
    'disponible': '#d4f8d4',
    'en sortie': '#ffe7c6',
    'en maintenance': '#ffd6d6',
    'immobilisé': '#ffb3b3'
}

class DashboardApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Tableau de bord - Gestion parc automobile')
        self.root.geometry('1000x600')
        self.build_ui()

    def build_ui(self):
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Fichier', menu=file_menu)
        file_menu.add_command(label='Quitter', command=self.root.quit)

        # Management menu
        mgmt_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Gestion', menu=mgmt_menu)
        mgmt_menu.add_command(label='Gestion des Véhicules', command=self.open_vehicles)
        mgmt_menu.add_command(label='Gestion des Employés', command=self.open_employees)
        mgmt_menu.add_separator()
        mgmt_menu.add_command(label='Réservations', command=self.open_reservations)
        mgmt_menu.add_command(label='Retours', command=self.open_returns)
        mgmt_menu.add_separator()
        mgmt_menu.add_command(label='Maintenance', command=self.placeholder)
        mgmt_menu.add_command(label='Ravitaillement', command=self.placeholder)

        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Rapports', menu=reports_menu)
        reports_menu.add_command(label='Statistiques', command=self.placeholder)
        reports_menu.add_command(label='Export', command=self.placeholder)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='?', menu=help_menu)
        help_menu.add_command(label='À propos', command=self.placeholder)

        # Top stats frame
        top = ttk.LabelFrame(self.root, text='Résumé du parc', padding=10)
        top.pack(fill='x', padx=10, pady=5)
        
        counts = get_dashboard_counts()
        ttk.Label(top, text=f"Total véhicules: {counts['total']}", font=('Arial', 11, 'bold')).pack(side='left', padx=15)
        ttk.Label(top, text=f"Disponibles: {counts['available']}", font=('Arial', 11, 'bold')).pack(side='left', padx=15)
        ttk.Label(top, text=f"En sortie: {counts['in_use']}", font=('Arial', 11, 'bold')).pack(side='left', padx=15)
        ttk.Label(top, text=f"En maintenance: {counts['maintenance']}", font=('Arial', 11, 'bold')).pack(side='left', padx=15)

        # Alert if full fleet
        if counts['available'] == 0 and counts['total'] > 0:
            alert = ttk.Label(self.root, text='Parc complet – Aucun véhicule de l\'entreprise disponible actuellement', 
                            foreground='red', font=('Arial', 12, 'bold'))
            alert.pack(fill='x', padx=10, pady=5)

        # Quick actions frame
        actions_frame = ttk.LabelFrame(self.root, text='Actions rapides', padding=10)
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(actions_frame, text='Gestion Véhicules', command=self.open_vehicles, width=20).pack(side='left', padx=5)
        ttk.Button(actions_frame, text='Gestion Employés', command=self.open_employees, width=20).pack(side='left', padx=5)
        ttk.Button(actions_frame, text='Nouvelle Réservation', command=self.open_reservations, width=20).pack(side='left', padx=5)
        ttk.Button(actions_frame, text='Retour Véhicule', command=self.open_returns, width=20).pack(side='left', padx=5)

        # Vehicle list frame
        tree_frame = ttk.LabelFrame(self.root, text='Véhicules disponibles', padding=10)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        columns = ('immatriculation','marque','modele','statut','service')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.load_vehicles()

    def load_vehicles(self):
        """Load and display available vehicles"""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for row in find_vehicles():
            status = row.get('statut') or 'disponible'
            tag = status
            self.tree.insert('', 'end', values=(row.get('immatriculation'), row.get('marque'), row.get('modele'), status, row.get('service_principal')), tags=(tag,))
            self.tree.tag_configure(tag, background=STATUS_COLORS.get(status, 'white'))

    def open_vehicles(self):
        """Open vehicle management window"""
        VehicleListWindow(self.root)

    def open_employees(self):
        """Open employee management window"""
        EmployeeListWindow(self.root)

    def open_reservations(self):
        """Open reservation window"""
        ReservationWindow(self.root)

    def open_returns(self):
        """Open vehicle return window"""
        ReturnWindow(self.root)

    def placeholder(self):
        """Placeholder for future features"""
        from tkinter import messagebox
        messagebox.showinfo('Bientôt disponible', 'Cette fonctionnalité sera bientôt disponible')

    def run(self):
        self.root.mainloop()
