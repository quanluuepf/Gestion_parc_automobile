import tkinter as tk
from tkinter import ttk
from datetime import datetime
from ..db import get_connection


class AlertsWindow:
    def __init__(self, parent):
        self.root = tk.Toplevel(parent)
        self.root.title('Alertes et échéances')
        self.root.geometry('900x420')
        self.build_ui()
        self.load_alerts()

    def build_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill='both', expand=True)

        columns = ('type', 'immatriculation', 'description', 'date_echeance', 'jours_restants')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings')
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=170)

        vsb = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=vsb.set)
        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')

        self.tree.tag_configure('overdue', background='#ffcccc')
        self.tree.tag_configure('soon', background='#fff0b3')
        self.tree.tag_configure('ok', background='#e6ffea')

    def load_alerts(self):
        self.tree.delete(*self.tree.get_children())
        today = datetime.today().date()
        conn = get_connection()
        c = conn.cursor()

        # maintenances with next due
        c.execute('''SELECT m.id, v.immatriculation, m.type_intervention, m.date_prochaine_echeance
                     FROM maintenances m
                     LEFT JOIN vehicules v ON v.id = m.vehicule_id
                     WHERE m.date_prochaine_echeance IS NOT NULL''')
        for mid, immat, typ, due in c.fetchall():
            try:
                d = datetime.strptime(due, '%Y-%m-%d').date()
            except Exception:
                continue
            days = (d - today).days
            tag = 'ok'
            if days < 0:
                tag = 'overdue'
            elif days <= 30:
                tag = 'soon'
            self.tree.insert('', 'end', values=('Maintenance', immat or '', typ or '', due, days), tags=(tag,))

        # documents with due dates
        c.execute('''SELECT d.id, v.immatriculation, d.type_document, d.date_echeance
                     FROM documents d
                     LEFT JOIN vehicules v ON v.id = d.vehicule_id
                     WHERE d.date_echeance IS NOT NULL''')
        for did, immat, doc_type, due in c.fetchall():
            try:
                d = datetime.strptime(due, '%Y-%m-%d').date()
            except Exception:
                continue
            days = (d - today).days
            tag = 'ok'
            if days < 0:
                tag = 'overdue'
            elif days <= 30:
                tag = 'soon'
            self.tree.insert('', 'end', values=('Document', immat or '', doc_type or '', due, days), tags=(tag,))

        conn.close()
