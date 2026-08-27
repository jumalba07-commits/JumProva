"""
Servicio para limpieza de sistema y archivos.
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import hashlib
from datetime import datetime, timedelta

# ========== ARCHIVOS PROTEGIDOS (NUNCA ELIMINAR) ==========
PROTECTED_FILES = {
    # Archivos del sistema
    'ntldr', 'bootmgr', 'bootnxt', 'boot.sdi',
    'pagefile.sys', 'swapfile.sys', 'hiberfil.sys',
    'winload.exe', 'winload.efi', 'winresume.exe',
    'ntoskrnl.exe', 'hal.dll', 'kdcom.dll',
    'bootstat.dat', 'BCD', 'BCD.LOG',
    
    # Archivos de configuración
    'boot.ini', 'win.ini', 'system.ini', 'desktop.ini',
    
    # Archivos de recuperación
    'recovery', 'reagent.xml',
    
    # Archivos de Windows
    'explorer.exe', 'regedit.exe', 'cmd.exe',
    'taskmgr.exe', 'notepad.exe', 'calc.exe',
}

PROTECTED_FOLDERS = {
    # Carpetas del sistema (en raíz)
    'Windows', 'WINNT',
    'System32', 'SysWOW64',
    'WinSxS', 'Microsoft.NET',
    'Program Files', 'Program Files (x86)',
    'ProgramData', 'Boot',
    'System Volume Information', '$Recycle.Bin',
    'Recovery', 'PerfLogs',
    'Temp', 'Temporary Internet Files',
    # Carpetas de usuario críticas
    'AppData', 'Application Data',
    'Local Settings', 'Cookies',
    'Desktop', 'Documents', 'Downloads',
    'Favorites', 'Links', 'Music', 'Pictures', 'Videos',
}

# Extensiones que nunca se deben eliminar (archivos del sistema)
PROTECTED_EXTENSIONS = {
    '.dll', '.sys', '.exe', '.msi', '.cab', 
    '.cat', '.inf', '.ini', '.hlp', '.chm',
    '.ocx', '.cpl', '.scr', '.drv', '.dat',
    '.log'  # logs del sistema (no los borramos)
}


class SystemCleaner:
    """Servicio de limpieza de sistema y archivos."""

    def __init__(self):
        self.files_to_clean = []
        self.cleaned_files = []
        self.errors = []
        self.protected_skipped = []
        self.cancel_requested = False
        self.is_running = False

    def _is_protected(self, file_path: Path) -> Tuple[bool, str]:
        """
        Verifica si un archivo o carpeta está protegido.
        
        Returns:
            (True/False, razón)
        """
        try:
            # 1. Verificar si es un archivo del sistema en la raíz
            if file_path.parent == file_path.root:
                # Archivos en la raíz del disco (C:\, D:\, etc.)
                if file_path.name.lower() in [f.lower() for f in PROTECTED_FILES]:
                    return True, f"Archivo del sistema en raíz: {file_path.name}"

            # 2. Verificar nombre de archivo protegido
            if file_path.name.lower() in [f.lower() for f in PROTECTED_FILES]:
                return True, f"Archivo del sistema: {file_path.name}"

            # 3. Verificar si está dentro de una carpeta protegida
            for protected in PROTECTED_FOLDERS:
                if protected.lower() in [p.lower() for p in file_path.parts]:
                    return True, f"Carpeta protegida: {protected}"

            # 4. Verificar extensiones protegidas (archivos del sistema)
            if file_path.suffix.lower() in PROTECTED_EXTENSIONS:
                # Permitir solo si está en carpeta de usuario (Documentos, Descargas, etc.)
                user_folders = ['Desktop', 'Documents', 'Downloads', 'Music', 'Pictures', 'Videos']
                is_user_folder = any(folder in [p for p in file_path.parts] for folder in user_folders)
                if not is_user_folder:
                    return True, f"Extensión de sistema: {file_path.suffix}"

            # 5. Verificar archivos ocultos del sistema
            if file_path.name.startswith('$') or file_path.name.startswith('~'):
                return True, f"Archivo oculto del sistema: {file_path.name}"

            return False, ""

        except Exception:
            # Si no podemos verificar, lo protegemos por seguridad
            return True, "No se pudo verificar el archivo"

    def scan(
        self,
        folder: Path,
        include_subfolders: bool = True,
        include_hidden: bool = False,
        clean_temp: bool = True,
        clean_recycle: bool = True,
        clean_cache: bool = True,
        clean_empty: bool = True,
        clean_duplicates: bool = False,
        clean_large: bool = False,
        clean_small: bool = False,
        clean_thumbnails: bool = False,
        clean_logs: bool = False,
        clean_backup: bool = False,
        clean_windows_temp: bool = False,
        clean_downloads: bool = False,
        large_size_mb: int = 100,
        small_size_kb: int = 10,
        logs_days_old: int = 30,
        downloads_days_old: int = 30,
        progress_callback=None
    ) -> List[Dict]:
        """
        Escanea el sistema en busca de archivos a limpiar.
        """
        self.cancel_requested = False
        self.is_running = True
        self.files_to_clean = []

        # Inicio
        if progress_callback:
            progress_callback(0, 100, "Iniciando escaneo...")

        # 1. Papelera de reciclaje
        if clean_recycle:
            self._scan_recycle_bin()
            if progress_callback:
                progress_callback(10, 100, f"🗑️ Papelera: {len(self.files_to_clean)} archivos")

        # 2. Archivos temporales del sistema
        if clean_temp:
            self._scan_temp_files()
            if progress_callback:
                progress_callback(20, 100, f"📁 Temp sistema: {len(self.files_to_clean)} archivos")

        # 3. Caché de navegadores
        if clean_cache:
            self._scan_cache_files()
            if progress_callback:
                progress_callback(25, 100, f"🌐 Caché navegadores: {len(self.files_to_clean)} archivos")

        # 4. Miniaturas
        if clean_thumbnails:
            self._scan_thumbnails()
            if progress_callback:
                progress_callback(30, 100, f"🖼️ Miniaturas: {len(self.files_to_clean)} archivos")

        # 5. Archivos temporales de Windows
        if clean_windows_temp:
            self._scan_windows_temp()
            if progress_callback:
                progress_callback(35, 100, f"📦 Temp Windows: {len(self.files_to_clean)} archivos")

        # 6. Archivos de respaldo
        if clean_backup:
            self._scan_backup_files(folder, include_subfolders, include_hidden)
            if progress_callback:
                progress_callback(40, 100, f"💾 Respaldo (.bak,.tmp,.old): {len(self.files_to_clean)} archivos")

        # 7. Archivos vacíos
        if clean_empty:
            self._scan_empty_files(folder, include_subfolders, include_hidden)
            if progress_callback:
                progress_callback(50, 100, f"📄 Archivos vacíos: {len(self.files_to_clean)} archivos")

        # 8. Archivos pequeños
        if clean_small:
            self._scan_small_files(folder, include_subfolders, include_hidden, small_size_kb)
            if progress_callback:
                progress_callback(60, 100, f"📄 Archivos pequeños (<{small_size_kb}KB): {len(self.files_to_clean)} archivos")

        # 9. Archivos grandes
        if clean_large:
            self._scan_large_files(folder, include_subfolders, include_hidden, large_size_mb)
            if progress_callback:
                progress_callback(70, 100, f"📦 Archivos grandes (>{large_size_mb}MB): {len(self.files_to_clean)} archivos")

        # 10. Archivos .log antiguos
        if clean_logs:
            self._scan_logs(folder, include_subfolders, include_hidden, logs_days_old)
            if progress_callback:
                progress_callback(80, 100, f"📁 Logs antiguos ({logs_days_old}+ días): {len(self.files_to_clean)} archivos")

        # 11. Descargas antiguas
        if clean_downloads:
            self._scan_downloads(folder, include_subfolders, include_hidden, downloads_days_old)
            if progress_callback:
                progress_callback(90, 100, f"⬇️ Descargas antiguas ({downloads_days_old}+ días): {len(self.files_to_clean)} archivos")

        # 12. Archivos duplicados
        if clean_duplicates:
            self._scan_duplicate_files(folder, include_subfolders, include_hidden)
            if progress_callback:
                progress_callback(100, 100, f"🔄 Duplicados: {len(self.files_to_clean)} archivos")

        self.is_running = False

        # Final
        if progress_callback:
            progress_callback(100, 100, f"✅ Escaneo completado: {len(self.files_to_clean)} archivos")

        return self.files_to_clean

    def _scan_recycle_bin(self):
        """Escanea la papelera de reciclaje."""
        # Windows
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes

            try:
                # Usar SHQueryRecycleBin para obtener información
                # Esta es una implementación simplificada
                recycle_paths = [
                    Path(os.environ.get('SystemDrive', 'C:')) / '$Recycle.Bin',
                    Path(os.environ.get('SystemDrive', 'C:')) / 'RECYCLER',
                ]
                for path in recycle_paths:
                    if path.exists():
                        for item in path.rglob('*'):
                            if item.is_file():
                                # Obtener tamaño
                                try:
                                    size = item.stat().st_size
                                    self.files_to_clean.append({
                                        'path': str(item),
                                        'size': size,
                                        'size_mb': size / (1024 * 1024),
                                        'type': 'recycle',
                                        'description': 'Papelera de reciclaje'
                                    })
                                except:
                                    pass
            except:
                pass

        # Linux/Mac
        else:
            recycle_path = Path.home() / '.local' / 'share' / 'Trash'
            if recycle_path.exists():
                for item in recycle_path.rglob('*'):
                    if item.is_file():
                        try:
                            size = item.stat().st_size
                            self.files_to_clean.append({
                                'path': str(item),
                                'size': size,
                                'size_mb': size / (1024 * 1024),
                                'type': 'recycle',
                                'description': 'Papelera de reciclaje'
                            })
                        except:
                            pass

    def _scan_temp_files(self):
        """Escanea archivos temporales del sistema."""
        temp_dirs = [
            Path(tempfile.gettempdir()),
            Path(os.environ.get('TEMP', '')),
            Path(os.environ.get('TMP', '')),
        ]

        # Añadir directorios temporales del sistema en Windows
        if os.name == 'nt':
            temp_dirs.append(Path(os.environ.get('SystemRoot', 'C:\\Windows')) / 'Temp')

        for temp_dir in temp_dirs:
            if temp_dir and temp_dir.exists():
                try:
                    for item in temp_dir.rglob('*'):
                        if self.cancel_requested:
                            return
                        if item.is_file():
                            try:
                                # Solo archivos antiguos (más de 1 día)
                                if (datetime.now() - datetime.fromtimestamp(item.stat().st_mtime)).days > 1:
                                    size = item.stat().st_size
                                    self.files_to_clean.append({
                                        'path': str(item),
                                        'size': size,
                                        'size_mb': size / (1024 * 1024),
                                        'type': 'temp',
                                        'description': 'Archivo temporal del sistema'
                                    })
                            except:
                                pass
                except:
                    pass

    def _scan_cache_files(self):
        """Escanea cachés de navegadores y aplicaciones."""
        cache_dirs = []

        # Chrome
        if os.name == 'nt':
            chrome_cache = Path(os.environ.get('LOCALAPPDATA', '')) / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'Cache'
        else:
            chrome_cache = Path.home() / '.cache' / 'google-chrome'

        if chrome_cache.exists():
            cache_dirs.append(chrome_cache)

        # Firefox
        if os.name == 'nt':
            firefox_cache = Path(os.environ.get('APPDATA', '')) / 'Mozilla' / 'Firefox' / 'Profiles'
        else:
            firefox_cache = Path.home() / '.mozilla' / 'firefox'

        if firefox_cache.exists():
            for profile in firefox_cache.glob('*'):
                cache_dirs.append(profile / 'cache2')

        # Edge
        if os.name == 'nt':
            edge_cache = Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'Edge' / 'User Data' / 'Default' / 'Cache'
            if edge_cache.exists():
                cache_dirs.append(edge_cache)

        for cache_dir in cache_dirs:
            if cache_dir and cache_dir.exists():
                try:
                    for item in cache_dir.rglob('*'):
                        if self.cancel_requested:
                            return
                        if item.is_file():
                            try:
                                size = item.stat().st_size
                                self.files_to_clean.append({
                                    'path': str(item),
                                    'size': size,
                                    'size_mb': size / (1024 * 1024),
                                    'type': 'cache',
                                    'description': f'Caché: {cache_dir.parent.name}'
                                })
                            except:
                                pass
                except:
                    pass

    def _scan_empty_files(self, folder: Path, include_subfolders: bool, include_hidden: bool):
        """Escanea archivos vacíos y carpetas vacías."""
        if not folder.exists():
            return

        if include_subfolders:
            iterator = folder.rglob('*')
        else:
            iterator = folder.glob('*')

        for item in iterator:
            if self.cancel_requested:
                return

            # Ocultos
            if not include_hidden and item.name.startswith('.'):
                continue

            try:
                if item.is_file() and item.stat().st_size == 0:
                    self.files_to_clean.append({
                        'path': str(item),
                        'size': 0,
                        'size_mb': 0,
                        'type': 'empty',
                        'description': 'Archivo vacío'
                    })
                elif item.is_dir() and not any(item.iterdir()):
                    # Carpeta vacía
                    self.files_to_clean.append({
                        'path': str(item),
                        'size': 0,
                        'size_mb': 0,
                        'type': 'empty_dir',
                        'description': 'Carpeta vacía'
                    })
            except:
                pass

    def _scan_large_files(self, folder: Path, include_subfolders: bool, include_hidden: bool, large_size_mb: int):
        """Escanea archivos grandes."""
        if not folder.exists():
            return

        if include_subfolders:
            iterator = folder.rglob('*')
        else:
            iterator = folder.glob('*')

        for item in iterator:
            if self.cancel_requested:
                return

            if not include_hidden and item.name.startswith('.'):
                continue

            if item.is_file():
                try:
                    size = item.stat().st_size
                    size_mb = size / (1024 * 1024)
                    if size_mb >= large_size_mb:
                        self.files_to_clean.append({
                            'path': str(item),
                            'size': size,
                            'size_mb': size_mb,
                            'type': 'large',
                            'description': f'Archivo grande ({size_mb:.1f} MB)'
                        })
                except:
                    pass

    def _scan_duplicate_files(self, folder: Path, include_subfolders: bool, include_hidden: bool):
        """Escanea archivos duplicados."""
        if not folder.exists():
            return

        # Diccionario para almacenar archivos por tamaño y hash
        files_by_hash = {}

        if include_subfolders:
            iterator = folder.rglob('*')
        else:
            iterator = folder.glob('*')

        # Primera pasada: agrupar por tamaño
        files_by_size = {}
        for item in iterator:
            if self.cancel_requested:
                return

            if not include_hidden and item.name.startswith('.'):
                continue

            if item.is_file():
                try:
                    size = item.stat().st_size
                    # Si el tamaño es 0, es un archivo vacío (ya lo capturamos en empty)
                    if size > 0:
                        files_by_size.setdefault(size, []).append(item)
                except:
                    pass

        # Segunda pasada: comparar por hash dentro de cada grupo de tamaño
        for size, files in files_by_size.items():
            if len(files) < 2:
                continue

            for i in range(len(files)):
                if self.cancel_requested:
                    return

                file1 = files[i]
                try:
                    hash1 = self._get_file_hash(file1)
                    if hash1:
                        for j in range(i + 1, len(files)):
                            file2 = files[j]
                            try:
                                hash2 = self._get_file_hash(file2)
                                if hash1 == hash2:
                                    # Es duplicado
                                    self.files_to_clean.append({
                                        'path': str(file2),
                                        'size': size,
                                        'size_mb': size / (1024 * 1024),
                                        'type': 'duplicate',
                                        'description': f'Duplicado de: {file1.name}'
                                    })
                            except:
                                pass
                except:
                    pass

    def _scan_small_files(self, folder: Path, include_subfolders: bool, include_hidden: bool, small_size_kb: int = 10):
        """Escanea archivos pequeños (menos de X KB)."""
        if not folder.exists():
            return

        if include_subfolders:
            iterator = folder.rglob('*')
        else:
            iterator = folder.glob('*')

        for item in iterator:
            if self.cancel_requested:
                return

            if not include_hidden and item.name.startswith('.'):
                continue

            if item.is_file():
                try:
                    size = item.stat().st_size
                    size_kb = size / 1024
                    if 0 < size_kb <= small_size_kb:
                        self.files_to_clean.append({
                            'path': str(item),
                            'size': size,
                            'size_mb': size / (1024 * 1024),
                            'type': 'small',
                            'description': f'Archivo pequeño ({size_kb:.1f} KB)'
                        })
                except:
                    pass

    def _scan_thumbnails(self):
        """Escanea caché de miniaturas."""
        thumbnail_paths = []

        # Windows
        if os.name == 'nt':
            thumbnail_paths.append(Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'Windows' / 'Explorer')
            thumbnail_paths.append(Path(os.environ.get('APPDATA', '')) / 'Microsoft' / 'Windows' / 'Thumbcache')

        # Linux
        else:
            thumbnail_paths.append(Path.home() / '.cache' / 'thumbnails')
            thumbnail_paths.append(Path.home() / '.thumbnails')

        for thumb_path in thumbnail_paths:
            if thumb_path and thumb_path.exists():
                try:
                    for item in thumb_path.rglob('*'):
                        if self.cancel_requested:
                            return
                        if item.is_file():
                            try:
                                size = item.stat().st_size
                                self.files_to_clean.append({
                                    'path': str(item),
                                    'size': size,
                                    'size_mb': size / (1024 * 1024),
                                    'type': 'thumbnails',
                                    'description': 'Miniatura'
                                })
                            except:
                                pass
                except:
                    pass

    def _scan_logs(self, folder: Path, include_subfolders: bool, include_hidden: bool, days_old: int = 30):
        """Escanea archivos de log antiguos."""
        if not folder.exists():
            return

        if include_subfolders:
            iterator = folder.rglob('*')
        else:
            iterator = folder.glob('*')

        # Extensiones de log
        log_extensions = {'.log', '.txt'}

        for item in iterator:
            if self.cancel_requested:
                return

            if not include_hidden and item.name.startswith('.'):
                continue

            if item.is_file() and item.suffix.lower() in log_extensions:
                try:
                    # Verificar si es antiguo (más de X días)
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if (datetime.now() - mtime).days > days_old:
                        size = item.stat().st_size
                        self.files_to_clean.append({
                            'path': str(item),
                            'size': size,
                            'size_mb': size / (1024 * 1024),
                            'type': 'logs',
                            'description': f'Log antiguo ({days_old}+ días)'
                        })
                except:
                    pass

    def _scan_backup_files(self, folder: Path, include_subfolders: bool, include_hidden: bool):
        """Escanea archivos de respaldo (.bak, .tmp, .old)."""
        if not folder.exists():
            return

        backup_extensions = {'.bak', '.tmp', '.old', '.backup', '.~'}

        if include_subfolders:
            iterator = folder.rglob('*')
        else:
            iterator = folder.glob('*')

        for item in iterator:
            if self.cancel_requested:
                return

            if not include_hidden and item.name.startswith('.'):
                continue

            if item.is_file() and item.suffix.lower() in backup_extensions:
                try:
                    size = item.stat().st_size
                    self.files_to_clean.append({
                        'path': str(item),
                        'size': size,
                        'size_mb': size / (1024 * 1024),
                        'type': 'backup',
                        'description': f'Archivo de respaldo ({item.suffix})'
                    })
                except:
                    pass

    def _scan_windows_temp(self):
        """Escanea archivos temporales específicos de Windows."""
        if os.name != 'nt':
            return

        windows_temp_dirs = [
            Path(os.environ.get('SystemRoot', 'C:\\Windows')) / 'Prefetch',
            Path(os.environ.get('SystemRoot', 'C:\\Windows')) / 'Temp',
            Path(os.environ.get('SystemRoot', 'C:\\Windows')) / 'SoftwareDistribution' / 'Download',
        ]

        for temp_dir in windows_temp_dirs:
            if temp_dir and temp_dir.exists():
                try:
                    for item in temp_dir.rglob('*'):
                        if self.cancel_requested:
                            return
                        if item.is_file():
                            try:
                                size = item.stat().st_size
                                self.files_to_clean.append({
                                    'path': str(item),
                                    'size': size,
                                    'size_mb': size / (1024 * 1024),
                                    'type': 'windows_temp',
                                    'description': 'Archivo temporal de Windows'
                                })
                            except:
                                pass
                except:
                    pass

    def _scan_downloads(self, folder: Path, include_subfolders: bool, include_hidden: bool, days_old: int = 30):
        """Escanea archivos antiguos en la carpeta de Descargas."""
        downloads_path = Path.home() / 'Downloads' if os.name == 'nt' else Path.home() / 'Descargas'
        
        if not downloads_path.exists() or downloads_path == folder:
            return

        if include_subfolders:
            iterator = downloads_path.rglob('*')
        else:
            iterator = downloads_path.glob('*')

        for item in iterator:
            if self.cancel_requested:
                return

            if not include_hidden and item.name.startswith('.'):
                continue

            if item.is_file():
                try:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if (datetime.now() - mtime).days > days_old:
                        size = item.stat().st_size
                        self.files_to_clean.append({
                            'path': str(item),
                            'size': size,
                            'size_mb': size / (1024 * 1024),
                            'type': 'downloads',
                            'description': f'Descarga antigua ({days_old}+ días)'
                        })
                except:
                    pass

    def _get_file_hash(self, file_path: Path, chunk_size: int = 8192) -> Optional[str]:
        """Calcula el hash MD5 de un archivo."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return None

    def clean(self, files_to_clean: List[Dict], progress_callback=None) -> Dict:
        """
        Elimina los archivos seleccionados, protegiendo los críticos del sistema.
        """
        self.cancel_requested = False
        self.is_running = True
        self.cleaned_files = []
        self.errors = []
        self.protected_skipped = []  # <--- NUEVO: archivos protegidos saltados

        total = len(files_to_clean)
        processed = 0

        if progress_callback:
            progress_callback(0, total)

        for file_info in files_to_clean:
            if self.cancel_requested:
                self.is_running = False
                return {
                    "cleaned": len(self.cleaned_files),
                    "errors": len(self.errors),
                    "protected": len(self.protected_skipped),  # <--- NUEVO
                    "cancelled": True,
                    "total": total
                }

            try:
                path = Path(file_info['path'])
                
                # ---- VERIFICAR PROTECCIÓN ----
                is_protected, reason = self._is_protected(path)
                if is_protected:
                    self.protected_skipped.append((str(path), reason))
                    processed += 1
                    if progress_callback:
                        progress_callback(processed, total)
                    continue  # Saltar este archivo

                if path.exists():
                    if path.is_file():
                        path.unlink()
                    else:
                        shutil.rmtree(path)
                    self.cleaned_files.append(file_info)
                else:
                    self.errors.append((file_info['path'], "Archivo no encontrado"))

            except PermissionError as e:
                self.errors.append((file_info['path'], f"Permiso denegado: {str(e)}"))
            except Exception as e:
                self.errors.append((file_info['path'], str(e)))

            processed += 1
            if progress_callback:
                progress_callback(processed, total)

        self.is_running = False

        return {
            "cleaned": len(self.cleaned_files),
            "errors": len(self.errors),
            "protected": len(self.protected_skipped),  # <--- NUEVO
            "cancelled": False,
            "total": total,
            "details": self.cleaned_files,
            "error_details": self.errors,
            "protected_details": self.protected_skipped  # <--- NUEVO
        }

    def cancel(self):
        """Solicita la cancelación."""
        self.cancel_requested = True

    def get_summary(self, files: List[Dict]) -> Dict:
        """Obtiene un resumen de los archivos escaneados."""
        total_size = sum(f.get('size', 0) for f in files)
        total_files = len(files)

        types = {}
        for f in files:
            tipo = f.get('type', 'other')
            types[tipo] = types.get(tipo, 0) + 1

        return {
            'total_files': total_files,
            'total_size': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'total_size_gb': total_size / (1024 * 1024 * 1024),
            'types': types
        }
