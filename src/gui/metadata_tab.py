"""
Pestaña para gestionar metadatos de música - Diseño como Limpieza.
"""
import threading
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

from ..core.metadata_manager import MetadataManager
from ..core.name_cleaner import NameCleaner


class MetadataTab(ttk.Frame):
    """Pestaña de gestión de metadatos y limpieza de nombres."""

    def __init__(self, parent):
        super().__init__(parent, style='Box.TFrame')
        self.metadata_manager = MetadataManager()
        self.name_cleaner = NameCleaner()

        # Variables
        self.source_var = tk.StringVar()
        self.search_subfolders_var = tk.BooleanVar(value=True)
        self.current_files = []
        self.current_index = 0
        self.editing_file = None

        # Limpieza de nombres
        self.remove_track_var = tk.BooleanVar(value=True)
        self.remove_brackets_var = tk.BooleanVar(value=True)
        self.remove_parentheses_var = tk.BooleanVar(value=True)
        self.remove_words_var = tk.StringVar()
        self.custom_text_var = tk.StringVar()

        # Variables para edición
        self.edit_artista_var = tk.StringVar()
        self.edit_album_var = tk.StringVar()
        self.edit_titulo_var = tk.StringVar()
        self.edit_año_var = tk.StringVar()
        self.edit_genero_var = tk.StringVar()
        self.edit_numero_var = tk.StringVar()

        # ========== VARIABLES FALTANTES ==========
        self.use_metadata_var = tk.BooleanVar(value=True)
        self.parse_filename_var = tk.BooleanVar(value=True)
        self.order_var = tk.StringVar(value="año_album_artista")
        self.operation_var = tk.StringVar(value="move")

        # Estado
        self.is_scanning = False
        self.is_running = False

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

        ttk.Label(text_frame, text="🏷️ Metadatos", style='Title.TLabel').pack(anchor="w")
        ttk.Label(text_frame, text="Gestiona metadatos y limpia nombres de archivos de música", style='Subtitle.TLabel').pack(anchor="w")

        # ========== FILA 1: UBICACIÓN Y ESCANEO ==========
        top_frame = ttk.LabelFrame(main_frame, text="📂 UBICACIÓN Y ESCANEO", style='Box.TLabelframe', padding=5)
        top_frame.grid(row=1, column=0, sticky="ew", pady=(2, 4))
        top_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(top_frame, text="Carpeta:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky="w")
        ttk.Entry(top_frame, textvariable=self.source_var, style='Custom.TEntry', font=('Segoe UI', 9)).grid(row=0, column=1, sticky="ew", padx=(5, 8))
        ttk.Button(top_frame, text="📂 Examinar", command=self._select_source, style='Secondary.TButton', width=10).grid(row=0, column=2, padx=(0, 5))
        self.scan_button = ttk.Button(top_frame, text="🔍 ESCANEAR", command=self._scan_files, style='Accent.TButton', width=14)
        self.scan_button.grid(row=0, column=3)

        scan_opts_frame = ttk.Frame(top_frame, style='Box.TFrame')
        scan_opts_frame.grid(row=1, column=0, columnspan=4, sticky="w", pady=(2, 0))
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

        columns = ("Archivo", "Artista", "Álbum", "Título", "Año", "Estado")
        self.tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=12)
        self.tree.heading("Archivo", text="📄 Archivo")
        self.tree.heading("Artista", text="🎤 Artista")
        self.tree.heading("Álbum", text="💿 Álbum")
        self.tree.heading("Título", text="🎵 Título")
        self.tree.heading("Año", text="📅 Año")
        self.tree.heading("Estado", text="✅ Estado")

        self.tree.column("Archivo", width=150, anchor="w")
        self.tree.column("Artista", width=100, anchor="w")
        self.tree.column("Álbum", width=100, anchor="w")
        self.tree.column("Título", width=100, anchor="w")
        self.tree.column("Año", width=50, anchor="center")
        self.tree.column("Estado", width=50, anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind('<<TreeviewSelect>>', self._on_select_file)

        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        summary_frame = ttk.Frame(results_frame, style='Box.TFrame')
        summary_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 0))

        self.total_label = ttk.Label(summary_frame, text="Total: 0", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold'))
        self.total_label.pack(side="left", padx=(0, 15))
        self.complete_label = ttk.Label(summary_frame, text="✅ Completos: 0", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold'), foreground='#00d2ff')
        self.complete_label.pack(side="left", padx=(0, 15))
        self.incomplete_label = ttk.Label(summary_frame, text="⚠️ Incompletos: 0", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold'), foreground='#ffd93d')
        self.incomplete_label.pack(side="left", padx=(0, 15))
        self.missing_label = ttk.Label(summary_frame, text="❌ Sin metadatos: 0", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold'), foreground='#e94560')
        self.missing_label.pack(side="left")

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

        # Fuente de información
        ttk.Label(options_frame, text="📋 Fuente de información:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).pack(anchor="w", pady=(0, 5))
        ttk.Checkbutton(options_frame, text="🎵 Leer metadatos ID3 (recomendado)", variable=self.use_metadata_var, style='Custom.TCheckbutton').pack(anchor="w", pady=1)
        ttk.Checkbutton(options_frame, text="📝 Analizar nombre del archivo", variable=self.parse_filename_var, style='Custom.TCheckbutton').pack(anchor="w", pady=1)

        # Estructura de carpetas
        ttk.Label(options_frame, text="\n📂 Estructura de carpetas:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).pack(anchor="w", pady=(5, 5))
        orden_frame = ttk.Frame(options_frame, style='Box.TFrame')
        orden_frame.pack(anchor="w", fill="x", pady=(0, 5))

        ttk.Radiobutton(orden_frame, text="📁 Año / Álbum / Artista (por defecto)", variable=self.order_var, value="año_album_artista", style='Custom.TRadiobutton').pack(anchor="w", pady=0)
        ttk.Radiobutton(orden_frame, text="📁 Artista / Año / Álbum", variable=self.order_var, value="artista_año_album", style='Custom.TRadiobutton').pack(anchor="w", pady=0)
        ttk.Radiobutton(orden_frame, text="📁 Álbum / Artista", variable=self.order_var, value="album_artista", style='Custom.TRadiobutton').pack(anchor="w", pady=0)
        ttk.Radiobutton(orden_frame, text="📁 Año / Género", variable=self.order_var, value="año_genero", style='Custom.TRadiobutton').pack(anchor="w", pady=0)

        # Modo
        ttk.Label(options_frame, text="\n🔧 Modo:", style='Subtitle.TLabel', font=('Segoe UI', 9, 'bold')).pack(anchor="w", pady=(5, 5))
        ttk.Radiobutton(options_frame, text="📦 Mover", variable=self.operation_var, value="move", style='Custom.TRadiobutton').pack(anchor="w", pady=0)
        ttk.Radiobutton(options_frame, text="📋 Copiar", variable=self.operation_var, value="copy", style='Custom.TRadiobutton').pack(anchor="w", pady=0)

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
        accion_frame.grid_columnconfigure(3, weight=1)

        self.save_individual_button = ttk.Button(accion_frame, text="💾 GUARDAR", command=self._save_metadata, style='Accent.TButton', state="disabled")
        self.save_individual_button.grid(row=0, column=0, sticky="ew", padx=(0, 4), pady=2)

        self.save_metadata_button = ttk.Button(accion_frame, text="💾 GUARDAR TODO", command=self._save_all_metadata, style='Accent.TButton')
        self.save_metadata_button.grid(row=0, column=1, sticky="ew", padx=(4, 4), pady=2)

        self.rename_files_button = ttk.Button(accion_frame, text="📝 RENOMBRAR", command=self._rename_files, style='Accent.TButton')
        self.rename_files_button.grid(row=0, column=2, sticky="ew", padx=(4, 4), pady=2)

        self.clean_all_button = ttk.Button(accion_frame, text="🧹 LIMPIAR TODO", command=self._clean_all, style='Secondary.TButton')
        self.clean_all_button.grid(row=0, column=3, sticky="ew", padx=(4, 0), pady=2)

        self.progress = ttk.Progressbar(accion_frame, mode='determinate', style='Custom.Horizontal.TProgressbar', maximum=100)
        self.progress.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(4, 0))

        self.progress_label = ttk.Label(accion_frame, text="", style='Subtitle.TLabel', font=('Segoe UI', 8))
        self.progress_label.grid(row=2, column=0, columnspan=4, sticky="e", pady=(1, 0))

    # ========== MÉTODOS DE FUNCIONALIDAD ==========

    def _select_source(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta")
        if folder:
            self.source_var.set(folder)

    def _scan_files(self):
        if not self.source_var.get():
            messagebox.showerror("Error", "Selecciona una carpeta.")
            return

        source = Path(self.source_var.get())
        if not source.exists():
            messagebox.showerror("Error", "La carpeta no existe.")
            return

        self.is_scanning = True
        self.scan_button.config(state="disabled")
        self._log("🔍 Escaneando archivos...")

        thread = threading.Thread(target=self._run_scan)
        thread.daemon = True
        thread.start()

    def _run_scan(self):
        try:
            source = Path(self.source_var.get())
            results = self.metadata_manager.scan_folder(
                source,
                self.search_subfolders_var.get()
            )

            self.current_files = results
            self.after(0, self._on_scan_complete)

        except Exception as e:
            self.after(0, self._on_scan_error, str(e))

    def _on_scan_complete(self):
        self.is_scanning = False
        self.scan_button.config(state="normal")

        for item in self.tree.get_children():
            self.tree.delete(item)

        total = len(self.current_files)
        complete = sum(1 for f in self.current_files if f.get('completo', False))
        incomplete = sum(1 for f in self.current_files if not f.get('completo', False) and any(f.get('faltan', [])))
        missing = sum(1 for f in self.current_files if not f.get('artista', '') and not f.get('titulo', ''))

        self.total_label.config(text=f"Total: {total}")
        self.complete_label.config(text=f"✅ Completos: {complete}")
        self.incomplete_label.config(text=f"⚠️ Incompletos: {incomplete}")
        self.missing_label.config(text=f"❌ Sin metadatos: {missing}")

        for file_info in self.current_files[:100]:
            status = "✅" if file_info.get('completo', False) else "⚠️"
            self.tree.insert("", "end", values=(
                file_info.get('archivo', ''),
                file_info.get('artista', '')[:15],
                file_info.get('album', '')[:15],
                file_info.get('titulo', '')[:15],
                file_info.get('año', ''),
                status
            ))

        self._log(f"✅ Escaneo completado: {total} archivos encontrados")

    def _on_scan_error(self, error_msg: str):
        self.is_scanning = False
        self.scan_button.config(state="normal")
        self._log(f"❌ Error: {error_msg}")
        messagebox.showerror("Error", error_msg)

    def _on_select_file(self, event):
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.tree.item(item, 'values')
        if not values:
            return

        filename = values[0]
        for idx, file_info in enumerate(self.current_files):
            if file_info.get('archivo') == filename:
                self.current_index = idx
                self._load_file_to_editor(file_info)
                break

    def _load_file_to_editor(self, file_info):
        self.editing_file = file_info
        self.file_display.config(text=file_info.get('archivo', '')[:40])
        self.edit_artista_var.set(file_info.get('artista', ''))
        self.edit_album_var.set(file_info.get('album', ''))
        self.edit_titulo_var.set(file_info.get('titulo', ''))
        self.edit_año_var.set(file_info.get('año', ''))
        self.edit_genero_var.set(file_info.get('genero', ''))
        self.edit_numero_var.set(file_info.get('numero', ''))
        self.save_individual_button.config(state="normal")

    def _save_metadata(self):
        if not self.editing_file:
            return

        self.editing_file['artista'] = self.edit_artista_var.get().strip()
        self.editing_file['album'] = self.edit_album_var.get().strip()
        self.editing_file['titulo'] = self.edit_titulo_var.get().strip()
        self.editing_file['año'] = self.edit_año_var.get().strip()
        self.editing_file['genero'] = self.edit_genero_var.get().strip()
        self.editing_file['numero'] = self.edit_numero_var.get().strip()

        file_path = Path(self.editing_file.get('ruta', ''))
        if file_path.exists():
            success = self.metadata_manager.save_metadata(file_path, self.editing_file)
            if success:
                self._log(f"✅ Metadatos guardados: {file_path.name}")
                messagebox.showinfo("Éxito", "Metadatos guardados correctamente.")
                self.save_individual_button.config(state="disabled")
                self._update_tree_item()
            else:
                messagebox.showerror("Error", "No se pudieron guardar los metadatos.")

    def _update_tree_item(self):
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            if values and values[0] == self.editing_file.get('archivo'):
                self.tree.item(item, values=(
                    self.editing_file.get('archivo', ''),
                    self.editing_file.get('artista', '')[:15],
                    self.editing_file.get('album', '')[:15],
                    self.editing_file.get('titulo', '')[:15],
                    self.editing_file.get('año', ''),
                    "✅"
                ))
                break

    def _next_file(self):
        if self.current_index < len(self.current_files) - 1:
            self.current_index += 1
            self._load_file_to_editor(self.current_files[self.current_index])

    def _prev_file(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._load_file_to_editor(self.current_files[self.current_index])

    def _apply_clean(self):
        if not self.source_var.get():
            messagebox.showerror("Error", "Selecciona una carpeta.")
            return

        remove_words = [w.strip() for w in self.remove_words_var.get().split(',') if w.strip()]
        custom_text = self.custom_text_var.get().strip()

        selected = []
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            if values:
                for file_info in self.current_files:
                    if file_info.get('archivo') == values[0]:
                        selected.append(Path(file_info.get('ruta')))
                        break

        if not selected:
            messagebox.showerror("Error", "No hay archivos para limpiar.")
            return

        self.is_running = True
        self.clean_button.config(state="disabled")
        self._log("🧹 Limpiando nombres...")

        thread = threading.Thread(target=self._run_clean, args=(selected, remove_words, custom_text))
        thread.daemon = True
        thread.start()

    def _run_clean(self, files, remove_words, custom_text):
        try:
            result = self.name_cleaner.rename_files(
                files,
                remove_track_numbers=self.remove_track_var.get(),
                remove_brackets=self.remove_brackets_var.get(),
                remove_parentheses=self.remove_parentheses_var.get(),
                remove_words=remove_words,
                custom_text=custom_text,
                progress_callback=self._update_progress
            )

            self.after(0, self._on_clean_complete, result)

        except Exception as e:
            self.after(0, self._on_clean_error, str(e))

    def _on_clean_complete(self, result):
        self.is_running = False
        self.clean_button.config(state="normal")
        self.progress['value'] = 0
        self.progress_label.config(text="")

        self._log(f"✅ Limpieza completada: {result['renamed']} archivos renombrados")
        messagebox.showinfo("Completado", f"{result['renamed']} archivos renombrados.\nErrores: {result['errors']}")

        self._scan_files()

    def _on_clean_error(self, error_msg):
        self.is_running = False
        self.clean_button.config(state="normal")
        self.progress['value'] = 0
        self.progress_label.config(text="")
        self._log(f"❌ Error: {error_msg}")
        messagebox.showerror("Error", error_msg)

    def _save_all_metadata(self):
        if not self.current_files:
            messagebox.showerror("Error", "Primero escanea archivos.")
            return

        incomplete = [f for f in self.current_files if not f.get('completo', False)]
        if not incomplete:
            messagebox.showinfo("Info", "Todos los archivos están completos.")
            return

        saved = 0
        for file_info in incomplete:
            file_path = Path(file_info.get('ruta', ''))
            if file_path.exists():
                success = self.metadata_manager.save_metadata(file_path, file_info)
                if success:
                    saved += 1

        self._log(f"💾 Metadatos guardados: {saved}/{len(incomplete)}")
        messagebox.showinfo("Completado", f"Metadatos guardados: {saved}/{len(incomplete)}")

    def _rename_files(self):
        if not self.current_files:
            messagebox.showerror("Error", "Primero escanea archivos.")
            return

        for file_info in self.current_files:
            if not file_info.get('artista') and not file_info.get('titulo'):
                artista, titulo = self.name_cleaner.extract_artist_title(file_info.get('archivo', ''))
                if artista and titulo:
                    file_info['artista'] = artista
                    file_info['titulo'] = titulo

        self._log("📝 Intentando extraer Artista - Título de nombres...")
        self._scan_files()

    def _update_progress(self, current, total):
        if total > 0:
            porcentaje = int((current / total) * 100)
            self.progress['value'] = porcentaje
            self.progress_label.config(text=f"{current}/{total} ({porcentaje}%)")

    def _cancel_operation(self):
        if self.is_running:
            self.is_running = False
            self._log("⏹ Operación cancelada")

    def _clean_all(self):
        self.source_var.set("")
        self.tree.delete(*self.tree.get_children())
        self.current_files = []
        self.total_label.config(text="Total: 0")
        self.complete_label.config(text="✅ Completos: 0")
        self.incomplete_label.config(text="⚠️ Incompletos: 0")
        self.missing_label.config(text="❌ Sin metadatos: 0")
        self.progress['value'] = 0
        self.progress_label.config(text="")
        self.file_display.config(text="Selecciona un archivo")
        self.edit_artista_var.set("")
        self.edit_album_var.set("")
        self.edit_titulo_var.set("")
        self.edit_año_var.set("")
        self.edit_genero_var.set("")
        self.edit_numero_var.set("")
        self.save_individual_button.config(state="disabled")
        self.log_text.delete("1.0", tk.END)
        self._log("🧹 Todo limpiado. Listo para empezar.")

    def _log(self, message: str):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
