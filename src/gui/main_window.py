"""
Ventana principal con diseño moderno y recuadros.
"""
import tkinter as tk
from tkinter import ttk
import os
from pathlib import Path
import sys

# ============================================
# FUNCIÓN PARA OBTENER LA RUTA CORRECTA
# ============================================
def resource_path(relative_path):
    """Obtiene la ruta del archivo, funciona tanto en desarrollo como en compilado."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# Intentar importar Pillow para imágenes
try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from .organize_tab import OrganizeTab
from .desorganize_tab import DesorganizeTab
from .rename_tab import RenameTab
from .music_tab import MusicTab
from .metadata_tab import MetadataTab
from .cleaner_tab import CleanerTab
from .about_tab import AboutTab


class MainWindow(tk.Tk):
    """Ventana principal de la aplicación con diseño moderno."""

    def __init__(self):
        super().__init__()

        # ============================================
        # OCULTAR VENTANA COMPLETAMENTE
        # ============================================
        self.withdraw()
        self.configure(bg='#0f0f1a')

        # Configuración básica de la ventana
        self.title("📁 Organizador de Archivos Pro")
        self.geometry("1024x768")
        self.minsize(1024, 768)

        # ----- ICONO DE LA VENTANA -----
        self._set_window_icon()

        # Configurar estilo
        self._setup_styles()

        # Configurar grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Crear contenedor principal
        self._create_main_container()

        # Crear pestañas
        self._create_tabs()

        # Vincular tecla Escape para salir de pantalla completa
        self.bind('<Escape>', self._toggle_fullscreen)

        # ============================================
        # MOSTRAR VENTANA CUANDO TODO ESTÉ LISTO
        # ============================================
        self.after(100, self._show_window)

    def _show_window(self):
        """Muestra la ventana cuando todo está cargado."""
        # Pantalla completa
        try:
            self.state('zoomed')
        except:
            try:
                self.attributes('-fullscreen', True)
            except:
                self.geometry("{0}x{1}+0+0".format(
                    self.winfo_screenwidth(), 
                    self.winfo_screenheight()
                ))

        # Mostrar ventana
        self.deiconify()
        self.lift()
        self.focus_force()
        self.update_idletasks()

    def _set_window_icon(self):
        """Establece el icono de la ventana usando resource_path."""
        try:
            # Buscar el icono en diferentes ubicaciones
            icon_paths = [
                resource_path("src/assets/jumprova.ico"),
                resource_path("assets/jumprova.ico"),
                resource_path("jumprova.ico"),
            ]
            
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    self.iconbitmap(icon_path)
                    return
        except:
            pass

    def _load_logo(self):
        """Carga el logo desde assets/jumprova.png usando resource_path."""
        if not PILLOW_AVAILABLE:
            return None
            
        try:
            logo_paths = [
                resource_path("src/assets/jumprova.png"),
                resource_path("assets/jumprova.png"),
                resource_path("jumprova.png"),
            ]
            
            for logo_path in logo_paths:
                if os.path.exists(logo_path):
                    logo_image = Image.open(logo_path)
                    logo_image.thumbnail((60, 60), Image.Resampling.LANCZOS)
                    return ImageTk.PhotoImage(logo_image)
        except Exception as e:
            print(f"No se pudo cargar el logo: {e}")
            
        return None


    def _toggle_fullscreen(self, event=None):
        """Alterna entre pantalla completa y ventana normal."""
        try:
            current_state = self.attributes('-fullscreen')
            self.attributes('-fullscreen', not current_state)
        except:
            pass

    def _setup_styles(self):
        """Configura los estilos personalizados."""
        style = ttk.Style()

        COLORS = {
            'bg': '#0f0f1a',
            'bg_light': '#1a1a2e',
            'accent': '#e94560',
            'accent_hover': '#ff6b81',
            'text': '#ffffff',
            'text_secondary': '#b8b8d0',
            'card_bg': '#1e1e32',
            'card_border': '#2a2a4a',
            'success': '#00d2ff',
            'warning': '#ffd93d'
        }

        style.theme_use('clam')

        # Pestañas
        style.configure('Custom.TNotebook',
                        background=COLORS['bg'],
                        borderwidth=0,
                        tabmargins=[5, 3, 5, 0])

        style.configure('Custom.TNotebook.Tab',
                        background=COLORS['bg_light'],
                        foreground=COLORS['text_secondary'],
                        padding=[15, 8],
                        font=('Segoe UI', 10, 'bold'),
                        borderwidth=0,
                        focusthickness=0)

        style.map('Custom.TNotebook.Tab',
                  background=[('selected', COLORS['accent'])],
                  foreground=[('selected', COLORS['text'])])

        # Botones principales
        style.configure('Accent.TButton',
                        background=COLORS['accent'],
                        foreground='white',
                        padding=[20, 8],
                        font=('Segoe UI', 10, 'bold'),
                        borderwidth=0,
                        focusthickness=0)

        style.map('Accent.TButton',
                  background=[('active', COLORS['accent_hover']),
                              ('disabled', '#555577')],
                  foreground=[('disabled', '#888899')])

        # Botones secundarios
        style.configure('Secondary.TButton',
                        background=COLORS['bg_light'],
                        foreground=COLORS['text'],
                        padding=[10, 6],
                        font=('Segoe UI', 9, 'bold'),
                        borderwidth=1,
                        relief='solid')

        style.map('Secondary.TButton',
                  background=[('active', COLORS['card_bg'])],
                  foreground=[('active', COLORS['text'])],
                  bordercolor=[('active', COLORS['accent'])])

        # Labels
        style.configure('Title.TLabel',
                        foreground=COLORS['text'],
                        font=('Segoe UI', 16, 'bold'),
                        background=COLORS['bg'])

        style.configure('Subtitle.TLabel',
                        foreground=COLORS['text_secondary'],
                        font=('Segoe UI', 9),
                        background=COLORS['bg'])

        # Frames con borde (recuadros)
        style.configure('Box.TFrame',
                        background=COLORS['card_bg'],
                        relief='solid',
                        borderwidth=1,
                        bordercolor=COLORS['card_border'])

        style.configure('Box.TLabelframe',
                        background=COLORS['card_bg'],
                        foreground=COLORS['text'],
                        font=('Segoe UI', 10, 'bold'),
                        relief='solid',
                        borderwidth=1,
                        bordercolor=COLORS['card_border'])

        style.configure('Box.TLabelframe.Label',
                        background=COLORS['card_bg'],
                        foreground=COLORS['text'],
                        font=('Segoe UI', 10, 'bold'))

        # Entry
        style.configure('Custom.TEntry',
                        fieldbackground=COLORS['bg_light'],
                        foreground=COLORS['text'],
                        borderwidth=0,
                        padding=4)

        # Checkbox y radiobutton
        style.configure('Custom.TCheckbutton',
                        background=COLORS['card_bg'],
                        foreground=COLORS['text'],
                        font=('Segoe UI', 9),
                        padding=3)

        style.map('Custom.TCheckbutton',
                  background=[('active', COLORS['card_bg'])])

        style.configure('Custom.TRadiobutton',
                        background=COLORS['card_bg'],
                        foreground=COLORS['text'],
                        font=('Segoe UI', 9),
                        padding=3)

        # Progressbar
        style.configure('Custom.Horizontal.TProgressbar',
                        background=COLORS['success'],
                        troughcolor=COLORS['bg_light'],
                        borderwidth=0,
                        thickness=8)

    def _create_main_container(self):
        """Crea el contenedor principal con fondo."""
        self.main_container = tk.Frame(self, bg='#0f0f1a')
        self.main_container.grid(row=0, column=0, sticky="nsew")

        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

    def _create_tabs(self):
        """Crea las pestañas con diseño moderno y logo."""
        # Barra superior con título y logo
        header = tk.Frame(self.main_container, bg='#0f0f1a', height=60)
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(10, 0))
        header.grid_propagate(False)

        # ----- LOGO (izquierda) -----
        logo_photo = self._load_logo()
        if logo_photo:
            logo_label = tk.Label(
                header,
                image=logo_photo,
                bg='#0f0f1a'
            )
            logo_label.image = logo_photo
            logo_label.pack(side="left", padx=(0, 12))
        else:
            logo_label = tk.Label(
                header,
                text="📁",
                font=('Segoe UI', 34),
                bg='#0f0f1a',
                fg='#ffffff'
            )
            logo_label.pack(side="left", padx=(0, 12))

        # ----- TÍTULO (izquierda) -----
        title_label = tk.Label(
            header,
            text="Organizador de Archivos",
            font=('Segoe UI', 20, 'bold'),
            bg='#0f0f1a',
            fg='#ffffff'
        )
        title_label.pack(side="left")

        # ----- SUBTÍTULO (al lado, en AMARILLO) -----
        subtitle_label = tk.Label(
            header,
            text="Organiza y desorganiza tus archivos de forma inteligente",
            font=('Segoe UI', 10),
            bg='#0f0f1a',
            fg='#ffd93d'
        )
        subtitle_label.pack(side="left", padx=(15, 0))

        # Notebook
        self.notebook = ttk.Notebook(
            self.main_container,
            style='Custom.TNotebook'
        )
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=30, pady=15)

        # ========== PESTAÑAS ==========
        # Organizar
        self.organize_tab = OrganizeTab(self.notebook)
        self.notebook.add(self.organize_tab, text="📁 Organizar")

        # Desorganizar
        self.desorganize_tab = DesorganizeTab(self.notebook)
        self.notebook.add(self.desorganize_tab, text="🔄 Desorganizar")

        # Renombrar
        self.rename_tab = RenameTab(self.notebook)
        self.notebook.add(self.rename_tab, text="📝 Renombrar")

        # Música
        self.music_tab = MusicTab(self.notebook)
        self.notebook.add(self.music_tab, text="🎵 Música")

        # Metadatos
        self.metadata_tab = MetadataTab(self.notebook)
        self.notebook.add(self.metadata_tab, text="🏷️ Metadatos")

        # Limpiar
        self.cleaner_tab = CleanerTab(self.notebook)
        self.notebook.add(self.cleaner_tab, text="🧹 Limpiar")

        # Acerca de
        self.about_tab = AboutTab(self.notebook)
        self.notebook.add(self.about_tab, text="ℹ️ Acerca de")

        # ============================================
        # FORZAR EL DIBUJADO DE LA VENTANA
        # ============================================
        self.update_idletasks()
            
        
