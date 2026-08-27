"""
Pestaña para desorganizar archivos - Diseño tipo Limpieza/Metadatos.
"""
import threading
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

from ..core.desorganizer import Desorganizer


class DesorganizeTab(ttk.Frame):
    """Pestaña de desorganización con diseño tipo Limpieza."""

    def __init__(self, parent):
        super().__init__(parent, style='Box.TFrame')
        self.desorganizer = Desorganizer()

        # Variables
        self.source_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.operation_var = tk.StringVar(value="move")
        self.search_subfolders_var = tk.BooleanVar(value=True)
        self.mode_var = tk.StringVar(value="all")

        # Estado
        self.is_running = False
        self.operation_thread = None

        self._create_widgets()

    def _create_widgets(self):
        """Crea los widgets en diseño tipo Limpieza."""
        main_frame = ttk.Frame(self, style='Box.TFrame')
        main_frame.pack(fill="both", expand=True, padx=8, pady=4)

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

        # ========== FILA 0: TÍTULO ==========
        title_frame = ttk.Frame(main_frame, style='Box.TFrame')
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)

        text_frame = ttk.Frame(title_frame, style='Box.TFrame')
        text_frame.grid(row=0, column=0, sticky="w")

        ttk.Label(text_frame, text="🔄 Desorganizar Archivos", style='Title.TLabel').pack(anchor="w")
        ttk.Label(text_frame, text="Revierte la organización: todos los archivos juntos en una carpeta", style='Subtitle.TLabel').pack(anchor="w")

        # ========== FILA 1: UBICACIÓN ==========
        top_frame = ttk.LabelFrame(main_frame, text="📂 UBICACIÓN", style='Box.TLabelframe', padding=5)
        top_frame.grid(row=1, column=0, sticky="ew", pady=(2, 4))
        top_frame.grid_columnconfigure(1, weight=1)

        # Origen
        ttk.Label(top_frame, text="Origen:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky="w")
        ttk.Entry(top_frame, textvariable=self.source_var, style='Custom.TEntry', font=('Segoe UI', 9)).grid(row=0, column=1, sticky="ew", padx=(5, 8))
        ttk.Button(top_frame, text="📂 Examinar", command=self._select_source, style='Secondary.TButton', width=14).grid(row=0, column=2, padx=(0, 5))

        # Destino
        ttk.Label(top_frame, text="Destino:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).grid(row=1, column=0, sticky="w", pady=(2, 0))
        ttk.Entry(top_frame, textvariable=self.dest_var, style='Custom.TEntry', font=('Segoe UI', 9)).grid(row=1, column=1, sticky="ew", padx=(5, 8), pady=(2, 0))

        dest_btn_frame = ttk.Frame(top_frame, style='Box.TFrame')
        dest_btn_frame.grid(row=1, column=2, pady=(2, 0))

        ttk.Button(dest_btn_frame, text="↩️ Usar mismo", command=self._use_same_destination, style='Secondary.TButton', width=14).pack(side="left", padx=(0, 5))
        ttk.Button(dest_btn_frame, text="📂 Examinar", command=self._select_destination, style='Secondary.TButton', width=14).pack(side="left")

        # Opciones de escaneo
        scan_opts_frame = ttk.Frame(top_frame, style='Box.TFrame')
        scan_opts_frame.grid(row=2, column=0, columnspan=3, sticky="w", pady=(5, 0))
        ttk.Checkbutton(scan_opts_frame, text="🔍 Buscar en subcarpetas", variable=self.search_subfolders_var, style='Custom.TCheckbutton').pack(side="left")

        # ========== FILA 2: RESULTADOS + OPCIONES + ACTIVIDAD ==========
        content_frame = ttk.Frame(main_frame, style='Box.TFrame')
        content_frame.grid(row=2, column=0, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=2)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # ----- COLUMNA IZQUIERDA: RESULTADOS -----
        results_frame = ttk.LabelFrame(content_frame, text="📊 RESULTADOS", style='Box.TLabelframe', padding=4)
        results_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        columns = ("Archivo", "Origen", "Acción")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=12)
        self.tree.heading("Archivo", text="📄 Archivo")
        self.tree.heading("Origen", text="📂 Origen")
        self.tree.heading("Acción", text="✅ Acción")

        self.tree.column("Archivo", width=220, anchor="w")
        self.tree.column("Origen", width=200, anchor="w")
        self.tree.column("Acción", width=80, anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Resumen
        summary_frame = ttk.Frame(results_frame, style='Box.TFrame')
        summary_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))

        self.total_files_label = ttk.Label(summary_frame, text="Archivos: 0", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold'))
        self.total_files_label.pack(side="left", padx=(0, 15))
        self.total_size_label = ttk.Label(summary_frame, text="Tamaño total: 0 MB", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold'), foreground='#ffd93d')
        self.total_size_label.pack(side="left")

        # ----- COLUMNA DERECHA: OPCIONES + ACTIVIDAD -----
        right_frame = ttk.Frame(content_frame, style='Box.TFrame')
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        right_frame.grid_rowconfigure(0, weight=0)
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        # ----- OPCIONES -----
        options_frame = ttk.LabelFrame(right_frame, text="⚙️ OPCIONES", style='Box.TLabelframe', padding=4)
        options_frame.grid(row=0, column=0, sticky="ew", pady=(0, 1))
        options_frame.grid_columnconfigure(0, weight=1)

        # Modo
        ttk.Label(options_frame, text="📂 ¿Qué desorganizar?", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).pack(anchor="w", pady=(0, 5))

        ttk.Radiobutton(options_frame, text="📁 Todo (Fotos, Videos, Música y Documentos)", variable=self.mode_var, value="all", style='Custom.TRadiobutton').pack(anchor="w", pady=1)
        ttk.Radiobutton(options_frame, text="📸 Fotos y Videos", variable=self.mode_var, value="photos_videos", style='Custom.TRadiobutton').pack(anchor="w", pady=1)
        ttk.Radiobutton(options_frame, text="🎵 Solo Música", variable=self.mode_var, value="music", style='Custom.TRadiobutton').pack(anchor="w", pady=1)
        ttk.Radiobutton(options_frame, text="📄 Solo Documentos", variable=self.mode_var, value="documents", style='Custom.TRadiobutton').pack(anchor="w", pady=1)

        # Modo de operación
        ttk.Label(options_frame, text="\n🔧 Modo:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).pack(anchor="w", pady=(5, 5))

        mode_frame = ttk.Frame(options_frame, style='Box.TFrame')
        mode_frame.pack(anchor="w", fill="x")

        ttk.Radiobutton(mode_frame, text="📦 Mover", variable=self.operation_var, value="move", style='Custom.TRadiobutton').pack(side="left", padx=(0, 15))
        ttk.Radiobutton(mode_frame, text="📋 Copiar", variable=self.operation_var, value="copy", style='Custom.TRadiobutton').pack(side="left")

        # Advertencia
        ttk.Label(options_frame, text="\n⚠️ Las carpetas vacías se eliminarán", style='Subtitle.TLabel', font=('Segoe UI', 9, 'italic'), foreground='#ffd93d').pack(anchor="w", pady=(5, 0))

        # ----- ACTIVIDAD (debajo de opciones) -----
        actividad_frame = ttk.LabelFrame(right_frame, text="📝 ACTIVIDAD", style='Box.TLabelframe', padding=3)
        actividad_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 0))
        actividad_frame.grid_columnconfigure(0, weight=1)
        actividad_frame.grid_rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            actividad_frame,
            height=4,
            bg='#111122',
            fg='#b8b8d0',
            font=('Consolas', 8),
            relief='flat',
            borderwidth=0,
            wrap='word'
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # ========== FILA 3: ACCIÓN ==========
        accion_frame = ttk.LabelFrame(main_frame, text="🚀 ACCIÓN", style='Box.TLabelframe', padding=5)
        accion_frame.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        accion_frame.grid_columnconfigure(0, weight=1)
        accion_frame.grid_columnconfigure(1, weight=1)
        accion_frame.grid_columnconfigure(2, weight=1)

        self.desorganize_button = ttk.Button(accion_frame, text="🔄 DESORGANIZAR", command=self._desorganize_files, style='Accent.TButton')
        self.desorganize_button.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)

        self.cancel_button = ttk.Button(accion_frame, text="⏹ CANCELAR", command=self._cancel_operation, style='Secondary.TButton', state="disabled")
        self.cancel_button.grid(row=0, column=1, sticky="ew", padx=(4, 4), pady=2)

        self.clean_button = ttk.Button(accion_frame, text="🧹 LIMPIAR TODO", command=self._clean_all, style='Secondary.TButton')
        self.clean_button.grid(row=0, column=2, sticky="ew", padx=(4, 0), pady=2)

        self.progress = ttk.Progressbar(accion_frame, mode='determinate', style='Custom.Horizontal.TProgressbar', maximum=100)
        self.progress.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(4, 0))

        self.progress_label = ttk.Label(accion_frame, text="", style='Subtitle.TLabel', font=('Segoe UI', 8))
        self.progress_label.grid(row=2, column=0, columnspan=3, sticky="e", pady=(1, 0))

    # ========== MÉTODOS DE FUNCIONALIDAD ==========

    def _use_same_destination(self):
        if self.source_var.get():
            self.dest_var.set(self.source_var.get())

    def _select_source(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta origen")
        if folder:
            self.source_var.set(folder)

    def _select_destination(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta destino")
        if folder:
            self.dest_var.set(folder)

    def _update_progress(self, current, total):
        if total > 0:
            porcentaje = int((current / total) * 100)
            self.progress['value'] = porcentaje
            self.progress_label.config(text=f"{current}/{total} ({porcentaje}%)")

    def _desorganize_files(self):
        if not self._validate_inputs():
            return

        self.is_running = True
        self.desorganize_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.clean_button.config(state="disabled")

        self.desorganizer.file_handler.reset()
        self.desorganizer.cancel_requested = False

        self.progress['value'] = 0
        self.progress_label.config(text="")

        mode_labels = {
            "all": "Todo (Fotos, Videos, Música y Documentos)",
            "photos_videos": "Fotos y Videos",
            "music": "Solo Música",
            "documents": "Solo Documentos"
        }

        self._log("🔄 INICIANDO DESORGANIZACIÓN...")
        self._log(f"📂 Origen: {self.source_var.get()}")
        self._log(f"📂 Destino: {self.dest_var.get()}")
        self._log(f"📂 Modo: {mode_labels.get(self.mode_var.get(), 'Desconocido')}")
        self._log(f"🔧 Operación: {'Mover' if self.operation_var.get() == 'move' else 'Copiar'}")
        self._log("-" * 40)

        thread = threading.Thread(target=self._run_desorganizer)
        thread.daemon = True
        thread.start()

    def _run_desorganizer(self):
        try:
            source = Path(self.source_var.get())
            dest = Path(self.dest_var.get())

            summary = self.desorganizer.desorganize(
                source_dir=source,
                dest_dir=dest,
                operation_mode=self.operation_var.get(),
                search_subfolders=self.search_subfolders_var.get(),
                mode=self.mode_var.get(),
                progress_callback=self._update_progress
            )

            self.after(0, self._on_desorganize_complete, summary)

        except Exception as e:
            self.after(0, self._on_desorganize_error, str(e))

    def _cancel_operation(self):
        if self.is_running:
            self.desorganizer.cancel()
            self._log("⏹ SOLICITANDO CANCELACIÓN...")

    def _clean_all(self):
        self.source_var.set("")
        self.dest_var.set("")
        self.tree.delete(*self.tree.get_children())
        self.total_files_label.config(text="Archivos: 0")
        self.total_size_label.config(text="Tamaño total: 0 MB")
        self.log_text.delete("1.0", tk.END)
        self.progress['value'] = 0
        self.progress_label.config(text="")
        self._log("🧹 Todo limpiado. Listo para empezar.")

    def _on_desorganize_complete(self, summary: dict):
        self.is_running = False
        self.progress['value'] = 100

        self.desorganize_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.clean_button.config(state="normal")

        self._log("-" * 40)

        if summary.get('cancelled', False):
            self._log(f"⏹ OPERACIÓN CANCELADA")
            self._log(f"📊 Procesados: {summary['processed']} de {summary['total']}")
            messagebox.showinfo("Cancelado",
                f"Operación cancelada.\nProcesados: {summary['processed']} de {summary['total']}")
        else:
            self._log(f"✅ ¡DESORGANIZACIÓN COMPLETADA!")
            self._log(f"📊 Archivos procesados: {summary['processed']}  |  ⚠️ Errores: {summary['errors']}")

            self.total_files_label.config(text=f"Archivos: {summary['processed']}")
            self.total_size_label.config(text="✅ Desorganización completada")

            if summary['errors'] > 0:
                messagebox.showwarning(
                    "Completado con errores",
                    f"✅ Procesados: {summary['processed']}\n⚠️ Errores: {summary['errors']}"
                )
            else:
                messagebox.showinfo("Éxito", f"✅ {summary['processed']} archivos desorganizados correctamente.")

    def _on_desorganize_error(self, error_msg: str):
        self.is_running = False
        self.progress['value'] = 0

        self.desorganize_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.clean_button.config(state="normal")

        self._log(f"❌ ERROR: {error_msg}")
        messagebox.showerror("Error", error_msg)

    def _validate_inputs(self) -> bool:
        if not self.source_var.get():
            messagebox.showerror("Error", "Selecciona una carpeta origen.")
            return False

        if not self.dest_var.get():
            messagebox.showerror("Error", "Selecciona una carpeta destino.")
            return False

        source = Path(self.source_var.get())
        if not source.exists():
            messagebox.showerror("Error", "La carpeta origen no existe.")
            return False

        mode = self.mode_var.get()

        if mode == "photos_videos":
            fotos = source / "Fotos"
            videos = source / "Videos"
            if not fotos.exists() and not videos.exists():
                messagebox.showerror("Error", "No se encontraron carpetas 'Fotos' o 'Videos'.")
                return False

        elif mode == "music":
            musica = source / "Música"
            if not musica.exists():
                messagebox.showerror("Error", "No se encontró la carpeta 'Música'.")
                return False

        elif mode == "documents":
            documentos = source / "Documentos"
            if not documentos.exists():
                messagebox.showerror("Error", "No se encontró la carpeta 'Documentos'.")
                return False

        else:  # "all"
            fotos = source / "Fotos"
            videos = source / "Videos"
            musica = source / "Música"
            documentos = source / "Documentos"
            if not fotos.exists() and not videos.exists() and not musica.exists() and not documentos.exists():
                messagebox.showerror("Error", "No se encontraron carpetas 'Fotos', 'Videos', 'Música' o 'Documentos'.")
                return False

        return True

    def _log(self, message: str):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
