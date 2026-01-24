import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from ..models import add_employee, find_employees, get_connection
from ..db import get_connection as db_connection

# Color codes for license status
LICENSE_COLORS = {
    'valid': '#90EE90',        # Green
    'warning': '#FFD700',       # Yellow (expiring soon)
    'expired': '#FF6347'        # Red (expired)
}

class EmployeeListWindow:
    """Main window for employee list, search, and management"""
    def __init__(self, parent=None):
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        self.root.title('Gestion des Employés')
        self.root.geometry('1000x600')
        self.build_ui()
        self.load_employees()

    def build_ui(self):
        # Top search and filter frame
        search_frame = ttk.LabelFrame(self.root, text='Recherche et Filtres', padding=10)
        search_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(search_frame, text='Recherche:').grid(row=0, column=0, sticky='w', padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.load_employees())
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).grid(row=0, column=1, padx=5)

        ttk.Label(search_frame, text='Autorisé à conduire:').grid(row=0, column=2, sticky='w', padx=5)
        self.auth_var = tk.StringVar(value='')
        auth_combo = ttk.Combobox(search_frame, textvariable=self.auth_var, 
                                   values=['', 'Oui', 'Non'], state='readonly', width=15)
        auth_combo.grid(row=0, column=3, padx=5)
        auth_combo.bind('<<ComboboxSelected>>', lambda *args: self.load_employees())

        # Action buttons
        button_frame = ttk.Frame(search_frame)
        button_frame.grid(row=0, column=4, columnspan=3, padx=10)
        ttk.Button(button_frame, text='Ajouter', command=self.open_add_employee).pack(side='left', padx=2)
        ttk.Button(button_frame, text='Modifier', command=self.open_edit_employee).pack(side='left', padx=2)
        ttk.Button(button_frame, text='Détails', command=self.open_employee_detail).pack(side='left', padx=2)
        ttk.Button(button_frame, text='Supprimer', command=self.delete_employee).pack(side='left', padx=2)

        # Alerts frame
        self.alert_label = ttk.Label(self.root, text='', foreground='red', font=('Arial', 10))
        self.alert_label.pack(fill='x', padx=10, pady=5)

        # Tree view for employees
        tree_frame = ttk.Frame(self.root, padding=10)
        tree_frame.pack(fill='both', expand=True)

        columns = ('Matricule', 'Nom', 'Prénom', 'Service', 'Téléphone', 'Autorisé', 'Permis Validité')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == 'Matricule':
                self.tree.column(col, width=80)
            elif col == 'Permis Validité':
                self.tree.column(col, width=120)
            elif col == 'Autorisé':
                self.tree.column(col, width=70)
            else:
                self.tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Status bar
        self.status_bar = ttk.Label(self.root, text='', relief='sunken')
        self.status_bar.pack(fill='x', side='bottom')

    def load_employees(self):
        """Load employees with current filters"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get employees
        search_text = self.search_var.get()
        employees = find_employees(filter_text=search_text if search_text else None)

        # Apply authorization filter
        if self.auth_var.get() == 'Oui':
            employees = [e for e in employees if e.get('autorise_conduire')]
        elif self.auth_var.get() == 'Non':
            employees = [e for e in employees if not e.get('autorise_conduire')]

        # Check for license expiration alerts
        alerts = []
        today = datetime.now().date()
        warning_date = today + timedelta(days=30)

        for emp in employees:
            if emp.get('date_validite_permis'):
                try:
                    exp_date = datetime.strptime(emp.get('date_validite_permis'), '%Y-%m-%d').date()
                    if exp_date < today:
                        alerts.append(f"{emp.get('nom')} {emp.get('prenom')}: Permis EXPIRÉ")
                    elif exp_date <= warning_date:
                        alerts.append(f"{emp.get('nom')} {emp.get('prenom')}: Permis expire bientôt ({exp_date})")
                except:
                    pass

        if alerts:
            self.alert_label.config(text=' | '.join(alerts[:3]))
        else:
            self.alert_label.config(text='')

        # Insert employees
        for employee in employees:
            auth_status = 'Oui' if employee.get('autorise_conduire') else 'Non'
            permit_date = employee.get('date_validite_permis') or 'N/A'
            
            # Determine tag color based on license status
            tag = 'valid'
            if permit_date != 'N/A':
                try:
                    exp_date = datetime.strptime(permit_date, '%Y-%m-%d').date()
                    if exp_date < today:
                        tag = 'expired'
                    elif exp_date <= warning_date:
                        tag = 'warning'
                except:
                    pass

            self.tree.insert('', 'end', 
                           values=(
                               employee.get('matricule'),
                               employee.get('nom'),
                               employee.get('prenom'),
                               employee.get('service'),
                               employee.get('telephone'),
                               auth_status,
                               permit_date
                           ),
                           tags=(tag,))
            self.tree.tag_configure(tag, background=LICENSE_COLORS.get(tag, 'white'))

        self.status_bar.config(text=f'Total employés: {len(employees)}')

    def get_selected_employee(self):
        """Get the selected employee from the tree"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning('Sélection', 'Veuillez sélectionner un employé')
            return None
        matricule = self.tree.item(selection[0])['values'][0]
        employees = find_employees()
        for e in employees:
            if e.get('matricule') == matricule:
                return e
        return None

    def open_add_employee(self):
        """Open add employee form"""
        AddEditEmployeeWindow(self.root, callback=self.load_employees)

    def open_edit_employee(self):
        """Open edit employee form"""
        employee = self.get_selected_employee()
        if employee:
            AddEditEmployeeWindow(self.root, employee=employee, callback=self.load_employees)

    def open_employee_detail(self):
        """Open employee detail window"""
        employee = self.get_selected_employee()
        if employee:
            EmployeeDetailWindow(self.root, employee)

    def delete_employee(self):
        """Delete selected employee"""
        employee = self.get_selected_employee()
        if not employee:
            return
        
        if messagebox.askyesno('Confirmer', f'Supprimer {employee.get("nom")} {employee.get("prenom")}?'):
            conn = db_connection()
            c = conn.cursor()
            c.execute('DELETE FROM employes WHERE id = ?', (employee.get('id'),))
            conn.commit()
            conn.close()
            self.load_employees()
            messagebox.showinfo('Succès', 'Employé supprimé')


