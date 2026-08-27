"""
Pestaña para renombrar archivos en masa - Diseño tipo Limpieza/Metadatos.
"""
import threading
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

from ..core.renamer import FileRenamer


class RenameTab(ttk.Frame):
    """Pestaña de renombrado masivo con diseño tipo Limpieza."""

    def __init__(self, parent):
        super().__init__(parent, style='Box.TFrame')
        self.renamer = FileRenamer()

        # Variables
        self.source_var = tk.StringVar()
        self.include_subfolders_var = tk.BooleanVar(value=True)
        
        # Opciones de renombrado
        self.prefix_var = tk.StringVar()
        self.base_name_var = tk.StringVar()
        self.suffix_var = tk.StringVar()
        self.numbering_var = tk.BooleanVar(value=False)
        self.number_start_var = tk.StringVar(value="1")
        self.number_digits_var = tk.StringVar(value="2")
        self.replace_from_var = tk.StringVar()
        self.replace_to_var = tk.StringVar()
        self.use_date_var = tk.BooleanVar(value=False)
        self.date_format_var = tk.StringVar(value="%Y-%m-%d")
        self.lowercase_var = tk.BooleanVar(value=False)
        self.uppercase_var = tk.BooleanVar(value=False)
        self.remove_spaces_var = tk.BooleanVar(value=False)
        
        # Extensiones
        self.extensions_var = tk.StringVar(value="*.jpg,*.png,*.mp4,*.pdf")
        
        # Estado
        self.is_running = False
        self.operation_thread = None
        self.preview_data = []

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

        ttk.Label(text_frame, text="📝 Renombrar Archivos", style='Title.TLabel').pack(anchor="w")
        ttk.Label(text_frame, text="Renombra múltiples archivos con patrones personalizados", style='Subtitle.TLabel').pack(anchor="w")

        # ========== FILA 1: UBICACIÓN Y EXTENSIONES ==========
        top_frame = ttk.LabelFrame(main_frame, text="📂 UBICACIÓN", style='Box.TLabelframe', padding=5)
        top_frame.grid(row=1, column=0, sticky="ew", pady=(2, 4))
        top_frame.grid_columnconfigure(1, weight=1)

        # Origen
        ttk.Label(top_frame, text="Origen:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky="w")
        ttk.Entry(top_frame, textvariable=self.source_var, style='Custom.TEntry', font=('Segoe UI', 9)).grid(row=0, column=1, sticky="ew", padx=(5, 8))
        ttk.Button(top_frame, text="📂 Examinar", command=self._select_source, style='Secondary.TButton', width=10).grid(row=0, column=2, padx=(0, 5))

        # Extensiones
        ttk.Label(top_frame, text="Extensiones:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).grid(row=1, column=0, sticky="w", pady=(2, 0))
        ttk.Entry(top_frame, textvariable=self.extensions_var, style='Custom.TEntry', font=('Segoe UI', 9)).grid(row=1, column=1, sticky="ew", padx=(5, 8), pady=(2, 0))
        ttk.Label(top_frame, text="*.jpg,*.png,*.mp4", style='Subtitle.TLabel', font=('Segoe UI', 8, 'italic'), foreground='#b8b8d0').grid(row=1, column=2, padx=(0, 5), pady=(2, 0))

        # Opciones de escaneo
        scan_opts_frame = ttk.Frame(top_frame, style='Box.TFrame')
        scan_opts_frame.grid(row=2, column=0, columnspan=3, sticky="w", pady=(5, 0))
        ttk.Checkbutton(scan_opts_frame, text="🔍 Buscar en subcarpetas", variable=self.include_subfolders_var, style='Custom.TCheckbutton').pack(side="left")

        # ========== FILA 2: RESULTADOS + OPCIONES + ACTIVIDAD ==========
        content_frame = ttk.Frame(main_frame, style='Box.TFrame')
        content_frame.grid(row=2, column=0, sticky="nsew")
        content_frame.grid_columnconfigure(0, weight=2)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)

        # ----- COLUMNA IZQUIERDA: VISTA PREVIA -----
        preview_frame = ttk.LabelFrame(content_frame, text="📋 VISTA PREVIA", style='Box.TLabelframe', padding=4)
        preview_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        columns = ("Original", "Nuevo")
        self.tree = ttk.Treeview(preview_frame, columns=columns, show="headings", height=12)
        self.tree.heading("Original", text="📄 Nombre Original")
        self.tree.heading("Nuevo", text="✅ Nuevo Nombre")

        self.tree.column("Original", width=250, anchor="w")
        self.tree.column("Nuevo", width=250, anchor="w")

        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Resumen
        summary_frame = ttk.Frame(preview_frame, style='Box.TFrame')
        summary_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))

        self.preview_count_label = ttk.Label(summary_frame, text="Archivos: 0", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold'))
        self.preview_count_label.pack(side="left", padx=(0, 15))
        self.preview_status_label = ttk.Label(summary_frame, text="", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold'), foreground='#ffd93d')
        self.preview_status_label.pack(side="left")

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

        # Prefijo + Nombre base (misma línea)
        row1 = ttk.Frame(options_frame, style='Box.TFrame')
        row1.pack(anchor="w", fill="x", pady=2)
        row1.grid_columnconfigure(1, weight=1)
        row1.grid_columnconfigure(3, weight=1)

        ttk.Label(row1, text="Prefijo:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky="w", padx=(0, 5))
        ttk.Entry(row1, textvariable=self.prefix_var, style='Custom.TEntry', font=('Segoe UI', 9)).grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ttk.Label(row1, text="📝 Nombre base:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).grid(row=0, column=2, sticky="w", padx=(0, 5))
        ttk.Entry(row1, textvariable=self.base_name_var, style='Custom.TEntry', font=('Segoe UI', 9)).grid(row=0, column=3, sticky="ew")

        # Sufijo + Reemplazar (misma línea)
        row2 = ttk.Frame(options_frame, style='Box.TFrame')
        row2.pack(anchor="w", fill="x", pady=2)
        row2.grid_columnconfigure(1, weight=1)
        row2.grid_columnconfigure(3, weight=1)

        ttk.Label(row2, text="Sufijo:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky="w", padx=(0, 5))
        ttk.Entry(row2, textvariable=self.suffix_var, style='Custom.TEntry', font=('Segoe UI', 9)).grid(row=0, column=1, sticky="ew", padx=(0, 10))
        ttk.Label(row2, text="Reemplazar:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).grid(row=0, column=2, sticky="w", padx=(0, 5))

        replace_frame = ttk.Frame(row2, style='Box.TFrame')
        replace_frame.grid(row=0, column=3, sticky="ew")
        ttk.Entry(replace_frame, textvariable=self.replace_from_var, style='Custom.TEntry', font=('Segoe UI', 9), width=8).pack(side="left", fill="x", expand=True, padx=(0, 2))
        ttk.Label(replace_frame, text="→", style='Subtitle.TLabel', font=('Segoe UI', 10, 'bold')).pack(side="left", padx=2)
        ttk.Entry(replace_frame, textvariable=self.replace_to_var, style='Custom.TEntry', font=('Segoe UI', 9), width=8).pack(side="left", fill="x", expand=True, padx=(2, 0))

        # Numeración + Fecha + Opciones
        row3 = ttk.Frame(options_frame, style='Box.TFrame')
        row3.pack(anchor="w", fill="x", pady=(5, 2))

        # Numeración
        num_frame = ttk.Frame(row3, style='Box.TFrame')
        num_frame.pack(side="left", padx=(0, 15))
        ttk.Checkbutton(num_frame, text="Numeración:", variable=self.numbering_var, style='Custom.TCheckbutton').pack(side="left")
        ttk.Entry(num_frame, textvariable=self.number_start_var, style='Custom.TEntry', font=('Segoe UI', 9), width=3).pack(side="left", padx=(5, 2))
        ttk.Label(num_frame, text="→", style='Subtitle.TLabel', font=('Segoe UI', 10, 'bold')).pack(side="left", padx=2)
        ttk.Entry(num_frame, textvariable=self.number_digits_var, style='Custom.TEntry', font=('Segoe UI', 9), width=3).pack(side="left", padx=2)
        ttk.Label(num_frame, text="dígitos", style='Subtitle.TLabel', font=('Segoe UI', 8)).pack(side="left", padx=(2, 0))

        # Fecha
        date_frame = ttk.Frame(row3, style='Box.TFrame')
        date_frame.pack(side="left", padx=(0, 15))
        ttk.Checkbutton(date_frame, text="📅 Fecha", variable=self.use_date_var, style='Custom.TCheckbutton').pack(side="left")
        ttk.Entry(date_frame, textvariable=self.date_format_var, style='Custom.TEntry', font=('Segoe UI', 9), width=10).pack(side="left", padx=5)
        ttk.Label(date_frame, text="(%Y-%m-%d)", style='Subtitle.TLabel', font=('Segoe UI', 8, 'italic')).pack(side="left")

        # Opciones extras
        extra_frame = ttk.Frame(options_frame, style='Box.TFrame')
        extra_frame.pack(anchor="w", fill="x", pady=(5, 0))

        ttk.Checkbutton(extra_frame, text="🔡 Minúsculas", variable=self.lowercase_var, style='Custom.TCheckbutton').pack(side="left", padx=(0, 10))
        ttk.Checkbutton(extra_frame, text="🔠 Mayúsculas", variable=self.uppercase_var, style='Custom.TCheckbutton').pack(side="left", padx=(0, 10))
        ttk.Checkbutton(extra_frame, text="✨ Eliminar espacios", variable=self.remove_spaces_var, style='Custom.TCheckbutton').pack(side="left")

        # Botón Vista Previa
        preview_btn_frame = ttk.Frame(options_frame, style='Box.TFrame')
        preview_btn_frame.pack(anchor="w", fill="x", pady=(8, 0))

        self.preview_button = ttk.Button(preview_btn_frame, text="👁️ VISTA PREVIA", command=self._generate_preview, style='Secondary.TButton')
        self.preview_button.pack(side="left")

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

        self.rename_button = ttk.Button(accion_frame, text="🔄 RENOMBRAR", command=self._execute_rename, style='Accent.TButton')
        self.rename_button.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)

        self.cancel_button = ttk.Button(accion_frame, text="⏹ CANCELAR", command=self._cancel_operation, style='Secondary.TButton', state="disabled")
        self.cancel_button.grid(row=0, column=1, sticky="ew", padx=(4, 4), pady=2)

        self.clean_button = ttk.Button(accion_frame, text="🧹 LIMPIAR TODO", command=self._clean_all, style='Secondary.TButton')
        self.clean_button.grid(row=0, column=2, sticky="ew", padx=(4, 0), pady=2)

        self.progress = ttk.Progressbar(accion_frame, mode='determinate', style='Custom.Horizontal.TProgressbar', maximum=100)
        self.progress.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(4, 0))

        self.progress_label = ttk.Label(accion_frame, text="", style='Subtitle.TLabel', font=('Segoe UI', 8))
        self.progress_label.grid(row=2, column=0, columnspan=3, sticky="e", pady=(1, 0))

    # ========== MÉTODOS DE FUNCIONALIDAD ==========

    def _select_source(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta origen")
        if folder:
            self.source_var.set(folder)

    def _parse_extensions(self) -> list:
        ext_str = self.extensions_var.get().strip()
        if not ext_str:
            return None
        ext_list = [e.strip() for e in ext_str.split(',') if e.strip()]
        cleaned = []
        for e in ext_list:
            if not e.startswith('*'):
                if not e.startswith('.'):
                    e = f".{e}"
            else:
                e = e.replace('*', '')
                if not e.startswith('.'):
                    e = f".{e}"
            cleaned.append(e)
        return cleaned

    def _update_progress(self, current, total):
        if total > 0:
            porcentaje = int((current / total) * 100)
            self.progress['value'] = porcentaje
            self.progress_label.config(text=f"{current}/{total} ({porcentaje}%)")

    def _generate_preview(self):
        if not self.source_var.get():
            messagebox.showerror("Error", "Selecciona una carpeta origen.")
            return

        source = Path(self.source_var.get())
        if not source.exists():
            messagebox.showerror("Error", "La carpeta origen no existe.")
            return

        try:
            extensions = self._parse_extensions()
            number_start = int(self.number_start_var.get() or 1)
            number_digits = int(self.number_digits_var.get() or 2)

            self.tree.delete(*self.tree.get_children())

            preview = self.renamer.get_preview(
                source_dir=source,
                include_subfolders=self.include_subfolders_var.get(),
                extensions=extensions,
                base_name=self.base_name_var.get(),
                prefix=self.prefix_var.get(),
                suffix=self.suffix_var.get(),
                numbering=self.numbering_var.get(),
                number_start=number_start,
                number_digits=number_digits,
                replace_from=self.replace_from_var.get(),
                replace_to=self.replace_to_var.get(),
                use_date=self.use_date_var.get(),
                date_format=self.date_format_var.get(),
                lowercase=self.lowercase_var.get(),
                uppercase=self.uppercase_var.get(),
                remove_spaces=self.remove_spaces_var.get()
            )

            self.preview_data = preview

            if not preview:
                self._log("📭 No se encontraron archivos.")
                self.preview_count_label.config(text="Archivos: 0")
                self.preview_status_label.config(text="")
                return

            for orig, new in preview[:50]:
                self.tree.insert("", "end", values=(orig.name, new))

            count = len(preview)
            self._log(f"👁️ Vista previa generada: {count} archivos")
            self.preview_count_label.config(text=f"Archivos: {count}")
            self.preview_status_label.config(text="✅ Listo para renombrar")

            if count > 50:
                self._log(f"ℹ️ Mostrando los primeros 50 de {count} archivos")

        except ValueError as e:
            messagebox.showerror("Error", f"Valor inválido en numeración:\n{e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar preview:\n{e}")

    def _execute_rename(self):
        if not self.source_var.get():
            messagebox.showerror("Error", "Selecciona una carpeta origen.")
            return

        if not self.preview_data:
            messagebox.showerror("Error", "Genera una vista previa primero.")
            return

        count = len(self.preview_data)
        if not messagebox.askyesno(
            "Confirmar renombrado",
            f"¿Renombrar {count} archivos?\n\nEsta acción no se puede deshacer fácilmente."
        ):
            return

        self.is_running = True
        self.rename_button.config(state="disabled")
        self.preview_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.clean_button.config(state="disabled")

        self.renamer.reset()
        self.progress['value'] = 0
        self._log("🔄 INICIANDO RENOMBRADO...")

        thread = threading.Thread(target=self._run_rename)
        thread.daemon = True
        thread.start()

    def _run_rename(self):
        try:
            source = Path(self.source_var.get())
            number_start = int(self.number_start_var.get() or 1)
            number_digits = int(self.number_digits_var.get() or 2)
            extensions = self._parse_extensions()

            summary = self.renamer.rename_files(
                source_dir=source,
                include_subfolders=self.include_subfolders_var.get(),
                extensions=extensions,
                base_name=self.base_name_var.get(),
                prefix=self.prefix_var.get(),
                suffix=self.suffix_var.get(),
                numbering=self.numbering_var.get(),
                number_start=number_start,
                number_digits=number_digits,
                replace_from=self.replace_from_var.get(),
                replace_to=self.replace_to_var.get(),
                use_date=self.use_date_var.get(),
                date_format=self.date_format_var.get(),
                lowercase=self.lowercase_var.get(),
                uppercase=self.uppercase_var.get(),
                remove_spaces=self.remove_spaces_var.get(),
                progress_callback=self._update_progress
            )

            self.after(0, self._on_rename_complete, summary)

        except Exception as e:
            self.after(0, self._on_rename_error, str(e))

    def _cancel_operation(self):
        if self.is_running:
            self.renamer.cancel()
            self._log("⏹ SOLICITANDO CANCELACIÓN...")

    def _clean_all(self):
        self.source_var.set("")
        self.prefix_var.set("")
        self.suffix_var.set("")
        self.base_name_var.set("")
        self.replace_from_var.set("")
        self.replace_to_var.set("")
        self.extensions_var.set("*.jpg,*.png,*.mp4,*.pdf")
        self.tree.delete(*self.tree.get_children())
        self.preview_data = []
        self.preview_count_label.config(text="Archivos: 0")
        self.preview_status_label.config(text="")
        self.log_text.delete("1.0", tk.END)
        self.progress['value'] = 0
        self.progress_label.config(text="")
        self._log("🧹 Todo limpiado. Listo para empezar.")

    def _on_rename_complete(self, summary: dict):
        self.is_running = False
        self.progress['value'] = 100

        self.rename_button.config(state="normal")
        self.preview_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.clean_button.config(state="normal")

        self._log("-" * 40)

        if summary.get('cancelled', False):
            self._log(f"⏹ OPERACIÓN CANCELADA")
            self._log(f"📊 Procesados: {summary['processed']} de {summary['total']}")
            messagebox.showinfo("Cancelado",
                f"Operación cancelada.\nProcesados: {summary['processed']} de {summary['total']}")
        else:
            self._log(f"✅ ¡RENOMBRADO COMPLETADO!")
            self._log(f"📊 Archivos renombrados: {summary['processed']}  |  ⚠️ Errores: {summary['errors']}")

            self.preview_status_label.config(text="✅ Renombrado completado")

            # Actualizar preview
            self._generate_preview()

            if summary['errors'] > 0:
                messagebox.showwarning(
                    "Completado con errores",
                    f"✅ Renombrados: {summary['processed']}\n⚠️ Errores: {summary['errors']}"
                )
            else:
                messagebox.showinfo("Éxito", f"✅ {summary['processed']} archivos renombrados correctamente.")

    def _on_rename_error(self, error_msg: str):
        self.is_running = False
        self.progress['value'] = 0

        self.rename_button.config(state="normal")
        self.preview_button.config(state="normal")
        self.cancel_button.config(state="disabled")
        self.clean_button.config(state="normal")

        self._log(f"❌ ERROR: {error_msg}")
        messagebox.showerror("Error", error_msg)

    def _log(self, message: str):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
