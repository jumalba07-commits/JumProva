"""
Pestaña Acerca de - Información de la aplicación.
"""
import tkinter as tk
from tkinter import ttk
from pathlib import Path

try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class AboutTab(ttk.Frame):
    """Pestaña Acerca de."""

    def __init__(self, parent):
        super().__init__(parent, style='Box.TFrame')
        self._create_widgets()

    def _create_widgets(self):
        """Crea los widgets de la interfaz."""
        main_frame = ttk.Frame(self, style='Box.TFrame')
        main_frame.pack(fill="both", expand=True, padx=8, pady=4)

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # ========== FILA 0: TÍTULO ==========
        title_frame = ttk.Frame(main_frame, style='Box.TFrame')
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)

        text_frame = ttk.Frame(title_frame, style='Box.TFrame')
        text_frame.grid(row=0, column=0, sticky="w")

        ttk.Label(text_frame, text="ℹ️ Acerca de", style='Title.TLabel').pack(anchor="w")
        ttk.Label(text_frame, text="Información sobre la aplicación", style='Subtitle.TLabel').pack(anchor="w")

        # ========== FILA 1: CONTENIDO ==========
        content_frame = ttk.Frame(main_frame, style='Box.TFrame')
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # ----- MARCO CENTRAL -----
        center_frame = ttk.Frame(content_frame, style='Box.TFrame')
        center_frame.grid(row=0, column=0, sticky="nsew")
        center_frame.grid_columnconfigure(0, weight=1)

        # Tarjeta de información
        card_frame = ttk.LabelFrame(
            center_frame,
            text="📋 INFORMACIÓN",
            style='Box.TLabelframe',
            padding=20
        )
        card_frame.grid(row=0, column=0, sticky="nsew", padx=50, pady=20)

        # Logo
        logo_photo = self._load_logo()
        if logo_photo:
            logo_label = tk.Label(
                card_frame,
                image=logo_photo,
                bg='#1e1e32'
            )
            logo_label.image = logo_photo
            logo_label.pack(pady=(0, 15))
        else:
            logo_label = tk.Label(
                card_frame,
                text="📁",
                font=('Segoe UI', 48),
                bg='#1e1e32',
                fg='#ffffff'
            )
            logo_label.pack(pady=(0, 15))

        # Nombre de la app
        ttk.Label(
            card_frame,
            text="JumProva",
            style='Title.TLabel',
            font=('Segoe UI', 28, 'bold')
        ).pack()

        ttk.Label(
            card_frame,
            text="Versión 1.0.0",
            style='Subtitle.TLabel',
            font=('Segoe UI', 12)
        ).pack()

        ttk.Label(
            card_frame,
            text="Organizador de Archivos Profesional",
            style='Subtitle.TLabel',
            font=('Segoe UI', 11, 'italic')
        ).pack(pady=(5, 10))

        # Separador
        ttk.Separator(card_frame, orient='horizontal').pack(fill="x", pady=10)

        # Desarrollador
        ttk.Label(
            card_frame,
            text="👨‍💻 Desarrollado por Juan José Rivera",
            style='Subtitle.TLabel',
            font=('Segoe UI', 10)
        ).pack()

        ttk.Label(
            card_frame,
            text="📧 jumalba@hotmail.com",
            style='Subtitle.TLabel',
            font=('Segoe UI', 10)
        ).pack()

        # Año
        ttk.Label(
            card_frame,
            text="© 2026 JumProva. Todos los derechos reservados.",
            style='Subtitle.TLabel',
            font=('Segoe UI', 9)
        ).pack(pady=(5, 0))

        # Botón Contacto (único)
        btn_frame = ttk.Frame(card_frame, style='Box.TFrame')
        btn_frame.pack(pady=(15, 0))

        ttk.Button(
            btn_frame,
            text="📧 Enviar correo",
            command=self._send_email,
            style='Accent.TButton',
            width=15
        ).pack()

        # ========== FILA 2: TECNOLOGÍAS ==========
        tech_frame = ttk.LabelFrame(
            center_frame,
            text="🛠️ TECNOLOGÍAS",
            style='Box.TLabelframe',
            padding=15
        )
        tech_frame.grid(row=1, column=0, sticky="ew", padx=50, pady=(0, 20))

        tech_text = """• Python 3.11+
• Tkinter (GUI nativa)
• Mutagen (metadatos de música)
• Pillow (procesamiento de imágenes)

📦 Dependencias:
• mutagen >= 1.46.0
• pillow >= 10.0.0

📝 Licencia: MIT"""
        ttk.Label(
            tech_frame,
            text=tech_text,
            style='Subtitle.TLabel',
            font=('Consolas', 10)
        ).pack(anchor="w")

        # ========== FILA 3: CERRAR ==========
        close_frame = ttk.Frame(main_frame, style='Box.TFrame')
        close_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        ttk.Button(
            close_frame,
            text="✅ CERRAR",
            command=self._close,
            style='Secondary.TButton',
            width=15
        ).pack()

    def _load_logo(self):
        """Carga el logo desde assets/jumprova.png."""
        if not PILLOW_AVAILABLE:
            return None

        try:
            logo_paths = [
                Path(__file__).parent.parent / "assets" / "jumprova.png",
                Path("assets") / "jumprova.png",
            ]

            for logo_path in logo_paths:
                if logo_path.exists():
                    logo_image = Image.open(logo_path)
                    logo_image.thumbnail((100, 100), Image.Resampling.LANCZOS)
                    return ImageTk.PhotoImage(logo_image)
        except Exception:
            pass

        return None

    def _send_email(self):
        """Abrir correo con destinatario predefinido."""
        import webbrowser
        webbrowser.open("mailto:jumalba@hotmail.com?subject=Contacto%20JumProva")

    def _close(self):
        """Cerrar la pestaña (seleccionar la primera pestaña)."""
        parent = self.master
        while not isinstance(parent, ttk.Notebook):
            parent = parent.master
        parent.select(0)
