import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
from ..db import get_connection
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import csv
import datetime


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.datetime.strptime(s, '%Y-%m-%d').date()
    except Exception:
        return None


class StatisticsWindow(tk.Toplevel):
    """Fenêtre de statistiques et rapports"""
    def __init__(self, master=None):
        super().__init__(master)
        self.title('Statistiques & Rapports')
        self.geometry('900x650')
        self.build_ui()

    def build_ui(self):
        control = ttk.Frame(self)
        control.pack(fill='x', padx=10, pady=6)

        ttk.Label(control, text='Date début (YYYY-MM-DD):').pack(side='left')
        self.start_entry = ttk.Entry(control, width=12)
        self.start_entry.pack(side='left', padx=4)
        ttk.Label(control, text='Date fin (YYYY-MM-DD):').pack(side='left', padx=(8,0))
        self.end_entry = ttk.Entry(control, width=12)
        self.end_entry.pack(side='left', padx=4)

        ttk.Button(control, text='Calculer', command=self.calculate).pack(side='left', padx=8)
        ttk.Button(control, text='Exporter CSV', command=self.export_csv).pack(side='left')
        ttk.Button(control, text='Exporter PDF', command=self.export_pdf).pack(side='left', padx=6)

        # Notebook for charts / tables
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill='both', expand=True, padx=10, pady=8)

        self.frame_charts = ttk.Frame(self.nb)
        self.frame_tables = ttk.Frame(self.nb)
        self.nb.add(self.frame_charts, text='Graphiques')
        self.nb.add(self.frame_tables, text='Données')

        # Chart canvas
        self.fig = Figure(figsize=(8, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_charts)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # Table treeview
        self.tree = ttk.Treeview(self.frame_tables, columns=('a','b','c','d'), show='headings')
        self.tree.pack(fill='both', expand=True)

        # store last results
        self.last_results = {}

    # ------------------ Data queries ------------------
    def _date_clause(self, field, start, end):
        clauses = []
        params = []
        if start:
            clauses.append(f"{field} >= ?")
            params.append(start.isoformat())
        if end:
            clauses.append(f"{field} <= ?")
            params.append(end.isoformat())
        if clauses:
            return ' AND '.join(clauses), params
        return '', []

    def calculate(self):
        start = _parse_date(self.start_entry.get())
        end = _parse_date(self.end_entry.get())
        try:
            conn = get_connection()
            c = conn.cursor()

            # Total kilometrage (current - initial)
            c.execute('SELECT id, immatriculation, kilometrage_initial, kilometrage_actuel, type_vehicule FROM vehicules')
            vehs = [dict(r) for r in c.fetchall()]
            km_per_vehicle = []
            total_km = 0
            for v in vehs:
                km = (v.get('kilometrage_actuel') or 0) - (v.get('kilometrage_initial') or 0)
                km_per_vehicle.append({'id': v['id'], 'imm': v['immatriculation'], 'km': km, 'type': v.get('type_vehicule')})
                total_km += km

            # Period kms from sorties_reservations (if date range provided)
            period_km = 0
            if start or end:
                clause, params = self._date_clause('date_sortie_reelle', start, end)
                q = 'SELECT km_retour, km_depart FROM sorties_reservations'
                if clause:
                    q += ' WHERE ' + clause
                c.execute(q, params)
                for r in c.fetchall():
                    km_r = (r['km_retour'] or 0) - (r['km_depart'] or 0)
                    period_km += max(km_r, 0)

            # Costs per vehicle
            c.execute('SELECT v.id, v.immatriculation, IFNULL(SUM(r.cout),0) as fuel_cost FROM vehicules v LEFT JOIN ravitaillements r ON r.vehicule_id = v.id GROUP BY v.id')
            fuel = {r['id']: r['fuel_cost'] for r in c.fetchall()}
            c.execute('SELECT v.id, IFNULL(SUM(m.cout),0) as maint_cost FROM vehicules v LEFT JOIN maintenances m ON m.vehicule_id = v.id GROUP BY v.id')
            maint = {r['id']: r['maint_cost'] for r in c.fetchall()}

            costs = []
            for v in km_per_vehicle:
                vid = v['id']
                f = fuel.get(vid, 0) or 0
                m = maint.get(vid, 0) or 0
                total = f + m
                costs.append({'imm': v['imm'], 'fuel': f, 'maintenance': m, 'total': total})

            # Most active employees
            clause2, params2 = self._date_clause('date_sortie_reelle', start, end)
            q2 = 'SELECT employe_id, COUNT(*) as sorties, SUM(COALESCE(km_retour,0)-COALESCE(km_depart,0)) as km FROM sorties_reservations'
            if clause2:
                q2 += ' WHERE ' + clause2
            q2 += ' GROUP BY employe_id ORDER BY sorties DESC LIMIT 10'
            c.execute(q2, params2)
            employees = [dict(r) for r in c.fetchall()]

            # Consumption per vehicle
            c.execute('SELECT vehicule_id, IFNULL(SUM(quantite_litres),0) as liters FROM ravitaillements GROUP BY vehicule_id')
            liters = {r['vehicule_id']: r['liters'] for r in c.fetchall()}
            c.execute('SELECT vehicule_id, SUM(COALESCE(km_retour,0)-COALESCE(km_depart,0)) as km FROM sorties_reservations GROUP BY vehicule_id')
            kms_from_trips = {r['vehicule_id']: r['km'] for r in c.fetchall()}
            consumption = []
            for v in vehs:
                vid = v['id']
                lit = liters.get(vid, 0) or 0
                km = kms_from_trips.get(vid, 0) or 0
                if km > 0:
                    cons_100 = (lit / km) * 100
                else:
                    cons_100 = None
                consumption.append({'imm': v['immatriculation'], 'liters': lit, 'km': km, 'l_per_100km': cons_100, 'type': v.get('type_vehicule')})

            conn.close()

            self.last_results = {
                'km_per_vehicle': km_per_vehicle,
                'total_km': total_km,
                'period_km': period_km,
                'costs': costs,
                'employees': employees,
                'consumption': consumption
            }

            self._render_results()

        except Exception as e:
            messagebox.showerror('Erreur', str(e))

    # ------------------ Rendering ------------------
    def _render_results(self):
        self.fig.clf()
        ax1 = self.fig.add_subplot(221)
        ax2 = self.fig.add_subplot(222)
        ax3 = self.fig.add_subplot(212)

        # km per vehicle bar
        km_data = sorted(self.last_results['km_per_vehicle'], key=lambda x: x['km'], reverse=True)[:10]
        labels = [v['imm'] for v in km_data]
        vals = [v['km'] for v in km_data]
        ax1.bar(labels, vals)
        ax1.set_title('Kilométrage par véhicule (top 10)')
        ax1.tick_params(axis='x', rotation=45)

        # costs per vehicle
        costs_data = sorted(self.last_results['costs'], key=lambda x: x['total'], reverse=True)[:10]
        labels2 = [c['imm'] for c in costs_data]
        vals2 = [c['total'] for c in costs_data]
        ax2.bar(labels2, vals2, color='orange')
        ax2.set_title('Coût total par véhicule (top 10)')
        ax2.tick_params(axis='x', rotation=45)

        # top employees pie
        emp = self.last_results['employees'][:8]
        if emp:
            labels3 = [str(e['employe_id']) + ' (' + str(e['sorties']) + ')' for e in emp]
            vals3 = [e['km'] or 0 for e in emp]
            ax3.pie(vals3, labels=labels3, autopct='%1.1f%%')
            ax3.set_title('Top employés par km (période)')
        else:
            ax3.text(0.5, 0.5, 'Pas de données', ha='center')

        self.fig.tight_layout()
        self.canvas.draw()

        # Fill table with consumption as default
        for col in self.tree['columns']:
            self.tree.heading(col, text='')
            self.tree.column(col, width=200)
        self.tree['columns'] = ('imm', 'liters', 'km', 'l_per_100km')
        self.tree.delete(*self.tree.get_children())
        for row in self.last_results['consumption']:
            lpk = f"{row['l_per_100km']:.2f}" if row['l_per_100km'] is not None else ''
            self.tree.insert('', 'end', values=(row['imm'], row['liters'], row['km'], lpk))

    # ------------------ Exports ------------------
    def export_csv(self):
        if not self.last_results:
            messagebox.showinfo('Info', 'Aucune donnée à exporter. Cliquez sur Calculer d\u00e9abord.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
        if not path:
            return
        # Export consumption table
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Immatriculation','Litres','Km','L/100km'])
            for r in self.last_results['consumption']:
                lpk = f"{r['l_per_100km']:.2f}" if r['l_per_100km'] is not None else ''
                writer.writerow([r['imm'], r['liters'], r['km'], lpk])
        messagebox.showinfo('Export', f'Export CSV enregistré: {path}')

    def export_pdf(self):
        if not self.last_results:
            messagebox.showinfo('Info', 'Aucune donnée à exporter. Cliquez sur Calculer d\u00e9abord.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF','*.pdf')])
        if not path:
            return
        # Create PDF with the three figures
        pp = PdfPages(path)
        # recreate same plots as in UI
        fig1 = plt.figure(figsize=(8, 6))
        ax = fig1.add_subplot(111)
        km_data = sorted(self.last_results['km_per_vehicle'], key=lambda x: x['km'], reverse=True)[:10]
        labels = [v['imm'] for v in km_data]
        vals = [v['km'] for v in km_data]
        ax.bar(labels, vals)
        ax.set_title('Kilométrage par véhicule (top 10)')
        ax.tick_params(axis='x', rotation=45)
        fig1.tight_layout()
        pp.savefig(fig1)
        plt.close(fig1)

        fig2 = plt.figure(figsize=(8, 6))
        ax2 = fig2.add_subplot(111)
        costs_data = sorted(self.last_results['costs'], key=lambda x: x['total'], reverse=True)[:10]
        labels2 = [c['imm'] for c in costs_data]
        vals2 = [c['total'] for c in costs_data]
        ax2.bar(labels2, vals2, color='orange')
        ax2.set_title('Coût total par véhicule (top 10)')
        ax2.tick_params(axis='x', rotation=45)
        fig2.tight_layout()
        pp.savefig(fig2)
        plt.close(fig2)

        # Add a simple table page for consumption
        fig3 = plt.figure(figsize=(8.27, 11.69))
        ax3 = fig3.add_subplot(111)
        ax3.axis('off')
        table_data = [[r['imm'], r['liters'], r['km'], f"{r['l_per_100km']:.2f}" if r['l_per_100km'] is not None else ''] for r in self.last_results['consumption']]
        col_labels = ['Immatriculation','Litres','Km','L/100km']
        ax3.table(cellText=table_data, colLabels=col_labels, loc='center')
        fig3.tight_layout()
        pp.savefig(fig3)
        plt.close(fig3)

        pp.close()
        messagebox.showinfo('Export', f'Export PDF enregistré: {path}')
