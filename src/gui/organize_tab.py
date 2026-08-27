"""
Pestaña para organizar archivos - Diseño tipo Limpieza/Metadatos.
"""
import threading
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

from ..core.organizer import PhotoVideoOrganizer


class OrganizeTab(ttk.Frame):
    """Pestaña de organización con diseño tipo Limpieza."""

    def __init__(self, parent):
        super().__init__(parent, style='Box.TFrame')
        self.organizer = PhotoVideoOrganizer()

        # Variables
        self.source_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.photos_var = tk.BooleanVar(value=True)
        self.videos_var = tk.BooleanVar(value=True)
        self.documents_var = tk.BooleanVar(value=False)
        self.operation_var = tk.StringVar(value="move")
        self.search_subfolders_var = tk.BooleanVar(value=True)

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

        ttk.Label(text_frame, text="📁 Organizar Archivos", style='Title.TLabel').pack(anchor="w")
        ttk.Label(text_frame, text="Clasifica tus archivos por tipo y fecha automáticamente", style='Subtitle.TLabel').pack(anchor="w")

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

        # ----- COLUMNA IZQUIERDA: RESULTADOS (Vista previa) -----
        results_frame = ttk.LabelFrame(content_frame, text="📊 VISTA PREVIA", style='Box.TLabelframe', padding=4)
        results_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        columns = ("Archivo", "Destino", "Acción")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=12)
        self.tree.heading("Archivo", text="📄 Archivo")
        self.tree.heading("Destino", text="📂 Destino")
        self.tree.heading("Acción", text="✅ Acción")

        self.tree.column("Archivo", width=220, anchor="w")
        self.tree.column("Destino", width=200, anchor="w")
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

        # Tipo de archivos
        ttk.Label(options_frame, text="📋 Tipo de archivos:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).pack(anchor="w", pady=(0, 5))

        ttk.Checkbutton(options_frame, text="📸 Fotos (JPG, PNG, GIF, HEIC...)", variable=self.photos_var, style='Custom.TCheckbutton').pack(anchor="w", pady=1)
        ttk.Checkbutton(options_frame, text="🎬 Videos (MP4, AVI, MKV, MOV...)", variable=self.videos_var, style='Custom.TCheckbutton').pack(anchor="w", pady=1)
        ttk.Checkbutton(options_frame, text="📄 Documentos (PDF, Word, Excel, TXT...)", variable=self.documents_var, style='Custom.TCheckbutton').pack(anchor="w", pady=1)

        # Modo
        ttk.Label(options_frame, text="\n🔧 Modo:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).pack(anchor="w", pady=(5, 5))

        mode_frame = ttk.Frame(options_frame, style='Box.TFrame')
        mode_frame.pack(anchor="w", fill="x")

        ttk.Radiobutton(mode_frame, text="📦 Mover", variable=self.operation_var, value="move", style='Custom.TRadiobutton').pack(side="left", padx=(0, 15))
        ttk.Radiobutton(mode_frame, text="📋 Copiar", variable=self.operation_var, value="copy", style='Custom.TRadiobutton').pack(side="left")

        # Estructura
        ttk.Label(options_frame, text="\n📁 Estructura:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).pack(anchor="w", pady=(5, 5))

        estructura_text = """📸 Fotos → AÑO/MES/DÍA/
🎬 Videos → AÑO/MES/DÍA/
📄 Documentos → EXTENSION/"""
        ttk.Label(options_frame, text=estructura_text, style='Subtitle.TLabel', font=('Consolas', 8)).pack(anchor="w")

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

        self.organize_button = ttk.Button(accion_frame, text="▶ ORGANIZAR", command=self._organize_files, style='Accent.TButton')
        self.organize_button.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)

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

    def _organize_files(self):
        if not self._validate_inputs():
            return

        self.is_running = True
        self.organize_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.clean_button.config(state="disabled")

        self.organizer.file_handler.reset()
        self.organizer.cancel_requested = False

        self.progress['value'] = 0
        self.progress_label.config(text="")

        self._log("🚀 INICIANDO ORGANIZACIÓN...")
        self._log(f"📂 Origen: {self.source_var.get()}")
        self._log(f"📂 Destino: {self.dest_var.get()}")
        self._log(f"🔧 Modo: {'Mover' if self.operation_var.get() == 'move' else 'Copiar'}")

        types = []
        if self.photos_var.get():
            types.append("Fotos")
        if self.videos_var.get():
            types.append("Videos")
        if self.documents_var.get():
            types.append("Documentos")
        self._log(f"📋 Tipos: {', '.join(types)}")
        self._log("-" * 40)

        thread = threading.Thread(target=self._run_organizer)
        thread.daemon = True
        thread.start()

    def _run_organizer(self):
        try:
            source = Path(self.source_var.get())
            dest = Path(self.dest_var.get())

            summary = self.organizer.organize(
                source_dir=source,
                dest_dir=dest,
                organize_photos=self.photos_var.get(),
                organize_videos=self.videos_var.get(),
                organize_documents=self.documents_var.get(),
                operation_mode=self.operation_var.get(),
                search_subfolders=self.search_subfolders_var.get(),
                progress_callback=self._update_progress
            )

            self.after(0, self._on_organize_complete, summary)

        except Exception as e:
            self.after(0, self._on_organize_error, str(e))

    def _cancel_operation(self):
        if self.is_running:
            self.organizer.cancel()
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

    def _on_organize_complete(self, summary: dict):
        self.is_running = False
        self.progress['value'] = 100

        self.organize_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.clean_button.config(state="normal")

        self._log("-" * 40)

        if summary.get('cancelled', False):
            self._log(f"⏹ OPERACIÓN CANCELADA")
            self._log(f"📊 Procesados: {summary['processed']} de {summary['total']}")
            messagebox.showinfo("Cancelado",
                f"Operación cancelada.\nProcesados: {summary['processed']} de {summary['total']}")
        else:
            self._log(f"✅ ¡COMPLETADO!")
            self._log(f"📊 Procesados: {summary['processed']}  |  ⚠️ Errores: {summary['errors']}")

            # Actualizar resumen
            self.total_files_label.config(text=f"Archivos: {summary['processed']}")
            self.total_size_label.config(text="✅ Organización completada")

            if summary['errors'] > 0:
                messagebox.showwarning(
                    "Completado con errores",
                    f"✅ Procesados: {summary['processed']}\n⚠️ Errores: {summary['errors']}"
                )
            else:
                messagebox.showinfo("Éxito", f"✅ {summary['processed']} archivos organizados correctamente.")

    def _on_organize_error(self, error_msg: str):
        self.is_running = False
        self.progress['value'] = 0

        self.organize_button.config(state="normal")
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

        if not self.photos_var.get() and not self.videos_var.get() and not self.documents_var.get():
            messagebox.showerror("Error", "Selecciona al menos un tipo de archivo.")
            return False

        return True

    def _log(self, message: str):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
