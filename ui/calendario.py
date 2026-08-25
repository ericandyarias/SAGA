"""
Calendario emergente para elegir una fecha (día / mes / año).
"""
import calendar
import tkinter as tk
from datetime import date


MESES = (
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
)
DIAS = ("Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do")


class CalendarioPopup(tk.Toplevel):
    def __init__(self, parent, fecha_inicial=None, al_elegir=None):
        super().__init__(parent)
        self.al_elegir = al_elegir
        self.fecha = fecha_inicial or date.today()
        self.anio = self.fecha.year
        self.mes = self.fecha.month

        self.title("Elegir fecha")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.configure(bg="#f4f6f7")
        marco = tk.Frame(self, bg="#f4f6f7", padx=10, pady=10)
        marco.pack()

        nav = tk.Frame(marco, bg="#f4f6f7")
        nav.pack(fill="x", pady=(0, 8))
        tk.Button(nav, text="◀", width=3, command=self._mes_anterior, relief="flat", bg="#d5dbdb").pack(side="left")
        self.label_mes = tk.Label(nav, font=("Arial", 11, "bold"), bg="#f4f6f7", fg="#1b4f72")
        self.label_mes.pack(side="left", expand=True)
        tk.Button(nav, text="▶", width=3, command=self._mes_siguiente, relief="flat", bg="#d5dbdb").pack(side="right")

        self.grilla = tk.Frame(marco, bg="#f4f6f7")
        self.grilla.pack()
        self._dibujar()

        self.update_idletasks()
        try:
            px = parent.winfo_rootx() + 40
            py = parent.winfo_rooty() + 80
            self.geometry(f"+{px}+{py}")
        except Exception:
            pass

        self.bind("<Escape>", lambda e: self.destroy())
        self.focus_set()

    def _mes_anterior(self):
        if self.mes == 1:
            self.mes = 12
            self.anio -= 1
        else:
            self.mes -= 1
        self._dibujar()

    def _mes_siguiente(self):
        if self.mes == 12:
            self.mes = 1
            self.anio += 1
        else:
            self.mes += 1
        self._dibujar()

    def _dibujar(self):
        for w in self.grilla.winfo_children():
            w.destroy()
        self.label_mes.config(text=f"{MESES[self.mes - 1]} {self.anio}")

        for i, nom in enumerate(DIAS):
            tk.Label(
                self.grilla, text=nom, width=4, font=("Arial", 8, "bold"),
                bg="#1b4f72", fg="white"
            ).grid(row=0, column=i, padx=1, pady=1)

        cal = calendar.Calendar(firstweekday=0)
        fila = 1
        hoy = date.today()
        for semana in cal.monthdayscalendar(self.anio, self.mes):
            for col, dia in enumerate(semana):
                if dia == 0:
                    tk.Label(self.grilla, text="", width=4, bg="#f4f6f7").grid(row=fila, column=col)
                    continue
                actual = date(self.anio, self.mes, dia)
                es_hoy = actual == hoy
                bg = "#117a65" if es_hoy else "#ffffff"
                fg = "white" if es_hoy else "#1a1a1a"
                btn = tk.Button(
                    self.grilla,
                    text=str(dia),
                    width=4,
                    relief="flat",
                    bg=bg,
                    fg=fg,
                    command=lambda d=actual: self._elegir(d)
                )
                btn.grid(row=fila, column=col, padx=1, pady=1)
            fila += 1

    def _elegir(self, fecha):
        if self.al_elegir:
            self.al_elegir(fecha)
        self.destroy()
