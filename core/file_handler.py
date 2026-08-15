import os
import shutil
from pathlib import Path



class FileHandler:
    """Maneja operaciones con archivos - VERSIÓN OPTIMIZADA Y RÁPIDA"""

    def __init__(self):
        self.stats = {
            "moved": 0,
            "copied": 0,
            "renamed": 0,
            "errors": 0,
            "created_dirs": 0
        }
        self.log_callback = None

    def set_log_callback(self, callback):
        self.log_callback = callback

    def _log(self, message):
        if self.log_callback:
            self.log_callback(message)

    def move_file(self, source, destination, operation="move"):
        """Mover o copiar un archivo - VERSIÓN RÁPIDA"""
        source = Path(source)
        destination = Path(destination)

        # Crear directorio destino si no existe
        if not destination.parent.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            self.stats["created_dirs"] += 1

        # Verificar si el archivo destino ya existe
        if destination.exists():
            destination = self._handle_duplicate(destination)

        try:
            # ============================================
            # MOVER: Usar shutil.move (más rápido que copiar+eliminar)
            # ============================================
            if operation == "move" or operation == "mover":
                # Intentar mover directamente (es más rápido)
                try:
                    shutil.move(str(source), str(destination))
                    self.stats["moved"] += 1
                    return destination
                except Exception as e:
                    # Si falla (ej: diferentes discos), usar método alternativo
                    self._log(
                        f"     ⚠️ shutil.move falló, usando copia+eliminación: {e}")

                    # Copiar
                    shutil.copy2(str(source), str(destination))

                    # Verificar copia
                    if destination.exists():
                        # Eliminar original (rápido)
                        self._fast_delete(str(source))
                        self.stats["moved"] += 1
                    else:
                        raise Exception("La copia falló")

            # ============================================
            # COPIAR
            # ============================================
            else:
                shutil.copy2(str(source), str(destination))
                self.stats["copied"] += 1

            return destination

        except Exception as e:
            self.stats["errors"] += 1
            raise Exception(f"Error en {source.name}: {str(e)}")

    def _fast_delete(self, file_path):
        """Eliminación rápida - solo intenta los métodos más efectivos"""
        file_path = Path(file_path)

        if not file_path.exists():
            return

        # MÉTODO 1: os.remove (el más rápido)
        try:
            os.remove(str(file_path))
            return
        except BaseException:
            pass

        # MÉTODO 2: Cambiar atributos y eliminar
        try:
            os.chmod(str(file_path), 0o777)
            os.remove(str(file_path))
            return
        except BaseException:
            pass

        # MÉTODO 3: Si falla, no esperamos más, lo dejamos para después
        # (No usamos subprocess ni PowerShell porque son lentos)
        pass

    def _handle_duplicate(self, file_path):
        """Manejar archivos duplicados"""
        file_path = Path(file_path)
        counter = 1
        base_name = file_path.stem
        extension = file_path.suffix
        parent = file_path.parent

        while True:
            new_name = f"{base_name} ({counter}){extension}"
            new_path = parent / new_name
            if not new_path.exists():
                self.stats["renamed"] += 1
                return new_path
            counter += 1

    def get_stats(self):
        return self.stats.copy()

    def reset_stats(self):
        self.stats = {
            "moved": 0,
            "copied": 0,
            "renamed": 0,
            "errors": 0,
            "created_dirs": 0
        }
