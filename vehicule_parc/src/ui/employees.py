import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from ..models import add_employee, find_employees
from ..db import get_connection as db_connection

# Couleurs statut permis
LICENSE_COLORS = {
    'valid': '#90EE90',
    'warning': '#FFD700',
    'expired': '#FF6347'
}


class EmployeeListWindow:
    def __init__(self, parent=None):
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title('Gestion des Employés')
        self.root.geometry('1000x600')
        self.build_ui()
        self.load_employees()

    # ================= UI =================
    def build_ui(self):
        search_frame = ttk.LabelFrame(self.root, text='Recherche et Filtres', padding=10)
        search_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(search_frame, text='Recherche:').grid(row=0, column=0, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *_: self.load_employees())
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).grid(row=0, column=1)

        ttk.Label(search_frame, text='Autorisé à conduire:').grid(row=0, column=2, padx=5)
        self.auth_var = tk.StringVar(value='')
        ttk.Combobox(
            search_frame,
            textvariable=self.auth_var,
            values=['', 'Oui', 'Non'],
            state='readonly',
            width=10
        ).grid(row=0, column=3)

        ttk.Button(search_frame, text='Ajouter', command=self.open_add_employee).grid(row=0, column=4, padx=5)
        ttk.Button(search_frame, text='Modifier', command=self.open_edit_employee).grid(row=0, column=5, padx=5)
        ttk.Button(search_frame, text='Supprimer', command=self.delete_employee).grid(row=0, column=6, padx=5)

        self.alert_label = ttk.Label(self.root, foreground='red')
        self.alert_label.pack(fill='x', padx=10)

        columns = ('Matricule', 'Nom', 'Prénom', 'Service', 'Téléphone', 'Autorisé', 'Permis')
        self.tree = ttk.Treeview(self.root, columns=columns, show='headings')

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)

        self.tree.pack(fill='both', expand=True, padx=10, pady=5)

        self.status_bar = ttk.Label(self.root, relief='sunken')
        self.status_bar.pack(fill='x')

    # ================= DATA =================
    def load_employees(self):
        self.tree.delete(*self.tree.get_children())

        employees = find_employees(filter_text=self.search_var.get() or None)

        if self.auth_var.get() == 'Oui':
            employees = [e for e in employees if e['autorise_conduire']]
        elif self.auth_var.get() == 'Non':
            employees = [e for e in employees if not e['autorise_conduire']]

        today = datetime.now().date()
        warning = today + timedelta(days=30)
        alerts = []

        for emp in employees:
            tag = 'valid'
            permit = emp.get('date_validite_permis')

            if permit:
                try:
                    exp = datetime.strptime(permit, '%Y-%m-%d').date()
                    if exp < today:
                        tag = 'expired'
                        alerts.append(f"{emp['nom']} {emp['prenom']} : permis expiré")
                    elif exp <= warning:
                        tag = 'warning'
                except:
                    pass

            self.tree.insert(
                '',
                'end',
                iid=str(emp['id']),  # ID BDD
                values=(
                    emp['matricule'],
                    emp['nom'],
                    emp['prenom'],
                    emp['service'],
                    emp['telephone'],
                    'Oui' if emp['autorise_conduire'] else 'Non',
                    permit or 'N/A'
                ),
                tags=(tag,)
            )

        for tag, color in LICENSE_COLORS.items():
            self.tree.tag_configure(tag, background=color)

        self.alert_label.config(text=' | '.join(alerts[:3]))
        self.status_bar.config(text=f'Total employés : {len(employees)}')

    # ================= SELECTION =================
    def get_selected_employee(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning('Sélection', 'Veuillez sélectionner un employé')
            return None

        emp_id = int(selection[0])

        conn = db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM employes WHERE id = ?', (emp_id,))
        row = c.fetchone()
        columns = [d[0] for d in c.description]
        conn.close()

        return dict(zip(columns, row)) if row else None

    # ================= ACTIONS =================
    def open_add_employee(self):
        AddEditEmployeeWindow(self.root, callback=self.load_employees)

    def open_edit_employee(self):
        emp = self.get_selected_employee()
        if emp:
            AddEditEmployeeWindow(self.root, employee=emp, callback=self.load_employees)

    def delete_employee(self):
        emp = self.get_selected_employee()
        if not emp:
            return

        if messagebox.askyesno(
            'Confirmation',
            f'Supprimer {emp["nom"]} {emp["prenom"]} ?'
        ):
            conn = db_connection()
            c = conn.cursor()
            c.execute('DELETE FROM employes WHERE id = ?', (emp['id'],))
            conn.commit()
            conn.close()
            self.load_employees()
            messagebox.showinfo('Succès', 'Employé supprimé')


# ================= FORMULAIRE =================
class AddEditEmployeeWindow:
    def __init__(self, parent, employee=None, callback=None):
        self.employee = employee
        self.callback = callback

        self.window = tk.Toplevel(parent)
        self.window.title('Modifier' if employee else 'Ajouter')
        self.window.geometry('500x500')

        self.entries = {}
        self.build_ui()
        if employee:
            self.populate()

    def build_ui(self):
        frame = ttk.Frame(self.window, padding=15)
        frame.pack(fill='both', expand=True)

        fields = [
            ('Matricule', 'matricule'),
            ('Nom', 'nom'),
            ('Prénom', 'prenom'),
            ('Service', 'service'),
            ('Téléphone', 'telephone'),
            ('Email', 'email'),
            ('N° permis', 'num_permis'),
            ('Validité permis', 'date_validite_permis'),
        ]

        for i, (label, key) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky='w')
            e = ttk.Entry(frame, width=40)
            e.grid(row=i, column=1)
            self.entries[key] = e

        self.auth_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text='Autorisé à conduire', variable=self.auth_var)\
            .grid(row=len(fields), column=1, sticky='w')

        ttk.Button(frame, text='Enregistrer', command=self.save)\
            .grid(row=len(fields)+1, column=1, pady=20)

    def populate(self):
        for k, e in self.entries.items():
            if self.employee.get(k):
                e.insert(0, self.employee[k])
        self.auth_var.set(bool(self.employee.get('autorise_conduire')))

    def save(self):
        data = {k: e.get() or None for k, e in self.entries.items()}
        data['autorise_conduire'] = self.auth_var.get()

        conn = db_connection()
        c = conn.cursor()

        if self.employee:
            fields = ', '.join(f"{k}=?" for k in data)
            c.execute(
                f'UPDATE employes SET {fields} WHERE id=?',
                list(data.values()) + [self.employee['id']]
            )
        else:
            add_employee(data)

        conn.commit()
        conn.close()

        if self.callback:
            self.callback()
        self.window.destroy()
