#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Organizador Pro - Gestión Inteligente de Archivos
Versión: 1.0.0
Descripción: Aplicación modular para organizar archivos automáticamente
Autor: Tu Nombre
Licencia: MIT (Gratuita y Open Source)
"""

import tkinter as tk
from gui.main_window import MainWindow


def main():
    """Punto de entrada principal"""
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
