"""
Servicio para desorganizar archivos.
"""
from pathlib import Path
from typing import List, Optional

from .file_handler import FileHandler
from ..config import settings


class Desorganizer:
    """
    Desorganiza archivos: mueve/copia todos los archivos desde Fotos/, Videos/ o Música/
    a una sola carpeta destino, eliminando las carpetas vacías.
    """

    def __init__(self):
        self.file_handler = FileHandler()
        self.excluded_dirs = {settings.PHOTOS_FOLDER, settings.VIDEOS_FOLDER, settings.DOCUMENTS_FOLDER}
        self.cancel_requested = False
        self.is_running = False
        

    def desorganize(
        self,
        source_dir: Path,
        dest_dir: Path,
        operation_mode: str = "move",
        search_subfolders: bool = True,
        mode: str = "all",  # "all", "photos_videos", "music"
        progress_callback=None
    ) -> dict:
        """
        Desorganiza archivos desde source_dir a dest_dir.

        Args:
            source_dir: Directorio origen
            dest_dir: Directorio destino
            operation_mode: "move" o "copy"
            search_subfolders: Buscar recursivamente
            mode: "all" (todo), "photos_videos" (Fotos/Videos), "music" (Música)
            progress_callback: Callback para progreso
        """
        self.cancel_requested = False
        self.is_running = True
        self.file_handler.reset()

        try:
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Obtener archivos según el modo
            files = self._get_files_to_desorganize(source_dir, search_subfolders, mode)

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

                if operation_mode == "move":
                    success = self.file_handler.safe_move(file_path, dest_dir)
                else:
                    success = self.file_handler.safe_copy(file_path, dest_dir)

                processed += 1

                if progress_callback:
                    progress_callback(processed, total)

            # Eliminar carpetas vacías
            self._remove_empty_folders(source_dir)

            self.is_running = False
            return self.file_handler.get_summary()

        except Exception as e:
            self.is_running = False
            raise e

    def _get_files_to_desorganize(
        self,
        source_dir: Path,
        search_subfolders: bool,
        mode: str = "all"
    ) -> List[Path]:
        """
        Obtiene todos los archivos según el modo seleccionado.
        """
        files = []

        # Extensiones de música
        music_extensions = {
            '.mp3', '.flac', '.wav', '.aac', '.m4a',
            '.ogg', '.wma', '.opus', '.aiff', '.alac'
        }

        # Definir carpetas a buscar según modo
        if mode == "photos_videos":
            categories = [settings.PHOTOS_FOLDER, settings.VIDEOS_FOLDER]
            
            for category in categories:
                category_path = source_dir / category
                if not category_path.exists():
                    continue
                if search_subfolders:
                    iterator = category_path.rglob("*")
                else:
                    iterator = category_path.glob("*")
                for item in iterator:
                    if item.is_file():
                        files.append(item)

        elif mode == "music":
            # Buscar en carpeta Música/ si existe
            music_folder = source_dir / "Música"
            if music_folder.exists():
                if search_subfolders:
                    iterator = music_folder.rglob("*")
                else:
                    iterator = music_folder.glob("*")
                for item in iterator:
                    if item.is_file() and item.suffix.lower() in music_extensions:
                        files.append(item)

            # Buscar música suelta en el resto del directorio
            excluded = {settings.PHOTOS_FOLDER, settings.VIDEOS_FOLDER, "Música", settings.DOCUMENTS_FOLDER}
            if search_subfolders:
                iterator = source_dir.rglob("*")
            else:
                iterator = source_dir.glob("*")

            for item in iterator:
                if item.is_file() and item.suffix.lower() in music_extensions:
                    parts = item.parts
                    is_excluded = False
                    for exc in excluded:
                        if exc in parts:
                            is_excluded = True
                            break
                    if not is_excluded:
                        files.append(item)

        elif mode == "documents":  # <--- NUEVO
            # Buscar en carpeta Documentos/
            documents_folder = source_dir / settings.DOCUMENTS_FOLDER
            if documents_folder.exists():
                if search_subfolders:
                    iterator = documents_folder.rglob("*")
                else:
                    iterator = documents_folder.glob("*")
                for item in iterator:
                    if item.is_file():
                        files.append(item)

            # Buscar documentos sueltos en el resto del directorio
            excluded = {settings.PHOTOS_FOLDER, settings.VIDEOS_FOLDER, "Música", settings.DOCUMENTS_FOLDER}
            if search_subfolders:
                iterator = source_dir.rglob("*")
            else:
                iterator = source_dir.glob("*")

            for item in iterator:
                if item.is_file():
                    parts = item.parts
                    is_excluded = False
                    for exc in excluded:
                        if exc in parts:
                            is_excluded = True
                            break
                    if not is_excluded:
                        # Verificar si es un documento por extensión
                        ext = item.suffix.lower()
                        if ext in settings.DOCUMENT_EXTENSIONS:
                            files.append(item)

        else:  # "all"
            # Buscar en todas las carpetas organizadas
            categories = [
                settings.PHOTOS_FOLDER,
                settings.VIDEOS_FOLDER,
                "Música",
                settings.DOCUMENTS_FOLDER
            ]
            
            for category in categories:
                category_path = source_dir / category
                if not category_path.exists():
                    continue
                if search_subfolders:
                    iterator = category_path.rglob("*")
                else:
                    iterator = category_path.glob("*")
                for item in iterator:
                    if item.is_file():
                        files.append(item)

            # Buscar archivos sueltos en la raíz
            excluded = {settings.PHOTOS_FOLDER, settings.VIDEOS_FOLDER, "Música", settings.DOCUMENTS_FOLDER}
            if search_subfolders:
                iterator = source_dir.rglob("*")
            else:
                iterator = source_dir.glob("*")

            for item in iterator:
                if item.is_file():
                    parts = item.parts
                    is_excluded = False
                    for exc in excluded:
                        if exc in parts:
                            is_excluded = True
                            break
                    if not is_excluded:
                        files.append(item)

        return files

    def _remove_empty_folders(self, root_dir: Path):
        """Elimina todas las carpetas vacías dentro del directorio raíz."""
        for dirpath in sorted(root_dir.rglob("*"), reverse=True):
            if dirpath.is_dir() and not any(dirpath.iterdir()):
                try:
                    dirpath.rmdir()
                except OSError:
                    pass

    def cancel(self):
        """Solicita la cancelación de la operación."""
        self.cancel_requested = True
