import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from threading import Thread
import os
import shutil
import time
from datetime import datetime, timedelta
import hashlib


class SpaceLiberatorTab:
    """Pestaña para liberar espacio en disco"""

    def __init__(self, parent, organizer):
        self.parent = parent
        self.organizer = organizer
        self.is_running = False
        self.current_files = []
        self.duplicates = []
        self.empty_folders = []
        self.temp_files = []
        self.selected_items = []

        # Variables
        self.target_dir = tk.StringVar()
        self.include_subfolders = tk.BooleanVar(value=True)

        # Checkboxes de limpieza
        self.clean_duplicates = tk.BooleanVar(value=True)
        self.clean_temp = tk.BooleanVar(value=True)
        self.clean_empty = tk.BooleanVar(value=True)
        self.clean_large = tk.BooleanVar(value=True)
        self.clean_old = tk.BooleanVar(value=True)
        self.clean_recycle = tk.BooleanVar(value=True)
        self.clean_logs = tk.BooleanVar(value=True)
        self.clean_cache = tk.BooleanVar(value=True)

        # Variables para tamaños
        self.large_size_mb = tk.IntVar(value=100)
        self.old_days = tk.IntVar(value=30)
        self.min_duplicate_size_kb = tk.IntVar(value=100)

        # Variables de acción
        self.action = tk.StringVar(value="move_trash")

        # Variables para tiempo
        self.tiempo_inicio = None
        self.progreso_anterior = 0
        self.tiempo_anterior = None

        # Variables para control de cancelación
        self.cancelar_limpieza = False
        self.limpiando = False

        # Lista de archivos temporales por extensión
        self.temp_extensions = {
            '.tmp', '.temp', '.log', '.cache', '.thumb', '.thumbnail',
            '.bak', '.old', '.~', '.swp', '.swo', '.dmp',
            '.chk', '.fnd', '.tmp', '.gid', '.fts', '.ftg'
        }

        self.temp_folders = [
            'temp', 'tmp', 'cache', 'thumbnails', 'thumbcache',
            'recycle.bin', '$recycle.bin', 'system volume information'
        ]

        self.log_extensions = {'.log', '.txt', '.old', '.bak'}

        # ============================================
        # SISTEMA DE PROTECCIÓN
        # ============================================

        # 1. Rutas protegidas (NUNCA se tocan)
        self.rutas_protegidas = [
            r'C:\Windows',
            r'C:\Program Files',
            r'C:\Program Files (x86)',
            r'C:\ProgramData',
            r'C:\System Volume Information',
            r'C:\Recovery',
            r'C:\Boot',
            r'$Recycle.Bin',
            'System Volume Information',
            'site-packages',
            'pythoncore',
            'Microsoft.NET',
            'WindowsApps',
        ]

        # 2. Extensiones protegidas (NUNCA se tocan)
        self.extensiones_protegidas = {
            '.dll', '.sys', '.drv', '.exe', '.msi', '.msp',
            '.pyd', '.pyc', '.pdb', '.manifest', '.cat',
            '.inf', '.ini', '.cfg', '.config', '.xml',
            '.dat', '.db', '.mdf', '.ldf',
        }

        # 3. Nombres de archivo protegidos
        self.archivos_protegidos = [
            'python.exe', 'pythonw.exe', 'pip.exe', 'pip3.exe',
            'python.dll', 'python3.dll', 'pythoncore.dll',
            'ntdll.dll', 'kernel32.dll', 'user32.dll',
            'shell32.dll', 'advapi32.dll', 'msvcrt.dll',
        ]

        # 4. Carpetas de usuario que no se tocan
        self.carpetas_usuario_protegidas = [
            'Desktop', 'Documents', 'Pictures', 'Music', 'Videos',
            'Downloads', 'Favorites', 'OneDrive', 'Dropbox',
            'Google Drive', 'iCloudDrive'
        ]

        self._build_ui()

    def _build_ui(self):
        """Construir la interfaz de la pestaña Liberador de espacio"""

        # ===== Contenedor principal =====
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # ============================================
        # FILA 1: Carpeta y botones
        # ============================================
        frame_fila1 = ttk.Frame(main_frame)
        frame_fila1.pack(fill="x", pady=2)

        ttk.Label(frame_fila1, text="📁 Carpeta:").pack(side=tk.LEFT, padx=2)
        ttk.Entry(
            frame_fila1,
            textvariable=self.target_dir,
            width=45).pack(
            side=tk.LEFT,
            padx=2)
        ttk.Button(
            frame_fila1,
            text="📂",
            command=lambda: self._select_folder(),
            width=3).pack(
            side=tk.LEFT,
            padx=2)

        ttk.Checkbutton(
            frame_fila1,
            text="📂 Subcarpetas",
            variable=self.include_subfolders).pack(
            side=tk.LEFT,
            padx=10)

        # ---- ADVERTENCIA DE SEGURIDAD (creativa) ----
        warning_frame = tk.Frame(
            main_frame,
            bg="#fff3cd",
            relief=tk.RAISED,
            bd=2)
        warning_frame.pack(fill="x", pady=5)
        warning_frame.configure(height=50)
        warning_frame.pack_propagate(False)

        # Icono y texto
        icon_frame = tk.Frame(warning_frame, bg="#fff3cd")
        icon_frame.pack(side=tk.LEFT, padx=10, pady=5)

        tk.Label(
            icon_frame,
            text="⚠️",
            font=(
                "Arial",
                20),
            bg="#fff3cd").pack()

        text_frame = tk.Frame(warning_frame, bg="#fff3cd")
        text_frame.pack(side=tk.LEFT, fill="both", expand=True, pady=5)

        tk.Label(
            text_frame,
            text="🧠 Cuidado con lo que marcas. Revisa siempre el informe antes de limpiar.",
            font=(
                "Arial",
                10,
                "bold"),
            fg="#856404",
            bg="#fff3cd",
            anchor="w").pack(
            anchor="w")

        tk.Label(
            text_frame,
            text="💡 Este liberador es inteligente, pero no adivina. Si no sabes qué es un archivo, NO lo borres.",
            font=(
                "Arial",
                8),
            fg="#856404",
            bg="#fff3cd",
            anchor="w").pack(
            anchor="w")

        # ============================================
        # FILA 2: Opciones de limpieza (en columnas)
        # ============================================
        frame_fila2 = ttk.LabelFrame(
            main_frame, text="🧹 Qué limpiar", padding=5)
        frame_fila2.pack(fill="x", pady=2)

        # Columna 1
        col1 = ttk.Frame(frame_fila2)
        col1.pack(side=tk.LEFT, fill="both", expand=True, padx=5)

        ttk.Checkbutton(col1, text="🔄 Duplicados",
                        variable=self.clean_duplicates).pack(anchor="w")
        ttk.Checkbutton(col1, text="📄 Temporales",
                        variable=self.clean_temp).pack(anchor="w")
        ttk.Checkbutton(col1, text="📁 Carpetas vacías",
                        variable=self.clean_empty).pack(anchor="w")
        ttk.Checkbutton(col1, text="📦 Archivos grandes",
                        variable=self.clean_large).pack(anchor="w")

        # Columna 2
        col2 = ttk.Frame(frame_fila2)
        col2.pack(side=tk.LEFT, fill="both", expand=True, padx=5)

        ttk.Checkbutton(col2, text="⏳ Archivos antiguos",
                        variable=self.clean_old).pack(anchor="w")
        ttk.Checkbutton(col2, text="🗑️ Papelera reciclaje",
                        variable=self.clean_recycle).pack(anchor="w")
        ttk.Checkbutton(col2, text="📋 Logs y depuración",
                        variable=self.clean_logs).pack(anchor="w")
        ttk.Checkbutton(col2, text="💾 Cachés de apps",
                        variable=self.clean_cache).pack(anchor="w")

        # Columna 3: Parámetros
        col3 = ttk.Frame(frame_fila2)
        col3.pack(side=tk.RIGHT, fill="both", expand=True, padx=5)

        ttk.Label(col3, text="Grandes >").pack(anchor="w")
        frame_spin1 = ttk.Frame(col3)
        frame_spin1.pack(anchor="w")
        ttk.Spinbox(
            frame_spin1,
            from_=1,
            to=10000,
            textvariable=self.large_size_mb,
            width=8).pack(
            side=tk.LEFT)
        ttk.Label(frame_spin1, text="MB").pack(side=tk.LEFT, padx=2)

        ttk.Label(col3, text="Antiguos >").pack(anchor="w", pady=(5, 0))
        frame_spin2 = ttk.Frame(col3)
        frame_spin2.pack(anchor="w")
        ttk.Spinbox(
            frame_spin2,
            from_=1,
            to=365,
            textvariable=self.old_days,
            width=8).pack(
            side=tk.LEFT)
        ttk.Label(frame_spin2, text="días").pack(side=tk.LEFT, padx=2)

        ttk.Label(col3, text="Duplicados >").pack(anchor="w", pady=(5, 0))
        frame_spin3 = ttk.Frame(col3)
        frame_spin3.pack(anchor="w")
        ttk.Spinbox(
            frame_spin3,
            from_=1,
            to=100000,
            textvariable=self.min_duplicate_size_kb,
            width=8).pack(
            side=tk.LEFT)
        ttk.Label(frame_spin3, text="KB").pack(side=tk.LEFT, padx=2)

        # ============================================
        # FILA 3: Acción y botones
        # ============================================
        frame_fila3 = ttk.Frame(main_frame)
        frame_fila3.pack(fill="x", pady=2)

        # Acción (izquierda)
        frame_accion = ttk.LabelFrame(frame_fila3, text="🎯 Acción", padding=3)
        frame_accion.pack(side=tk.LEFT, fill="x", expand=True)

        ttk.Radiobutton(frame_accion, text="🗑️ Eliminar", variable=self.action,
                        value="delete").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(
            frame_accion,
            text="📁 Mover a basura",
            variable=self.action,
            value="move_trash").pack(
            side=tk.LEFT,
            padx=5)
        ttk.Radiobutton(frame_accion, text="❓ Preguntar", variable=self.action,
                        value="ask").pack(side=tk.LEFT, padx=5)

        # Botones (derecha)
        frame_botones = ttk.Frame(frame_fila3)
        frame_botones.pack(side=tk.RIGHT, padx=5)

        self.btn_scan = ttk.Button(frame_botones, text="🔍 ANALIZAR",
                                   command=self._analizar_espacio,
                                   style="Accent.TButton")
        self.btn_scan.pack(side=tk.LEFT, padx=2, ipadx=10)

        self.btn_informe = ttk.Button(frame_botones, text="📄 INFORME",
                                      command=self._generar_informe,
                                      state="disabled")
        self.btn_informe.pack(side=tk.LEFT, padx=2, ipadx=10)

        self.btn_clean = ttk.Button(frame_botones, text="🧹 LIMPIAR",
                                    command=self._liberar_espacio,
                                    state="disabled",
                                    style="Accent.TButton")
        self.btn_clean.pack(side=tk.LEFT, padx=2, ipadx=10)

        self.btn_cancel = ttk.Button(frame_botones, text="⛔ CANCELAR",
                                     command=self._cancelar_limpieza,
                                     state="disabled")
        self.btn_cancel.pack(side=tk.LEFT, padx=2, ipadx=10)

        # ===== PANEL INFERIOR: Resultados, progreso y log =====
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="both", expand=True, pady=2)

        # ---- Resumen (compacto) ----
        frame_resumen = ttk.LabelFrame(
            bottom_frame, text="📊 Resumen", padding=2)
        frame_resumen.pack(fill="x", pady=1)

        self.label_resumen = ttk.Label(
            frame_resumen,
            text="🔍 Analiza una carpeta para ver qué espacio puedes liberar.")
        self.label_resumen.pack(anchor="w", padx=5)

        # ---- TABLA DE RESULTADOS (arriba) ----
        frame_tabla = ttk.LabelFrame(
            bottom_frame,
            text="📋 Resultados encontrados",
            padding=2)
        frame_tabla.pack(fill="both", expand=True, pady=1)

        columns = ("Archivo", "Tamaño", "Tipo", "Ubicación", "Motivo")
        self.tree = ttk.Treeview(
            frame_tabla,
            columns=columns,
            show="headings",
            height=8)
        self.tree.heading("Archivo", text="Archivo")
        self.tree.heading("Tamaño", text="Tamaño")
        self.tree.heading("Tipo", text="Tipo")
        self.tree.heading("Ubicación", text="Ubicación")
        self.tree.heading("Motivo", text="Motivo")

        self.tree.column("Archivo", width=130)
        self.tree.column("Tamaño", width=65)
        self.tree.column("Tipo", width=75)
        self.tree.column("Ubicación", width=150)
        self.tree.column("Motivo", width=90)

        scroll = ttk.Scrollbar(
            frame_tabla,
            orient="vertical",
            command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # ---- BARRA DE PROGRESO (en medio) ----
        frame_progreso = ttk.LabelFrame(
            bottom_frame, text="📊 Progreso", padding=2)
        frame_progreso.pack(fill="x", pady=1)

        self.progress_bar = ttk.Progressbar(
            frame_progreso, length=400, mode='determinate')
        self.progress_bar.pack(fill="x", pady=2)

        frame_info = ttk.Frame(frame_progreso)
        frame_info.pack(fill="x", pady=1)

        self.label_porcentaje = ttk.Label(
            frame_info, text="0%", font=(
                "Arial", 9, "bold"))
        self.label_porcentaje.pack(side=tk.LEFT, padx=5)

        self.label_eta = ttk.Label(
            frame_info,
            text="⏱️ --:--",
            font=(
                "Arial",
                9))
        self.label_eta.pack(side=tk.RIGHT, padx=5)

        self.label_progress = ttk.Label(
            frame_info, text="Esperando...", font=(
                "Arial", 8), anchor="center")
        self.label_progress.pack(side=tk.LEFT, fill="x", expand=True, padx=10)

        # ---- LOG (abajo) ----
        frame_log = ttk.LabelFrame(bottom_frame, text="📋 Registro", padding=2)
        frame_log.pack(fill="both", expand=True, pady=1)

        log_frame = ttk.Frame(frame_log)
        log_frame.pack(fill="both", expand=True)

        scroll_log = ttk.Scrollbar(log_frame)
        scroll_log.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(log_frame,
                                yscrollcommand=scroll_log.set,
                                font=("Consolas", 8),
                                bg="#f8f9fa",
                                wrap=tk.WORD,
                                relief=tk.SUNKEN,
                                borderwidth=1,
                                height=6)
        self.log_text.pack(side=tk.LEFT, fill="both", expand=True)
        scroll_log.config(command=self.log_text.yview)

        self.log_text.tag_configure("info", foreground="#2c3e50")
        self.log_text.tag_configure("success", foreground="#27ae60")
        self.log_text.tag_configure("error", foreground="#e74c3c")
        self.log_text.tag_configure("warning", foreground="#f39c12")
        self.log_text.tag_configure("bold", font=("Consolas", 8, "bold"))

        self._log("💾 Listo para analizar espacio...", "info")

    def _select_folder(self):
        """Seleccionar carpeta"""
        folder = filedialog.askdirectory()
        if folder:
            self.target_dir.set(folder)

    def _log(self, message, tag="info"):
        """Añadir mensaje al log con scroll automático"""
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.update_idletasks()

    def _update_progress(self, value, text=""):
        """Actualizar barra de progreso con porcentaje y tiempo"""
        # Redondear el progreso
        progreso = round(value, 1)

        # Actualizar barra
        self.progress_bar.config(value=progreso)

        # Actualizar porcentaje (siempre visible)
        self.label_porcentaje.config(text=f"{progreso:.1f}%")

        # Calcular y actualizar ETA
        eta_text = self._calcular_eta(progreso)
        self.label_eta.config(text=f"⏱️ {eta_text}")

        # Actualizar nombre del archivo (si se proporciona)
        if text:
            self.label_progress.config(text=text)

        self.parent.update_idletasks()

    def _reset_progress(self):
        """Resetear la barra de progreso"""
        self.progress_bar.config(value=0)
        self.label_porcentaje.config(text="0%")
        self.label_eta.config(text="⏱️ --:--")
        self.label_progress.config(text="Esperando...")
        self.parent.update_idletasks()

    def _format_size(self, size_bytes):
        """Formatear tamaño de archivo"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def _calcular_eta(self, progreso_actual):
        """Calcular tiempo estimado de finalización"""
        if not self.tiempo_inicio or progreso_actual <= 0:
            return "--:--"

        tiempo_actual = time.time()
        tiempo_transcurrido = tiempo_actual - self.tiempo_inicio

        if progreso_actual > 1:
            tiempo_total_estimado = (
                tiempo_transcurrido / progreso_actual) * 100
            tiempo_restante = tiempo_total_estimado - tiempo_transcurrido

            if tiempo_restante <= 0:
                return "00:00"

            if tiempo_restante < 60:
                return f"00:{int(tiempo_restante):02d}"
            elif tiempo_restante < 3600:
                minutos = int(tiempo_restante // 60)
                segundos = int(tiempo_restante % 60)
                return f"{minutos:02d}:{segundos:02d}"
            else:
                horas = int(tiempo_restante // 3600)
                minutos = int((tiempo_restante % 3600) // 60)
                return f"{horas:02d}:{minutos:02d}"

        return "--:--"

    def _cancelar_limpieza(self):
        """Cancelar el proceso de limpieza en curso"""
        if not self.limpiando:
            return

        if messagebox.askyesno(
            "⛔ Cancelar limpieza",
            "¿Seguro que quieres cancelar la limpieza?\n\n"
            "⚠️ Los archivos ya eliminados no se recuperarán.\n"
                "✅ Los archivos no procesados permanecerán en la lista."):

            self.cancelar_limpieza = True
            self._log("⛔ Cancelación solicitada...", "warning")
            self._update_progress(
                self.progress_bar.cget('value'),
                "⛔ Cancelando...")

    def _es_archivo_protegido(self, file_path):
        """Verificar si un archivo está protegido"""
        file_path = Path(file_path)
        file_str = str(file_path).lower()
        file_name = file_path.name.lower()
        _ = str(file_path.parent).lower()

        # 1. Verificar extensiones protegidas
        if file_path.suffix.lower() in self.extensiones_protegidas:
            return True, "Extensión protegida"

        # 2. Verificar nombres de archivo protegidos
        if file_name in [f.lower() for f in self.archivos_protegidos]:
            return True, "Archivo protegido por nombre"

        # 3. Verificar rutas protegidas
        for ruta in self.rutas_protegidas:
            if ruta.lower() in file_str:
                return True, f"Ruta protegida: {ruta}"

        # 4. Verificar carpetas de usuario protegidas
        for carpeta in self.carpetas_usuario_protegidas:
            if f'\\{carpeta.lower()}\\' in file_str or file_str.endswith(
                    f'\\{carpeta.lower()}'):
                return True, f"Carpeta de usuario protegida: {carpeta}"

        # 5. Verificar si está en site-packages de Python
        if 'site-packages' in file_str or 'pythoncore' in file_str:
            return True, "Paquete de Python"

        # 6. Verificar archivos del sistema (ocultos o del sistema)
        try:
            if file_path.exists():
                import ctypes
                FILE_ATTRIBUTE_SYSTEM = 0x4

                attrs = ctypes.windll.kernel32.GetFileAttributesW(
                    str(file_path))
                if attrs & FILE_ATTRIBUTE_SYSTEM:
                    return True, "Archivo del sistema"
        except BaseException:
            pass

        return False, ""

    def _analizar_espacio(self):
        """Analizar espacio en la carpeta seleccionada"""
        folder = self.target_dir.get()
        if not folder or not Path(folder).exists():
            messagebox.showerror("Error", "❌ Selecciona una carpeta válida")
            return

        if not any([
            self.clean_duplicates.get(),
            self.clean_temp.get(),
            self.clean_empty.get(),
            self.clean_large.get(),
            self.clean_old.get(),
            self.clean_recycle.get(),
            self.clean_logs.get(),
            self.clean_cache.get()
        ]):
            messagebox.showwarning("Advertencia",
                                   "Selecciona al menos una opción de limpieza")
            return

        # Limpiar resultados anteriores
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.log_text.delete(1.0, tk.END)
        self.current_files = []
        self.duplicates = []
        self.empty_folders = []
        self.temp_files = []
        self.cancelar_limpieza = False
        self._reset_progress()
        self.tiempo_inicio = time.time()
        self.progreso_anterior = 0
        self.tiempo_anterior = self.tiempo_inicio

        self._log("=" * 50, "bold")
        self._log("🔍 INICIANDO ANÁLISIS", "bold")
        self._log(f"📁 {folder}", "info")
        self._log("=" * 50, "bold")

        self.btn_clean.config(state="disabled")
        self.btn_informe.config(state="disabled")
        self.btn_scan.config(state="disabled")
        self._update_progress(0, "🔍 Analizando...")

        def analizar():
            try:
                folder_path = Path(folder)
                all_files = []
                all_folders = []

                if self.include_subfolders.get():
                    all_files = list(folder_path.rglob("*"))
                    all_folders = [
                        p for p in folder_path.rglob("*") if p.is_dir()]
                else:
                    all_files = list(folder_path.iterdir())
                    all_folders = [
                        p for p in folder_path.iterdir() if p.is_dir()]

                total_files = len([f for f in all_files if f.is_file()])

                # Calcular tareas para el progreso
                tareas = 0
                if self.clean_temp.get():
                    tareas += 1
                if self.clean_duplicates.get():
                    tareas += 1
                if self.clean_empty.get():
                    tareas += 1
                if self.clean_large.get():
                    tareas += 1
                if self.clean_old.get():
                    tareas += 1
                if self.clean_logs.get():
                    tareas += 1
                if self.clean_recycle.get():
                    tareas += 1
                if self.clean_cache.get():
                    tareas += 1

                if tareas == 0:
                    tareas = 1

                tarea_actual = 0
                progreso_por_tarea = 100 / tareas

                # 1. TEMPORALES
                if self.clean_temp.get():
                    tarea_actual += 1
                    progreso_base = (tarea_actual - 1) * progreso_por_tarea
                    self.parent.after(
                        0, lambda: self._log(
                            "🔍 Buscando archivos temporales...", "info"))
                    temp_count = 0

                    for i, file_path in enumerate(all_files):
                        if not file_path.is_file():
                            continue

                        if file_path.suffix.lower() in self.temp_extensions:
                            self.temp_files.append({
                                "path": file_path,
                                "name": file_path.name,
                                "size": file_path.stat().st_size if file_path.exists() else 0,
                                "tipo": "Temporal",
                                "motivo": "Extensión temporal"
                            })
                            temp_count += 1
                            continue

                        for temp_folder in self.temp_folders:
                            if temp_folder in str(file_path.parent).lower():
                                self.temp_files.append({
                                    "path": file_path,
                                    "name": file_path.name,
                                    "size": file_path.stat().st_size if file_path.exists() else 0,
                                    "tipo": "Temporal",
                                    "motivo": f"Carpeta: {temp_folder}"
                                })
                                temp_count += 1
                                break

                        if i % 50 == 0:
                            progreso_tarea = (
                                i / total_files) * progreso_por_tarea
                            progreso_total = progreso_base + progreso_tarea
                            self.parent.after(
                                0, lambda p=progreso_total: self._update_progress(
                                    p, f"📄 {
                                        file_path.name}"))

                    self.parent.after(
                        0, lambda: self._log(
                            f"   ✅ Temporales: {temp_count}", "success"))

                # 2. DUPLICADOS
                if self.clean_duplicates.get():
                    tarea_actual += 1
                    progreso_base = (tarea_actual - 1) * progreso_por_tarea
                    self.parent.after(
                        0, lambda: self._log(
                            "🔍 Buscando archivos duplicados...", "info"))
                    size_map = {}
                    dup_count = 0

                    for i, file_path in enumerate(all_files):
                        if not file_path.is_file():
                            continue

                        try:
                            size = file_path.stat().st_size
                            if size < self.min_duplicate_size_kb.get() * 1024:
                                continue

                            if size not in size_map:
                                size_map[size] = []
                            size_map[size].append(file_path)
                        except BaseException:
                            pass

                        if i % 50 == 0:
                            progreso_tarea = (
                                i / total_files) * progreso_por_tarea
                            progreso_total = progreso_base + progreso_tarea
                            self.parent.after(
                                0, lambda p=progreso_total: self._update_progress(
                                    p, f"📄 {
                                        file_path.name}"))

                    for size, files in size_map.items():
                        if len(files) < 2:
                            continue

                        hash_map = {}
                        for file_path in files:
                            try:
                                with open(file_path, 'rb') as f:
                                    data = f.read(65536)
                                    file_hash = hashlib.md5(data).hexdigest()

                                if file_hash not in hash_map:
                                    hash_map[file_hash] = []
                                hash_map[file_hash].append(file_path)
                            except BaseException:
                                pass

                        for hash_value, file_list in hash_map.items():
                            if len(file_list) > 1:
                                for i, file_path in enumerate(
                                        file_list[1:], 1):
                                    self.duplicates.append({
                                        "path": file_path,
                                        "name": file_path.name,
                                        "size": file_path.stat().st_size if file_path.exists() else 0,
                                        "tipo": "Duplicado",
                                        "motivo": f"Duplicado de: {file_list[0].name}"
                                    })
                                    dup_count += 1

                    self.parent.after(
                        0, lambda: self._log(
                            f"   ✅ Duplicados: {dup_count}", "success"))

                # 3. CARPETAS VACÍAS
                if self.clean_empty.get():
                    tarea_actual += 1
                    progreso_base = (tarea_actual - 1) * progreso_por_tarea
                    self.parent.after(
                        0, lambda: self._log(
                            "🔍 Buscando carpetas vacías...", "info"))
                    empty_count = 0

                    for folder_path in all_folders:
                        try:
                            if not any(folder_path.iterdir()):
                                self.empty_folders.append({
                                    "path": folder_path,
                                    "name": folder_path.name,
                                    "size": 0,
                                    "tipo": "Carpeta vacía",
                                    "motivo": "Carpeta vacía"
                                })
                                empty_count += 1
                        except BaseException:
                            pass

                    self.parent.after(
                        0, lambda: self._log(
                            f"   ✅ Carpetas vacías: {empty_count}", "success"))

                # 4. ARCHIVOS GRANDES
                if self.clean_large.get():
                    tarea_actual += 1
                    progreso_base = (tarea_actual - 1) * progreso_por_tarea
                    self.parent.after(0, lambda: self._log(
                        f"🔍 Buscando archivos grandes (+{self.large_size_mb.get()}MB)...", "info"))
                    large_count = 0
                    min_size = self.large_size_mb.get() * 1024 * 1024

                    for i, file_path in enumerate(all_files):
                        if not file_path.is_file():
                            continue

                        try:
                            size = file_path.stat().st_size
                            if size >= min_size:
                                self.current_files.append({
                                    "path": file_path,
                                    "name": file_path.name,
                                    "size": size,
                                    "tipo": "Archivo grande",
                                    "motivo": f"{size / (1024 * 1024):.1f} MB"
                                })
                                large_count += 1
                        except BaseException:
                            pass

                        if i % 50 == 0:
                            progreso_tarea = (
                                i / total_files) * progreso_por_tarea
                            progreso_total = progreso_base + progreso_tarea
                            self.parent.after(
                                0, lambda p=progreso_total: self._update_progress(
                                    p, f"📄 {
                                        file_path.name}"))

                    self.parent.after(
                        0, lambda: self._log(
                            f"   ✅ Grandes: {large_count}", "success"))

                # 5. ARCHIVOS ANTIGUOS
                if self.clean_old.get():
                    tarea_actual += 1
                    progreso_base = (tarea_actual - 1) * progreso_por_tarea
                    self.parent.after(0, lambda: self._log(
                        f"🔍 Buscando archivos antiguos (+{self.old_days.get()} días)...", "info"))
                    old_count = 0
                    cutoff = datetime.now() - timedelta(days=self.old_days.get())

                    for i, file_path in enumerate(all_files):
                        if not file_path.is_file():
                            continue

                        try:
                            mtime = datetime.fromtimestamp(
                                file_path.stat().st_mtime)
                            if mtime < cutoff:
                                self.current_files.append({
                                    "path": file_path,
                                    "name": file_path.name,
                                    "size": file_path.stat().st_size,
                                    "tipo": "Archivo antiguo",
                                    "motivo": f"{self.old_days.get()} días"
                                })
                                old_count += 1
                        except BaseException:
                            pass

                        if i % 50 == 0:
                            progreso_tarea = (
                                i / total_files) * progreso_por_tarea
                            progreso_total = progreso_base + progreso_tarea
                            self.parent.after(
                                0, lambda p=progreso_total: self._update_progress(
                                    p, f"📄 {
                                        file_path.name}"))

                    self.parent.after(
                        0, lambda: self._log(
                            f"   ✅ Antiguos: {old_count}", "success"))

                # 6. LOGS
                if self.clean_logs.get():
                    tarea_actual += 1
                    progreso_base = (tarea_actual - 1) * progreso_por_tarea
                    self.parent.after(
                        0, lambda: self._log(
                            "🔍 Buscando logs y depuración...", "info"))
                    log_count = 0

                    for i, file_path in enumerate(all_files):
                        if not file_path.is_file():
                            continue

                        if file_path.suffix.lower() in self.log_extensions:
                            self.current_files.append({
                                "path": file_path,
                                "name": file_path.name,
                                "size": file_path.stat().st_size if file_path.exists() else 0,
                                "tipo": "Log",
                                "motivo": "Log/depuración"
                            })
                            log_count += 1

                        if i % 50 == 0:
                            progreso_tarea = (
                                i / total_files) * progreso_por_tarea
                            progreso_total = progreso_base + progreso_tarea
                            self.parent.after(
                                0, lambda p=progreso_total: self._update_progress(
                                    p, f"📄 {
                                        file_path.name}"))

                    self.parent.after(
                        0, lambda: self._log(
                            f"   ✅ Logs: {log_count}", "success"))

                # 7. PAPELERA
                if self.clean_recycle.get():
                    tarea_actual += 1
                    progreso_base = (tarea_actual - 1) * progreso_por_tarea
                    self.parent.after(
                        0, lambda: self._log(
                            "🔍 Buscando papelera de reciclaje...", "info"))
                    recycle_count = 0

                    for i, file_path in enumerate(all_files):
                        if not file_path.is_file():
                            continue

                        if '$recycle.bin' in str(file_path).lower(
                        ) or 'recycler' in str(file_path).lower():
                            self.current_files.append({
                                "path": file_path,
                                "name": file_path.name,
                                "size": file_path.stat().st_size if file_path.exists() else 0,
                                "tipo": "Papelera",
                                "motivo": "Papelera reciclaje"
                            })
                            recycle_count += 1

                        if i % 50 == 0:
                            progreso_tarea = (
                                i / total_files) * progreso_por_tarea
                            progreso_total = progreso_base + progreso_tarea
                            self.parent.after(
                                0, lambda p=progreso_total: self._update_progress(
                                    p, f"📄 {
                                        file_path.name}"))

                    self.parent.after(
                        0, lambda: self._log(
                            f"   ✅ Papelera: {recycle_count}", "success"))

                # 8. CACHÉS
                if self.clean_cache.get():
                    tarea_actual += 1
                    progreso_base = (tarea_actual - 1) * progreso_por_tarea
                    self.parent.after(
                        0, lambda: self._log(
                            "🔍 Buscando cachés...", "info"))
                    cache_count = 0
                    cache_patterns = [
                        'cache', 'thumbcache', 'thumbnail', 'preview']

                    for i, file_path in enumerate(all_files):
                        if not file_path.is_file():
                            continue

                        for pattern in cache_patterns:
                            if pattern in str(file_path).lower():
                                self.current_files.append({
                                    "path": file_path,
                                    "name": file_path.name,
                                    "size": file_path.stat().st_size if file_path.exists() else 0,
                                    "tipo": "Caché",
                                    "motivo": f"Caché ({pattern})"
                                })
                                cache_count += 1
                                break

                        if i % 50 == 0:
                            progreso_tarea = (
                                i / total_files) * progreso_por_tarea
                            progreso_total = progreso_base + progreso_tarea
                            self.parent.after(
                                0, lambda p=progreso_total: self._update_progress(
                                    p, f"📄 {
                                        file_path.name}"))

                    self.parent.after(
                        0, lambda: self._log(
                            f"   ✅ Cachés: {cache_count}", "success"))

                self.parent.after(0, self._mostrar_resultados)

            except Exception as e:
                error_msg = str(e)
                self.parent.after(
                    0, lambda: self._log(
                        f"❌ Error: {error_msg}", "error"))
            finally:
                self.parent.after(
                    0, lambda: self.btn_scan.config(
                        state="normal"))
                self.parent.after(
                    0, lambda: self._update_progress(
                        100, "✅ Análisis completado"))

        Thread(target=analizar, daemon=True).start()

    def _mostrar_resultados(self):
        """Mostrar resultados del análisis"""
        all_items = []
        all_items.extend(self.current_files)
        all_items.extend(self.duplicates)
        all_items.extend(self.empty_folders)
        all_items.extend(self.temp_files)

        # Calcular tiempo total
        if self.tiempo_inicio:
            tiempo_total = time.time() - self.tiempo_inicio
            if tiempo_total < 60:
                tiempo_str = f"{int(tiempo_total)} segundos"
            elif tiempo_total < 3600:
                minutos = int(tiempo_total // 60)
                segundos = int(tiempo_total % 60)
                tiempo_str = f"{minutos}m {segundos}s"
            else:
                horas = int(tiempo_total // 3600)
                minutos = int((tiempo_total % 3600) // 60)
                tiempo_str = f"{horas}h {minutos}m"
        else:
            tiempo_str = "0 segundos"

        if not all_items:
            self._log("", "info")
            self._log("✅ No se encontraron archivos para limpiar", "success")
            self.label_resumen.config(
                text="✅ No se encontraron archivos para limpiar. ¡Tu sistema está limpio!")
            self.btn_clean.config(state="disabled")
            self.btn_informe.config(state="disabled")
            self._update_progress(
                100, f"✅ Análisis completado en {tiempo_str}")
            return

        # Ordenar por tamaño
        all_items.sort(key=lambda x: x.get("size", 0), reverse=True)

        total_size = 0
        for item in all_items:
            size = item.get("size", 0)
            total_size += size

            size_str = self._format_size(size)
            tipo = item.get("tipo", "Desconocido")
            motivo = item.get("motivo", "")
            path = item.get("path", "")
            name = item.get("name", str(path))

            # Verificar seguridad
            es_protegido, razon = self._es_archivo_protegido(path)
            if es_protegido:
                self.tree.insert("", "end", values=(
                    name,
                    size_str,
                    tipo,
                    str(path.parent) if path else "",
                    motivo
                ))
            else:
                self.tree.insert("", "end", values=(
                    name,
                    size_str,
                    tipo,
                    str(path.parent) if path else "",
                    motivo
                ))

        total_mb = total_size / (1024 * 1024)
        total_gb = total_mb / 1024

        if total_gb > 1:
            size_str = f"{total_gb:.2f} GB"
        else:
            size_str = f"{total_mb:.1f} MB"

        self._log("", "info")
        self._log("=" * 50, "bold")
        self._log("✅ ANÁLISIS COMPLETADO", "success")
        self._log(f"📊 Archivos: {len(all_items)}", "info")
        self._log(f"📦 Espacio: {size_str}", "info")
        self._log(f"⏱️ Tiempo: {tiempo_str}", "info")
        self._log("=" * 50, "bold")

        resumen = f"📊 {
            len(all_items)} archivos | 📦 {size_str} | ⏱️ {tiempo_str}"
        self.label_resumen.config(text=resumen)

        self.btn_clean.config(state="normal")
        self.btn_informe.config(state="normal")
        self._update_progress(100, f"✅ Análisis completado en {tiempo_str}")

    def _generar_informe(self):
        """Generar un archivo de informe con TODOS los datos"""
        items = self.tree.get_children()
        if not items:
            messagebox.showinfo("Info", "No hay archivos para generar informe")
            return

        archivo_informe = filedialog.asksaveasfilename(
            title="Guardar informe de archivos encontrados",
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )

        if not archivo_informe:
            return

        try:
            with open(archivo_informe, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("INFORME DE ARCHIVOS ENCONTRADOS - LIBERADOR DE ESPACIO\n")
                f.write("=" * 80 + "\n")
                f.write(
                    f"Fecha: {
                        datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Carpeta analizada: {self.target_dir.get()}\n")
                f.write("=" * 80 + "\n\n")

                total_archivos = len(items)
                total_size = 0
                tipos = {}

                for item in items:
                    values = self.tree.item(item, 'values')
                    if len(values) < 5:
                        continue

                    tipo = values[2]
                    tipos[tipo] = tipos.get(tipo, 0) + 1

                    tamaño_str = values[1]
                    try:
                        if 'GB' in tamaño_str:
                            total_size += float(tamaño_str.replace('GB',
                                                '').strip()) * 1024 * 1024 * 1024
                        elif 'MB' in tamaño_str:
                            total_size += float(tamaño_str.replace('MB',
                                                '').strip()) * 1024 * 1024
                        elif 'KB' in tamaño_str:
                            total_size += float(tamaño_str.replace('KB',
                                                '').strip()) * 1024
                    except BaseException:
                        pass

                total_mb = total_size / (1024 * 1024)
                total_gb = total_mb / 1024

                f.write("RESUMEN\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total archivos encontrados: {total_archivos}\n")

                if total_gb > 1:
                    f.write(f"Espacio total: {total_gb:.2f} GB\n")
                else:
                    f.write(f"Espacio total: {total_mb:.1f} MB\n")

                f.write("\nDesglose por tipo:\n")
                for tipo, count in sorted(
                        tipos.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"  • {tipo}: {count} archivos\n")

                f.write("\n" + "=" * 80 + "\n\n")

                f.write("LISTA DE ARCHIVOS ENCONTRADOS\n")
                f.write("-" * 40 + "\n\n")

                for i, item in enumerate(items, 1):
                    values = self.tree.item(item, 'values')
                    if len(values) < 5:
                        continue

                    archivo = values[0]
                    tamaño = values[1]
                    tipo = values[2]
                    ubicacion = values[3]
                    motivo = values[4]

                    f.write(f"[{i}] {archivo}\n")
                    f.write(f"    Tamaño: {tamaño}\n")
                    f.write(f"    Tipo: {tipo}\n")
                    f.write(f"    Ubicación: {ubicacion}\n")
                    f.write(f"    Motivo: {motivo}\n")
                    f.write("\n")

                f.write("=" * 80 + "\n")
                f.write("⚠️ IMPORTANTE\n")
                f.write("=" * 80 + "\n")
                f.write(
                    "Este informe muestra los archivos que el liberador de espacio ha encontrado.\n")
                f.write(
                    "Antes de eliminarlos, asegúrate de que no son necesarios para tu sistema.\n")
                f.write(
                    "Revisa la ubicación de cada archivo antes de proceder con la limpieza.\n")
                f.write("=" * 80 + "\n")

            self._log(f"✅ Informe guardado: {archivo_informe}", "success")
            messagebox.showinfo(
                "Éxito", f"✅ Informe guardado correctamente\n\n{archivo_informe}")

            if messagebox.askyesno(
                "Abrir informe",
                    "¿Quieres abrir el archivo de informe ahora?"):
                os.startfile(archivo_informe)

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo guardar el informe:\n{
                    str(e)}")

    def _liberar_espacio(self):
        """Liberar espacio - CON SOPORTE DE CANCELACIÓN Y VERIFICACIÓN DE SEGURIDAD"""
        items = self.tree.get_children()
        if not items:
            messagebox.showinfo("Info", "No hay archivos para liberar")
            return

        # 1. CALCULAR ESPACIO TOTAL
        total_size = 0
        for item in items:
            values = self.tree.item(item, 'values')
            if len(values) >= 2:
                size_str = values[1]
                try:
                    if 'GB' in size_str:
                        total_size += float(size_str.replace('GB',
                                            '').strip()) * 1024 * 1024 * 1024
                    elif 'MB' in size_str:
                        total_size += float(size_str.replace('MB',
                                            '').strip()) * 1024 * 1024
                    elif 'KB' in size_str:
                        total_size += float(size_str.replace('KB',
                                            '').strip()) * 1024
                except BaseException:
                    pass

        total_gb = total_size / (1024 * 1024 * 1024)
        total_mb = total_size / (1024 * 1024)

        if total_gb > 1:
            espacio_str = f"{total_gb:.2f} GB"
        else:
            espacio_str = f"{total_mb:.1f} MB"

        # 2. CONFIRMAR
        if not messagebox.askyesno("⚠️ Confirmar eliminación",
                                   f"¿Eliminar {len(items)} archivos?\n\n"
                                   f"📦 Espacio a liberar: {espacio_str}\n"
                                   f"📁 Archivos: {len(items)}\n\n"
                                   f"⚠️ Esta acción no se puede deshacer."):
            return

        # 3. RESETEAR ESTADO
        self.cancelar_limpieza = False
        self.limpiando = True

        self._log("=" * 50, "bold")
        self._log("🧹 INICIANDO LIBERACIÓN DE ESPACIO", "bold")
        self._log(f"📦 Espacio a liberar: {espacio_str}", "info")
        self._log(f"📁 Archivos a eliminar: {len(items)}", "info")
        self._log("=" * 50, "bold")

        self.btn_clean.config(state="disabled")
        self.btn_scan.config(state="disabled")
        self.btn_informe.config(state="disabled")
        self.btn_cancel.config(state="normal")
        self._reset_progress()
        self.tiempo_inicio = time.time()

        # 4. ELIMINAR
        def liberar():
            eliminados = 0
            errores = 0
            cancelados = 0
            protegidos = 0
            total_items = len(items)
            items_list = list(items)

            for i, item in enumerate(items_list):
                # Verificar cancelación
                if self.cancelar_limpieza:
                    cancelados = total_items - i
                    self._log(
                        f"⛔ Limpieza cancelada por el usuario",
                        "warning")
                    self._log(f"📊 Pendientes: {cancelados} archivos", "info")
                    break

                try:
                    values = self.tree.item(item, 'values')
                    if len(values) < 5:
                        continue
                except BaseException:
                    continue

                nombre_archivo = values[0]

                # Progreso y ETA
                progress = (i / total_items) * 100
                eta = self._calcular_eta(progress)
                self.parent.after(
                    0,
                    lambda p=progress,
                    n=nombre_archivo: self._update_progress(
                        p,
                        f"🧹 {n}"))
                self.parent.after(
                    0, lambda e=eta: self.label_eta.config(
                        text=f"⏱️ {e}"))

                try:
                    # Buscar el archivo
                    file_path = None
                    for file_info in self.current_files + self.duplicates + \
                            self.empty_folders + self.temp_files:
                        if file_info.get("name") == nombre_archivo:
                            file_path = file_info.get("path")
                            break

                    if not file_path and len(values) >= 4:
                        ubicacion = values[3]
                        if ubicacion:
                            file_path = Path(ubicacion) / nombre_archivo
                        else:
                            file_path = Path(nombre_archivo)

                    if not file_path:
                        raise Exception("Ruta no encontrada")

                    # VERIFICACIÓN DE SEGURIDAD
                    es_protegido, razon = self._es_archivo_protegido(file_path)
                    if es_protegido:
                        protegidos += 1
                        self._log(
                            f"🔴 {nombre_archivo} - PROTEGIDO: {razon}", "error")
                        self.parent.after(
                            0, lambda i=item: self.tree.delete(i))
                        continue

                    if not file_path.exists():
                        self._log(f"⚠️ No existe: {nombre_archivo}", "warning")
                        self.parent.after(
                            0, lambda i=item: self.tree.delete(i))
                        continue

                    # Eliminar
                    if self.action.get() == "delete":
                        if file_path.is_dir():
                            shutil.rmtree(str(file_path))
                        else:
                            os.remove(str(file_path))
                    elif self.action.get() == "move_trash":
                        try:
                            import send2trash
                            send2trash.send2trash(str(file_path))
                        except BaseException:
                            if file_path.is_dir():
                                shutil.rmtree(str(file_path))
                            else:
                                os.remove(str(file_path))
                    else:  # ask
                        if messagebox.askyesno(
                            "Eliminar", f"¿Eliminar {
                                file_path.name}?"):
                            if file_path.is_dir():
                                shutil.rmtree(str(file_path))
                            else:
                                os.remove(str(file_path))
                        else:
                            continue

                    eliminados += 1
                    self._log(f"✅ {nombre_archivo}", "success")
                    self.parent.after(0, lambda i=item: self.tree.delete(i))

                except Exception as e:
                    errores += 1
                    self._log(f"❌ {nombre_archivo}: {str(e)}", "error")
                    self.parent.after(0, lambda i=item: self.tree.delete(i))

            # 5. FINALIZAR
            self.parent.after(
                0, lambda: self._update_progress(
                    100, "✅ Proceso finalizado"))
            self._log("", "info")
            self._log("=" * 50, "bold")

            if self.cancelar_limpieza:
                self._log("⛔ LIMPIEZA CANCELADA", "warning")
                self._log(f"📁 Eliminados: {eliminados}", "info")
                self._log(f"⏸️ Pendientes: {cancelados}", "info")
                self._log(f"🔴 Protegidos: {protegidos}", "info")
                self._log(
                    f"❌ Errores: {errores}",
                    "error" if errores > 0 else "info")
            else:
                self._log("✅ LIBERACIÓN COMPLETADA", "success")
                self._log(f"📁 Eliminados: {eliminados}", "info")
                self._log(f"🔴 Protegidos: {protegidos}", "info")
                self._log(
                    f"❌ Errores: {errores}",
                    "error" if errores > 0 else "info")

            self._log("=" * 50, "bold")

            # Resumen
            if self.cancelar_limpieza:
                resumen_msg = f"⛔ Cancelado | Eliminados: {eliminados} | Pendientes: {cancelados} | Protegidos: {protegidos}"
            else:
                resumen_msg = f"✅ Liberados {eliminados} archivos"
                if protegidos > 0:
                    resumen_msg += f" | 🔴 Protegidos: {protegidos}"
                if errores > 0:
                    resumen_msg += f" | ❌ {errores} errores"

            self.parent.after(
                0, lambda: self.label_resumen.config(
                    text=resumen_msg))

            # Ventana emergente
            if self.cancelar_limpieza:
                msg = f"⛔ Limpieza cancelada\n\n📁 Eliminados: {eliminados}\n⏸️ Pendientes: {cancelados}\n🔴 Protegidos: {protegidos}"
                if errores > 0:
                    msg += f"\n❌ Errores: {errores}"
                self.parent.after(
                    0, lambda: messagebox.showinfo(
                        "⛔ Cancelado", msg))
            else:
                msg = f"✅ Liberación completada\n\n📁 Eliminados: {eliminados}"
                if protegidos > 0:
                    msg += f"\n🔴 Protegidos (no eliminados): {protegidos}"
                if errores > 0:
                    msg += f"\n❌ Errores: {errores}"
                self.parent.after(
                    0, lambda: messagebox.showinfo(
                        "✅ Completado", msg))

            # Habilitar botones
            self.parent.after(
                0, lambda: self.btn_clean.config(
                    state="disabled"))
            self.parent.after(0, lambda: self.btn_scan.config(state="normal"))
            self.parent.after(
                0, lambda: self.btn_informe.config(
                    state="normal"))
            self.parent.after(
                0, lambda: self.btn_cancel.config(
                    state="disabled"))
            self.parent.after(0, lambda: setattr(self, 'limpiando', False))
            self.parent.after(
                0, lambda: setattr(
                    self, 'cancelar_limpieza', False))

        Thread(target=liberar, daemon=True).start()
