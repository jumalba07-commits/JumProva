"""
Modelos de datos para el organizador de archivos.
"""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class FileItem:
    """Representa un archivo a organizar."""
    path: Path
    category: str
    date: datetime
    size: int

    @property
    def extension(self) -> str:
        return self.path.suffix.lower()

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def destination_folder(self) -> Path:
        """Retorna la ruta de destino para este archivo."""
        from ..config import settings
        
        if self.category == settings.DOCUMENTS_FOLDER:
            # Documentos: Documentos/extension_sin_punto/
            ext = self.path.suffix[1:].lower() if self.path.suffix else "sin_extension"
            return Path(self.category) / ext
        else:
            # Fotos y Videos: Categoría/AÑO/MES/DÍA/
            return Path(self.category) / self.date.strftime("%Y") / self.date.strftime("%m") / self.date.strftime("%d")