class AddEditEmployeeWindow:
    """Form for adding/editing employees"""
    def __init__(self, parent, employee=None, callback=None):
        self.window = tk.Toplevel(parent)
        self.window.title('Ajouter un employé' if not employee else 'Modifier un employé')
        self.window.geometry('600x550')
        self.employee = employee
        self.callback = callback
        self.build_ui()
        if employee:
            self.populate_fields()

    def build_ui(self):
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.pack(fill='both', expand=True)

        fields = [
            ('Matricule *', 'matricule', 'entry'),
            ('Nom *', 'nom', 'entry'),
            ('Prénom *', 'prenom', 'entry'),
            ('Service', 'service', 'entry'),
            ('Téléphone professionnel', 'telephone', 'entry'),
            ('Email professionnel', 'email', 'entry'),
            ('Numéro permis de conduire', 'num_permis', 'entry'),
            ('Date validité permis (YYYY-MM-DD)', 'date_validite_permis', 'entry'),
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

            row += 1

        # Autorisation checkbox
        ttk.Label(main_frame, text='Autorisé à conduire').grid(row=row, column=0, sticky='w', pady=5)
        self.auth_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, variable=self.auth_var).grid(row=row, column=1, sticky='w', pady=5)

        row += 1

        # Photo path
        ttk.Label(main_frame, text='Photo (employé ou permis)').grid(row=row, column=0, sticky='w', pady=5)
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
        """Populate fields with existing employee data"""
        for key, entry in self.entries.items():
            value = self.employee.get(key)
            if value:
                entry.delete(0, tk.END)
                entry.insert(0, str(value))
        
        self.auth_var.set(bool(self.employee.get('autorise_conduire')))
        
        if self.employee.get('photo_path'):
            self.photo_var.set(self.employee.get('photo_path'))

    def validate_date(self, date_str):
        """Validate date format YYYY-MM-DD"""
        if not date_str:
            return True
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def save(self):
        """Save employee data"""
        # Validate required fields
        required = ['matricule', 'nom', 'prenom']
        for field in required:
            if not self.entries[field].get():
                messagebox.showerror('Erreur', f'{field} est obligatoire')
                return

        # Validate date format
        permit_date = self.entries['date_validite_permis'].get()
        if permit_date and not self.validate_date(permit_date):
            messagebox.showerror('Erreur', 'Date permis invalide (format: YYYY-MM-DD)')
            return

        data = {}
        for key, entry in self.entries.items():
            value = entry.get()
            data[key] = value if value else None

        data['autorise_conduire'] = self.auth_var.get()
        data['photo_path'] = self.photo_var.get()

        try:
            if self.employee:
                # Update existing
                conn = db_connection()
                c = conn.cursor()
                update_fields = ', '.join([f'{k} = ?' for k in data.keys()])
                values = list(data.values()) + [self.employee.get('id')]
                c.execute(f'UPDATE employes SET {update_fields} WHERE id = ?', values)
                conn.commit()
                conn.close()
                messagebox.showinfo('Succès', 'Employé modifié')
            else:
                # Add new
                add_employee(data)
                messagebox.showinfo('Succès', 'Employé ajouté')

            if self.callback:
                self.callback()
            self.window.destroy()
        except Exception as e:
            messagebox.showerror('Erreur', f'Erreur lors de l\'enregistrement: {str(e)}')


