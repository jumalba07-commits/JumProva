"""
Servicio principal de organización de archivos.
"""
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set
import threading

from .file_handler import FileHandler
from .models import FileItem
from ..config import settings


class PhotoVideoOrganizer:
    """
    Organiza fotos, videos y documentos.
    """

    def __init__(self):
        self.file_handler = FileHandler()
        self.excluded_dirs = {settings.PHOTOS_FOLDER, settings.VIDEOS_FOLDER, settings.DOCUMENTS_FOLDER}
        self.cancel_requested = False
        self.is_running = False

    def organize(
        self,
        source_dir: Path,
        dest_dir: Path,
        organize_photos: bool = True,
        organize_videos: bool = True,
        organize_documents: bool = False,
        operation_mode: str = "move",
        search_subfolders: bool = True,
        progress_callback=None
    ) -> dict:
        """
        Organiza archivos desde source_dir a dest_dir.
        """
        self.cancel_requested = False
        self.is_running = True
        self.file_handler.reset()

        try:
            # Crear carpetas de destino
            self._create_destination_folders(dest_dir, organize_photos, organize_videos, organize_documents)

            # Obtener archivos
            files = self._get_files_to_organize(
                source_dir, dest_dir,
                organize_photos,
                organize_videos,
                organize_documents,
                search_subfolders
            )

            total = len(files)
            processed = 0

            if progress_callback:
                progress_callback(0, total)

            for file_item in files:
                if self.cancel_requested:
                    self.is_running = False
                    return {
                        "processed": processed,
                        "errors": len(self.file_handler.errors),
                        "cancelled": True,
                        "total": total
                    }

                destination_base = dest_dir / file_item.destination_folder

                if operation_mode == "move":
                    self.file_handler.safe_move(file_item.path, destination_base)
                else:
                    self.file_handler.safe_copy(file_item.path, destination_base)

                processed += 1

                if progress_callback:
                    progress_callback(processed, total)

            self.is_running = False
            return self.file_handler.get_summary()

        except Exception as e:
            self.is_running = False
            raise e

    def _create_destination_folders(
        self,
        dest_dir: Path,
        include_photos: bool,
        include_videos: bool,
        include_documents: bool
    ):
        """Crea las carpetas base de destino."""
        if include_photos:
            (dest_dir / settings.PHOTOS_FOLDER).mkdir(parents=True, exist_ok=True)
        if include_videos:
            (dest_dir / settings.VIDEOS_FOLDER).mkdir(parents=True, exist_ok=True)
        if include_documents:
            (dest_dir / settings.DOCUMENTS_FOLDER).mkdir(parents=True, exist_ok=True)

    def _get_files_to_organize(
        self,
        source_dir: Path,
        dest_dir: Path,
        include_photos: bool,
        include_videos: bool,
        include_documents: bool,
        search_subfolders: bool = True
    ) -> List[FileItem]:
        """
        Obtiene lista de archivos a organizar según extensión.
        """
        files = []
        extensions = set()

        if include_photos:
            extensions.update(settings.PHOTO_EXTENSIONS)
        if include_videos:
            extensions.update(settings.VIDEO_EXTENSIONS)
        if include_documents:
            extensions.update(settings.DOCUMENT_EXTENSIONS)

        if search_subfolders:
            iterator = source_dir.rglob("*")
        else:
            iterator = source_dir.glob("*")

        for file_path in iterator:
            if self._is_in_excluded_folder(file_path):
                continue

            if file_path.is_file() and file_path.suffix.lower() in extensions:
                ext = file_path.suffix.lower()
                
                # Determinar categoría
                if ext in settings.PHOTO_EXTENSIONS:
                    category = settings.PHOTOS_FOLDER
                elif ext in settings.VIDEO_EXTENSIONS:
                    category = settings.VIDEOS_FOLDER
                else:
                    category = settings.DOCUMENTS_FOLDER

                date = self._extract_date(file_path)

                file_item = FileItem(
                    path=file_path,
                    category=category,
                    date=date,
                    size=file_path.stat().st_size
                )
                files.append(file_item)

        return files

    def _is_in_excluded_folder(self, path: Path) -> bool:
        """Verifica si el archivo está dentro de una carpeta excluida."""
        parts = path.parts
        for excluded in self.excluded_dirs:
            if excluded in parts:
                return True
        return False

    def _extract_date(self, file_path: Path) -> datetime:
        """Extrae la fecha de un archivo."""
        mtime = file_path.stat().st_mtime
        return datetime.fromtimestamp(mtime)

    def cancel(self):
        """Solicita la cancelación."""
        self.cancel_requested = True
