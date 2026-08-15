import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from threading import Thread
import os
import shutil

class DesorganizeTab:
    """Pestaña para recolectar archivos de subcarpetas en una sola carpeta"""
    
    def __init__(self, parent, organizer):
        self.parent = parent
        self.organizer = organizer
        self.is_running = False
        
        # Variables
        self.source_dir = tk.StringVar()
        self.dest_dir = tk.StringVar()
        self.include_subfolders = tk.BooleanVar(value=True)
        self.keep_structure = tk.BooleanVar(value=False)
        self.delete_empty = tk.BooleanVar(value=True)
        self.only_media = tk.BooleanVar(value=True)
        self.operation = tk.StringVar(value="move")
        
        # Extensiones multimedia
        self.media_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
            '.webp', '.heic', '.heif', '.raw', '.cr2', '.nef', '.arw',
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            '.m4v', '.mpg', '.mpeg', '.3gp', '.mts', '.m2ts',
            '.dng', '.orf', '.rw2', '.pef', '.srw'
        }
        
        self._build_ui()
    
    def _build_ui(self):
        """Construir la interfaz de la pestaña Desorganizar"""
        
        # ===== Contenedor principal =====
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # ===== SECCIÓN SUPERIOR: Configuración =====
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", pady=2)
        
        # ---- Instrucciones ----
        frame_instrucciones = ttk.LabelFrame(top_frame, text="📋 Instrucciones", padding=8)
        frame_instrucciones.pack(fill="x", pady=3)
        
        tk.Label(frame_instrucciones, 
                text="Recoge TODOS los archivos de las subcarpetas y los junta en una sola carpeta.",
                font=("Arial", 9), fg="#2c3e50").pack(anchor="w")
        tk.Label(frame_instrucciones, 
                text="✅ Las fechas originales de los archivos se conservan automáticamente.",
                font=("Arial", 9), fg="#27ae60").pack(anchor="w")
        
        # ---- Carpetas ----
        frame_carpetas = ttk.LabelFrame(top_frame, text="📁 Carpetas", padding=10)
        frame_carpetas.pack(fill="x", pady=3)
        
        ttk.Label(frame_carpetas, text="Origen:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(frame_carpetas, textvariable=self.source_dir, width=55).grid(row=0, column=1, padx=5)
        ttk.Button(frame_carpetas, text="📂", command=lambda: self._select_folder("source")).grid(row=0, column=2)
        
        ttk.Label(frame_carpetas, text="Destino:").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(frame_carpetas, textvariable=self.dest_dir, width=55).grid(row=1, column=1, padx=5)
        ttk.Button(frame_carpetas, text="📂", command=lambda: self._select_folder("dest")).grid(row=1, column=2)
        
        ttk.Button(frame_carpetas, text="↹ Usar misma carpeta", 
                  command=self._use_same_folder).grid(row=2, column=1, pady=5)
        
        # ---- Opciones ----
        frame_opciones = ttk.LabelFrame(top_frame, text="⚙️ Opciones", padding=10)
        frame_opciones.pack(fill="x", pady=3)
        
        ttk.Label(frame_opciones, text="Operación:").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(frame_opciones, text="Mover", variable=self.operation, 
                       value="move").grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(frame_opciones, text="Copiar", variable=self.operation, 
                       value="copy").grid(row=0, column=2, sticky="w")
        
        ttk.Checkbutton(frame_opciones, text="📂 Incluir subcarpetas (recursivo)",
                       variable=self.include_subfolders).grid(row=1, column=0, columnspan=3, sticky="w", pady=3)
        
        ttk.Checkbutton(frame_opciones, text="📁 Mantener estructura en nombres (ej: carpeta_archivo.jpg)",
                       variable=self.keep_structure).grid(row=2, column=0, columnspan=3, sticky="w", pady=3)
        
        ttk.Checkbutton(frame_opciones, text="📷 Solo fotos y videos (ignorar otros archivos)",
                       variable=self.only_media).grid(row=3, column=0, columnspan=3, sticky="w", pady=3)
        
        ttk.Checkbutton(frame_opciones, text="🗑️ Eliminar carpetas vacías después",
                       variable=self.delete_empty).grid(row=4, column=0, columnspan=3, sticky="w", pady=3)
        
        # ---- BOTONES ----
        frame_botones = ttk.Frame(top_frame)
        frame_botones.pack(pady=8, fill="x")
        
        # Botón ESCANEAR (muestra resultado en el log)
        self.btn_scan = ttk.Button(frame_botones, text="🔍 ESCANEAR", 
                                  command=self._scan_folder)
        self.btn_scan.pack(side=tk.LEFT, padx=5, fill="x", expand=True, ipady=3)

        # ===== NUEVO: Botón Limpiar todo =====
        self.btn_clear_desorganize = ttk.Button(frame_botones, text="🧹 LIMPIAR TODO", 
                                               command=self._clear_all_desorganize)
        self.btn_clear_desorganize.pack(side=tk.RIGHT, padx=5, fill="x", expand=True, ipady=3)
        
        # Botón DESORGANIZAR
        self.btn_desorganize = ttk.Button(frame_botones, text="🔄 DESORGANIZAR", 
                                         command=self._start_desorganize,
                                         style="Accent.TButton")
        self.btn_desorganize.pack(side=tk.RIGHT, padx=5, fill="x", expand=True, ipady=3)
        
        # Estilo para el botón
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))
        
        # ===== SECCIÓN INFERIOR: Progreso y Log =====
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill="both", expand=True, pady=2)
        
        # ---- Progreso ----
        frame_progreso = ttk.LabelFrame(bottom_frame, text="📊 Progreso", padding=8)
        frame_progreso.pack(fill="x", pady=3)
        
        self.progress_bar = ttk.Progressbar(frame_progreso, length=400, mode='determinate')
        self.progress_bar.pack(fill="x", pady=5)
        
        self.label_progress = ttk.Label(frame_progreso, text="Esperando...")
        self.label_progress.pack()
        
        # ---- LOG (donde se muestra TODO el escaneo y el progreso) ----
        frame_log = ttk.LabelFrame(bottom_frame, text="📋 Registro", padding=8)
        frame_log.pack(fill="both", expand=True, pady=3)
        
        log_frame = ttk.Frame(frame_log)
        log_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, 
                               yscrollcommand=scrollbar.set,
                               font=("Consolas", 9),
                               bg="#f8f9fa",
                               wrap=tk.WORD,
                               relief=tk.SUNKEN,
                               borderwidth=1)
        self.log_text.pack(side=tk.LEFT, fill="both", expand=True)
        
        scrollbar.config(command=self.log_text.yview)
        
        self.log_text.tag_configure("info", foreground="#2c3e50")
        self.log_text.tag_configure("success", foreground="#27ae60")
        self.log_text.tag_configure("error", foreground="#e74c3c")
        self.log_text.tag_configure("warning", foreground="#f39c12")
        self.log_text.tag_configure("bold", font=("Consolas", 9, "bold"))
        
        frame_log_buttons = ttk.Frame(frame_log)
        frame_log_buttons.pack(pady=5)
        
        ttk.Button(frame_log_buttons, text="🗑️ Limpiar", command=self._clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_log_buttons, text="💾 Guardar", command=self._save_log).pack(side=tk.LEFT, padx=5)
        
        # Mensaje inicial
        self._log_message("📋 Listo para desorganizar...", "info")
    
    def _select_folder(self, tipo):
        """Seleccionar carpeta usando el explorador"""
        folder = filedialog.askdirectory()
        if folder:
            if tipo == "source":
                self.source_dir.set(folder)
            else:
                self.dest_dir.set(folder)
            self._log_message(f"📁 Carpeta: {folder}", "info")
    
    def _use_same_folder(self):
        """Usar misma carpeta origen como destino"""
        source = self.source_dir.get()
        if source:
            self.dest_dir.set(source)
            self._log_message(f"↹ Destino = Origen: {source}", "info")
        else:
            messagebox.showwarning("Advertencia", "Primero selecciona una carpeta origen")
    
    def _scroll_to_end(self):
        """Forzar scroll al final del log"""
        try:
            self.log_text.see(tk.END)
            self.log_text.update_idletasks()
        except:
            pass
    
    def _log_message(self, message, tag="info"):
        """Añadir mensaje al log con scroll automático al final"""
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self._scroll_to_end()

    def _clear_all_desorganize(self):
        """Limpiar todos los campos y el log en la pestaña Desorganizar"""
        # Limpiar campos de texto
        self.source_dir.set("")
        self.dest_dir.set("")
        
        # Limpiar el log
        self._clear_log()
        
        # Resetear barra de progreso
        self.progress_bar.config(value=0)
        self.label_progress.config(text="Esperando...")
        
        # Resetear botones
        self.btn_desorganize.config(state="normal")
        self.btn_scan.config(state="normal")
        
        # Mensaje informativo
        self._log_message("🧹 Datos limpiados correctamente")
    
    def _clear_log(self):
        """Limpiar el log"""
        self.log_text.delete(1.0, tk.END)
        self._log_message("📋 Log limpiado", "info")
    
    def _save_log(self):
        """Guardar log en archivo"""
        try:
            content = self.log_text.get(1.0, tk.END)
            if not content.strip():
                messagebox.showinfo("Info", "El registro está vacío")
                return
            
            log_file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Archivos de texto", "*.txt")]
            )
            
            if log_file:
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Éxito", f"✅ Registro guardado en:\n{log_file}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el log:\n{str(e)}")
    
    # ============================================
    # ESCANEAR - MUESTRA EL RESULTADO EN EL LOG
    # ============================================
    def _scan_folder(self):
        """Escanear la carpeta y mostrar el resultado en el log"""
        folder = self.source_dir.get()
        if not folder or not Path(folder).exists():
            messagebox.showerror("Error", "❌ Selecciona una carpeta válida")
            return
        
        self._log_message("=" * 60, "info")
        self._log_message("🔍 INICIANDO ESCANEO", "bold")
        self._log_message(f"📁 Carpeta: {folder}", "info")
        self._log_message("", "info")
        
        self.btn_scan.config(state="disabled")
        
        def scan():
            try:
                folder_path = Path(folder)
                total_files = 0
                total_size = 0
                file_list = []
                
                for root, dirs, files in os.walk(folder_path):
                    if not self.include_subfolders.get() and root != str(folder_path):
                        continue
                    
                    for file in files:
                        file_path = Path(root) / file
                        
                        # Aplicar filtro de solo media
                        if self.only_media.get():
                            if file_path.suffix.lower() not in self.media_extensions:
                                continue
                        
                        try:
                            size = file_path.stat().st_size
                            total_files += 1
                            total_size += size
                            file_list.append({
                                "name": file,
                                "path": file_path,
                                "size": size
                            })
                        except:
                            pass
                
                # Mostrar resultados en el log
                self.parent.after(0, lambda: self._show_scan_results(file_list, total_files, total_size, folder_path))
                self.parent.after(0, lambda: self.btn_scan.config(state="normal"))
                
            except Exception as e:
                error_msg = str(e)
                self.parent.after(0, lambda: self._log_message(f"❌ Error al escanear: {str(e)}", "error"))
                self.parent.after(0, lambda: self.btn_scan.config(state="normal"))
        
        Thread(target=scan, daemon=True).start()
    
    def _show_scan_results(self, file_list, total_files, total_size, folder_path):
        """Mostrar los resultados del escaneo en el log"""
        
        total_mb = total_size / (1024 * 1024)
        
        self._log_message("📊 RESULTADOS DEL ESCANEO", "bold")
        self._log_message(f"📄 Archivos encontrados: {total_files:,}", "info")
        self._log_message(f"📦 Tamaño total: {total_mb:.2f} MB", "info")
        self._log_message(f"📁 Carpeta: {folder_path}", "info")
        self._log_message("", "info")
        
        # Mostrar los primeros 50 archivos (para no saturar)
        if total_files > 0:
            self._log_message("📋 PRIMEROS ARCHIVOS ENCONTRADOS:", "bold")
            for i, file_info in enumerate(file_list[:50]):
                size_kb = file_info["size"] / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
                self._log_message(f"   {i+1}. {file_info['name']} ({size_str})", "info")
            
            if total_files > 50:
                self._log_message(f"   ... y {total_files - 50} archivos más", "info")
        
        self._log_message("", "info")
        self._log_message("✅ Escaneo completado", "success")
        self._log_message("=" * 60, "info")
        self._log_message("", "info")
        self._log_message("💡 Presiona 'DESORGANIZAR' para procesar todos los archivos", "info")
        
        # Habilitar el botón de desorganizar
        self.btn_desorganize.config(state="normal")
    
    def _preserve_metadata(self, source, destination):
        """Preservar TODOS los metadatos del archivo original"""
        try:
            stat = source.stat()
            atime = stat.st_atime
            mtime = stat.st_mtime
            os.utime(destination, (atime, mtime))
            return True
        except:
            return False
    
    def _copy_file_preserving_dates(self, source, dest_file):
        shutil.copy2(str(source), str(dest_file))
        self._preserve_metadata(source, dest_file)
    
    def _move_file_preserving_dates(self, source, dest_file):
        shutil.copy2(str(source), str(dest_file))
        self._preserve_metadata(source, dest_file)
        try:
            os.remove(str(source))
        except:
            pass
    
    def _start_desorganize(self):
        """Iniciar el proceso de desorganización"""
        source = self.source_dir.get()
        dest = self.dest_dir.get()
        
        if not source or not dest:
            messagebox.showerror("Error", "❌ Selecciona ambas carpetas")
            return
        
        if not Path(source).exists():
            messagebox.showerror("Error", "❌ La carpeta origen no existe")
            return
        
        if not messagebox.askyesno("Confirmar", 
            f"¿Seguro que quieres {'mover' if self.operation.get() == 'move' else 'copiar'} TODOS los archivos a una sola carpeta?\n\n"
            f"📁 Origen: {source}\n"
            f"📁 Destino: {dest}\n"
            f"🔄 {'Mover' if self.operation.get() == 'move' else 'Copiar'}\n"
            f"📂 Subcarpetas: {'Incluir' if self.include_subfolders.get() else 'Solo raíz'}\n"
            f"📷 {'Solo fotos/videos' if self.only_media.get() else 'Todos los archivos'}\n\n"
            f"⚠️ {'Se ELIMINARÁN los originales' if self.operation.get() == 'move' else 'Se DEJARÁN copias'}"):
            return
        
        self._clear_log()
        self.progress_bar.config(value=0)
        self.label_progress.config(text="⏳ Preparando...")
        self.btn_desorganize.config(state="disabled")
        self.btn_scan.config(state="disabled")
        
        self._log_message("=" * 60, "info")
        self._log_message("🔄 INICIANDO DESORGANIZACIÓN", "bold")
        self._log_message(f"📁 Origen: {source}", "info")
        self._log_message(f"📁 Destino: {dest}", "info")
        self._log_message(f"🔄 {'Mover' if self.operation.get() == 'move' else 'Copiar'}", "info")
        self._log_message("=" * 60, "info")
        
        def run():
            try:
                self._desorganize_files(source, dest)
            except Exception as e:
                error_msg = str(e)
                self.parent.after(0, lambda: messagebox.showerror("Error", f"Error inesperado:\n{str(e)}"))
            finally:
                self.parent.after(0, lambda: self.btn_desorganize.config(state="normal"))
                self.parent.after(0, lambda: self.btn_scan.config(state="normal"))
                self.parent.after(0, lambda: self.label_progress.config(text="✅ Proceso completado"))
                self.parent.after(0, lambda: self.progress_bar.config(value=100))
                self.parent.after(0, self._scroll_to_end)
        
        Thread(target=run, daemon=True).start()
    
    def _desorganize_files(self, source, dest):
        """Recolectar todos los archivos en una sola carpeta"""
        source = Path(source)
        dest = Path(dest)
        dest.mkdir(parents=True, exist_ok=True)
        
        files = []
        
        if self.include_subfolders.get():
            for root, dirs, files_in_dir in os.walk(source):
                for file in files_in_dir:
                    file_path = Path(root) / file
                    if self.only_media.get():
                        if file_path.suffix.lower() in self.media_extensions:
                            files.append(file_path)
                    else:
                        files.append(file_path)
        else:
            for file in source.iterdir():
                if file.is_file():
                    if self.only_media.get():
                        if file.suffix.lower() in self.media_extensions:
                            files.append(file)
                    else:
                        files.append(file)
        
        total = len(files)
        self._log_message(f"📊 Archivos a procesar: {total}", "info")
        
        if total == 0:
            self._log_message("⚠️ No se encontraron archivos para procesar", "warning")
            return
        
        processed = 0
        moved = 0
        copied = 0
        errors = 0
        
        for file_path in files:
            processed += 1
            
            try:
                if self.keep_structure.get():
                    rel_path = file_path.relative_to(source)
                    new_name = str(rel_path).replace(os.sep, "_")
                else:
                    new_name = file_path.name
                
                dest_file = dest / new_name
                counter = 1
                base_name = dest_file.stem
                ext = dest_file.suffix
                
                while dest_file.exists():
                    new_name = f"{base_name} ({counter}){ext}"
                    dest_file = dest / new_name
                    counter += 1
                
                if self.operation.get() == "move":
                    self._move_file_preserving_dates(file_path, dest_file)
                    moved += 1
                    self._log_message(f"✅ {file_path.name}", "success")
                else:
                    self._copy_file_preserving_dates(file_path, dest_file)
                    copied += 1
                    self._log_message(f"📄 {file_path.name}", "info")
                
                progress = (processed / total) * 100
                self.parent.after(0, lambda p=progress, n=file_path.name: self._update_progress(p, n))
                
            except Exception as e:
                errors += 1
                self._log_message(f"❌ {file_path.name}: {str(e)}", "error")
        
        if self.delete_empty.get() and self.operation.get() == "move":
            self._log_message("🗑️ Eliminando carpetas vacías...", "info")
            self._remove_empty_dirs(source)
        
        self._log_message("\n" + "=" * 60, "info")
        self._log_message("✅ DESORGANIZACIÓN COMPLETADA", "bold")
        self._log_message(f"📊 Procesados: {processed}", "info")
        self._log_message(f"📁 Movidos: {moved}", "info")
        self._log_message(f"📄 Copiados: {copied}", "info")
        self._log_message(f"❌ Errores: {errors}", "error" if errors > 0 else "info")
        self._log_message("=" * 60, "info")
        
        self.parent.after(0, self._scroll_to_end)
        
        msg = f"✅ Completado!\n\nProcesados: {processed}\nMovidos: {moved}\nCopiados: {copied}\nErrores: {errors}"
        self.parent.after(0, lambda: messagebox.showinfo("✅ Completado", msg))
    
    def _update_progress(self, progress, name):
        self.progress_bar.config(value=progress)
        self.label_progress.config(text=f"📄 {name}")
        self._scroll_to_end()
    
    def _remove_empty_dirs(self, directory):
        directory = Path(directory)
        for item in directory.iterdir():
            if item.is_dir():
                self._remove_empty_dirs(item)
        try:
            if directory.exists() and not any(directory.iterdir()):
                directory.rmdir()
                self._log_message(f"🗑️ Carpeta eliminada: {directory}", "info")
        except:
            pass
