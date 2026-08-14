# gui/cleaner_tab.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from threading import Thread
from core.file_cleaner import FileCleaner

class CleanerTab:
    """Pestaña de limpieza de archivos basura"""
    
    def __init__(self, parent, organizer):
        self.parent = parent
        self.organizer = organizer
        self.cleaner = FileCleaner()
        self.junk_files = []
        
        self.target_dir = tk.StringVar()
        self.min_size = tk.IntVar(value=4)  # KB
        self.include_subfolders = tk.BooleanVar(value=True)
        self.action = tk.StringVar(value="move")
        
        self._build_ui()
    
    def _build_ui(self):
        """Construir la interfaz de la pestaña de limpieza"""

        # ---- INFORMACIÓN DE LIMPIEZA (creativa) ----
        info_frame = tk.Frame(self.parent, bg="#e8f8f5", relief=tk.RAISED, bd=2)
        info_frame.pack(fill="x", pady=5, padx=5)
        info_frame.configure(height=55)
        info_frame.pack_propagate(False)
        
        # Icono
        tk.Label(info_frame, text="🧹", font=("Arial", 24), bg="#e8f8f5").pack(side=tk.LEFT, padx=15)
        
        # Texto
        text_frame = tk.Frame(info_frame, bg="#e8f8f5")
        text_frame.pack(side=tk.LEFT, fill="both", expand=True, pady=5)
        
        tk.Label(text_frame, 
                text="🪠 Limpiador de archivos basura",
                font=("Arial", 11, "bold"), fg="#0b7a6b", bg="#e8f8f5", anchor="w").pack(anchor="w")
        
        tk.Label(text_frame, 
                text="Elimina miniaturas, archivos temporales, logs antiguos y cachés que ya no sirven.",
                font=("Arial", 9), fg="#148f77", bg="#e8f8f5", anchor="w").pack(anchor="w")
        
        tk.Label(text_frame, 
                text="📸 Especialmente útil para limpiar miniaturas de imágenes que no se pueden abrir y solo ocupan espacio.",
                font=("Arial", 8), fg="#1abc9c", bg="#e8f8f5", anchor="w").pack(anchor="w")
        
        # ===== Carpeta destino =====
        frame_folder = ttk.LabelFrame(self.parent, text="📂 Carpeta a limpiar", padding=10)
        frame_folder.pack(fill="x", pady=5)
        
        ttk.Label(frame_folder, text="Carpeta:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame_folder, textvariable=self.target_dir, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(frame_folder, text="📂", command=self._select_folder).grid(row=0, column=2)
        
        # ===== Opciones =====
        frame_opciones = ttk.LabelFrame(self.parent, text="⚙️ Opciones de limpieza", padding=10)
        frame_opciones.pack(fill="x", pady=5)
        
        # Tamaño mínimo
        ttk.Label(frame_opciones, text="Tamaño mínimo (KB):").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(frame_opciones, from_=0, to=100, textvariable=self.min_size, width=10).grid(row=0, column=1, padx=5, sticky="w")
        ttk.Label(frame_opciones, text="(archivos más pequeños serán considerados basura)").grid(row=0, column=2, sticky="w", padx=5)
        
        # Subcarpetas
        ttk.Checkbutton(frame_opciones, text="📂 Incluir subcarpetas", 
                       variable=self.include_subfolders).grid(row=1, column=0, columnspan=3, sticky="w", pady=5)
        
        # Acción
        ttk.Label(frame_opciones, text="Acción:").grid(row=2, column=0, sticky="w")
        ttk.Radiobutton(frame_opciones, text="🗑️ Eliminar permanentemente", variable=self.action, 
                       value="delete").grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(frame_opciones, text="📁 Mover a carpeta 'Basura'", variable=self.action, 
                       value="move").grid(row=2, column=2, sticky="w")
        
        # ===== Botones =====
        frame_botones = ttk.Frame(self.parent)
        frame_botones.pack(pady=10)
        
        ttk.Button(frame_botones, text="🔍 Escanear basura", 
                  command=self._scan_junk).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame_botones, text="📊 Analizar carpeta", 
                  command=self._analyze_folder).pack(side=tk.LEFT, padx=5)
        
        self.btn_clean = ttk.Button(frame_botones, text="🧹 Limpiar ahora", 
                                   command=self._clean_junk, state="disabled")
        self.btn_clean.pack(side=tk.LEFT, padx=5)
        
        # ===== Resultados =====
        frame_resultados = ttk.LabelFrame(self.parent, text="📋 Resultados del escaneo", padding=10)
        frame_resultados.pack(fill="both", expand=True, pady=5)
        
        # Tabla de resultados
        columns = ("Archivo", "Tamaño", "Razón", "Carpeta")
        self.tree_results = ttk.Treeview(frame_resultados, columns=columns, show="headings", height=10)
        self.tree_results.heading("Archivo", text="Archivo")
        self.tree_results.heading("Tamaño", text="Tamaño")
        self.tree_results.heading("Razón", text="Razón")
        self.tree_results.heading("Carpeta", text="Carpeta")
        
        self.tree_results.column("Archivo", width=200)
        self.tree_results.column("Tamaño", width=80)
        self.tree_results.column("Razón", width=250)
        self.tree_results.column("Carpeta", width=200)
        
        # Scroll
        scroll = ttk.Scrollbar(frame_resultados, orient="vertical", command=self.tree_results.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_results.configure(yscrollcommand=scroll.set)
        self.tree_results.pack(fill="both", expand=True)
        
        # ===== Estadísticas =====
        frame_stats = ttk.LabelFrame(self.parent, text="📊 Estadísticas", padding=10)
        frame_stats.pack(fill="x", pady=5)
        
        self.label_stats = ttk.Label(frame_stats, text="ℹ️ Esperando escaneo...")
        self.label_stats.pack()
    
    def _select_folder(self):
        """Seleccionar carpeta"""
        folder = filedialog.askdirectory()
        if folder:
            self.target_dir.set(folder)
    
    def _scan_junk(self):
        """Escanear archivos basura"""
        folder = self.target_dir.get()
        if not folder or not Path(folder).exists():
            messagebox.showerror("Error", "❌ Selecciona una carpeta válida")
            return
        
        # Limpiar tabla
        for item in self.tree_results.get_children():
            self.tree_results.delete(item)
        
        self.btn_clean.config(state="disabled")
        self.label_stats.config(text="🔍 Escaneando archivos basura...")
        
        def scan():
            try:
                self.junk_files = self.cleaner.scan_for_junk(
                    folder, 
                    self.min_size.get(), 
                    self.include_subfolders.get()
                )
                
                # Mostrar resultados en la interfaz
                self.parent.after(0, self._show_results)
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Error", f"Error al escanear:\n{str(e)}"))
                self.parent.after(0, lambda: self.label_stats.config(text="❌ Error en el escaneo"))
        
        Thread(target=scan, daemon=True).start()
    
    def _show_results(self):
        """Mostrar resultados del escaneo"""
        # Limpiar tabla
        for item in self.tree_results.get_children():
            self.tree_results.delete(item)
        
        # Mostrar archivos
        for file_info in self.junk_files:
            self.tree_results.insert("", "end", values=(
                file_info["path"].name,
                f"{file_info['size_kb']:.1f} KB",
                file_info["reason"],
                str(file_info["path"].parent)
            ))
        
        # Actualizar estadísticas
        stats = self.cleaner.get_stats()
        total_size = sum(f["size_kb"] for f in self.junk_files)
        
        self.label_stats.config(text=f"""
📊 Encontrados: {stats['total_detected']} archivos basura
📦 Tamaño total: {total_size:.1f} KB
🗑️ Listos para limpiar
        """)
        
        if stats['total_detected'] > 0:
            self.btn_clean.config(state="normal")
            messagebox.showinfo("✅ Escaneo completado", 
                f"Se encontraron {stats['total_detected']} archivos basura\n"
                f"📦 Tamaño total: {total_size:.1f} KB\n\n"
                f"💡 Puedes revisar la lista y luego limpiar.")
        else:
            messagebox.showinfo("✅ Escaneo completado", "🎉 No se encontraron archivos basura")
    
    def _clean_junk(self):
        """Limpiar archivos basura"""
        if not self.junk_files:
            messagebox.showinfo("Info", "No hay archivos para limpiar")
            return
        
        # Confirmar
        total = len(self.junk_files)
        action_text = "eliminar permanentemente" if self.action.get() == "delete" else "mover a la carpeta Basura"
        
        if not messagebox.askyesno("⚠️ Confirmar", 
            f"¿Seguro que quieres {action_text} {total} archivos basura?\n\n"
            f"📦 Tamaño total: {sum(f['size_kb'] for f in self.junk_files):.1f} KB\n"
            f"⚠️ Esta acción no se puede deshacer fácilmente."):
            return
        
        self.btn_clean.config(state="disabled")
        self.label_stats.config(text="🧹 Limpiando archivos basura...")
        
        def clean():
            try:
                if self.action.get() == "delete":
                    result = self.cleaner.delete_files(self.junk_files)
                    msg = f"✅ Eliminados permanentemente: {len(result['deleted'])} archivos"
                else:
                    result = self.cleaner.move_to_recycle(self.junk_files)
                    msg = f"✅ Movidos a 'Basura': {len(result['moved'])} archivos"
                
                if result["errors"]:
                    msg += f"\n❌ Errores: {len(result['errors'])}"
                    for error in result["errors"][:5]:  # Mostrar solo los primeros 5
                        msg += f"\n   • {error}"
                    if len(result["errors"]) > 5:
                        msg += f"\n   ... y {len(result['errors']) - 5} más"
                
                self.parent.after(0, lambda: messagebox.showinfo("✅ Limpieza completada", msg))
                self.parent.after(0, self._scan_junk)  # Rescanear
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Error", f"Error en la limpieza:\n{str(e)}"))
                self.parent.after(0, lambda: self.btn_clean.config(state="normal"))
        
        Thread(target=clean, daemon=True).start()
    
    def _analyze_folder(self):
        """Analizar la carpeta y mostrar estadísticas"""
        folder = self.target_dir.get()
        if not folder or not Path(folder).exists():
            messagebox.showerror("Error", "❌ Selecciona una carpeta válida")
            return
        
        self.label_stats.config(text="📊 Analizando carpeta...")
        
        def analyze():
            try:
                summary = self.cleaner.get_size_summary(folder)
                
                msg = f"""
📊 ANÁLISIS DE CARPETA

📁 Carpeta: {folder}

📄 Archivos totales: {summary['total_files']:,}
📦 Tamaño total: {summary['total_size_mb']:.2f} MB

🪠 Archivos pequeños (<4KB): {summary['small_files']:,}
📏 Tamaño de archivos pequeños: {summary['small_size_kb']:.1f} KB
📊 Porcentaje de basura: {summary['small_percentage']:.1f}%

{'='*50}
💡 {'⚠️ ¡Hay muchos archivos pequeños! Considera limpiar.' if summary['small_percentage'] > 10 else '✅ La carpeta está bastante limpia.'}
                """
                
                self.parent.after(0, lambda: messagebox.showinfo("📊 Análisis completado", msg))
                self.parent.after(0, lambda: self.label_stats.config(text="✅ Análisis completado"))
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Error", f"Error al analizar:\n{str(e)}"))
                self.parent.after(0, lambda: self.label_stats.config(text="❌ Error en el análisis"))
        
        Thread(target=analyze, daemon=True).start()
