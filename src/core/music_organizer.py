"""
Servicio para organizar archivos de música.
"""
from pathlib import Path
from typing import List, Dict, Optional

from .music_parser import MusicParser
from .file_handler import FileHandler


class MusicOrganizer:
    """Organiza archivos de música por Artista/Álbum/Año."""

    def __init__(self):
        self.file_handler = FileHandler()
        self.cancel_requested = False
        self.is_running = False

    def organize(
        self,
        source_dir: Path,
        dest_dir: Path,
        use_metadata: bool = True,
        parse_filename: bool = True,
        search_subfolders: bool = True,
        operation_mode: str = "move",
        order: str = "año_album_artista",
        progress_callback=None
    ) -> Dict:
        """
        Organiza archivos de música.

        Args:
            source_dir: Directorio origen
            dest_dir: Directorio destino base
            use_metadata: Usar metadatos ID3
            parse_filename: Analizar nombre del archivo
            search_subfolders: Buscar en subcarpetas
            operation_mode: "move" o "copy"
            progress_callback: Callback para progreso

        Returns:
            Resumen de la operación
        """
        self.cancel_requested = False
        self.is_running = True
        self.file_handler.reset()

        try:
            # Extensiones de audio soportadas
            audio_extensions = {
                '.mp3', '.flac', '.wav', '.aac', '.m4a',
                '.ogg', '.wma', '.opus', '.aiff', '.alac'
            }

            # Obtener archivos
            files = self._get_audio_files(source_dir, audio_extensions, search_subfolders)

            total = len(files)
            processed = 0

            if progress_callback:
                progress_callback(0, total)

            for file_path in files:
                if self.cancel_requested:
                    self.is_running = False
                    return {
                        "processed": processed,
                        "errors": len(self.file_handler.errors),
                        "cancelled": True,
                        "total": total
                    }

                # Extraer información
                info = MusicParser.extract_info(file_path, use_metadata)

                # Si no hay título y no se puede parsear, usar nombre
                if not info.get("titulo"):
                    info["titulo"] = file_path.stem

                # Generar ruta destino
                dest_path = MusicParser.get_destination_path(dest_dir, info, order)

                # Mover o copiar
                if operation_mode == "move":
                    self.file_handler.safe_move(file_path, dest_path)
                else:
                    self.file_handler.safe_copy(file_path, dest_path)

                processed += 1

                if progress_callback:
                    progress_callback(processed, total)

            self.is_running = False
            return self.file_handler.get_summary()

        except Exception as e:
            self.is_running = False
            raise e

    def _get_audio_files(
        self,
        source_dir: Path,
        extensions: set,
        search_subfolders: bool
    ) -> List[Path]:
        """Obtiene archivos de audio del directorio."""
        files = []

        if search_subfolders:
            iterator = source_dir.rglob("*")
        else:
            iterator = source_dir.glob("*")

        for item in iterator:
            if item.is_file() and item.suffix.lower() in extensions:
                files.append(item)

        return files

    def cancel(self):
        """Solicita la cancelación."""
        self.cancel_requested = True
