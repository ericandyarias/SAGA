"""
Scroll con rueda del mouse para canvas de Tkinter.

Evita interferencias entre paneles: solo scrollea el contenedor
que está bajo el cursor, y solo si el contenido desborda.
"""
import tkinter as tk

_registros = []
_enlace_global = False


def contenido_desborda(canvas, margen=2):
    """True si el contenido del canvas es más alto que el área visible."""
    try:
        if not canvas.winfo_exists():
            return False
        bbox = canvas.bbox("all")
        if not bbox:
            return False
        alto_contenido = bbox[3] - bbox[1]
        alto_visible = canvas.winfo_height()
        return alto_contenido > alto_visible + margen
    except tk.TclError:
        return False


def actualizar_region_scroll(canvas):
    """Actualiza scrollregion y vuelve al inicio si no hay nada que scrollear."""
    try:
        if not canvas.winfo_exists():
            return
        canvas.configure(scrollregion=canvas.bbox("all"))
        if not contenido_desborda(canvas):
            canvas.yview_moveto(0)
    except tk.TclError:
        pass


def _es_dentro(widget, contenedor):
    actual = widget
    while actual is not None:
        if actual == contenedor:
            return True
        try:
            padre = actual.nametowidget(actual.winfo_parent())
        except (tk.TclError, KeyError, AttributeError):
            break
        if padre == actual:
            break
        actual = padre
    return False


def _widget_del_evento(event):
    widget = event.widget
    if isinstance(widget, str):
        for contenedor, canvas in list(_registros):
            try:
                if canvas.winfo_exists():
                    return canvas.nametowidget(widget)
            except (tk.TclError, KeyError):
                continue
        return None

    if widget is not None:
        return widget

    for contenedor, canvas in list(_registros):
        try:
            if canvas.winfo_exists():
                return canvas.winfo_containing(event.x_root, event.y_root)
        except tk.TclError:
            continue
    return None


def _al_rueda(event):
    widget = _widget_del_evento(event)
    if widget is None:
        return

    for contenedor, canvas in list(_registros):
        try:
            if not canvas.winfo_exists() or not contenedor.winfo_exists():
                continue
        except tk.TclError:
            continue

        if not _es_dentro(widget, contenedor):
            continue

        if contenido_desborda(canvas):
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except (tk.TclError, ZeroDivisionError, TypeError):
                pass
        return "break"


def habilitar_scroll_rueda(contenedor, canvas):
    """Registra un panel (canvas + su marco) para scroll con rueda."""
    global _enlace_global
    par = (contenedor, canvas)
    if par not in _registros:
        _registros.append(par)

    if _enlace_global:
        return

    try:
        raiz = contenedor.winfo_toplevel()
        raiz.bind_all("<MouseWheel>", _al_rueda)
        _enlace_global = True
    except tk.TclError:
        pass
