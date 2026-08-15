import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from threading import Thread
import queue

from core.organizer import Organizer
from config.settings import config
from gui.cleaner_tab import CleanerTab
from gui.desorganize_tab import DesorganizeTab
from gui.metadata_tab import MetadataTab
from gui.space_liberator_tab import SpaceLiberatorTab
from gui.security_tab import SecurityTab

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("JumProva v1.0 - Gestión Inteligente de Archivos")
        self.root.geometry("1000x750")
        self.root.minsize(800, 600)

        # ============================================
        # ICONO DE LA VENTANA
        # ============================================
        try:
            self.root.iconbitmap("jumprova.ico")
        except:
            pass
        
        # Variables
        self.source_dir = tk.StringVar()
        self.dest_dir = tk.StringVar()
        self.operation = tk.StringVar(value="mover")
        self.use_metadata = tk.BooleanVar(value=config.get("use_metadata", True))
        self.include_subfolders = tk.BooleanVar(value=config.get("include_subfolders", False))
        self.handle_unknown = tk.StringVar(value=config.get("unknown_files", "ignore"))
        
        # Organizador
        self.organizer = Organizer()
        
        # Control de proceso
        self.is_running = False
        
        # Construir interfaz
        self._build_ui()
        
        # Conectar callbacks
        self._setup_callbacks()
        
        # Cargar categorías
        self._load_categories()
    
    def _build_ui(self):
        """Construir todos los elementos de la interfaz"""
        
        # ===== Título con LOGO =====
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=100)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        
        # Frame interno para logo y texto
        inner_frame = tk.Frame(title_frame, bg="#2c3e50")
        inner_frame.pack(pady=8)
        
        # ============================================
        # MOSTRAR LOGO (CON SOPORTE PARA .EXE)
        # ============================================
        try:
            from PIL import Image, ImageTk
            import os
            import sys
            
            # Determinar la ruta base (funciona en .exe y en desarrollo)
            if getattr(sys, 'frozen', False):
                # Estamos en el .exe
                base_path = sys._MEIPASS
            else:
                # Estamos en desarrollo
                base_path = os.path.abspath(".")
            
            logo_path = os.path.join(base_path, "jumprova.png")
                        
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                img = img.resize((60, 60), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
                
                lbl_logo = tk.Label(inner_frame, image=self.logo_img, bg="#2c3e50")
                lbl_logo.pack(side=tk.LEFT, padx=(0, 15))
              
            else:
                # Si no hay logo, usar emoji
                
                tk.Label(inner_frame, text="📂", font=("Arial", 40), bg="#2c3e50").pack(side=tk.LEFT, padx=(0, 15))
        except Exception as e:
            
            # Si falla, usar emoji
            tk.Label(inner_frame, text="📂", font=("Arial", 40), bg="#2c3e50").pack(side=tk.LEFT, padx=(0, 15))
        
        # Texto del título
        text_frame = tk.Frame(inner_frame, bg="#2c3e50")
        text_frame.pack(side=tk.LEFT)
        
        tk.Label(text_frame, text="JumProva", 
                font=("Arial", 24, "bold"), fg="white", bg="#2c3e50").pack(anchor="w")
        tk.Label(text_frame, text="Gestión inteligente de archivos",
                font=("Arial", 10), fg="#bdc3c7", bg="#2c3e50").pack(anchor="w")
        
        # ===== Marco principal =====
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== CREAR NOTEBOOK (PESTAÑAS) =====
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)

        # PESTAÑA 1: ORGANIZADOR
        tab_organizer = ttk.Frame(self.notebook)
        self.notebook.add(tab_organizer, text="📂 Organizar")
        self._build_organizer_tab(tab_organizer)

        # PESTAÑA 2: LIMPIEZA
        tab_cleaner = ttk.Frame(self.notebook)
        self.notebook.add(tab_cleaner, text="🧹 Limpiar basura")
        from gui.cleaner_tab import CleanerTab
        self.cleaner_tab = CleanerTab(tab_cleaner, self.organizer)

        # PESTAÑA 3: DESORGANIZAR (NUEVA)
        tab_desorganize = ttk.Frame(self.notebook)
        self.notebook.add(tab_desorganize, text="🔄 Desorganizar")
        from gui.desorganize_tab import DesorganizeTab
        self.desorganize_tab = DesorganizeTab(tab_desorganize, self.organizer)

        # PESTAÑA 4: METADATOS
        tab_metadata = ttk.Frame(self.notebook)
        self.notebook.add(tab_metadata, text="🎵 Metadatos")
        self.metadata_tab = MetadataTab(tab_metadata, self.organizer)

        # PESTAÑA 5: LIBERADOR DE ESPACIO
        tab_liberator = ttk.Frame(self.notebook)
        self.notebook.add(tab_liberator, text="💾 Liberar espacio")
        self.liberator_tab = SpaceLiberatorTab(tab_liberator, self.organizer)

        # PESTAÑA 6: SEGURIDAD
        tab_security = ttk.Frame(self.notebook)
        self.notebook.add(tab_security, text="🛡 Seguridad")
        self.security_tab = SecurityTab(tab_security, self.organizer)

        # PESTAÑA 7: CONFIGURACIÓN
        tab_config = ttk.Frame(self.notebook)
        self.notebook.add(tab_config, text="⚙️ Configuración")
        self._build_config_tab(tab_config)
        
        # PESTAÑA 8: ACERCA DE (como pestaña)
        tab_acerca = ttk.Frame(self.notebook)
        self.notebook.add(tab_acerca, text="ℹ️ Acerca de")
        self._build_acerca_tab(tab_acerca)
    
    def _build_organizer_tab(self, parent):
        """Construir la pestaña de organización"""
        
        # ===== SECCIÓN 1: Carpetas =====
        frame_carpetas = ttk.LabelFrame(parent, text="📁 Carpetas", padding=10)
        frame_carpetas.pack(fill="x", pady=5)
        
        # Origen
        ttk.Label(frame_carpetas, text="Origen:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(frame_carpetas, textvariable=self.source_dir, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(frame_carpetas, text="📂", command=lambda: self._select_folder("source")).grid(row=0, column=2)
        
        # Destino
        ttk.Label(frame_carpetas, text="Destino:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(frame_carpetas, textvariable=self.dest_dir, width=60).grid(row=1, column=1, padx=5)
        ttk.Button(frame_carpetas, text="📂", command=lambda: self._select_folder("dest")).grid(row=1, column=2)
        
        # Botón usar misma carpeta
        ttk.Button(frame_carpetas, text="↹ Usar misma carpeta", 
                  command=self._use_same_folder).grid(row=2, column=1, pady=5)

        # ===== SECCIÓN 2: Opciones de Audio =====
        frame_audio = ttk.LabelFrame(parent, text="🎵 Opciones para archivos de audio", padding=10)
        frame_audio.pack(fill="x", pady=5)
        
        self.audio_organize = tk.StringVar(value="año")  # año, artista, genero, ninguno
        
        ttk.Label(frame_audio, text="Organizar audios por:").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(frame_audio, text="📅 Año", variable=self.audio_organize, 
                       value="año").grid(row=0, column=1, sticky="w", padx=5)
        ttk.Radiobutton(frame_audio, text="🎸 Artista", variable=self.audio_organize, 
                       value="artista").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Radiobutton(frame_audio, text="🎵 Género", variable=self.audio_organize, 
                       value="genero").grid(row=0, column=3, sticky="w", padx=5)
        ttk.Radiobutton(frame_audio, text="📂 Sin organizar (solo metadatos)", variable=self.audio_organize, 
                       value="ninguno").grid(row=0, column=4, sticky="w", padx=5)
        
        # ===== SECCIÓN 3: Opciones =====
        frame_opciones = ttk.LabelFrame(parent, text="⚙️ Opciones", padding=10)
        frame_opciones.pack(fill="x", pady=5)
        
        # Modo de operación
        ttk.Label(frame_opciones, text="Operación:").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(frame_opciones, text="Mover", variable=self.operation, 
                       value="mover").grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(frame_opciones, text="Copiar", variable=self.operation, 
                       value="copiar").grid(row=0, column=2, sticky="w")
        
        # Opciones avanzadas
        ttk.Checkbutton(frame_opciones, text="📷 Usar metadatos EXIF (fecha real de captura)",
                       variable=self.use_metadata).grid(row=1, column=0, columnspan=3, sticky="w", pady=5)
        
        ttk.Checkbutton(frame_opciones, text="📂 Incluir subcarpetas (procesar recursivamente)",
                       variable=self.include_subfolders).grid(row=2, column=0, columnspan=3, sticky="w", pady=5)
        
        # Manejo de archivos desconocidos
        ttk.Label(frame_opciones, text="Archivos desconocidos:").grid(row=3, column=0, sticky="w")
        ttk.Combobox(frame_opciones, textvariable=self.handle_unknown,
                    values=["ignore", "move_to_others", "ask"], state="readonly", width=20).grid(row=3, column=1, sticky="w")
        
        # ===== SECCIÓN 4: Categorías =====
        frame_categorias = ttk.LabelFrame(parent, text="🏷 Categorías Activas", padding=10)
        frame_categorias.pack(fill="x", pady=5)
        
        # Marco para treeview con scroll
        tree_frame = ttk.Frame(frame_categorias)
        tree_frame.pack(fill="x", pady=5)
        
        # Treeview
        columns = ("Categoría", "Carpeta", "Extensiones", "Metadatos")
        self.tree_categories = ttk.Treeview(tree_frame, columns=columns, show="headings", height=6)
        self.tree_categories.heading("Categoría", text="Categoría")
        self.tree_categories.heading("Carpeta", text="Carpeta destino")
        self.tree_categories.heading("Extensiones", text="Extensiones")
        self.tree_categories.heading("Metadatos", text="Metadatos EXIF")
        
        self.tree_categories.column("Categoría", width=120)
        self.tree_categories.column("Carpeta", width=150)
        self.tree_categories.column("Extensiones", width=500)
        self.tree_categories.column("Metadatos", width=100)
        
        # Scrollbar
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_categories.yview)
        self.tree_categories.configure(yscrollcommand=scroll.set)
        
        self.tree_categories.pack(side=tk.LEFT, fill="x", expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botón recargar
        ttk.Button(frame_categorias, text="🔄 Recargar categorías", 
                  command=self._load_categories).pack(pady=5)
        
        # ===== SECCIÓN 5: Botones de control =====
        frame_botones = ttk.Frame(parent)
        frame_botones.pack(pady=15, fill="x")
        
        # Botón Iniciar
        self.btn_start = ttk.Button(frame_botones, text="🚀 INICIAR ORGANIZACIÓN", 
                                   command=self._start_organization)
        self.btn_start.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
        
        # Botón Cancelar (inicialmente deshabilitado)
        self.btn_cancel = ttk.Button(frame_botones, text="🛑 CANCELAR", 
                                    command=self._cancel_organization,
                                    state="disabled")
        self.btn_cancel.pack(side=tk.RIGHT, padx=5, fill="x", expand=True)

        # ===== NUEVO: Botón Limpiar todo =====
        self.btn_clear_organizer = ttk.Button(frame_botones, text="🧹 LIMPIAR TODO", 
                                             command=self._clear_all_organizer)
        self.btn_clear_organizer.pack(side=tk.RIGHT, padx=5, fill="x", expand=True)
        
        # ===== SECCIÓN 6: Progreso =====
        frame_progreso = ttk.LabelFrame(parent, text="📊 Progreso", padding=10)
        frame_progreso.pack(fill="x", pady=5)
        
        self.progress_bar = ttk.Progressbar(frame_progreso, length=400, mode='determinate')
        self.progress_bar.pack(fill="x", pady=5)
        
        self.label_progress = ttk.Label(frame_progreso, text="Listo para organizar")
        self.label_progress.pack()
        
        # ===== SECCIÓN 7: Log =====
        frame_log = ttk.LabelFrame(parent, text="📋 Registro", padding=10)
        frame_log.pack(fill="both", expand=True, pady=5)
        
        # Texto del log con scroll
        log_frame = ttk.Frame(frame_log)
        log_frame.pack(fill="both", expand=True)
        
        scroll_log = ttk.Scrollbar(log_frame)
        scroll_log.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=10, yscrollcommand=scroll_log.set,
                               font=("Consolas", 9), bg="#f8f9fa", wrap=tk.WORD)
        self.log_text.pack(fill="both", expand=True)
        scroll_log.config(command=self.log_text.yview)
        
        # Botones de log
        frame_log_buttons = ttk.Frame(frame_log)
        frame_log_buttons.pack(pady=5)
        
        ttk.Button(frame_log_buttons, text="🗑 Limpiar", command=self._clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_log_buttons, text="💾 Guardar", command=self._save_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_log_buttons, text="📊 Estadísticas", command=self._show_stats).pack(side=tk.LEFT, padx=5)
    
    def _build_config_tab(self, parent):
        """Construir la pestaña de configuración"""
        
        # ===== SECCIÓN: CATEGORÍAS =====
        tk.Label(parent, text="📂 Configuración de Categorías", 
                font=("Arial", 14, "bold")).pack(pady=10)
        
        tk.Label(parent, text="Selecciona las categorías que quieres usar al organizar archivos:",
                font=("Arial", 10), fg="#7f8c8d").pack(pady=(0, 15))
        
        frame_categorias = ttk.LabelFrame(parent, text="📂 Categorías Activas", padding=10)
        frame_categorias.pack(fill="both", expand=True, padx=20, pady=10)
        
        categories = self.organizer.classifier.get_all_categories()
        active = self.organizer.classifier.get_active_categories()
        
        self.category_vars = {}
        
        row = 0
        col = 0
        for name, data in categories.items():
            is_active = name in active
            var = tk.BooleanVar(value=is_active)
            self.category_vars[name] = var
            
            metadata_info = "📷" if data.get("metadata", False) else "📄"
            cb = ttk.Checkbutton(frame_categorias, 
                                text=f"{data['folder']} ({len(data['extensions'])} ext) {metadata_info}",
                                variable=var)
            cb.grid(row=row, column=col, sticky="w", padx=10, pady=3)
            
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        frame_botones = ttk.Frame(parent)
        frame_botones.pack(pady=15)
        
        ttk.Button(frame_botones, text="💾 Guardar configuración", 
                  command=self._save_category_config).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_botones, text="🔄 Restaurar predeterminadas", 
                  command=self._restore_default_categories).pack(side=tk.LEFT, padx=5)
        
        tk.Label(parent, 
                text="💡 Las categorías inactivas no se mostrarán en 'Organizar'.",
                font=("Arial", 9), fg="#7f8c8d").pack(pady=5)

    def _save_category_config(self):
        """Guardar configuración de categorías y actualizar vista"""
        active = [name for name, var in self.category_vars.items() if var.get()]

        if not active:
            messagebox.showwarning("Advertencia", "Debes tener al menos una categoría activa")
            return

        # Guardar en el clasificador y en el archivo
        self.organizer.classifier.set_active_categories(active)

        # 🔥 RECARGAR LA VISTA DE CATEGORÍAS (esto es lo que faltaba)
        self._load_categories()

        messagebox.showinfo("Éxito", f"✅ Configuración guardada\n\nCategorías activas:\n• " + "\n• ".join(active))

    def _restore_default_categories(self):
        """Restaurar categorías predeterminadas y recargar vista"""
        default = ["fotos", "videos", "documentos", "comprimidos"]

        for name, var in self.category_vars.items():
            var.set(name in default)

        messagebox.showinfo("Info", "Categorías restauradas a las predeterminadas.\nHaz clic en 'Guardar' para aplicar los cambios.")
    
    def _select_folder(self, tipo):
        """Seleccionar carpeta usando el explorador"""
        folder = filedialog.askdirectory()
        if folder:
            if tipo == "source":
                self.source_dir.set(folder)
            else:
                self.dest_dir.set(folder)
            self._log_message(f"📁 Carpeta seleccionada: {folder}")
    
    def _use_same_folder(self):
        """Usar misma carpeta origen como destino"""
        source = self.source_dir.get()
        if source:
            self.dest_dir.set(source)
            self._log_message(f"↹ Destino configurado como la misma carpeta: {source}")
        else:
            messagebox.showwarning("Advertencia", "Primero selecciona una carpeta origen")
    
    def _load_categories(self):
        """Cargar categorías en el treeview (solo las ACTIVAS)"""
        # Limpiar treeview
        for item in self.tree_categories.get_children():
            self.tree_categories.delete(item)
        
        # Obtener datos
        categories = self.organizer.classifier.get_all_categories()
        active = self.organizer.classifier.get_active_categories()
        
        # Mostrar SOLO las categorías activas
        for name, data in categories.items():
            if name not in active:
                continue  # Saltar inactivas
            
            # ============================================
            # MOSTRAR TODAS LAS EXTENSIONES (SIN ABREVIAR)
            # ============================================
            ext_list = data.get("extensions", [])
            ext_str = ", ".join(ext_list)  # ← AHORA TODAS, SIN CORTAR
            
            usa_metadata = "✓" if data.get("metadata", False) else "✗"
            
            self.tree_categories.insert("", "end", values=(
                data.get("folder", name.capitalize()),
                data.get("folder", name.capitalize()),
                ext_str,
                usa_metadata
            ))
        
        # Ajustar ancho de la columna de extensiones para que quepan todas
        self.tree_categories.column("Extensiones", width=500)
        
        # Forzar actualización visual
        self.tree_categories.update_idletasks()
    
    def _log_message(self, message):
        """Añadir mensaje al log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def _clear_all_organizer(self):
        """Limpiar todos los campos y el log en la pestaña Organizar"""
        # Limpiar campos de texto
        self.source_dir.set("")
        self.dest_dir.set("")
        
        # Limpiar el log
        self._clear_log()
        
        # Resetear barra de progreso
        self.progress_bar.config(value=0)
        self.label_progress.config(text="Listo para organizar")
        
        # Resetear botones
        self.btn_start.config(state="normal")
        self.btn_cancel.config(state="disabled")
        
        # Resetear estadísticas del organizador
        self.organizer.file_handler.reset_stats()
        
        # Mensaje informativo
        self._log_message("🧹 Datos limpiados correctamente")
    
    def _clear_log(self):
        """Limpiar el log"""
        self.log_text.delete(1.0, tk.END)
    
    def _save_log(self):
        """Guardar log en archivo"""
        try:
            log_content = self.log_text.get(1.0, tk.END)
            if not log_content.strip():
                messagebox.showinfo("Info", "El registro está vacío")
                return
            
            log_file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
            )
            
            if log_file:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                messagebox.showinfo("Éxito", f"✅ Registro guardado en:\n{log_file}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el log:\n{str(e)}")
    
    def _show_stats(self):
        """Mostrar estadísticas de la última organización"""
        stats = self.organizer.file_handler.get_stats()
        
        stats_text = f"""
