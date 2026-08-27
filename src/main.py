"""
Punto de entrada principal de la aplicación.
"""
import sys
import os
from pathlib import Path

# ============================================
# AÑADIR LA RUTA DEL PROYECTO AL PATH
# ============================================
# Esto permite que las importaciones funcionen en compilado
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================
# FUNCIÓN PARA OBTENER LA RUTA CORRECTA (COMPILADO/DESARROLLO)
# ============================================
def resource_path(relative_path):
    """Obtiene la ruta del archivo, funciona tanto en desarrollo como en compilado."""
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # En desarrollo, usar la ruta relativa
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def main():
    """Inicia la aplicación."""
    from src.gui.main_window import MainWindow
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
