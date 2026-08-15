import os
import shutil
from pathlib import Path



class FileCleaner:
    """Detecta y maneja archivos basura (miniaturas, temporales, corruptos)"""

    def __init__(self):
        # Extensiones de archivos temporales/basura
        self.temp_extensions = {
            '.tmp', '.temp', '.log', '.cache', '.thumb', '.thumbnail',
            '.ini', '.cfg', '.config', '.lock', '.pid'
        }

        # Nombres comunes de miniaturas
        self.thumb_names = [
            'thumbs.db', 'thumb.db', '.thumbnails',
            'desktop.ini', 'folder.jpg', 'albumartsmall.jpg'
        ]

        # Archivos de sistema de Windows
        self.windows_temp = [
            '$recycle.bin', 'system volume information',
            'recycler', 'msocache'
        ]

        self.stats = {
            "deleted": 0,
            "moved": 0,
            "errors": 0,
            "total_detected": 0
        }

    def scan_for_junk(self, directory, min_size_kb=4, include_subfolders=True):
        """
        Escanea una carpeta en busca de archivos basura

        Args:
            directory: Carpeta a escanear
            min_size_kb: Tamaño mínimo en KB para considerar basura (4KB por defecto)
            include_subfolders: Incluir subcarpetas
        """
        directory = Path(directory)
        junk_files = []

        # Obtener archivos
        if include_subfolders:
            files = [f for f in directory.rglob("*") if f.is_file()]
        else:
            files = [f for f in directory.iterdir() if f.is_file()]

        for file_path in files:
            try:
                # Verificar si es basura
                if self._is_junk_file(file_path, min_size_kb):
                    junk_files.append({
                        "path": file_path,
                        "size_kb": file_path.stat().st_size / 1024,
                        "reason": self._get_junk_reason(file_path, min_size_kb),
                        "extension": file_path.suffix.lower()
                    })
            except BaseException:
                continue

        self.stats["total_detected"] = len(junk_files)
        return junk_files

    def _is_junk_file(self, file_path, min_size_kb):
        """Determina si un archivo es basura"""

        # 1. Verificar tamaño
        try:
            size_kb = file_path.stat().st_size / 1024
            if size_kb <= min_size_kb:
                return True
        except BaseException:
            pass

        # 2. Verificar extensiones temporales
        extension = file_path.suffix.lower()
        if extension in self.temp_extensions:
            return True

        # 3. Verificar nombres de miniaturas
        name = file_path.name.lower()
        for thumb_name in self.thumb_names:
            if thumb_name in name:
                return True

        # 4. Verificar si es un archivo corrupto (no se puede abrir)
        if self._is_corrupt_file(file_path):
            return True

        # 5. Verificar archivos vacíos
        try:
            if file_path.stat().st_size == 0:
                return True
        except BaseException:
            pass

        return False

    def _get_junk_reason(self, file_path, min_size_kb):
        """Obtener la razón por la que un archivo es considerado basura"""
        reasons = []

        # Tamaño
        try:
            size_kb = file_path.stat().st_size / 1024
            if size_kb <= min_size_kb:
                reasons.append(f"Tamaño pequeño ({size_kb:.1f}KB)")
        except BaseException:
            pass

        # Extensión temporal
        extension = file_path.suffix.lower()
        if extension in self.temp_extensions:
            reasons.append(f"Extensión temporal ({extension})")

        # Nombre de miniatura
        name = file_path.name.lower()
        for thumb_name in self.thumb_names:
            if thumb_name in name:
                reasons.append(f"Miniatura ({thumb_name})")
                break

        # Archivo corrupto
        if self._is_corrupt_file(file_path):
            reasons.append("Archivo corrupto o dañado")

        # Archivo vacío
        try:
            if file_path.stat().st_size == 0:
                reasons.append("Archivo vacío")
        except BaseException:
            pass

        return ", ".join(reasons) if reasons else "Archivo basura"

    def _is_corrupt_file(self, file_path):
        """Verificar si un archivo está corrupto (no se puede abrir)"""
        try:
            # Intentar abrir el archivo para lectura
            with open(file_path, 'rb') as f:
                # Leer solo los primeros bytes para verificar
                f.read(1024)
            return False
        except BaseException:
            return True

    def delete_files(self, junk_files, confirm=True):
        """Eliminar archivos basura"""
        deleted = []
        errors = []

        for file_info in junk_files:
            file_path = file_info["path"]
            try:
                os.remove(str(file_path))
                deleted.append(str(file_path))
                self.stats["deleted"] += 1
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")
                self.stats["errors"] += 1

        return {"deleted": deleted, "errors": errors}

    def move_to_recycle(self, junk_files, destination_folder="Basura"):
        """Mover archivos basura a una carpeta específica"""
        moved = []
        errors = []

        # Crear carpeta de basura
        dest_dir = Path(destination_folder)
        dest_dir.mkdir(exist_ok=True)

        for file_info in junk_files:
            file_path = file_info["path"]
            try:
                # Crear subcarpeta por fecha
                from datetime import datetime
                date_folder = datetime.now().strftime("%Y-%m-%d")
                dest_path = dest_dir / date_folder / file_path.name

                # Manejar duplicados
                if dest_path.exists():
                    counter = 1
                    base = dest_path.stem
                    ext = dest_path.suffix
                    while True:
                        new_path = dest_path.parent / \
                            f"{base} ({counter}){ext}"
                        if not new_path.exists():
                            dest_path = new_path
                            break
                        counter += 1

                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(file_path), str(dest_path))
                moved.append(str(dest_path))
                self.stats["moved"] += 1
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")
                self.stats["errors"] += 1

        return {"moved": moved, "errors": errors}

    def get_stats(self):
        """Obtener estadísticas"""
        return self.stats.copy()

    def reset_stats(self):
        """Resetear estadísticas"""
        self.stats = {
            "deleted": 0,
            "moved": 0,
            "errors": 0,
            "total_detected": 0}

    def get_size_summary(self, directory):
        """Obtener resumen de tamaños de archivos"""
        directory = Path(directory)
        total_size = 0
        file_count = 0
        small_files = 0
        small_size = 0

        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    size = file_path.stat().st_size
                    total_size += size
                    file_count += 1

                    if size <= 4 * 1024:  # 4KB
                        small_files += 1
                        small_size += size
                except BaseException:
                    pass

        return {
            "total_files": file_count,
            "total_size_mb": total_size / (1024 * 1024),
            "small_files": small_files,
            "small_size_kb": small_size / 1024,
            "small_percentage": (small_files / file_count * 100) if file_count > 0 else 0
        }