📊 ESTADÍSTICAS DE LA ÚLTIMA ORGANIZACIÓN

📁 Archivos movidos:    {stats['moved']}
📄 Archivos copiados:   {stats['copied']}
🔄 Archivos renombrados: {stats['renamed']}
❌ Errores:             {stats['errors']}
📂 Directorios creados: {stats['created_dirs']}

{'='*40}
Total archivos procesados: {stats['moved'] + stats['copied']}
        """
        
        messagebox.showinfo("📊 Estadísticas", stats_text)
    
    def _setup_callbacks(self):
        """Configurar callbacks del organizador"""
        
        def on_start(total):
            self.root.after(0, lambda: self._log_message(f"🚀 Iniciando organización de {total} archivos..."))
            self.root.after(0, lambda: self._set_running_state(True))
        
        def on_progress(progress, message):
            self.root.after(0, lambda: self.progress_bar.config(value=progress))
            self.root.after(0, lambda: self.label_progress.config(text=message[:60] + ("..." if len(message) > 60 else "")))
        
        def on_file_processed(file_path, status, message):
            icon = "✅" if status == "processed" else "⏭️"
            self.root.after(0, lambda: self._log_message(f"{icon} {file_path.name} {message}"))
        
        def on_complete(stats):
            self.root.after(0, lambda: self._set_running_state(False))
            self.root.after(0, lambda: self.progress_bar.config(value=100))
            
            if stats.get("cancelled", False):
                self.root.after(0, lambda: self.label_progress.config(text="🛑 Proceso cancelado"))
                self.root.after(0, lambda: self._log_message(f"\n{'='*60}"))
                self.root.after(0, lambda: self._log_message(f"🛑 PROCESO CANCELADO"))
                self.root.after(0, lambda: self._log_message(f"📊 Procesados: {stats.get('processed', 0)} archivos"))
                self.root.after(0, lambda: self._log_message(f"{'='*60}"))
                self.root.after(0, lambda: messagebox.showinfo("🛑 Cancelado", 
                    f"Proceso cancelado por el usuario.\n\n"
                    f"📊 Archivos procesados: {stats.get('processed', 0)}\n"
                    f"📁 Movidos: {stats.get('moved', 0)}\n"
                    f"📄 Copiados: {stats.get('copied', 0)}"))
            else:
                self.root.after(0, lambda: self.label_progress.config(text="✅ ¡Organización completada!"))
                
                msg = f"✅ Organización completada!\n\n"
                msg += f"📁 Archivos movidos: {stats['moved']}\n"
                msg += f"📄 Archivos copiados: {stats['copied']}\n"
                msg += f"🔄 Archivos renombrados: {stats['renamed']}\n"
                msg += f"❌ Errores: {stats['errors']}\n"
                msg += f"📂 Directorios creados: {stats['created_dirs']}"
                
                self.root.after(0, lambda: messagebox.showinfo("✅ Completado", msg))
                self.root.after(0, lambda: self._log_message(f"\n{'='*60}\n{msg}\n{'='*60}"))
        
        def on_error(error, file_path):
            self.root.after(0, lambda: self._log_message(f"❌ ERROR: {error}"))
            self.root.after(0, lambda: self._log_message(f"📁 Archivo: {file_path.name}"))
        
        def on_cancel():
            self.root.after(0, lambda: self._log_message("🛑 Solicitando cancelación..."))
            self.root.after(0, lambda: self.label_progress.config(text="🛑 Cancelando..."))
            self.root.after(0, lambda: self.btn_cancel.config(state="disabled", text="⏳ Cancelando..."))
        
        def on_log(message):
            """Recibir logs detallados del organizador"""
            self.root.after(0, lambda: self._log_message(f"  {message}"))
        
        # Registrar callbacks
        self.organizer.register_callback("on_start", on_start)
        self.organizer.register_callback("on_progress", on_progress)
        self.organizer.register_callback("on_file_processed", on_file_processed)
        self.organizer.register_callback("on_complete", on_complete)
        self.organizer.register_callback("on_error", on_error)
        self.organizer.register_callback("on_cancel", on_cancel)
        self.organizer.register_callback("on_log", on_log)  # ← NUEVO
    
    def _set_running_state(self, running):
        """Cambiar el estado de ejecución y habilitar/deshabilitar botones"""
        self.is_running = running
        
        if running:
            self.btn_start.config(state="disabled")
            self.btn_cancel.config(state="normal", text="🛑 CANCELAR")
        else:
            self.btn_start.config(state="normal")
            self.btn_cancel.config(state="disabled", text="🛑 CANCELAR")
    
    def _cancel_organization(self):
        """Cancelar el proceso de organización"""
        if self.is_running:
            if messagebox.askyesno("🛑 Cancelar", 
                "¿Seguro que quieres cancelar el proceso?\n\n"
                "Los archivos ya procesados permanecerán en su nueva ubicación."):
                self._log_message("🛑 Cancelación solicitada por el usuario")
                self.organizer.cancel()
                self.btn_cancel.config(state="disabled", text="⏳ Cancelando...")
    
    def _start_organization(self):
        """Iniciar el proceso de organización en un hilo separado"""
        
        # Validar carpetas
        source = self.source_dir.get()
        dest = self.dest_dir.get()
        
        if not source:
            messagebox.showerror("Error", "❌ Selecciona una carpeta origen")
            return
        
        if not dest:
            messagebox.showerror("Error", "❌ Selecciona una carpeta destino")
            return
        
        if not Path(source).exists():
            messagebox.showerror("Error", "❌ La carpeta origen no existe")
            return
        
        # Preguntar confirmación
        if not messagebox.askyesno("Confirmar", 
            f"¿Seguro que quieres organizar los archivos?\n\n"
            f"📁 Origen: {source}\n"
            f"📁 Destino: {dest}\n"
            f"🔄 Operación: {'Mover' if self.operation.get() == 'mover' else 'Copiar'}\n"
            f"📂 Incluir subcarpetas: {'Sí' if self.include_subfolders.get() else 'No'}\n"
            f"📷 Usar metadatos: {'Sí' if self.use_metadata.get() else 'No'}\n\n"
            f"⚠️ Esta acción no se puede deshacer fácilmente."):
            return
        
        # Limpiar log
        self._clear_log()
        self.progress_bar.config(value=0)
        self.label_progress.config(text="⏳ Preparando organización...")
        self._log_message("=" * 60)
        self._log_message("🚀 INICIANDO ORGANIZACIÓN")
        self._log_message(f"📁 Origen: {source}")
        self._log_message(f"📁 Destino: {dest}")
        self._log_message(f"🔄 Operación: {self.operation.get()}")
        self._log_message("=" * 60)
        
        # Actualizar configuración del organizador
        config.set("use_metadata", self.use_metadata.get())
        config.set("include_subfolders", self.include_subfolders.get())
        config.set("unknown_files", self.handle_unknown.get())
        
        # Iniciar en hilo separado
        def run_organization():
            try:
                result = self.organizer.organize(source, dest, self.operation.get())
                if isinstance(result, dict) and "error" in result:
                    self.root.after(0, lambda: messagebox.showerror("Error", result["error"]))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Error inesperado:\n{str(e)}"))
            finally:
                self.root.after(0, lambda: self._set_running_state(False))
        
        thread = Thread(target=run_organization)
        thread.daemon = True
        thread.start()

    def _build_acerca_tab(self, parent):
        """Construir la pestaña Acerca de - VISUAL Y LIMPIA (sin header duplicado)"""
        
        # ============================================
        # CONTENEDOR PRINCIPAL
        # ============================================
        main_frame = tk.Frame(parent, bg="#f0f2f5")
        main_frame.pack(fill="both", expand=True)
        
        # Canvas con scroll para que quepa todo
        canvas = tk.Canvas(main_frame, bg="#f0f2f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f2f5")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        
        # ============================================
        # CONTENIDO DENTRO DEL SCROLL
        # ============================================
        frame = tk.Frame(scrollable_frame, bg="#f0f2f5", padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        
        # ============================================
        # TARJETA DE DESCRIPCIÓN (con color)
        # ============================================
        desc_frame = tk.Frame(frame, bg="#2c3e50", relief=tk.RAISED, bd=1)
        desc_frame.pack(fill="x", pady=10)
        desc_frame.configure(height=70)
        desc_frame.pack_propagate(False)
        
        tk.Label(desc_frame, 
                text="🚀 JumProva es una aplicación todo-en-uno para organizar, limpiar,\n"
                     "   gestionar metadatos y proteger tu sistema de forma inteligente.",
                font=("Arial", 11), bg="#2c3e50", fg="white", justify="center").pack(expand=True)
        
        # ============================================
        # TARJETAS DE ESTADÍSTICAS (4 columnas)
        # ============================================
        stats_frame = tk.Frame(frame, bg="#f0f2f5")
        stats_frame.pack(fill="x", pady=10)
        
        stats = [
            ("📂", "7", "Módulos activos"),
            ("⚡", "1.0.0", "Versión actual"),
            ("📅", "2026", "Lanzamiento"),
            ("🌐", "MIT", "Licencia"),
        ]
        
        colores_stats = ["#3498db", "#2ecc71", "#f39c12", "#e74c3c"]
        
        for i, (icono, numero, texto) in enumerate(stats):
            card = tk.Frame(stats_frame, bg="white", relief=tk.RAISED, bd=1)
            card.grid(row=0, column=i, padx=6, pady=5, sticky="nsew")
            stats_frame.columnconfigure(i, weight=1)
            
            # Barra de color arriba
            color_bar = tk.Frame(card, bg=colores_stats[i], height=4)
            color_bar.pack(fill="x")
            
            tk.Label(card, text=icono, font=("Arial", 20), bg="white").pack(pady=(5,0))
            tk.Label(card, text=numero, font=("Arial", 16, "bold"), fg=colores_stats[i], bg="white").pack()
            tk.Label(card, text=texto, font=("Arial", 8), fg="#7f8c8d", bg="white").pack(pady=(0,5))
        
        # ============================================
        # SECCIÓN MÓDULOS + CARACTERÍSTICAS (2 columnas)
        # ============================================
        row_frame = tk.Frame(frame, bg="#f0f2f5")
        row_frame.pack(fill="both", expand=True, pady=10)
        
        # Columna Izquierda: Módulos
        col_left = tk.Frame(row_frame, bg="#f0f2f5")
        col_left.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 5))
        
        modulos_frame = tk.LabelFrame(col_left, text="🧩 Módulos principales", 
                                      font=("Arial", 12, "bold"), fg="#2c3e50",
                                      bg="#f0f2f5")
        modulos_frame.pack(fill="both", expand=True)
        
        modulos = [
            ("📂 Organizar", "Clasifica archivos por tipo, año, mes y día automáticamente", "#3498db"),
            ("🧹 Limpiar basura", "Elimina archivos temporales, miniaturas y basura del sistema", "#2ecc71"),
            ("🔄 Desorganizar", "Junta archivos de subcarpetas en una sola carpeta", "#f39c12"),
            ("🎵 Metadatos", "Gestiona artista, álbum, año, género y carátulas de audio", "#9b59b6"),
            ("💾 Liberar espacio", "Busca duplicados, archivos grandes, logs y cachés", "#e74c3c"),
            ("🛡 Seguridad", "Analiza procesos, archivos y conexiones en busca de malware", "#1abc9c"),
            ("⚙️ Configuración", "Activa o desactiva categorías según tus necesidades", "#95a5a6"),
        ]
        
        for titulo, desc, color in modulos:
            item = tk.Frame(modulos_frame, bg="white")
            item.pack(fill="x", pady=2, padx=3)
            
            # Pequeña barra de color a la izquierda
            barra = tk.Frame(item, bg=color, width=4)
            barra.pack(side=tk.LEFT, fill="y", padx=(0,5))
            
            text_frame = tk.Frame(item, bg="white")
            text_frame.pack(side=tk.LEFT, fill="x", expand=True)
            
            tk.Label(text_frame, text=titulo, font=("Arial", 10, "bold"), 
                    fg=color, bg="white").pack(anchor="w")
            tk.Label(text_frame, text=desc, font=("Arial", 8), 
                    fg="#7f8c8d", bg="white").pack(anchor="w", padx=(0,2))
        
        # Columna Derecha: Características + Información
        col_right = tk.Frame(row_frame, bg="#f0f2f5")
        col_right.pack(side=tk.RIGHT, fill="both", expand=True, padx=(5, 0))
        
        # Características
        features_frame = tk.LabelFrame(col_right, text="✨ Características destacadas", 
                                       font=("Arial", 12, "bold"), fg="#2c3e50",
                                       bg="#f0f2f5")
        features_frame.pack(fill="both", expand=True, pady=(0, 5))
        
        features = [
            ("✅", "Preservación de fechas originales", "No se pierde la información temporal"),
            ("📊", "Progreso en tiempo real con ETA", "Siempre sabes cuánto falta"),
            ("⛔", "Cancelación de procesos en curso", "Control total sobre las operaciones"),
            ("🛡", "Protección de archivos del sistema", "Seguridad ante todo"),
            ("📄", "Informes detallados en formato .txt", "Revisa antes de actuar"),
            ("💰", "Totalmente gratuito y Open Source", "Sin costes, sin límites"),
        ]
        
        for icono, titulo, desc in features:
            item = tk.Frame(features_frame, bg="white")
            item.pack(fill="x", pady=2, padx=3)
            
            row = tk.Frame(item, bg="white")
            row.pack(anchor="w", fill="x")
            
            tk.Label(row, text=icono, font=("Arial", 12), bg="white", width=3).pack(side=tk.LEFT)
            tk.Label(row, text=titulo, font=("Arial", 9, "bold"), fg="#2c3e50", bg="white").pack(side=tk.LEFT)
            tk.Label(item, text=desc, font=("Arial", 8), fg="#7f8c8d", bg="white").pack(anchor="w", padx=(25,0))
        
        # ============================================
        # INFORMACIÓN DEL DESARROLLADOR
        # ============================================
        info_frame = tk.LabelFrame(col_right, text="👨‍💻 Información del desarrollador", 
                                   font=("Arial", 12, "bold"), fg="#2c3e50",
                                   bg="#f0f2f5")
        info_frame.pack(fill="x", pady=(5, 0))
        
        info = [
            ("👨‍💻", "Desarrollador:", "Juan José Rivera"),
            ("📧", "Contacto:", "jumalba@hotmail.com"),
            ("📅", "Fecha:", "2026"),
            ("📜", "Licencia:", "MIT (Gratuita y Open Source)"),
            ("🐍", "Lenguaje:", "Python 3.x"),
            ("🖥", "Interfaz:", "Tkinter"),
            ("📦", "Dependencias:", "Pillow, mutagen, psutil, requests, musicbrainzngs"),
        ]
        
        for icono, label, value in info:
            row = tk.Frame(info_frame, bg="white")
            row.pack(fill="x", pady=1, padx=3)
            
            tk.Label(row, text=icono, font=("Arial", 10), bg="white", width=3).pack(side=tk.LEFT)
            tk.Label(row, text=label, font=("Arial", 9, "bold"), fg="#2c3e50", bg="white", width=14, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=value, font=("Arial", 9), fg="#34495e", bg="white", anchor="w").pack(side=tk.LEFT)
        
        # ============================================
        # FRASE FINAL
        # ============================================
        footer_frame = tk.Frame(frame, bg="#2c3e50", relief=tk.RAISED, bd=0)
        footer_frame.pack(fill="x", pady=(15, 0))
        footer_frame.configure(height=45)
        footer_frame.pack_propagate(False)
        
        tk.Label(footer_frame, 
                text='"Organiza, limpia, protege. Todo desde un solo lugar."',
                font=("Arial", 10, "italic"), fg="#f1c40f", bg="#2c3e50").pack(expand=True)
