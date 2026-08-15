import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import os
import re
from pathlib import Path
import time
import shutil

class SecurityTab:
    """Pestaña de seguridad - Cazador de malware (ESTILO LIBERADOR)"""
    
    def __init__(self, parent, organizer):
        self.parent = parent
        self.organizer = organizer
        self.is_running = False
        
        # Variables para control
        self.analizando = False
        self.cancelar_analisis = False
        
        # Lista de procesos sospechosos conocidos
        self.sospechosos = [
            'miner', 'crypto', 'bitcoin', 'monero', 'eth', 'mining',
            'trojan', 'backdoor', 'ransom', 'worm', 'virus', 'malware',
            'keylogger', 'spy', 'stealth', 'hack', 'exploit', 'payload',
            'crack', 'keygen', 'patch', 'activator', 'kms', 'rat', 'vnc'
        ]
        
        # Extensiones de archivos sospechosos
        self.extensiones_sospechosas = {
            '.exe', '.dll', '.vbs', '.bat', '.cmd', '.ps1', '.js', '.jse',
            '.vbe', '.wsf', '.wsh', '.scr', '.pif', '.com'
        }
        
        # Procesos legítimos de Windows
        self.procesos_legitimos = {
            'svchost.exe', 'explorer.exe', 'taskhost.exe', 'winlogon.exe',
            'lsass.exe', 'wininit.exe', 'services.exe', 'csrss.exe',
            'smss.exe', 'system', 'system idle process', 'dwm.exe',
            'ctfmon.exe', 'taskhostw.exe', 'winmgmt.exe', 'spoolsv.exe',
            'conhost.exe', 'cmd.exe', 'powershell.exe', 'python.exe',
            'pythonw.exe', 'firefox.exe', 'chrome.exe', 'msedge.exe'
        }

        # ============================================
        # PROCESOS QUE NUNCA SE MATAN (SEGURIDAD EXTREMA)
        # ============================================
        self.procesos_intocables = {
            'csrss.exe', 'winlogon.exe', 'services.exe', 'lsass.exe',
            'wininit.exe', 'smss.exe', 'system', 'system idle process',
            'dwm.exe', 'ctfmon.exe', 'taskhost.exe', 'taskhostw.exe',
            'svchost.exe', 'explorer.exe', 'winmgmt.exe', 'spoolsv.exe',
            'conhost.exe', 'cmd.exe', 'powershell.exe', 'python.exe',
            'pythonw.exe', 'msedge.exe', 'chrome.exe', 'firefox.exe',
            'SearchHost.exe', 'RuntimeBroker.exe', 'ShellExperienceHost.exe',
            'StartMenuExperienceHost.exe',
            'WindowsInternal.ComposableShell.Experiences.TextInput.InputApp.exe'
        }
        
        self._build_ui()
    
    def _build_ui(self):
        """Construir la interfaz - EXACTO COMO EL LIBERADOR"""
        
        # ===== Contenedor principal =====
        main_frame = ttk.Frame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # ============================================
        # FILA 1: Instrucciones
        # ============================================
        frame_instrucciones = ttk.LabelFrame(main_frame, text="🛡️ Cazador de malware", padding=5)
        frame_instrucciones.pack(fill="x", pady=3)
        
        tk.Label(frame_instrucciones, 
                text="Analiza procesos, archivos y conexiones de red en busca de actividad sospechosa.",
                font=("Arial", 9), fg="#2c3e50").pack(anchor="w")
        tk.Label(frame_instrucciones, 
                text="⚠️ No sustituye a un antivirus profesional. Es una herramienta complementaria.",
                font=("Arial", 9), fg="#e74c3c").pack(anchor="w")
        
        # ============================================
        # FILA 2: Botones (estilo Liberador)
        # ============================================
        frame_botones = ttk.Frame(main_frame)
        frame_botones.pack(fill="x", pady=3)
        
        self.btn_analizar = ttk.Button(frame_botones, text="🔍 ANALIZAR SISTEMA", 
                                      command=self._analizar_sistema,
                                      style="Accent.TButton")
        self.btn_analizar.pack(side=tk.LEFT, padx=2, ipadx=10)
        
        self.btn_revisar = ttk.Button(frame_botones, text="🔎 REVISAR ARCHIVOS", 
                                     command=self._revisar_archivos)
        self.btn_revisar.pack(side=tk.LEFT, padx=2, ipadx=10)
        
        self.btn_red = ttk.Button(frame_botones, text="🌐 REVISAR CONEXIONES", 
                                  command=self._revisar_conexiones)
        self.btn_red.pack(side=tk.LEFT, padx=2, ipadx=10)

        self.btn_matar_proceso = ttk.Button(frame_botones, text="💀 MATAR PROCESO", 
                                           command=self._matar_proceso_seleccionado,
                                           state="disabled")
        self.btn_matar_proceso.pack(side=tk.LEFT, padx=2, ipadx=10)

        self.btn_eliminar_archivo = ttk.Button(frame_botones, text="🗑️ ELIMINAR ARCHIVO", 
                                              command=self._eliminar_archivo_seleccionado,
                                              state="disabled")
        self.btn_eliminar_archivo.pack(side=tk.LEFT, padx=2, ipadx=10)
        
        self.btn_cancel = ttk.Button(frame_botones, text="⛔ CANCELAR", 
                                    command=self._cancelar_analisis,
                                    state="disabled")
        self.btn_cancel.pack(side=tk.LEFT, padx=2, ipadx=10)
        
        # ============================================
        # FILA 3: Resumen (compacto)
        # ============================================
        frame_resumen = ttk.LabelFrame(main_frame, text="📊 Resumen", padding=2)
        frame_resumen.pack(fill="x", pady=2)
        
        self.label_resumen = ttk.Label(frame_resumen, text="🔍 Haz clic en 'Analizar' para escanear tu sistema.")
        self.label_resumen.pack(anchor="w", padx=5)
        
        # ============================================
        # FILA 4: TABLA DE RESULTADOS (arriba)
        # ============================================
        frame_tabla = ttk.LabelFrame(main_frame, text="📋 Resultados encontrados", padding=2)
        frame_tabla.pack(fill="both", expand=True, pady=2)
        
        columns = ("Nombre", "PID", "Estado", "Riesgo", "Detalles")
        self.tree = ttk.Treeview(frame_tabla, columns=columns, show="headings", height=8)
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("PID", text="PID")
        self.tree.heading("Estado", text="Estado")
        self.tree.heading("Riesgo", text="Riesgo")
        self.tree.heading("Detalles", text="Detalles")
        
        self.tree.column("Nombre", width=130)
        self.tree.column("PID", width=55)
        self.tree.column("Estado", width=120)
        self.tree.column("Riesgo", width=60)
        self.tree.column("Detalles", width=300)
        
        scroll = ttk.Scrollbar(frame_tabla, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # ============================================
        # BINDING PARA SELECCIÓN
        # ============================================
        self.tree.bind("<<TreeviewSelect>>", self._on_select_item)
        
        # ============================================
        # FILA 5: BARRA DE PROGRESO (en medio)
        # ============================================
        frame_progreso = ttk.LabelFrame(main_frame, text="📊 Progreso", padding=2)
        frame_progreso.pack(fill="x", pady=2)
        
        self.progress_bar = ttk.Progressbar(frame_progreso, length=400, mode='determinate')
        self.progress_bar.pack(fill="x", pady=2)
        
        # Frame para información estática
        frame_info = ttk.Frame(frame_progreso)
        frame_info.pack(fill="x", pady=1)
        
        self.label_porcentaje = ttk.Label(frame_info, text="0%", font=("Arial", 9, "bold"))
        self.label_porcentaje.pack(side=tk.LEFT, padx=5)
        
        self.label_eta = ttk.Label(frame_info, text="⏱️ --:--", font=("Arial", 9))
        self.label_eta.pack(side=tk.RIGHT, padx=5)
        
        self.label_progress = ttk.Label(frame_info, text="Esperando...", font=("Arial", 8), anchor="center")
        self.label_progress.pack(side=tk.LEFT, fill="x", expand=True, padx=10)
        
        # ============================================
        # FILA 6: LOG (abajo)
        # ============================================
        frame_log = ttk.LabelFrame(main_frame, text="📋 Registro", padding=2)
        frame_log.pack(fill="both", expand=True, pady=2)
        
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
        
        self._log("🛡️ Listo para analizar seguridad...", "info")
    
    def _log(self, message, tag="info"):
        """Añadir mensaje al log"""
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)
        self.log_text.update_idletasks()

    def _on_select_item(self, event):
        """Habilitar botones según lo seleccionado"""
        selection = self.tree.selection()
        if not selection:
            self.btn_matar_proceso.config(state="disabled")
            self.btn_eliminar_archivo.config(state="disabled")
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        if len(values) < 2:
            return
        
        # Si es un proceso (tiene PID numérico)
        if values[1].isdigit():
            self.btn_matar_proceso.config(state="normal")
        else:
            self.btn_matar_proceso.config(state="disabled")
        
        self.btn_eliminar_archivo.config(state="normal")
    
    def _update_progress(self, value, text="", eta=""):
        """Actualizar barra de progreso"""
        self.progress_bar.config(value=value)
        self.label_porcentaje.config(text=f"{value:.1f}%")
        if eta:
            self.label_eta.config(text=f"⏱️ {eta}")
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
    
    def _cancelar_analisis(self):
        """Cancelar el análisis en curso"""
        if not self.analizando:
            return
        
        if messagebox.askyesno("⛔ Cancelar análisis", 
            "¿Seguro que quieres cancelar el análisis?"):
            self.cancelar_analisis = True
            self._log("⛔ Cancelación solicitada...", "warning")
    
    def _analizar_sistema(self):
        """Analizar procesos en busca de malware"""
        self._log("=" * 50, "bold")
        self._log("🔍 ANALIZANDO PROCESOS DEL SISTEMA", "bold")
        self._log("=" * 50, "bold")
        
        self.analizando = True
        self.cancelar_analisis = False
        self._reset_progress()
        
        self.btn_analizar.config(state="disabled")
        self.btn_revisar.config(state="disabled")
        self.btn_red.config(state="disabled")
        self.btn_cancel.config(state="normal")
        self._update_progress(0, "Iniciando análisis...")
        
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.tiempo_inicio = time.time()
        
        def analizar():
            try:
                import psutil
                procesos = []
                sospechosos_encontrados = 0
                total_procesos = len(psutil.pids())
                procesados = 0
                
                for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
                    if self.cancelar_analisis:
                        self._log("⛔ Análisis cancelado por el usuario", "warning")
                        break
                    
                    try:
                        info = proc.info
                        nombre = info.get('name', 'Desconocido')
                        pid = info.get('pid', 0)
                        exe = info.get('exe', '')
                        cmdline = ' '.join(info.get('cmdline', [])) if info.get('cmdline') else ''
                        
                        procesados += 1
                        progress = (procesados / total_procesos) * 100
                        
                        if procesados > 5:
                            tiempo_total = time.time() - self.tiempo_inicio
                            eta = (tiempo_total / procesados) * (total_procesos - procesados)
                            if eta < 60:
                                eta_str = f"{int(eta)}s"
                            else:
                                eta_str = f"{int(eta//60)}m {int(eta%60)}s"
                        else:
                            eta_str = "--:--"
                        
                        self.parent.after(0, lambda p=progress, n=nombre, e=eta_str: 
                            self._update_progress(p, f"📄 {n}", e))
                        
                        riesgo, detalles = self._evaluar_riesgo(nombre, exe, cmdline)
                        
                        if riesgo > 0:
                            sospechosos_encontrados += 1
                            procesos.append({
                                'nombre': nombre,
                                'pid': pid,
                                'exe': exe,
                                'cmdline': cmdline,
                                'riesgo': riesgo,
                                'detalles': detalles
                            })
                            self.parent.after(0, lambda: self._log(f"⚠️ {nombre} (PID: {pid}) - {detalles}", "warning"))
                        
                    except:
                        continue
                
                self.parent.after(0, lambda: self._mostrar_procesos(procesos, sospechosos_encontrados))
                self.parent.after(0, lambda: self._update_progress(100, "✅ Análisis completado"))
                
            except ImportError:
                self.parent.after(0, lambda: self._log("❌ psutil no instalado. Ejecuta: pip install psutil", "error"))
                self.parent.after(0, lambda: self._update_progress(0, "Error: psutil no instalado"))
            except Exception as e:
                self.parent.after(0, lambda: self._log(f"❌ Error: {str(e)}", "error"))
            finally:
                self.parent.after(0, lambda: self.btn_analizar.config(state="normal"))
                self.parent.after(0, lambda: self.btn_revisar.config(state="normal"))
                self.parent.after(0, lambda: self.btn_red.config(state="normal"))
                self.parent.after(0, lambda: self.btn_cancel.config(state="disabled"))
                self.parent.after(0, lambda: setattr(self, 'analizando', False))
                self.parent.after(0, lambda: setattr(self, 'cancelar_analisis', False))
                self.parent.after(0, lambda: self._update_progress(100, "✅ Análisis completado", "00:00"))
        
        Thread(target=analizar, daemon=True).start()
    
    def _evaluar_riesgo(self, nombre, exe, cmdline):
        """Evaluar el nivel de riesgo de un proceso"""
        riesgo = 0
        detalles = []
        
        # 1. Verificar nombre sospechoso
        for patron in self.sospechosos:
            if patron in nombre.lower():
                riesgo += 3
                detalles.append(f"Nombre sospechoso: {patron}")
                break
        
        # 2. Verificar ubicación del ejecutable
        if exe:
            exe_lower = exe.lower()
            if '\\temp\\' in exe_lower or '\\tmp\\' in exe_lower:
                riesgo += 2
                detalles.append("Ejecutable en carpeta temporal")
            if '\\downloads\\' in exe_lower:
                riesgo += 2
                detalles.append("Ejecutable en Downloads")
            if '\\appdata\\' in exe_lower and '\\microsoft\\' not in exe_lower:
                riesgo += 1
                detalles.append("Ejecutable en AppData")
            if '\\desktop\\' in exe_lower:
                riesgo += 1
                detalles.append("Ejecutable en Escritorio")
        
        # 3. Verificar línea de comandos
        if cmdline:
            cmdline_lower = cmdline.lower()
            for patron in ['-miner', '--miner', 'crypto', 'bitcoin', 'monero', '--cpu', '--gpu']:
                if patron in cmdline_lower:
                    riesgo += 2
                    detalles.append(f"Parámetro sospechoso: {patron}")
                    break
        
        return riesgo, ", ".join(detalles) if detalles else "Sin detalles"
    
    def _mostrar_procesos(self, procesos, sospechosos):
        """Mostrar procesos en la tabla con colores"""
        if not procesos:
            self._log("✅ No se encontraron procesos sospechosos", "success")
            self.label_resumen.config(text="✅ No se encontraron procesos sospechosos. ¡Sistema limpio!")
            return
        
        for proc in procesos:
            nombre = proc['nombre']
            pid = proc['pid']
            riesgo = proc['riesgo']
            detalles = proc.get('detalles', '')
            
            if riesgo >= 3:
                estado = "ALTO RIESGO"
                riesgo_texto = "🔴"
                tag = "alto"
            elif riesgo >= 2:
                estado = "RIESGO MEDIO"
                riesgo_texto = "🟡"
                tag = "medio"
            else:
                estado = "RIESGO BAJO"
                riesgo_texto = "🟠"
                tag = "bajo"
            
            item = self.tree.insert("", "end", values=(
                nombre,
                pid,
                estado,
                riesgo_texto,
                detalles[:200] if detalles else ""
            ))
            
            # Aplicar color a la fila según el riesgo
            if tag == "alto":
                self.tree.tag_configure('alto', background='#ffebee')  # Rojo claro
            elif tag == "medio":
                self.tree.tag_configure('medio', background='#fff8e1')  # Amarillo claro
            elif tag == "bajo":
                self.tree.tag_configure('bajo', background='#fff3e0')  # Naranja claro
            
            self.tree.item(item, tags=(tag,))
        
        self._log(f"📊 Procesos analizados: {len(procesos)}", "info")
        self._log(f"⚠️ Sospechosos encontrados: {sospechosos}", "warning" if sospechosos > 0 else "success")
        
        if sospechosos > 0:
            self.label_resumen.config(text=f"⚠️ Se encontraron {sospechosos} procesos sospechosos. Revisa la tabla.")
        else:
            self.label_resumen.config(text="✅ No se encontraron procesos sospechosos.")

    def _color_riesgo(self, riesgo):
        """Devolver texto coloreado para el riesgo"""
        if riesgo >= 3:
            return "🔴 ALTO"
        elif riesgo >= 2:
            return "🟡 MEDIO"
        else:
            return "🟠 BAJO"

    def _matar_proceso_seleccionado(self):
        """Matar el proceso seleccionado - CON VERIFICACIÓN EXTREMA"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Selecciona un proceso para matar")
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        if len(values) < 2:
            return
        
        nombre = values[0]
        pid = values[1]
        
        # ============================================
        # VERIFICACIÓN DE SEGURIDAD EXTREMA
        # ============================================
        
        # 1. Verificar si está en la lista de intocables
        if nombre.lower() in [p.lower() for p in self.procesos_intocables]:
            messagebox.showerror("⛔ SEGURIDAD", 
                f"❌ NO SE PUEDE MATAR\n\n"
                f"El proceso '{nombre}' es un proceso crítico del sistema.\n"
                f"Matarlo podría causar inestabilidad o un reinicio del sistema.\n\n"
                f"⚠️ Esta acción está bloqueada por seguridad.")
            return
        
        # 2. Verificar si es un proceso de sistema
        try:
            import psutil
            proc = psutil.Process(int(pid))
            
            if hasattr(proc, 'username'):
                usuario = proc.username()
                if usuario in ['SYSTEM', 'NT AUTHORITY\\SYSTEM', 'NT AUTHORITY\\LOCAL SERVICE', 'NT AUTHORITY\\NETWORK SERVICE']:
                    messagebox.showerror("⛔ SEGURIDAD", 
                        f"❌ NO SE PUEDE MATAR\n\n"
                        f"El proceso '{nombre}' es un proceso del sistema.\n"
                        f"Ejecutado por: {usuario}\n\n"
                        f"⚠️ Esta acción está bloqueada por seguridad.")
                    return
        except:
            pass
        
        # 3. Doble confirmación
        if not messagebox.askyesno("💀 ADVERTENCIA EXTREMA", 
            f"⚠️⚠️⚠️ ADVERTENCIA EXTREMA ⚠️⚠️⚠️\n\n"
            f"Estás a punto de finalizar el proceso:\n\n"
            f"📄 {nombre} (PID: {pid})\n\n"
            f"⚠️ Esto puede hacer que:\n"
            f"   • El programa asociado se cierre\n"
            f"   • Pierdas trabajo no guardado\n"
            f"   • El sistema se vuelva inestable\n\n"
            f"¿Estás SEGURO de que quieres continuar?"):
            return
        
        # 4. Último aviso
        if not messagebox.askyesno("💀 ÚLTIMA ADVERTENCIA", 
            f"¿REALMENTE quieres matar el proceso '{nombre}'?\n\n"
            f"❌ Esta acción NO se puede deshacer."):
            return
        
        # ============================================
        # EJECUTAR
        # ============================================
        try:
            proc = psutil.Process(int(pid))
            
            try:
                proc.terminate()
                self._log(f"⏳ Terminando proceso: {nombre} (PID: {pid})", "info")
                time.sleep(1)
            except:
                pass
            
            if proc.is_running():
                proc.kill()
                self._log(f"💀 Proceso forzado: {nombre} (PID: {pid})", "warning")
            
            self._log(f"✅ Proceso terminado: {nombre} (PID: {pid})", "success")
            self.tree.delete(item)
            messagebox.showinfo("Éxito", f"✅ Proceso terminado: {nombre}")
            
        except psutil.NoSuchProcess:
            self._log(f"⚠️ El proceso ya no existe: {nombre}", "warning")
            self.tree.delete(item)
        except Exception as e:
            self._log(f"❌ Error: {str(e)}", "error")
            messagebox.showerror("Error", f"No se pudo terminar el proceso:\n{str(e)}")

    def _eliminar_archivo_seleccionado(self):
        """Eliminar el archivo seleccionado - CON VERIFICACIÓN DE SEGURIDAD"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Info", "Selecciona un archivo para eliminar")
            return
        
        item = selection[0]
        values = self.tree.item(item, 'values')
        if len(values) < 1:
            return
        
        nombre = values[0]
        
        # ============================================
        # VERIFICACIÓN DE SEGURIDAD
        # ============================================
        
        # 1. Extensiones que nunca se borran
        extensiones_protegidas = {
            '.exe', '.dll', '.sys', '.drv', '.msi', '.msp',
            '.pyd', '.pyc', '.pdb', '.manifest', '.cat',
            '.inf', '.ini', '.cfg', '.config', '.xml'
        }
        
        if Path(nombre).suffix.lower() in extensiones_protegidas:
            messagebox.showerror("⛔ SEGURIDAD", 
                f"❌ NO SE PUEDE ELIMINAR\n\n"
                f"El archivo '{nombre}' tiene una extensión protegida.\n"
                f"Podría ser un archivo del sistema.\n\n"
                f"⚠️ Esta acción está bloqueada por seguridad.")
            return
        
        # 2. Archivos protegidos por nombre
        archivos_protegidos = [
            'python.exe', 'pythonw.exe', 'pip.exe', 'pip3.exe',
            'ntdll.dll', 'kernel32.dll', 'user32.dll',
            'shell32.dll', 'advapi32.dll', 'msvcrt.dll',
            'svchost.exe', 'explorer.exe', 'winlogon.exe',
            'lsass.exe', 'services.exe', 'csrss.exe', 'wininit.exe'
        ]
        
        if nombre.lower() in [p.lower() for p in archivos_protegidos]:
            messagebox.showerror("⛔ SEGURIDAD", 
                f"❌ NO SE PUEDE ELIMINAR\n\n"
                f"El archivo '{nombre}' es un archivo protegido del sistema.\n\n"
                f"⚠️ Esta acción está bloqueada por seguridad.")
            return
        
        # 3. Confirmación
        if not messagebox.askyesno("🗑️ ADVERTENCIA", 
            f"⚠️ Estás a punto de eliminar el archivo:\n\n"
            f"📄 {nombre}\n\n"
            f"⚠️ Esta acción NO se puede deshacer.\n\n"
            f"¿Estás seguro?"):
            return
        
        # ============================================
        # EJECUTAR
        # ============================================
        try:
            archivo_encontrado = None
            carpetas = [
                Path(os.environ.get('TEMP', '')),
                Path(os.environ.get('TMP', '')),
                Path(os.environ.get('USERPROFILE', '')) / 'Downloads',
                Path(os.environ.get('USERPROFILE', '')) / 'Desktop',
            ]
            
            for carpeta in carpetas:
                if not carpeta.exists():
                    continue
                for archivo in carpeta.glob("*"):
                    if archivo.name == nombre:
                        archivo_encontrado = archivo
                        break
                if archivo_encontrado:
                    break
            
            if not archivo_encontrado:
                messagebox.showinfo("Info", f"No se encontró el archivo:\n{nombre}")
                return
            
            # Verificar si está en carpeta de Windows
            if str(archivo_encontrado).lower().startswith('c:\\windows') or str(archivo_encontrado).lower().startswith('c:\\program files'):
                messagebox.showerror("⛔ SEGURIDAD", 
                    f"❌ NO SE PUEDE ELIMINAR\n\n"
                    f"El archivo está en una carpeta protegida de Windows.\n\n"
                    f"⚠️ Esta acción está bloqueada por seguridad.")
                return
            
            if archivo_encontrado.is_dir():
                shutil.rmtree(str(archivo_encontrado))
            else:
                os.remove(str(archivo_encontrado))
            
            self._log(f"🗑️ Archivo eliminado: {nombre}", "success")
            self.tree.delete(item)
            messagebox.showinfo("Éxito", f"✅ Archivo eliminado: {nombre}")
            
        except Exception as e:
            self._log(f"❌ Error al eliminar {nombre}: {str(e)}", "error")
            messagebox.showerror("Error", f"No se pudo eliminar el archivo:\n{str(e)}")
    
    def _revisar_archivos(self):
        """Revisar archivos en busca de malware"""
        self._log("=" * 50, "bold")
        self._log("🔎 REVISANDO ARCHIVOS SOSPECHOSOS", "bold")
        self._log("=" * 50, "bold")
        
        self.btn_revisar.config(state="disabled")
        self._update_progress(0, "Revisando archivos...")
        
        def revisar():
            try:
                carpetas = [
                    Path(os.environ.get('TEMP', '')),
                    Path(os.environ.get('TMP', '')),
                    Path(os.environ.get('USERPROFILE', '')) / 'Downloads',
                    Path(os.environ.get('USERPROFILE', '')) / 'Desktop',
                ]
                
                archivos_encontrados = 0
                total_archivos = 0
                
                for carpeta in carpetas:
                    if not carpeta.exists():
                        continue
                    
                    try:
                        archivos = list(carpeta.glob("*"))
                        total_archivos += len(archivos)
                        
                        for archivo in archivos:
                            if archivo.suffix.lower() in self.extensiones_sospechosas:
                                archivos_encontrados += 1
                                self.parent.after(0, lambda: self._log(f"⚠️ {archivo.name} ({archivo.parent})", "warning"))
                    except:
                        continue
                
                self.parent.after(0, lambda: self._log(f"✅ Revisión completada. Archivos sospechosos encontrados: {archivos_encontrados}", "info"))
                self.parent.after(0, lambda: self.label_resumen.config(text=f"📁 Archivos sospechosos encontrados: {archivos_encontrados}"))
                self.parent.after(0, lambda: self._update_progress(100, "✅ Revisión completada"))
                
            except Exception as e:
                self.parent.after(0, lambda: self._log(f"❌ Error: {str(e)}", "error"))
            finally:
                self.parent.after(0, lambda: self.btn_revisar.config(state="normal"))
        
        Thread(target=revisar, daemon=True).start()
    
    def _revisar_conexiones(self):
        """Revisar conexiones de red sospechosas"""
        self._log("=" * 50, "bold")
        self._log("🌐 REVISANDO CONEXIONES DE RED", "bold")
        self._log("=" * 50, "bold")
        
        self.btn_red.config(state="disabled")
        self._update_progress(0, "Revisando conexiones...")
        
        def revisar():
            try:
                import psutil
                conexiones = []
                conexiones_sospechosas = []
                
                # IPs y puertos sospechosos comunes
                puertos_sospechosos = {4444, 6667, 1337, 31337, 5555, 12345, 31337}
                ips_sospechosas = []
                
                for conn in psutil.net_connections(kind='inet'):
                    if conn.status == 'ESTABLISHED':
                        if conn.raddr:
                            ip = conn.raddr.ip
                            puerto = conn.raddr.port
                            if ip and not ip.startswith('127.'):
                                conexiones.append({
                                    'ip': ip,
                                    'puerto': puerto,
                                    'proceso': conn.pid
                                })
                                
                                # Detectar conexiones sospechosas
                                es_sospechosa = False
                                razon = []
                                
                                if puerto in puertos_sospechosos:
                                    es_sospechosa = True
                                    razon.append(f"Puerto sospechoso: {puerto}")
                                
                                # IPs privadas (excepto red local)
                                if ip.startswith('10.') or ip.startswith('172.16.') or ip.startswith('192.168.'):
                                    if not ip.startswith('192.168.1.'):  # Tu red local
                                        es_sospechosa = True
                                        razon.append(f"IP privada no local: {ip}")
                                
                                if es_sospechosa:
                                    conexiones_sospechosas.append({
                                        'ip': ip,
                                        'puerto': puerto,
                                        'proceso': conn.pid,
                                        'razon': ', '.join(razon)
                                    })
                
                # Mostrar conexiones en el log
                if conexiones:
                    self._log(f"📊 Conexiones establecidas: {len(conexiones)}", "info")
                    
                    for conn in conexiones:
                        self._log(f"   🌐 {conn['ip']}:{conn['puerto']} (PID: {conn['proceso']})", "info")
                    
                    # ============================================
                    # RESUMEN FINAL
                    # ============================================
                    self._log("", "info")
                    self._log("=" * 50, "bold")
                    self._log("✅ REVISIÓN DE CONEXIONES COMPLETADA", "success")
                    self._log(f"📊 Total de conexiones activas: {len(conexiones)}", "info")
                    
                    if conexiones_sospechosas:
                        self._log(f"⚠️ Conexiones sospechosas encontradas: {len(conexiones_sospechosas)}", "warning")
                        for conn in conexiones_sospechosas:
                            self._log(f"   🔴 {conn['ip']}:{conn['puerto']} (PID: {conn['proceso']}) - {conn['razon']}", "error")
                    else:
                        self._log("✅ No se encontraron conexiones sospechosas", "success")
                    
                    self._log("=" * 50, "bold")
                    
                    # Resumen en la interfaz
                    resumen = f"🌐 {len(conexiones)} conexiones activas"
                    if conexiones_sospechosas:
                        resumen += f" | ⚠️ {len(conexiones_sospechosas)} sospechosas"
                    else:
                        resumen += " | ✅ Todo seguro"
                    
                    self.parent.after(0, lambda: self.label_resumen.config(text=resumen))
                    
                    # Ventana emergente con resumen
                    mensaje = f"✅ Revisión de conexiones completada\n\n"
                    mensaje += f"📊 Conexiones activas: {len(conexiones)}\n"
                    if conexiones_sospechosas:
                        mensaje += f"⚠️ Conexiones sospechosas: {len(conexiones_sospechosas)}\n\n"
                        mensaje += "🔴 Conexiones sospechosas:\n"
                        for conn in conexiones_sospechosas[:5]:
                            mensaje += f"   • {conn['ip']}:{conn['puerto']} (PID: {conn['proceso']}) - {conn['razon']}\n"
                        if len(conexiones_sospechosas) > 5:
                            mensaje += f"   ... y {len(conexiones_sospechosas) - 5} más\n"
                    else:
                        mensaje += "✅ No se encontraron conexiones sospechosas\n"
                    
                    self.parent.after(0, lambda: messagebox.showinfo("🌐 Revisión completada", mensaje))
                    
                else:
                    self._log("✅ No hay conexiones activas", "info")
                    self.parent.after(0, lambda: self.label_resumen.config(text="🌐 No hay conexiones activas"))
                    self.parent.after(0, lambda: messagebox.showinfo("🌐 Revisión completada", 
                        "✅ No hay conexiones de red activas."))
                
                self.parent.after(0, lambda: self._update_progress(100, "✅ Revisión completada"))
                
            except ImportError:
                self.parent.after(0, lambda: self._log("❌ psutil no instalado", "error"))
                self.parent.after(0, lambda: self._update_progress(0, "Error: psutil no instalado"))
            except Exception as e:
                self.parent.after(0, lambda: self._log(f"❌ Error: {str(e)}", "error"))
            finally:
                self.parent.after(0, lambda: self.btn_red.config(state="normal"))
        
        Thread(target=revisar, daemon=True).start()
