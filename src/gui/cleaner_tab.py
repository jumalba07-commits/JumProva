"""
Pestaña de limpieza de sistema - Diseño como Metadatos.
"""
import threading
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

from ..core.cleaner import SystemCleaner


class CleanerTab(ttk.Frame):
    """Pestaña de limpieza de sistema."""

    def __init__(self, parent):
        super().__init__(parent, style='Box.TFrame')
        self.cleaner = SystemCleaner()

        # Variables
        self.folder_var = tk.StringVar()
        self.include_subfolders_var = tk.BooleanVar(value=True)
        self.include_hidden_var = tk.BooleanVar(value=False)
        
        # Opciones de limpieza
        self.clean_temp_var = tk.BooleanVar(value=True)
        self.clean_recycle_var = tk.BooleanVar(value=True)
        self.clean_cache_var = tk.BooleanVar(value=True)
        self.clean_empty_var = tk.BooleanVar(value=True)
        self.clean_duplicates_var = tk.BooleanVar(value=False)
        self.clean_large_var = tk.BooleanVar(value=False)
        self.clean_small_var = tk.BooleanVar(value=False)
        self.clean_thumbnails_var = tk.BooleanVar(value=False)
        self.clean_logs_var = tk.BooleanVar(value=False)
        self.clean_backup_var = tk.BooleanVar(value=False)
        self.clean_windows_temp_var = tk.BooleanVar(value=False)
        self.clean_downloads_var = tk.BooleanVar(value=False)
        self.remove_empty_dirs_var = tk.BooleanVar(value=True)
        
        self.large_size_var = tk.StringVar(value="100")
        self.small_size_var = tk.StringVar(value="10")
        self.logs_days_var = tk.StringVar(value="30")
        self.downloads_days_var = tk.StringVar(value="30")

        # Estado
        self.is_scanning = False
        self.is_running = False
        self.scan_results = []

        self._create_widgets()

    def _create_widgets(self):
        """Crea los widgets de la interfaz - diseño ultra compacto."""
        main_frame = ttk.Frame(self, style='Box.TFrame')
        main_frame.pack(fill="both", expand=True, padx=8, pady=4)

        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)

        # ========== FILA 0: TÍTULO ==========
        title_frame = ttk.Frame(main_frame, style='Box.TFrame')
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.grid_columnconfigure(0, weight=1)
        title_frame.grid_columnconfigure(1, weight=0)

        text_frame = ttk.Frame(title_frame, style='Box.TFrame')
        text_frame.grid(row=0, column=0, sticky="w")

        ttk.Label(text_frame, text="🧹 Limpieza de Sistema", style='Title.TLabel').pack(anchor="w")
        ttk.Label(text_frame, text="Libera espacio eliminando archivos innecesarios", style='Subtitle.TLabel').pack(anchor="w")

        warning_frame = ttk.Frame(title_frame, style='Box.TFrame')
        warning_frame.grid(row=0, column=1, sticky="e", padx=(10, 0))

        warning_label = tk.Label(
            warning_frame,
            text="⚠️ ¡PRECAUCIÓN!",
            font=('Segoe UI', 11, 'bold'),
            bg='#e94560',
            fg='#ffffff',
            padx=12,
            pady=3,
            relief='solid',
            borderwidth=2
        )
        warning_label.pack(side="left", padx=(0, 8))

        warning_sub = tk.Label(
            warning_frame,
            text="Revisa antes de eliminar  |  Archivos del sistema protegidos",
            font=('Segoe UI', 8, 'bold'),
            bg='#1e1e32',
            fg='#ffd93d'
        )
        warning_sub.pack(side="left")

        # ========== FILA 1: UBICACIÓN ==========
        top_frame = ttk.LabelFrame(main_frame, text="📂 UBICACIÓN", style='Box.TLabelframe', padding=5)
        top_frame.grid(row=1, column=0, sticky="ew", pady=(2, 4))
        top_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(top_frame, text="Carpeta:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky="w")
        ttk.Entry(top_frame, textvariable=self.folder_var, style='Custom.TEntry', font=('Segoe UI', 9)).grid(row=0, column=1, sticky="ew", padx=(5, 8))
        ttk.Button(top_frame, text="📂 Examinar", command=self._select_folder, style='Secondary.TButton', width=10).grid(row=0, column=2, padx=(0, 5))
        self.scan_button = ttk.Button(top_frame, text="🔍 ESCANEAR", command=self._scan_files, style='Accent.TButton', width=14)
        self.scan_button.grid(row=0, column=3)

        scan_opts_frame = ttk.Frame(top_frame, style='Box.TFrame')
        scan_opts_frame.grid(row=1, column=0, columnspan=4, sticky="w", pady=(2, 0))
        ttk.Checkbutton(scan_opts_frame, text="🔍 Buscar en subcarpetas", variable=self.include_subfolders_var, style='Custom.TCheckbutton').pack(side="left", padx=(0, 15))
        ttk.Checkbutton(scan_opts_frame, text="👁 Incluir archivos ocultos", variable=self.include_hidden_var, style='Custom.TCheckbutton').pack(side="left")

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

        columns = ("Archivo", "Tamaño", "Tipo", "Acción")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=12)
        self.tree.heading("Archivo", text="📄 Archivo")
        self.tree.heading("Tamaño", text="📦 Tamaño")
        self.tree.heading("Tipo", text="📋 Tipo")
        self.tree.heading("Acción", text="✅ Acción")
        self.tree.column("Archivo", width=220, anchor="w")
        self.tree.column("Tamaño", width=70, anchor="center")
        self.tree.column("Tipo", width=90, anchor="center")
        self.tree.column("Acción", width=70, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind('<<TreeviewSelect>>', self._on_select_file)

        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        summary_frame = ttk.Frame(results_frame, style='Box.TFrame')
        summary_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))

        self.total_files_label = ttk.Label(summary_frame, text="Archivos: 0", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold'))
        self.total_files_label.pack(side="left", padx=(0, 15))
        self.total_size_label = ttk.Label(summary_frame, text="Tamaño total: 0 MB", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold'), foreground='#ffd93d')
        self.total_size_label.pack(side="left")

        # ----- COLUMNA DERECHA: OPCIONES + ACTIVIDAD -----
        right_frame = ttk.Frame(content_frame, style='Box.TFrame')
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        right_frame.grid_rowconfigure(0, weight=0)  # Opciones NO se expanden
        right_frame.grid_rowconfigure(1, weight=1)  # Actividad SÍ se expande
        right_frame.grid_columnconfigure(0, weight=1)

        # ----- OPCIONES (2 columnas) -----
        options_frame = ttk.LabelFrame(right_frame, text="⚙️ OPCIONES DE LIMPIEZA", style='Box.TLabelframe', padding=4)
        options_frame.grid(row=0, column=0, sticky="ew", pady=(0, 1))
        options_frame.grid_columnconfigure(0, weight=1)
        options_frame.grid_columnconfigure(1, weight=1)

        # Columna izquierda
        left_opts = ttk.Frame(options_frame, style='Box.TFrame')
        left_opts.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        left_opts.grid_columnconfigure(0, weight=1)

        # SISTEMA
        sys_frame = ttk.LabelFrame(left_opts, text="🗑️ SISTEMA", style='Box.TLabelframe', padding=3)
        sys_frame.pack(fill="x", pady=(0, 3))
        ttk.Checkbutton(sys_frame, text="🗑️ Papelera de reciclaje", variable=self.clean_recycle_var, style='Custom.TCheckbutton').pack(anchor="w", pady=0)
        ttk.Checkbutton(sys_frame, text="📁 Temp del sistema", variable=self.clean_temp_var, style='Custom.TCheckbutton').pack(anchor="w", pady=0)
        ttk.Checkbutton(sys_frame, text="📦 Temp de Windows", variable=self.clean_windows_temp_var, style='Custom.TCheckbutton').pack(anchor="w", pady=0)
        ttk.Checkbutton(sys_frame, text="🌐 Caché navegadores", variable=self.clean_cache_var, style='Custom.TCheckbutton').pack(anchor="w", pady=0)

        # TAMAÑO
        size_frame = ttk.LabelFrame(left_opts, text="📊 TAMAÑO", style='Box.TLabelframe', padding=3)
        size_frame.pack(fill="x", pady=(0, 3))

        small_row = ttk.Frame(size_frame, style='Box.TFrame')
        small_row.pack(anchor="w", fill="x")
        ttk.Checkbutton(small_row, text="📄 Archivos pequeños", variable=self.clean_small_var, style='Custom.TCheckbutton').pack(side="left")
        size_small_frame = ttk.Frame(small_row, style='Box.TFrame')
        size_small_frame.pack(side="left", padx=(8, 0))
        ttk.Label(size_small_frame, text="<", style='Subtitle.TLabel', font=('Segoe UI', 8)).pack(side="left")
        ttk.Entry(size_small_frame, textvariable=self.small_size_var, style='Custom.TEntry', font=('Segoe UI', 8), width=3).pack(side="left", padx=2)
        ttk.Label(size_small_frame, text="KB", style='Subtitle.TLabel', font=('Segoe UI', 8)).pack(side="left")

        large_row = ttk.Frame(size_frame, style='Box.TFrame')
        large_row.pack(anchor="w", fill="x")
        ttk.Checkbutton(large_row, text="📦 Archivos grandes", variable=self.clean_large_var, style='Custom.TCheckbutton').pack(side="left")
        size_large_frame = ttk.Frame(large_row, style='Box.TFrame')
        size_large_frame.pack(side="left", padx=(8, 0))
        ttk.Label(size_large_frame, text=">", style='Subtitle.TLabel', font=('Segoe UI', 8)).pack(side="left")
        ttk.Entry(size_large_frame, textvariable=self.large_size_var, style='Custom.TEntry', font=('Segoe UI', 8), width=3).pack(side="left", padx=2)
        ttk.Label(size_large_frame, text="MB", style='Subtitle.TLabel', font=('Segoe UI', 8)).pack(side="left")

        # Columna derecha
        right_opts = ttk.Frame(options_frame, style='Box.TFrame')
        right_opts.grid(row=0, column=1, sticky="nsew", padx=(3, 0))
        right_opts.grid_columnconfigure(0, weight=1)

        # ARCHIVOS
        files_frame = ttk.LabelFrame(right_opts, text="📁 ARCHIVOS", style='Box.TLabelframe', padding=3)
        files_frame.pack(fill="x", pady=(0, 3))
        ttk.Checkbutton(files_frame, text="📄 Archivos vacíos (0 B)", variable=self.clean_empty_var, style='Custom.TCheckbutton').pack(anchor="w", pady=0)

        log_row = ttk.Frame(files_frame, style='Box.TFrame')
        log_row.pack(anchor="w", fill="x")
        ttk.Checkbutton(log_row, text="📁 .log antiguos", variable=self.clean_logs_var, style='Custom.TCheckbutton').pack(side="left")
        log_days_frame = ttk.Frame(log_row, style='Box.TFrame')
        log_days_frame.pack(side="left", padx=(8, 0))
        ttk.Label(log_days_frame, text="Días:", style='Subtitle.TLabel', font=('Segoe UI', 8)).pack(side="left")
        ttk.Entry(log_days_frame, textvariable=self.logs_days_var, style='Custom.TEntry', font=('Segoe UI', 8), width=3).pack(side="left", padx=2)

        ttk.Checkbutton(files_frame, text="💾 Archivos de respaldo", variable=self.clean_backup_var, style='Custom.TCheckbutton').pack(anchor="w", pady=0)
        ttk.Checkbutton(files_frame, text="🖼️ Miniaturas", variable=self.clean_thumbnails_var, style='Custom.TCheckbutton').pack(anchor="w", pady=0)

        # OTROS
        otros_frame = ttk.LabelFrame(right_opts, text="🧹 OTROS", style='Box.TLabelframe', padding=3)
        otros_frame.pack(fill="x", pady=(0, 3))
        ttk.Checkbutton(otros_frame, text="🔄 Archivos duplicados", variable=self.clean_duplicates_var, style='Custom.TCheckbutton').pack(anchor="w", pady=0)

        download_row = ttk.Frame(otros_frame, style='Box.TFrame')
        download_row.pack(anchor="w", fill="x")
        ttk.Checkbutton(download_row, text="⬇️ Descargas antiguas", variable=self.clean_downloads_var, style='Custom.TCheckbutton').pack(side="left")
        download_days_frame = ttk.Frame(download_row, style='Box.TFrame')
        download_days_frame.pack(side="left", padx=(8, 0))
        ttk.Label(download_days_frame, text="Días:", style='Subtitle.TLabel', font=('Segoe UI', 8)).pack(side="left")
        ttk.Entry(download_days_frame, textvariable=self.downloads_days_var, style='Custom.TEntry', font=('Segoe UI', 8), width=3).pack(side="left", padx=2)

        ttk.Checkbutton(otros_frame, text="🗑️ Eliminar carpetas vacías", variable=self.remove_empty_dirs_var, style='Custom.TCheckbutton').pack(anchor="w", pady=0)

        # ----- ACTIVIDAD (debajo de opciones, ocupa el resto) -----
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
        accion_frame.grid_columnconfigure(3, weight=1)  # <--- 4 columnas

        # Botones en una sola fila (todos juntos)
        self.scan_button = ttk.Button(accion_frame, text="🔍 ESCANEAR", command=self._scan_files, style='Accent.TButton')
        self.scan_button.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)

        self.clean_button = ttk.Button(accion_frame, text="🧹 LIMPIAR", command=self._clean_files, style='Accent.TButton', state="disabled")
        self.clean_button.grid(row=0, column=1, sticky="ew", padx=(4, 4), pady=2)

        self.cancel_button = ttk.Button(accion_frame, text="⏹ CANCELAR", command=self._cancel_operation, style='Secondary.TButton', state="disabled")
        self.cancel_button.grid(row=0, column=2, sticky="ew", padx=(4, 4), pady=2)

        self.clean_all_button = ttk.Button(accion_frame, text="🧹 LIMPIAR TODO", command=self._clean_all, style='Secondary.TButton')
        self.clean_all_button.grid(row=0, column=3, sticky="ew", padx=(4, 0), pady=2)

        self.progress = ttk.Progressbar(accion_frame, mode='determinate', style='Custom.Horizontal.TProgressbar', maximum=100)
        self.progress.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(4, 0))

        self.progress_label = ttk.Label(accion_frame, text="", style='Subtitle.TLabel', font=('Segoe UI', 8))
        self.progress_label.grid(row=2, column=0, columnspan=4, sticky="e", pady=(1, 0))

    # ========== MÉTODOS DE FUNCIONALIDAD ==========

    def _select_folder(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta a escanear")
        if folder:
            self.folder_var.set(folder)

    def _update_progress_scan(self, current, total, message=""):
        """Actualiza la barra de progreso y el texto de escaneo."""
        if total > 0:
            porcentaje = int((current / total) * 100)
            self.progress['value'] = porcentaje
            
            if message:
                self.progress_label.config(text=f"{message} ({porcentaje}%)")
            else:
                self.progress_label.config(text=f"🔍 Escaneando... {porcentaje}%")
            
            self._update_log_progress(f"{message if message else 'Escaneando...'} ({porcentaje}%)")

    def _update_log_progress(self, message: str):
        """Sobrescribe la última línea del log con el progreso."""
        if self.log_text.index('end-1c') != '1.0':
            self.log_text.delete("end-2l", "end-1l")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def _scan_files(self):
        if not self.folder_var.get():
            messagebox.showerror("Error", "Selecciona una carpeta para escanear.")
            return

        self.is_scanning = True
        self.scan_button.config(state="disabled")
        self.clean_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.clean_all_button.config(state="disabled")

        self.tree.delete(*self.tree.get_children())
        self.scan_results = []
        self.progress['value'] = 0
        self.progress_label.config(text="Escaneando...")

        self._log("🔍 Iniciando escaneo (archivos del sistema protegidos)...")

        thread = threading.Thread(target=self._run_scan)
        thread.daemon = True
        thread.start()

    def _run_scan(self):
        try:
            folder = Path(self.folder_var.get())
            large_size = int(self.large_size_var.get() or 100)
            small_size = int(self.small_size_var.get() or 10)
            logs_days = int(self.logs_days_var.get() or 30)
            downloads_days = int(self.downloads_days_var.get() or 30)

            self._log("🛡️ Protegiendo archivos críticos del sistema...")

            results = self.cleaner.scan(
                folder=folder,
                include_subfolders=self.include_subfolders_var.get(),
                include_hidden=self.include_hidden_var.get(),
                clean_temp=self.clean_temp_var.get(),
                clean_recycle=self.clean_recycle_var.get(),
                clean_cache=self.clean_cache_var.get(),
                clean_empty=self.clean_empty_var.get(),
                clean_duplicates=self.clean_duplicates_var.get(),
                clean_large=self.clean_large_var.get(),
                clean_small=self.clean_small_var.get(),
                clean_thumbnails=self.clean_thumbnails_var.get(),
                clean_logs=self.clean_logs_var.get(),
                clean_backup=self.clean_backup_var.get(),
                clean_windows_temp=self.clean_windows_temp_var.get(),
                clean_downloads=self.clean_downloads_var.get(),
                large_size_mb=large_size,
                small_size_kb=small_size,
                logs_days_old=logs_days,
                downloads_days_old=downloads_days,
                progress_callback=self._update_progress_scan
            )

            self.scan_results = results
            self.after(0, self._on_scan_complete)

        except Exception as e:
            self.after(0, self._on_scan_error, str(e))

    def _on_scan_complete(self):
        self.is_scanning = False
        self.scan_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.clean_all_button.config(state="normal")

        # Mostrar resultados
        for item in self.scan_results:
            size_mb = item.get('size_mb', 0)
            size_str = f"{size_mb:.1f} MB" if size_mb > 1 else f"{item.get('size', 0)} B"
            
            tipo = item.get('type', 'other')
            tipo_labels = {
                'recycle': '🗑️ Papelera',
                'temp': '📁 Temp',
                'cache': '🌐 Caché',
                'empty': '📄 Vacío',
                'empty_dir': '📁 Carpeta vacía',
                'duplicate': '🔄 Duplicado',
                'large': '📦 Grande',
                'small': '📄 Pequeño',
                'thumbnails': '🖼️ Miniatura',
                'logs': '📁 Log',
                'backup': '💾 Respaldo',
                'windows_temp': '📦 Temp Win',
                'downloads': '⬇️ Descarga'
            }
            tipo_label = tipo_labels.get(tipo, tipo)

            self.tree.insert("", "end", values=(
                item.get('path', ''),
                size_str,
                tipo_label,
                "🗑️ Eliminar"
            ))

        # Resumen
        summary = self.cleaner.get_summary(self.scan_results)
        total_files = summary.get('total_files', 0)
        total_size = summary.get('total_size', 0)
        total_size_mb = summary.get('total_size_mb', 0)

        self.total_files_label.config(text=f"Archivos: {total_files}")
        self.total_size_label.config(text=f"Tamaño total: {total_size_mb:.1f} MB ({total_size_mb/1024:.2f} GB)")

        self._log(f"✅ Escaneo completado: {total_files} archivos encontrados ({total_size_mb:.1f} MB)")

        if total_files > 0:
            self.clean_button.config(state="normal")
            messagebox.showinfo("Escaneo completado", 
                f"Se encontraron {total_files} archivos.\n"
                f"Tamaño total: {total_size_mb:.1f} MB")
        else:
            messagebox.showinfo("Escaneo completado", "No se encontraron archivos para limpiar.")

    def _on_scan_error(self, error_msg):
        self.is_scanning = False
        self.scan_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.clean_all_button.config(state="normal")
        self._log(f"❌ Error: {error_msg}")
        messagebox.showerror("Error", error_msg)

    def _clean_files(self):
        if not self.scan_results:
            messagebox.showerror("Error", "Primero escanea archivos.")
            return

        total_files = len(self.scan_results)
        total_size = sum(f.get('size', 0) for f in self.scan_results)
        total_size_mb = total_size / (1024 * 1024)

        if not messagebox.askyesno(
            "Confirmar limpieza",
            f"¿Eliminar {total_files} archivos?\n"
            f"Tamaño total: {total_size_mb:.1f} MB\n\n"
            "⚠️ Esta acción no se puede deshacer."
        ):
            return

        self.is_running = True
        self.scan_button.config(state="disabled")
        self.clean_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.clean_all_button.config(state="disabled")

        self.progress['value'] = 0
        self._log("🧹 Iniciando limpieza...")

        thread = threading.Thread(target=self._run_clean)
        thread.daemon = True
        thread.start()

    def _run_clean(self):
        try:
            result = self.cleaner.clean(
                self.scan_results,
                progress_callback=self._update_progress_clean
            )

            self.after(0, self._on_clean_complete, result)

        except Exception as e:
            self.after(0, self._on_clean_error, str(e))

    def _update_progress_clean(self, current, total):
        if total > 0:
            porcentaje = int((current / total) * 100)
            self.progress['value'] = porcentaje
            self.progress_label.config(text=f"Limpiando... {current}/{total} ({porcentaje}%)")

    def _on_clean_complete(self, result):
        self.is_running = False
        self.scan_button.config(state="normal")
        self.clean_button.config(state="disabled")
        self.cancel_button.config(state="disabled")
        self.clean_all_button.config(state="normal")

        self.progress['value'] = 100
        self.progress_label.config(text="")

        self._log("-" * 50)

        if result.get('cancelled', False):
            self._log(f"⏹ LIMPIEZA CANCELADA")
            self._log(f"📊 Limpiados: {result['cleaned']} de {result['total']}")
            messagebox.showinfo("Cancelado",
                f"Limpieza cancelada.\nLimpiados: {result['cleaned']} de {result['total']}")
        else:
            protected = result.get('protected', 0)
            msg = f"✅ Eliminados: {result['cleaned']}\n⚠️ Errores: {result['errors']}"
            if protected > 0:
                msg += f"\n🛡️ Protegidos (no eliminados): {protected}"
            
            self._log(f"✅ ¡LIMPIEZA COMPLETADA!")
            self._log(f"📊 Archivos eliminados: {result['cleaned']}")
            self._log(f"⚠️ Errores: {result['errors']}")
            if protected > 0:
                self._log(f"🛡️ Protegidos (no eliminados): {protected}")

            if result['errors'] > 0:
                messagebox.showwarning(
                    "Limpieza completada con errores",
                    msg
                )
            else:
                messagebox.showinfo("Éxito", msg)

        # Limpiar tabla
        self.tree.delete(*self.tree.get_children())
        self.scan_results = []
        self.total_files_label.config(text="Archivos: 0")
        self.total_size_label.config(text="Tamaño total: 0 MB")

    def _on_clean_error(self, error_msg):
        self.is_running = False
        self.scan_button.config(state="normal")
        self.clean_button.config(state="disabled")
        self.cancel_button.config(state="disabled")
        self.clean_all_button.config(state="normal")
        self.progress['value'] = 0
        self.progress_label.config(text="")
        self._log(f"❌ Error: {error_msg}")
        messagebox.showerror("Error", error_msg)

    def _cancel_operation(self):
        if self.is_scanning or self.is_running:
            self.cleaner.cancel()
            self._log("⏹ SOLICITANDO CANCELACIÓN...")

    def _clean_all(self):
        self.folder_var.set("")
        self.tree.delete(*self.tree.get_children())
        self.scan_results = []
        self.total_files_label.config(text="Archivos: 0")
        self.total_size_label.config(text="Tamaño total: 0 MB")
        self.progress['value'] = 0
        self.progress_label.config(text="")
        self.log_text.delete("1.0", tk.END)
        self.clean_button.config(state="disabled")
        self._log("🧹 Todo limpiado. Listo para empezar.")

    def _on_select_file(self, event):
        pass  # Por ahora no hacemos nada al seleccionar

    def _log(self, message: str):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
