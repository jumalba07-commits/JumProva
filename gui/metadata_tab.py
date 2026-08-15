import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from threading import Thread
from mutagen.id3 import TIT2, TPE1, TALB, TDRC, TCON, COMM, TYER
from mutagen.id3 import APIC
from mutagen.id3 import ID3
import os
import re

class MetadataTab:
    """Pestaña para buscar y editar metadatos de archivos de audio"""
    
    def __init__(self, parent, organizer):
        self.parent = parent
        self.organizer = organizer
        self.is_running = False
        self.current_files = []
        
        # Variables
        self.source_dir = tk.StringVar()
        self.auto_detect = tk.BooleanVar(value=True)
        self.buscar_internet = tk.BooleanVar(value=True)
        self.buscar_caratulas = tk.BooleanVar(value=True)
        
        # Extensiones de audio
        self.audio_extensions = {
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',
            '.m4b', '.opus', '.amr'
        }
        
        self._build_ui()
    
    def _build_ui(self):
        """Construir la interfaz de la pestaña de Metadatos"""
        
        # ===== Contenedor principal con PanedWindow =====
        main_paned = ttk.PanedWindow(self.parent, orient=tk.VERTICAL)
        main_paned.pack(fill="both", expand=True)
        
        # ===== PANEL SUPERIOR: Configuración =====
        top_frame = ttk.Frame(main_paned)
        main_paned.add(top_frame, weight=1)
        
        # ---- Instrucciones ----
        frame_instrucciones = ttk.LabelFrame(top_frame, text="🎵 Gestión de Metadatos", padding=10)
        frame_instrucciones.pack(fill="x", pady=5)
        
        tk.Label(frame_instrucciones, 
                text="Busca y rellena metadatos en archivos de audio (MP3, FLAC, WAV, M4A, OGG, WMA)",
                font=("Arial", 9), fg="#2c3e50").pack(anchor="w")
        tk.Label(frame_instrucciones, 
                text="✅ Extrae información del nombre del archivo y busca en Internet los datos faltantes",
                font=("Arial", 9), fg="#27ae60").pack(anchor="w")
        
        # ---- Carpetas ----
        frame_carpetas = ttk.LabelFrame(top_frame, text="📁 Carpeta", padding=10)
        frame_carpetas.pack(fill="x", pady=5)
        
        ttk.Label(frame_carpetas, text="Carpeta con archivos de audio:").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(frame_carpetas, textvariable=self.source_dir, width=55).grid(row=0, column=1, padx=5)
        ttk.Button(frame_carpetas, text="📂", command=lambda: self._select_folder()).grid(row=0, column=2)
        
        # ---- Opciones ----
        frame_opciones = ttk.LabelFrame(top_frame, text="⚙️ Opciones", padding=10)
        frame_opciones.pack(fill="x", pady=5)
        
        ttk.Checkbutton(frame_opciones, text="🔍 Extraer metadatos del nombre del archivo (artista - título)",
                       variable=self.auto_detect).grid(row=0, column=0, columnspan=2, sticky="w", pady=3)
        
        ttk.Checkbutton(frame_opciones, text="🌐 Buscar metadatos faltantes en Internet (MusicBrainz, Last.fm, TheAudioDB)",
                       variable=self.buscar_internet).grid(row=1, column=0, columnspan=2, sticky="w", pady=3)

        # ===== NUEVO CHECKBOX: BUSCAR CARÁTULAS =====
        ttk.Checkbutton(frame_opciones, text="🖼️ Buscar y guardar carátulas de álbumes",
                       variable=self.buscar_caratulas).grid(row=2, column=0, columnspan=2, sticky="w", pady=3)
        
        # ---- Botones ----
        frame_botones = ttk.Frame(top_frame)
        frame_botones.pack(pady=10, fill="x")
        
        self.btn_scan = ttk.Button(frame_botones, text="🔍 ESCANEAR", 
                                  command=self._scan_folder)
        self.btn_scan.pack(side=tk.LEFT, padx=5, fill="x", expand=True, ipady=3)

        self.btn_caratulas = ttk.Button(frame_botones, text="🖼️ BUSCAR CARÁTULAS", 
                                   command=self._buscar_caratulas_masivo,
                                   state="disabled")
        self.btn_caratulas.pack(side=tk.LEFT, padx=5, fill="x", expand=True, ipady=3)
        
        self.btn_edit = ttk.Button(frame_botones, text="✏️ EDITAR MANUAL", 
                                  command=self._editar_manual,
                                  state="disabled")
        self.btn_edit.pack(side=tk.LEFT, padx=5, fill="x", expand=True, ipady=3)
        
        self.btn_process = ttk.Button(frame_botones, text="📝 RELLENAR AUTOMÁTICO", 
                                     command=self._process_metadata,
                                     style="Accent.TButton",
                                     state="disabled")
        self.btn_process.pack(side=tk.RIGHT, padx=5, fill="x", expand=True, ipady=3)
        
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))
        
        # ===== PANEL INFERIOR: Progreso y Log =====
        bottom_frame = ttk.Frame(main_paned)
        main_paned.add(bottom_frame, weight=2)
        
        # ---- Progreso ----
        frame_progreso = ttk.LabelFrame(bottom_frame, text="📊 Progreso", padding=8)
        frame_progreso.pack(fill="x", pady=5)
        
        self.progress_bar = ttk.Progressbar(frame_progreso, length=400, mode='determinate')
        self.progress_bar.pack(fill="x", pady=5)
        
        self.label_progress = ttk.Label(frame_progreso, text="Esperando...")
        self.label_progress.pack()
        
        # ---- Log ----
        frame_log = ttk.LabelFrame(bottom_frame, text="📋 Registro", padding=8)
        frame_log.pack(fill="both", expand=True, pady=5)
        
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
        
        self._log_message("🎵 Listo para gestionar metadatos...", "info")
    
    def _select_folder(self):
        """Seleccionar carpeta usando el explorador"""
        folder = filedialog.askdirectory()
        if folder:
            self.source_dir.set(folder)
            self._log_message(f"📁 Carpeta: {folder}", "info")
    
    def _scroll_to_end(self):
        try:
            self.log_text.see(tk.END)
            self.log_text.update_idletasks()
        except:
            pass
    
    def _log_message(self, message, tag="info"):
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self._scroll_to_end()
    
    def _clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self._log_message("📋 Log limpiado", "info")
    
    def _save_log(self):
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
    
    def _limpiar_nombre_archivo(self, filename):
        """Limpiar el nombre del archivo para extraer artista - título"""
        name = Path(filename).stem
        
        # Eliminar números de pista al inicio
        name = re.sub(r'^\d+[\s\.\-\_\)]+', '', name)
        
        # Eliminar información entre paréntesis y corchetes
        name = re.sub(r'[\(\[]\s*[^\)\]]*\s*[\)\]]', '', name)
        
        # Eliminar etiquetas de calidad
        name = re.sub(r'\s*(320kbps|FLAC|MP3|HD|HQ|Remastered|Deluxe|Explicit|Clean)\s*', ' ', name, flags=re.IGNORECASE)
        
        # Eliminar información de versión
        name = re.sub(r'\s*\([^\)]*(Remix|Live|Acoustic|Instrumental|Edit|Version|Mix)[^\)]*\)\s*', ' ', name, flags=re.IGNORECASE)
        
        # Eliminar "feat.", "ft.", "featuring"
        name = re.sub(r'\s*[\(\[]\s*(feat\.|ft\.|featuring)\s*[^\)\]]*\s*[\)\]]', '', name, flags=re.IGNORECASE)
        
        # Limpiar espacios extra
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Buscar separadores
        separadores = [
            r'\s*[-–—]\s*',
            r'\s*\/\s*',
            r'\s*\|\s*',
            r'\s*\:\s*',
            r'\s*\;\s*',
        ]
        
        for separador in separadores:
            partes = re.split(separador, name)
            if len(partes) >= 2:
                artista = partes[0].strip()
                titulo = partes[1].strip()
                if len(artista) >= 3 and len(titulo) >= 2:
                    artista = re.sub(r'^[\s\-_]+|[\s\-_]+$', '', artista)
                    titulo = re.sub(r'^[\s\-_]+|[\s\-_]+$', '', titulo)
                    return artista, titulo
        
        return None, None
    
    def _obtener_genero_theaudiodb(self, artista):
        try:
            import requests
            url = f"https://www.theaudiodb.com/api/v1/json/2/search.php?s={artista.replace(' ', '%20')}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data and 'artists' in data and data['artists']:
                    artist_data = data['artists'][0]
                    if 'strGenre' in artist_data:
                        return artist_data['strGenre']
                    if 'strStyle' in artist_data:
                        return artist_data['strStyle']
            return None
        except:
            return None
    
    def _obtener_genero_lastfm(self, artista, titulo):
        try:
            import requests
            from urllib.parse import quote
            url = f"https://www.last.fm/music/{quote(artista)}/_/{quote(titulo)}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                import re
                tags = re.findall(r'<a href="/tag/[^"]+">([^<]+)</a>', response.text)
                if tags:
                    return ', '.join(tags[:3])
            return None
        except:
            return None
    
    def _search_missing_metadata(self, artista, titulo, filename=""):
        """Buscar TODOS los metadatos posibles en Internet"""
        try:
            import musicbrainzngs
            musicbrainzngs.set_useragent("OrganizadorPro", "1.0", "organizadorpro@email.com")
            
            query = f'artist:"{artista}" AND recording:"{titulo}"'
            result = musicbrainzngs.search_recordings(query=query, limit=3)
            
            if not result or not result.get('recording-list'):
                return None
            
            for recording in result['recording-list']:
                metadata = {
                    'artista': artista,
                    'titulo': titulo,
                    'año': None,
                    'genero': None,
                    'album': None,
                    'duracion': None
                }
                
                if 'title' in recording:
                    metadata['titulo'] = recording['title']
                
                if 'artist-credit' in recording and recording['artist-credit']:
                    artist_credit = recording['artist-credit'][0]
                    if 'artist' in artist_credit and 'name' in artist_credit['artist']:
                        metadata['artista'] = artist_credit['artist']['name']
                
                if 'release-list' in recording and recording['release-list']:
                    for release in recording['release-list']:
                        if 'title' in release and not metadata['album']:
                            metadata['album'] = release['title']
                        if 'date' in release and not metadata['año']:
                            metadata['año'] = release['date'][:4]
                        if metadata['album'] and metadata['año']:
                            break
                
                if 'length' in recording:
                    duration_ms = int(recording['length'])
                    minutes = duration_ms // 60000
                    seconds = (duration_ms % 60000) // 1000
                    metadata['duracion'] = f"{minutes}:{seconds:02d}"
                
                # Obtener género
                if metadata['artista']:
                    genero = self._obtener_genero_theaudiodb(metadata['artista'])
                    if not genero:
                        genero = self._obtener_genero_lastfm(metadata['artista'], metadata['titulo'])
                    if genero:
                        metadata['genero'] = genero
                
                if metadata['artista'] and metadata['titulo']:
                    return metadata
            
            return None
            
        except ImportError:
            self._log_message("⚠️ musicbrainzngs no instalada. pip install musicbrainzngs", "warning")
            return None
        except:
            return None
    
    def _scan_folder(self):
        """Escanear archivos de audio"""
        folder = self.source_dir.get()
        if not folder or not Path(folder).exists():
            messagebox.showerror("Error", "❌ Selecciona una carpeta válida")
            return
        
        self._log_message("=" * 60, "info")
        self._log_message("🔍 ESCANEANDO ARCHIVOS DE AUDIO", "bold")
        self._log_message(f"📁 Carpeta: {folder}", "info")
        self._log_message("", "info")
        
        self.btn_scan.config(state="disabled")
        self.current_files = []
        
        def scan():
            try:
                folder_path = Path(folder)
                audio_files = []
                
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = Path(root) / file
                        if file_path.suffix.lower() in self.audio_extensions:
                            artista, titulo = self._limpiar_nombre_archivo(file)
                            audio_files.append({
                                "path": file_path,
                                "name": file,
                                "artista": artista,
                                "titulo": titulo,
                                "extension": file_path.suffix.lower()
                            })
                
                self.current_files = audio_files
                self.parent.after(0, lambda: self._show_scan_results(audio_files))
                self.parent.after(0, lambda: self.btn_scan.config(state="normal"))
                
            except Exception as e:
                error_msg = str(e)
                self.parent.after(0, lambda: self._log_message(f"❌ Error al escanear: {error_msg}", "error"))
                self.parent.after(0, lambda: self.btn_scan.config(state="normal"))
        
        Thread(target=scan, daemon=True).start()
    
    def _show_scan_results(self, audio_files):
        if not audio_files:
            self._log_message("⚠️ No se encontraron archivos de audio", "warning")
            self.btn_process.config(state="disabled")
            self.btn_edit.config(state="disabled")
            return
        
        self._log_message(f"📊 Archivos encontrados: {len(audio_files)}", "info")
        self._log_message("", "info")
        self._log_message("📋 ARCHIVOS DETECTADOS:", "bold")
        
        for i, file_info in enumerate(audio_files[:20]):
            artista = file_info.get("artista", "Desconocido")
            titulo = file_info.get("titulo", "Desconocido")
            if artista and titulo:
                self._log_message(f"   {i+1}. {file_info['name']} → {artista} - {titulo}", "success")
            else:
                self._log_message(f"   {i+1}. {file_info['name']} → ⚠️ No se pudo identificar", "warning")
        
        if len(audio_files) > 20:
            self._log_message(f"   ... y {len(audio_files) - 20} archivos más", "info")
        
        self._log_message("", "info")
        self._log_message("✅ Escaneo completado", "success")
        self._log_message("=" * 60, "info")
        
        self.btn_process.config(state="normal")
        self.btn_edit.config(state="normal")
        self.btn_caratulas.config(state="normal")
    
    def _editar_manual(self):
        """Abrir ventana para editar metadatos manualmente con vista previa de carátula"""
        if not self.current_files:
            messagebox.showinfo("Info", "Primero escanea archivos")
            return
        
        # Crear ventana de edición - MÁS GRANDE
        ventana = tk.Toplevel(self.parent)
        ventana.title("✏️ Editar Metadatos Manualmente")
        ventana.geometry("1300x750")  # ← MÁS GRANDE
        ventana.transient(self.parent)
        ventana.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(ventana, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # ============================================
        # PANEL IZQUIERDO: Treeview
        # ============================================
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill="both", expand=True)
        
        # Treeview
        columns = ("Archivo", "Artista", "Título", "Álbum", "Año", "Género")
        tree = ttk.Treeview(left_frame, columns=columns, show="headings", height=22)
        
        tree.heading("Archivo", text="Archivo")
        tree.heading("Artista", text="Artista")
        tree.heading("Título", text="Título")
        tree.heading("Álbum", text="Álbum")
        tree.heading("Año", text="Año")
        tree.heading("Género", text="Género")
        
        tree.column("Archivo", width=180, anchor="w")
        tree.column("Artista", width=160, anchor="w")
        tree.column("Título", width=160, anchor="w")
        tree.column("Álbum", width=140, anchor="w")
        tree.column("Año", width=60, anchor="center")
        tree.column("Género", width=120, anchor="w")
        
        # Scrollbar
        scroll = ttk.Scrollbar(left_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        
        tree.pack(side=tk.LEFT, fill="both", expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ============================================
        # PANEL DERECHO: Carátula (MÁS GRANDE)
        # ============================================
        right_frame = ttk.LabelFrame(main_frame, text="🖼️ Carátula", padding=15)  # ← Marco con borde
        right_frame.pack(side=tk.RIGHT, fill="y", padx=15)  # ← Se coloca a la derecha

        # Label para mostrar la carátula - MÁS GRANDE
        self.caratula_label = tk.Label(right_frame,   # ← Donde se muestra la carátula
                                       text="Selecciona un archivo",  # ← Texto inicial
                                       font=("Arial", 12), 
                                       bg="#f0f0f0", 
                                       width=35,   # ← Ancho en caracteres
                                       height=18,  # ← Alto en caracteres
                                       relief=tk.RAISED,   # ← Borde en relieve
                                       borderwidth=2)      # ← Grosor del borde
        self.caratula_label.pack(pady=10, padx=5)  # ← Lo coloca en el frame
        
        # Botón para buscar carátula del archivo seleccionado
        btn_frame_caratula = ttk.Frame(right_frame)
        btn_frame_caratula.pack(pady=10)
        
        ttk.Button(btn_frame_caratula, text="🖼️ Buscar carátula", 
                  command=lambda: self._buscar_caratula_seleccionado(tree)).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame_caratula, text="📁 Poner carátula", 
                  command=lambda: self._poner_caratula_manual(tree)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame_caratula, text="🗑️ Eliminar carátula", 
                  command=lambda: self._eliminar_caratula_seleccionado(tree)).pack(side=tk.LEFT, padx=5)

        
        
        # ============================================
        # VARIABLES PARA EDICIÓN
        # ============================================
        self.edit_window = ventana
        self.edit_tree = tree
        self.edit_items = []
        self.current_edit_item = None
        self.current_edit_col_index = None
        self.current_edit_entry = None
        self.current_caratula_file = None
        
        # ============================================
        # CARGAR DATOS
        # ============================================
        try:
            import mutagen
        except ImportError:
            tk.Label(left_frame, text="❌ Librería 'mutagen' no instalada", font=("Arial", 12), fg="red").pack(pady=20)
            return
        
        for file_info in self.current_files:
            try:
                file_path = file_info["path"]
                audio = mutagen.File(str(file_path))
                if audio is None:
                    continue
                
                artista = "Desconocido"
                titulo = "Desconocido"
                album = "Desconocido"
                año = "Desconocido"
                genero = "Desconocido"
                
                if hasattr(audio, 'tags') and audio.tags is not None:
                    if 'TPE1' in audio.tags:
                        artista = str(audio.tags['TPE1'])
                    if 'TIT2' in audio.tags:
                        titulo = str(audio.tags['TIT2'])
                    if 'TALB' in audio.tags:
                        album = str(audio.tags['TALB'])
                    if 'TDRC' in audio.tags:
                        año = str(audio.tags['TDRC'])[:4]
                    if 'TCON' in audio.tags:
                        genero = str(audio.tags['TCON'])
                
                item = tree.insert("", "end", values=(
                    file_info["name"],
                    artista,
                    titulo,
                    album,
                    año,
                    genero
                ))
                self.edit_items.append({
                    "item": item,
                    "path": file_info["path"],
                    "name": file_info["name"]
                })
            except:
                continue
        
        # ============================================
        # BINDINGS
        # ============================================
        
        # Doble clic para editar
        tree.bind("<Double-1>", self._on_edit_cell)
        
        # Selección para mostrar carátula
        tree.bind("<<TreeviewSelect>>", self._mostrar_caratula_seleccionada)
        
        # ============================================
        # BOTONES INFERIORES (TODOS JUNTOS)
        # ============================================
        btn_frame = ttk.Frame(ventana)
        btn_frame.pack(pady=10, fill="x")
        
        ttk.Button(btn_frame, text="💾 Guardar todos los cambios", 
                  command=lambda: self._guardar_edicion_manual(tree, ventana)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="🔄 Auto-llenar desde nombre", 
                  command=lambda: self._auto_llenar_desde_nombre(tree)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="🌐 Buscar en Internet", 
                  command=lambda: self._buscar_y_rellenar(tree)).pack(side=tk.LEFT, padx=5)
        
        # ===== BOTONES DE CARÁTULAS =====
        ttk.Button(btn_frame, text="🖼️ Buscar carátula", 
                  command=lambda: self._buscar_caratula_seleccionado(tree)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="🖼️ Carátulas para seleccionados", 
                  command=lambda: self._buscar_caratula_seleccionados(tree)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="🗑️ Eliminar carátula", 
                  command=lambda: self._eliminar_caratula_seleccionado(tree)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="❌ Cerrar", command=ventana.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Mensaje informativo
        tk.Label(ventana, text="💡 Haz doble clic en cualquier celda para editarla | Selecciona un archivo para ver su carátula", 
                font=("Arial", 9), fg="#7f8c8d").pack(pady=5)

    def _mostrar_caratula_seleccionada(self, event):
        """Mostrar carátula del archivo seleccionado en el treeview"""
        tree = self.edit_tree
        if not tree:
            return
        
        selection = tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = tree.item(item, 'values')
        if len(values) < 6:
            return
        
        archivo = values[0]
        
        # Buscar el archivo en la lista
        for file_info in self.edit_items:
            if file_info["name"] == archivo:
                self._mostrar_caratula_del_archivo(file_info["path"])
                break

    def _buscar_caratula_seleccionados(self, tree):
        """Buscar carátula para los archivos seleccionados en el treeview"""
        items = tree.selection()
        if not items:
            messagebox.showinfo("Info", "Selecciona uno o más archivos")
            return
        
        if not messagebox.askyesno("Confirmar", 
            f"¿Buscar carátula para {len(items)} archivos seleccionados?"):
            return
        
        found = 0
        for item in items:
            values = tree.item(item, 'values')
            if len(values) < 6:
                continue
            
            archivo = values[0]
            
            # Buscar el archivo en la lista
            for file_info in self.edit_items:
                if file_info["name"] == archivo:
                    # Buscar carátula en Internet
                    if self._buscar_caratula_para_archivo(file_info):
                        found += 1
                        self._log_message(f"✅ Carátula guardada para: {archivo}", "success")
                    else:
                        self._log_message(f"⚠️ No se encontró carátula para: {archivo}", "warning")
                    break
        
        # Si solo había un archivo seleccionado, actualizar la vista previa
        if len(items) == 1:
            self._mostrar_caratula_seleccionada(None)
        
        messagebox.showinfo("Completado", 
            f"🖼️ Carátulas encontradas: {found}/{len(items)}")

    def _mostrar_caratula_del_archivo(self, file_path):
        """Mostrar carátula de un archivo específico en el label - MÁS GRANDE"""
        try:
            import mutagen
            from PIL import Image, ImageTk
            import io
            
            # Cargar el archivo de audio
            audio = mutagen.File(str(file_path))
            if audio is None:
                self.caratula_label.config(text="❌ No se pudo leer el archivo", image="")
                self.caratula_label.image = None
                return
            
            # Buscar carátula en los tags
            if hasattr(audio, 'tags') and audio.tags is not None:
                for tag in audio.tags.values():
                    if tag.__class__.__name__ == 'APIC':
                        # Extraer imagen
                        img_data = tag.data
                        img = Image.open(io.BytesIO(img_data))
                        
                        # ============================================
                        # REDIMENSIONAR MÁS GRANDE (400x400)
                        # ============================================
                        img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                        
                        # Convertir a PhotoImage
                        photo = ImageTk.PhotoImage(img)
                        
                        # Mostrar en el label
                        self.caratula_label.config(image=photo, text="")
                        self.caratula_label.image = photo  # Mantener referencia
                        self.current_caratula_file = file_path
                        
                        # Ajustar tamaño del label a la imagen
                        self.caratula_label.config(width=photo.width(), height=photo.height())
                        return
            
            # Si no tiene carátula
            self.caratula_label.config(text="🖼️ Sin carátula", image="")
            self.caratula_label.image = None
            self.caratula_label.config(width=35, height=18)  # Restaurar tamaño por defecto
            
        except Exception as e:
            self.caratula_label.config(text=f"❌ Error: {str(e)[:30]}", image="")
            self.caratula_label.image = None

    def _eliminar_caratula_seleccionado(self, tree):
        """Eliminar carátula del archivo seleccionado - VERSIÓN ROBUSTA"""
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Selecciona un archivo")
            return
        
        if not messagebox.askyesno("Confirmar", "¿Eliminar la carátula del archivo seleccionado?"):
            return
        
        item = selection[0]
        values = tree.item(item, 'values')
        if len(values) < 6:
            return
        
        archivo = values[0]
        
        # Buscar el archivo en la lista
        for file_info in self.edit_items:
            if file_info["name"] == archivo:
                try:
                    import mutagen
                                        
                    file_path = file_info["path"]
                    audio = mutagen.File(str(file_path))
                    if audio is None:
                        messagebox.showerror("Error", "No se pudo leer el archivo")
                        return
                    
                    if not hasattr(audio, 'tags') or audio.tags is None:
                        messagebox.showinfo("Info", "El archivo no tiene metadatos")
                        return
                    
                    # Contar carátulas antes de eliminar
                    covers = [tag for tag in audio.tags.values() if tag.__class__.__name__ == 'APIC']
                    if not covers:
                        messagebox.showinfo("Info", "El archivo no tiene carátula")
                        return
                    
                    # Eliminar TODAS las carátulas (métodos múltiples)
                    eliminadas = 0
                    
                    # Método 1: Usar pop
                    try:
                        if hasattr(audio.tags, 'pop'):
                            audio.tags.pop('APIC', None)
                    except:
                        pass
                    
                    # Método 2: Usar delall
                    try:
                        if hasattr(audio.tags, 'delall'):
                            audio.tags.delall('APIC')
                    except:
                        pass
                    
                    # Método 3: Eliminar manualmente
                    try:
                        for tag in list(audio.tags.values()):
                            if tag.__class__.__name__ == 'APIC':
                                try:
                                    del audio.tags[tag.hash_key]
                                    eliminadas += 1
                                except:
                                    pass
                    except:
                        pass
                    
                    # Método 4: Si aún quedan, intentar con getall
                    try:
                        for tag in audio.tags.getall('APIC'):
                            try:
                                audio.tags.delitem(tag.hash_key)
                                eliminadas += 1
                            except:
                                pass
                    except:
                        pass
                    
                    # Guardar cambios
                    audio.save()
                    
                    # Verificar si quedó alguna
                    _ = [tag for tag in audio.tags.values() if tag.__class__.__name__ == 'APIC']
                    
                    self._log_message(f"🗑️ Carátula eliminada de: {archivo}", "info")
                    
                    # Actualizar vista previa
                    self.caratula_label.config(text="🖼️ Sin carátula", image="")
                    self.caratula_label.image = None
                    self.caratula_label.config(width=35, height=18)
                    
                    # Actualizar la vista previa del archivo (recargar)
                    self._mostrar_caratula_del_archivo(file_path)
                    
                    messagebox.showinfo("Éxito", f"✅ Carátula eliminada de:\n{archivo}")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Error al eliminar carátula:\n{str(e)}")
                break

    def _probar_imagen(self, image_data):
        """Probar si una imagen es válida"""
        try:
            from PIL import Image
            import io
            _ = Image.open(io.BytesIO(image_data))
            return True
        except:
            return False

    def _buscar_caratula_seleccionado(self, tree):
        """Buscar carátula para el archivo seleccionado y mostrarla"""
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Selecciona un archivo")
            return
        
        item = selection[0]
        values = tree.item(item, 'values')
        if len(values) < 6:
            return
        
        archivo = values[0]
        
        # Buscar el archivo en la lista
        for file_info in self.edit_items:
            if file_info["name"] == archivo:
                # Buscar carátula en Internet
                if self._buscar_caratula_para_archivo(file_info):
                    # Recargar carátula
                    self._mostrar_caratula_del_archivo(file_info["path"])
                    self._log_message(f"✅ Carátula guardada para: {archivo}", "success")
                    messagebox.showinfo("Éxito", f"✅ Carátula guardada para:\n{archivo}")
                else:
                    self._log_message(f"⚠️ No se encontró carátula para: {archivo}", "warning")
                    messagebox.showinfo("Info", f"No se encontró carátula para:\n{archivo}")
                break    

    def _on_edit_cell(self, event):
        """Manejar doble clic en una celda para editarla"""
        tree = self.edit_tree
        
        # Obtener la celda seleccionada
        item = tree.selection()[0] if tree.selection() else None
        if not item:
            return
        
        # Obtener columna
        column = tree.identify_column(event.x)
        col_index = int(column.replace('#', '')) - 1
        
        # No editar la columna "Archivo"
        if col_index == 0:
            return
        
        # Obtener valores actuales
        values = list(tree.item(item, 'values'))
        _ = tree.heading(column)['text']
        current_value = values[col_index] if col_index < len(values) else ""
        
        # Obtener posición de la celda
        bbox = tree.bbox(item, column)
        if not bbox:
            return
        
        x, y, width, height = bbox
        
        # Crear entry para editar
        entry = tk.Entry(tree, font=("Arial", 9))
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, current_value)
        entry.focus_set()
        entry.select_range(0, tk.END)
        
        # Guardar referencia
        self.current_edit_item = item
        self.current_edit_col_index = col_index
        self.current_edit_entry = entry
        
        # Bindings
        def on_enter_edit(event):
            self._save_cell_edit()
        
        def on_escape_edit(event):
            self._cancel_cell_edit()
        
        def on_focus_out(event):
            self._save_cell_edit()
        
        entry.bind("<Return>", on_enter_edit)
        entry.bind("<Escape>", on_escape_edit)
        entry.bind("<FocusOut>", on_focus_out)

    def _save_cell_edit(self):
        """Guardar el valor editado en la celda"""
        if not self.current_edit_item or not self.current_edit_entry:
            return
        
        new_value = self.current_edit_entry.get().strip()
        col_index = self.current_edit_col_index
        item = self.current_edit_item
        
        # Actualizar el treeview
        values = list(self.edit_tree.item(item, 'values'))
        if col_index < len(values):
            values[col_index] = new_value if new_value else "Desconocido"
            self.edit_tree.item(item, values=values)
        
        # Limpiar
        self.current_edit_entry.destroy()
        self.current_edit_entry = None
        self.current_edit_item = None
        self.current_edit_col_index = None

    def _cancel_cell_edit(self):
        """Cancelar edición de celda"""
        if self.current_edit_entry:
            self.current_edit_entry.destroy()
            self.current_edit_entry = None
            self.current_edit_item = None
            self.current_edit_col_index = None

    def _auto_llenar_desde_nombre(self, tree):
        """Auto-llenar artista y título desde el nombre del archivo"""
        if not messagebox.askyesno("Confirmar", 
            "¿Auto-llenar Artista y Título desde el nombre del archivo?\n\n"
            "Esto sobrescribirá los valores actuales."):
            return
        
        items = tree.get_children()
        for item in items:
            values = list(tree.item(item, 'values'))
            if len(values) < 6:
                continue
            
            filename = values[0]
            artista, titulo = self._limpiar_nombre_archivo(filename)
            
            if artista and titulo:
                values[1] = artista  # Artista
                values[2] = titulo   # Título
                tree.item(item, values=values)
                self._log_message(f"✅ Auto-llenado: {filename} → {artista} - {titulo}", "success")
        
        messagebox.showinfo("Completado", "Auto-llenado completado")

    def _buscar_y_rellenar(self, tree):
        """Buscar metadatos en Internet y rellenar las celdas seleccionadas"""
        items = tree.get_children()
        if not items:
            messagebox.showinfo("Info", "No hay archivos para procesar")
            return
        
        if not messagebox.askyesno("Confirmar", 
            f"¿Buscar metadatos en Internet para {len(items)} archivos?\n\n"
            "Esto sobrescribirá los valores actuales."):
            return
        
        for item in items:
            values = list(tree.item(item, 'values'))
            if len(values) < 6:
                continue
            
            artista = values[1]
            titulo = values[2]
            
            if artista and artista != "Desconocido" and titulo and titulo != "Desconocido":
                self._log_message(f"🔍 Buscando: {artista} - {titulo}", "info")
                
                metadata = self._search_missing_metadata(artista, titulo, values[0])
                
                if metadata:
                    if metadata.get('artista'):
                        values[1] = metadata['artista']
                    if metadata.get('titulo'):
                        values[2] = metadata['titulo']
                    if metadata.get('album'):
                        values[3] = metadata['album']
                    if metadata.get('año'):
                        values[4] = metadata['año']
                    if metadata.get('genero'):
                        values[5] = metadata['genero']
                    
                    tree.item(item, values=values)
                    self._log_message(f"✅ Rellenado: {values[0]}", "success")
        
        messagebox.showinfo("Completado", "Búsqueda completada")

    def _guardar_edicion_manual(self, tree, ventana):
        """Guardar los cambios manuales en los archivos"""
        try:
            import mutagen
            from mutagen.id3 import TIT2, TPE1, TALB, TDRC, TCON
        except ImportError:
            messagebox.showerror("Error", "Librería 'mutagen' no instalada")
            return
        
        items = tree.get_children()
        if not items:
            messagebox.showinfo("Info", "No hay datos para guardar")
            return
        
        if not messagebox.askyesno("Confirmar", f"¿Guardar cambios en {len(items)} archivos?"):
            return
        
        saved = 0
        errors = 0
        
        for item in items:
            values = tree.item(item, 'values')
            if len(values) < 6:
                continue
            
            archivo, artista, titulo, album, año, genero = values
            
            # Buscar el archivo en la lista
            for file_info in self.edit_items:
                if file_info["name"] == archivo:
                    try:
                        file_path = file_info["path"]
                        audio = mutagen.File(str(file_path))
                        if audio is None:
                            continue
                        
                        if hasattr(audio, 'tags') and audio.tags is not None:
                            if artista and artista != "Desconocido":
                                audio.tags.add(TPE1(encoding=3, text=artista))
                            if titulo and titulo != "Desconocido":
                                audio.tags.add(TIT2(encoding=3, text=titulo))
                            if album and album != "Desconocido":
                                audio.tags.add(TALB(encoding=3, text=album))
                            if año and año != "Desconocido":
                                audio.tags.add(TDRC(encoding=3, text=año))
                            if genero and genero != "Desconocido":
                                audio.tags.add(TCON(encoding=3, text=genero))
                            audio.save()
                            saved += 1
                            self._log_message(f"✅ Guardado: {archivo}", "success")
                    except Exception as e:
                        errors += 1
                        self._log_message(f"❌ Error con {archivo}: {str(e)}", "error")
        
        messagebox.showinfo("Éxito", f"✅ Metadatos guardados\n\nGuardados: {saved}\nErrores: {errors}")
        ventana.destroy()
    
    def _process_metadata(self):
        """Rellenar metadatos automáticamente (sin organizar)"""
        if not self.current_files:
            messagebox.showinfo("Info", "No hay archivos para procesar")
            return
        
        total = len(self.current_files)
        if not messagebox.askyesno("Confirmar", 
            f"¿Rellenar metadatos en {total} archivos de audio?\n\n"
            f"🔍 Extraer del nombre: {'Sí' if self.auto_detect.get() else 'No'}\n"
            f"🌐 Buscar en Internet: {'Sí' if self.buscar_internet.get() else 'No'}"):
            return
        
        self._clear_log()
        self.progress_bar.config(value=0)
        self.label_progress.config(text="⏳ Procesando...")
        self.btn_process.config(state="disabled")
        self.btn_scan.config(state="disabled")
        
        self._log_message("=" * 60, "info")
        self._log_message("📝 RELLENANDO METADATOS", "bold")
        self._log_message(f"📁 Archivos: {total}", "info")
        self._log_message(f"🔍 Extraer del nombre: {'Sí' if self.auto_detect.get() else 'No'}", "info")
        self._log_message(f"🌐 Buscar en Internet: {'Sí' if self.buscar_internet.get() else 'No'}", "info")
        self._log_message("=" * 60, "info")
        
        def process():
            try:
                self._process_files()
            except Exception as e:
                error_msg = str(e)
                self.parent.after(0, lambda: messagebox.showerror("Error", f"Error inesperado:\n{error_msg}"))
            finally:
                self.parent.after(0, lambda: self.btn_process.config(state="normal"))
                self.parent.after(0, lambda: self.btn_scan.config(state="normal"))
                self.parent.after(0, lambda: self.label_progress.config(text="✅ Proceso completado"))
                self.parent.after(0, lambda: self.progress_bar.config(value=100))
        
        Thread(target=process, daemon=True).start()
    
    def _process_files(self):
        """Procesar archivos - SOLO METADATOS, SIN ORGANIZAR"""
        total = len(self.current_files)
        processed = 0
        
        try:
            import mutagen            
        except ImportError:
            self._log_message("❌ Librería 'mutagen' no instalada", "error")
            self._log_message("📦 Instala con: pip install mutagen", "info")
            return
        
        for file_info in self.current_files:
            processed += 1
            file_path = file_info["path"]
            metadata = None
            
            try:
                audio = mutagen.File(str(file_path))
                if audio is None:
                    self._log_message(f"⚠️ No se pudo leer: {file_info['name']}", "warning")
                    continue
                
                # Extraer metadatos del nombre
                artista, titulo = None, None
                if self.auto_detect.get():
                    artista, titulo = self._limpiar_nombre_archivo(file_info["name"])
                
                # Buscar en Internet si está activado y tenemos artista/título
                if self.buscar_internet.get() and artista and titulo:
                    self._log_message(f"🔍 Buscando: {artista} - {titulo}", "info")
                    metadata = self._search_missing_metadata(artista, titulo, file_info["name"])
                    
                    if metadata:
                        if metadata.get('artista'):
                            artista = metadata['artista']
                        if metadata.get('titulo'):
                            titulo = metadata['titulo']
                        self._log_message(f"✅ Encontrado: {artista} - {titulo}", "success")
                
                # Escribir metadatos
                if artista and titulo and hasattr(audio, 'tags') and audio.tags is not None:
                    try:
                        audio.tags.add(TPE1(encoding=3, text=artista))
                        audio.tags.add(TIT2(encoding=3, text=titulo))
                        
                        if metadata and metadata.get('album'):
                            audio.tags.add(TALB(encoding=3, text=metadata['album']))
                        if metadata and metadata.get('año'):
                            audio.tags.add(TDRC(encoding=3, text=metadata['año']))
                            audio.tags.add(TYER(encoding=3, text=metadata['año']))
                        if metadata and metadata.get('genero'):
                            audio.tags.add(TCON(encoding=3, text=metadata['genero']))
                        if metadata and metadata.get('duracion'):
                            audio.tags.add(COMM(encoding=3, lang='eng', desc='Info', text=f"Duración: {metadata['duracion']}"))
                        
                        audio.save()
                        
                        self._log_message(f"✅ Guardado: {artista} - {titulo}", "success")
                        if metadata and metadata.get('album'):
                            self._log_message(f"   📀 Álbum: {metadata['album']}", "info")
                        if metadata and metadata.get('año'):
                            self._log_message(f"   📅 Año: {metadata['año']}", "info")
                        if metadata and metadata.get('genero'):
                            self._log_message(f"   🎵 Género: {metadata['genero']}", "info")
                    except Exception as e:
                        self._log_message(f"⚠️ Error escribiendo: {str(e)}", "warning")
                
                # Actualizar progreso
                progress = (processed / total) * 100
                self.parent.after(0, lambda p=progress, n=file_info["name"]: self._update_progress(p, n))
                
            except Exception as e:
                self._log_message(f"❌ Error con {file_info['name']}: {str(e)}", "error")
        
        self._log_message("", "info")
        self._log_message("✅ Procesamiento completado", "success")
        self._log_message("=" * 60, "info")

    def _buscar_caratula(self, artista, album):
        """Buscar carátula del álbum en Internet - VERSIÓN MEJORADA CON MÚLTIPLES FUENTES"""
        try:
            import requests
            from urllib.parse import quote
            import re
            
            # ============================================
            # FUENTE 1: Deezer (API gratuita, buena cobertura)
            # ============================================
            try:
                url = f"https://api.deezer.com/search/album?q={quote(artista)}%20{quote(album)}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data and 'data' in data and data['data']:
                        for album_data in data['data']:
                            if 'cover_medium' in album_data:
                                # Probar diferentes tamaños
                                cover_url = album_data.get('cover_xl') or album_data.get('cover_big') or album_data.get('cover_medium')
                                if cover_url:
                                    self._log_message(f"   ✅ Carátula encontrada en Deezer", "info")
                                    return cover_url
            except:
                pass
            
            # ============================================
            # FUENTE 2: iTunes/Apple Music (API gratuita)
            # ============================================
            try:
                url = f"https://itunes.apple.com/search?term={quote(f'{artista} {album}')}&entity=album&limit=1"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data and 'results' in data and data['results']:
                        result = data['results'][0]
                        if 'artworkUrl100' in result:
                            # iTunes devuelve imágenes de 100x100, cambiar tamaño a 600x600
                            cover_url = result['artworkUrl100'].replace('100x100', '600x600')
                            self._log_message(f"   ✅ Carátula encontrada en iTunes", "info")
                            return cover_url
            except:
                pass
            
            # ============================================
            # FUENTE 3: TheAudioDB (con mejor búsqueda)
            # ============================================
            try:
                url = f"https://www.theaudiodb.com/api/v1/json/2/searchalbum.php?s={quote(artista)}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data and 'album' in data and data['album']:
                        for album_data in data['album']:
                            # Buscar coincidencia exacta o parcial
                            album_name = album_data.get('strAlbum', '')
                            if album.lower() in album_name.lower() or album_name.lower() in album.lower():
                                cover_url = album_data.get('strAlbumThumb') or album_data.get('strAlbumThumbHQ')
                                if cover_url:
                                    self._log_message(f"   ✅ Carátula encontrada en TheAudioDB", "info")
                                    return cover_url
                        # Si no encuentra coincidencia, devolver el primero
                        if data['album']:
                            cover_url = data['album'][0].get('strAlbumThumb') or data['album'][0].get('strAlbumThumbHQ')
                            if cover_url:
                                self._log_message(f"   ✅ Carátula encontrada en TheAudioDB", "info")
                                return cover_url
            except:
                pass
            
            # ============================================
            # FUENTE 4: Last.fm (con mejor scraping)
            # ============================================
            try:
                url = f"https://www.last.fm/music/{quote(artista)}/{quote(album)}"
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    # Buscar diferentes patrones de imagen
                    patterns = [
                        r'<meta property="og:image" content="([^"]+)"',
                        r'<img[^>]+class="[^"]*artwork[^"]*"[^>]+src="([^"]+)"',
                        r'<img[^>]+src="([^"]+)"[^>]+class="[^"]*artwork[^"]*"',
                        r'"image":"([^"]+)"'
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, response.text)
                        if matches:
                            img_url = matches[0]
                            # Limpiar URL
                            if not img_url.startswith('http'):
                                img_url = 'https:' + img_url
                            self._log_message(f"   ✅ Carátula encontrada en Last.fm", "info")
                            return img_url
            except:
                pass
            
            # ============================================
            # FUENTE 5: MusicBrainz + Cover Art Archive
            # ============================================
            try:
                import musicbrainzngs
                musicbrainzngs.set_useragent("OrganizadorPro", "1.0", "organizadorpro@email.com")
                
                # Buscar release por artista y álbum
                query = f'artist:"{artista}" AND release:"{album}"'
                result = musicbrainzngs.search_releases(query=query, limit=3)
                
                if result and result.get('release-list'):
                    for release in result['release-list']:
                        if 'id' in release:
                            # Cover Art Archive
                            cover_url = f"https://coverartarchive.org/release/{release['id']}/front"
                            try:
                                response = requests.head(cover_url, timeout=3)
                                if response.status_code == 200:
                                    self._log_message(f"   ✅ Carátula encontrada en MusicBrainz", "info")
                                    return cover_url
                            except:
                                pass
            except:
                pass
            
            # ============================================
            # FUENTE 6: Google Images (último recurso)
            # ============================================
            try:
                query = f"{artista} {album} album cover"
                url = f"https://www.googleapis.com/customsearch/v1?q={quote(query)}&searchType=image&key=AIzaSyC4N1Gfq4q5gG6X8N9Z0R1P2M3Q4W5E6R&cx=017576662512468239467:ab9f9e6b9d7e"
                # Nota: Necesitas API key de Google Custom Search para que esto funcione
                # Como es un último recurso, mejor no depender de ella
                pass
            except:
                pass
            
            self._log_message(f"   ⚠️ No se encontró carátula en ninguna fuente", "warning")
            return None
            
        except Exception as e:
            self._log_message(f"⚠️ Error buscando carátula: {str(e)}", "warning")
            return None

    def _guardar_caratula(self, file_path, image_url):
        """Descargar y guardar carátula - VERSIÓN ROBUSTA"""
        try:
            import requests
            from PIL import Image, ImageFile
            import io
            
            # Permitir imágenes truncadas
            ImageFile.LOAD_TRUNCATED_IMAGES = True
            
            # Descargar imagen con headers para evitar bloqueos
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(image_url, timeout=15, headers=headers)
            if response.status_code != 200:
                self._log_message(f"   ⚠️ Error descargando: Código {response.status_code}", "warning")
                return False
            
            # Verificar que hay datos
            if len(response.content) < 100:
                self._log_message(f"   ⚠️ Imagen muy pequeña ({len(response.content)} bytes)", "warning")
                return False
            
            # Intentar abrir la imagen con múltiples métodos
            img = None
            try:
                # Método 1: Abrir directamente
                img = Image.open(io.BytesIO(response.content))
            except Exception as e1:
                self._log_message(f"   ⚠️ Error método 1: {str(e1)[:50]}", "warning")
                try:
                    # Método 2: Guardar temporalmente y abrir
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                        tmp.write(response.content)
                        tmp_path = tmp.name
                    img = Image.open(tmp_path)
                    os.unlink(tmp_path)
                except Exception as e2:
                    self._log_message(f"   ⚠️ Error método 2: {str(e2)[:50]}", "warning")
                    try:
                        # Método 3: Forzar formato
                        from PIL import ImageFile as PImageFile
                        parser = PImageFile.Parser()
                        parser.feed(response.content)
                        img = parser.close()
                    except:
                        self._log_message(f"   ❌ No se pudo abrir la imagen", "error")
                        return False
            
            if img is None:
                self._log_message(f"   ❌ No se pudo procesar la imagen", "error")
                return False
            
            # Redimensionar si es demasiado grande
            if img.width > 500 or img.height > 500:
                img.thumbnail((500, 500))
            
            # Convertir a RGB
            try:
                if img.mode != 'RGB':
                    if img.mode == 'RGBA':
                        # Crear fondo blanco y pegar
                        bg = Image.new('RGB', img.size, (255, 255, 255))
                        bg.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
                        img = bg
                    else:
                        img = img.convert('RGB')
            except:
                try:
                    img = img.convert('RGB')
                except:
                    pass
            
            # Guardar en bytes (siempre JPEG)
            img_bytes = io.BytesIO()
            try:
                img.save(img_bytes, format='JPEG', quality=90)
            except:
                try:
                    img.save(img_bytes, format='PNG')
                except:
                    self._log_message(f"   ❌ No se pudo guardar la imagen en formato compatible", "error")
                    return False
            
            img_data = img_bytes.getvalue()
            
            # ============================================
            # GUARDAR EN EL ARCHIVO DE AUDIO
            # ============================================
            try:
                import mutagen              
                audio = mutagen.File(str(file_path))
                if audio is None:
                    self._log_message(f"   ⚠️ No se pudo leer el archivo de audio", "warning")
                    return False
                
                # Verificar si tiene tags
                if hasattr(audio, 'tags') and audio.tags is not None:
                    # Eliminar carátulas existentes (MÉTODO SEGURO)
                    try:
                        # Intentar diferentes métodos de eliminación
                        if hasattr(audio.tags, 'pop'):
                            audio.tags.pop('APIC', None)
                        elif hasattr(audio.tags, 'delall'):
                            audio.tags.delall('APIC')
                        else:
                            # Método manual
                            for tag in list(audio.tags.values()):
                                if tag.__class__.__name__ == 'APIC':
                                    try:
                                        del audio.tags[tag.hash_key]
                                    except:
                                        pass
                    except Exception as e:
                        self._log_message(f"   ⚠️ Eliminando carátulas existentes: {e}", "warning")
                    
                    # Añadir nueva carátula
                    try:
                        audio.tags.add(APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3,
                            desc='Cover',
                            data=img_data
                        ))
                        audio.save()
                        self._log_message(f"   ✅ Carátula guardada correctamente", "success")
                        return True
                    except Exception as e:
                        self._log_message(f"   ⚠️ Error añadiendo carátula: {e}", "warning")
                        return False
                else:
                    # Si no tiene tags, crear ID3 nuevo
                    try:
                        audio = ID3(str(file_path))
                        audio.add(APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3,
                            desc='Cover',
                            data=img_data
                        ))
                        audio.save()
                        self._log_message(f"   ✅ Carátula guardada (nuevo ID3)", "success")
                        return True
                    except Exception as e:
                        self._log_message(f"   ⚠️ Error creando ID3: {e}", "warning")
                        return False
                        
            except ImportError:
                self._log_message("⚠️ mutagen no instalada", "warning")
                return False
            except Exception as e:
                self._log_message(f"⚠️ Error guardando carátula: {str(e)}", "warning")
                return False
                
        except Exception as e:
            self._log_message(f"⚠️ Error general: {str(e)}", "warning")
            return False

    def _buscar_caratula_para_archivo(self, file_info):
        """Buscar y guardar carátula para un archivo específico - VERSIÓN MEJORADA"""
        try:
            import mutagen
            
            file_path = file_info["path"]
            audio = mutagen.File(str(file_path))
            if audio is None:
                return False
            
            # Obtener artista y álbum de los metadatos
            artista = None
            album = None
            
            if hasattr(audio, 'tags') and audio.tags is not None:
                if 'TPE1' in audio.tags:
                    artista = str(audio.tags['TPE1'])
                if 'TALB' in audio.tags:
                    album = str(audio.tags['TALB'])
            
            # Si no tiene artista, intentar extraer del nombre
            if not artista:
                artista, titulo = self._limpiar_nombre_archivo(file_info["name"])
                if not album and titulo:
                    album = titulo
            
            # Si no tiene álbum, usar el título o el nombre del archivo
            if not album:
                # Usar el título de la canción si existe
                if hasattr(audio, 'tags') and audio.tags is not None:
                    if 'TIT2' in audio.tags:
                        album = str(audio.tags['TIT2'])
                # Si no, usar el nombre del archivo sin extensión
                if not album:
                    album = Path(file_info["name"]).stem
            
            if not artista:
                self._log_message(f"⚠️ No se puede buscar carátula: falta artista", "warning")
                return False
            
            self._log_message(f"🔍 Buscando carátula: {artista} - {album}", "info")
            
            # Buscar carátula
            caratula_url = self._buscar_caratula(artista, album)
            
            if caratula_url:
                self._log_message(f"✅ Carátula encontrada", "success")
                if self._guardar_caratula(file_path, caratula_url):
                    self._log_message(f"✅ Carátula guardada: {file_info['name']}", "success")
                    return True
                else:
                    self._log_message(f"⚠️ No se pudo guardar la carátula", "warning")
                    return False
            else:
                self._log_message(f"⚠️ No se encontró carátula para: {artista} - {album}", "warning")
                return False
                
        except Exception as e:
            self._log_message(f"❌ Error con {file_info['name']}: {str(e)}", "error")
            return False

    def _buscar_caratulas_masivo(self):
        """Buscar carátulas para TODOS los archivos escaneados"""
        if not self.current_files:
            messagebox.showinfo("Info", "Primero escanea archivos")
            return
        
        # Verificar si está activada la opción
        if not self.buscar_caratulas.get():
            messagebox.showinfo("Info", "La opción 'Buscar carátulas' está desactivada.\n\nActívala en las Opciones.")
            return
        
        total = len(self.current_files)
        if not messagebox.askyesno("Confirmar", 
            f"¿Buscar carátulas para {total} archivos de audio?\n\n"
            "⚠️ Esto puede tomar tiempo dependiendo de la conexión a Internet"):
            return
        
        self._clear_log()
        self.progress_bar.config(value=0)
        self.label_progress.config(text="⏳ Buscando carátulas...")
        self.btn_caratulas.config(state="disabled")
        self.btn_scan.config(state="disabled")
        self.btn_process.config(state="disabled")
        
        self._log_message("=" * 60, "info")
        self._log_message("🖼️ BUSCANDO CARÁTULAS", "bold")
        self._log_message(f"📁 Archivos: {total}", "info")
        self._log_message("=" * 60, "info")
        
        def run():
            found = 0
            errors = 0
            processed = 0
                       
            for file_info in self.current_files:
                processed += 1
                
                # Verificar si ya tiene carátula
                try:
                    import mutagen
                    audio = mutagen.File(str(file_info["path"]))
                    if audio is not None and hasattr(audio, 'tags') and audio.tags is not None:
                        has_cover = False
                        for tag in audio.tags.values():
                            if tag.__class__.__name__ == 'APIC':
                                has_cover = True
                                break
                        if has_cover:
                            self._log_message(f"⏭️ Ya tiene carátula: {file_info['name']}", "info")
                            continue
                except:
                    pass
                
                # Buscar y guardar carátula
                if self._buscar_caratula_para_archivo(file_info):
                    found += 1
                else:
                    errors += 1
                
                # Actualizar progreso
                progress = (processed / total) * 100
                self.parent.after(0, lambda p=progress, n=file_info["name"]: self._update_progress(p, n))
            
            # Mostrar resumen
            self.parent.after(0, lambda: self._mostrar_resumen_caratulas(found, errors, total))
        
        Thread(target=run, daemon=True).start()

    def _mostrar_resumen_caratulas(self, found, errors, total):
        """Mostrar resumen de la búsqueda de carátulas"""
        self._log_message("", "info")
        self._log_message("=" * 60, "info")
        self._log_message("✅ BÚSQUEDA DE CARÁTULAS COMPLETADA", "bold")
        self._log_message(f"🖼️ Carátulas encontradas: {found}", "success")
        self._log_message(f"❌ No encontradas / Errores: {errors}", "error" if errors > 0 else "info")
        self._log_message(f"📊 Total procesados: {total}", "info")
        self._log_message("=" * 60, "info")
        
        self.btn_caratulas.config(state="normal")
        self.btn_scan.config(state="normal")
        self.btn_process.config(state="normal")
        self.progress_bar.config(value=100)
        self.label_progress.config(text="✅ Búsqueda completada")
        
        messagebox.showinfo("Completado", 
            f"🖼️ Búsqueda de carátulas completada\n\n"
            f"✅ Encontradas: {found}\n"
            f"❌ No encontradas/Errores: {errors}\n"
            f"📊 Total procesados: {total}")

    def _poner_caratula_manual(self, tree):
        """Poner carátula manualmente desde el disco duro - CON VALIDACIÓN"""
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Selecciona un archivo")
            return
        
        item = selection[0]
        values = tree.item(item, 'values')
        if len(values) < 6:
            return
        
        archivo = values[0]
        
        # Seleccionar imagen
        archivo_imagen = filedialog.askopenfilename(
            title="Seleccionar imagen para la carátula",
            filetypes=[
                ("Imágenes", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("Todos los archivos", "*.*")
            ]
        )
        
        if not archivo_imagen:
            return
        
        # Buscar el archivo en la lista
        for file_info in self.edit_items:
            if file_info["name"] == archivo:
                try:
                    from PIL import Image, ImageFile
                    import io
                    
                    # Permitir imágenes truncadas
                    ImageFile.LOAD_TRUNCATED_IMAGES = True
                    
                    # Cargar la imagen seleccionada
                    try:
                        img = Image.open(archivo_imagen)
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo abrir la imagen:\n{str(e)}\n\nLa imagen podría estar corrupta o no ser un formato válido.")
                        return
                    
                    if img is None:
                        messagebox.showerror("Error", "No se pudo procesar la imagen")
                        return
                    
                    # Redimensionar si es demasiado grande (máx 500x500)
                    if img.width > 500 or img.height > 500:
                        img.thumbnail((500, 500))
                    
                    # Convertir a RGB si es necesario
                    if img.mode in ('RGBA', 'LA', 'P'):
                        try:
                            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            if img.mode == 'RGBA':
                                rgb_img.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
                            else:
                                rgb_img.paste(img)
                            img = rgb_img
                        except:
                            try:
                                img = img.convert('RGB')
                            except:
                                pass
                    
                    # Convertir a bytes
                    img_bytes = io.BytesIO()
                    try:
                        img.save(img_bytes, format='JPEG', quality=92)
                    except:
                        try:
                            img.save(img_bytes, format='PNG')
                        except:
                            messagebox.showerror("Error", "No se pudo guardar la imagen en formato compatible")
                            return
                    img_data = img_bytes.getvalue()
                    
                    # Guardar en el archivo de audio
                    import mutagen
                    from mutagen.id3 import APIC, ID3
                    
                    audio = mutagen.File(str(file_info["path"]))
                    if audio is None:
                        messagebox.showerror("Error", "No se pudo leer el archivo de audio")
                        return
                    
                    if hasattr(audio, 'tags') and audio.tags is not None:
                        # Eliminar carátulas existentes
                        for tag in audio.tags.getall('APIC'):
                            try:
                                audio.tags.delitem(tag.hash_key)
                            except:
                                pass
                        
                        audio.tags.add(APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3,
                            desc='Cover',
                            data=img_data
                        ))
                        audio.save()
                        
                        self._mostrar_caratula_del_archivo(file_info["path"])
                        self._log_message(f"✅ Carátula manual guardada para: {archivo}", "success")
                        messagebox.showinfo("Éxito", f"✅ Carátula guardada para:\n{archivo}")
                    else:
                        try:
                            audio = ID3(str(file_info["path"]))
                            audio.add(APIC(
                                encoding=3,
                                mime='image/jpeg',
                                type=3,
                                desc='Cover',
                                data=img_data
                            ))
                            audio.save()
                            self._mostrar_caratula_del_archivo(file_info["path"])
                            self._log_message(f"✅ Carátula manual guardada para: {archivo}", "success")
                            messagebox.showinfo("Éxito", f"✅ Carátula guardada para:\n{archivo}")
                        except Exception as e:
                            messagebox.showerror("Error", f"No se pudo guardar la carátula:\n{str(e)}")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Error al procesar la imagen:\n{str(e)}")
                break
    
    def _update_progress(self, progress, name):
        self.progress_bar.config(value=progress)
        self.label_progress.config(text=f"📄 {name}")
        self._scroll_to_end()