class EmployeeDetailWindow:
    """Detailed view of an employee with assignment and history"""
    def __init__(self, parent, employee):
        self.window = tk.Toplevel(parent)
        self.window.title(f'Détails - {employee.get("nom")} {employee.get("prenom")}')
        self.window.geometry('900x600')
        self.employee = employee
        self.build_ui()
        self.load_data()

    def build_ui(self):
        # Notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # General info tab
        general_frame = ttk.Frame(notebook, padding=10)
        notebook.add(general_frame, text='Informations générales')

        fields = [
            ('Matricule', 'matricule'),
            ('Nom', 'nom'),
            ('Prénom', 'prenom'),
            ('Service', 'service'),
            ('Téléphone', 'telephone'),
            ('Email', 'email'),
            ('Numéro permis', 'num_permis'),
            ('Date validité permis', 'date_validite_permis'),
            ('Autorisé à conduire', 'autorise_conduire'),
        ]

        for i, (label, key) in enumerate(fields):
            ttk.Label(general_frame, text=label + ':').grid(row=i, column=0, sticky='w', pady=5)
            value = self.employee.get(key)
            if key == 'autorise_conduire':
                value = 'Oui' if value else 'Non'
            ttk.Label(general_frame, text=str(value or '')).grid(row=i, column=1, sticky='w', pady=5)

        # Affectation tab
        affectation_frame = ttk.Frame(notebook, padding=10)
        notebook.add(affectation_frame, text='Affectation véhicule')
        
        ttk.Label(affectation_frame, text='Véhicule assigné (si voiture de fonction):').pack(anchor='w', pady=5)
        self.affectation_label = ttk.Label(affectation_frame, text='Chargement...', foreground='blue')
        self.affectation_label.pack(anchor='w', pady=10)

        # History tab
        history_frame = ttk.Frame(notebook, padding=10)
        notebook.add(history_frame, text='Historique sorties')

        ttk.Label(history_frame, text='Sorties effectuées').pack(anchor='w', pady=5)
        self.history_tree = ttk.Treeview(history_frame, 
                                        columns=('Date Sortie', 'Véhicule', 'Motif', 'Destination', 'Durée', 'KM'), 
                                        show='headings', height=15)
        for col in self.history_tree['columns']:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=130)
        
        scrollbar = ttk.Scrollbar(history_frame, orient='vertical', command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        self.history_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def load_data(self):
        """Load vehicle assignment and history"""
        conn = db_connection()
        c = conn.cursor()

        # Check for permanent assignment
        c.execute('''SELECT v.immatriculation, v.marque, v.modele
                     FROM affectations_permanentes ap
                     JOIN vehicules v ON ap.vehicule_id = v.id
                     WHERE ap.employe_id = ? AND ap.date_fin IS NULL
                     LIMIT 1''', (self.employee.get('id'),))
        
        affectation = c.fetchone()
        if affectation:
            self.affectation_label.config(
                text=f"{affectation[0]} - {affectation[1]} {affectation[2]}",
                foreground='green'
            )
        else:
            self.affectation_label.config(text='Aucune voiture de fonction assignée')

        # Load trip history
        c.execute('''SELECT sr.date_sortie_reelle, v.immatriculation, sr.motif, sr.destination, 
                            sr.date_retour_reelle, sr.km_depart, sr.km_retour
                     FROM sorties_reservations sr
                     JOIN vehicules v ON sr.vehicule_id = v.id
                     WHERE sr.employe_id = ?
                     ORDER BY sr.date_sortie_reelle DESC''', (self.employee.get('id'),))
        
        for row in c.fetchall():
            date_out = row[0]
            vehicle = row[1]
            motif = row[2]
            destination = row[3]
            date_in = row[4]
            km_out = row[5] or 0
            km_in = row[6] or 0
            
            # Calculate duration and distance
            duration = '?'
            if date_out and date_in:
                try:
                    d1 = datetime.strptime(date_out, '%Y-%m-%d %H:%M:%S')
                    d2 = datetime.strptime(date_in, '%Y-%m-%d %H:%M:%S')
                    duration = str((d2 - d1).days) + 'j' if (d2 - d1).days > 0 else str(round((d2 - d1).total_seconds() / 3600)) + 'h'
                except:
                    pass
            
            distance = km_in - km_out if (km_in and km_out) else '?'
            
            self.history_tree.insert('', 'end', values=(date_out, vehicle, motif, destination, duration, distance))
        
        conn.close()
