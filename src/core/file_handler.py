"""
Operaciones de sistema de archivos seguras.
"""
import shutil
from pathlib import Path
from typing import List, Tuple


class FileHandler:
    """Maneja operaciones de archivo de forma segura."""
    
    def __init__(self):
        self.errors: List[Tuple[Path, str]] = []
        self.processed_files: List[Tuple[Path, Path, str]] = []  # (origen, destino, operación)
    
    def safe_move(self, source: Path, destination_dir: Path) -> bool:
        """
        Mueve un archivo de forma segura, evitando sobrescribir.
        
        Args:
            source: Ruta del archivo origen
            destination_dir: Directorio de destino
            
        Returns:
            True si se movió correctamente, False si hubo error
        """
        try:
            # Crear directorio destino si no existe
            destination_dir.mkdir(parents=True, exist_ok=True)
            
            # Construir ruta final
            destination = destination_dir / source.name
            
            # Si ya existe, añadir sufijo
            if destination.exists():
                destination = self._get_unique_path(destination)
            
            # Mover archivo
            shutil.move(str(source), str(destination))
            self.processed_files.append((source, destination, "move"))
            return True
            
        except Exception as e:
            self.errors.append((source, str(e)))
            return False
    
    def safe_copy(self, source: Path, destination_dir: Path) -> bool:
        """
        Copia un archivo de forma segura, evitando sobrescribir.
        
        Args:
            source: Ruta del archivo origen
            destination_dir: Directorio de destino
            
        Returns:
            True si se copió correctamente, False si hubo error
        """
        try:
            # Crear directorio destino si no existe
            destination_dir.mkdir(parents=True, exist_ok=True)
            
            # Construir ruta final
            destination = destination_dir / source.name
            
            # Si ya existe, añadir sufijo
            if destination.exists():
                destination = self._get_unique_path(destination)
            
            # Copiar archivo
            shutil.copy2(str(source), str(destination))
            self.processed_files.append((source, destination, "copy"))
            return True
            
        except Exception as e:
            self.errors.append((source, str(e)))
            return False
    
    def _get_unique_path(self, path: Path) -> Path:
        """Genera un nombre único si el archivo ya existe."""
        counter = 1
        stem = path.stem
        suffix = path.suffix
        
        while path.exists():
            new_name = f"{stem}_{counter}{suffix}"
            path = path.parent / new_name
            counter += 1
        
        return path
    
    def get_summary(self) -> dict:
        """Retorna un resumen de la operación."""
        return {
            "processed": len(self.processed_files),
            "errors": len(self.errors),
            "files": self.processed_files,
            "error_details": self.errors
        }
    
    def reset(self):
        """Reinicia los contadores de la operación."""
        self.errors.clear()
        self.processed_files.clear()