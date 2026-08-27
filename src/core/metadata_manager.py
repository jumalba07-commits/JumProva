"""
Gestión de metadatos de archivos de música.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from mutagen import File
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, TRCK
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


class MetadataManager:
    """Gestiona metadatos de archivos de música."""

    REQUIRED_FIELDS = ["artista", "album", "titulo", "año"]

    @staticmethod
    def get_metadata(file_path: Path) -> Dict:
        """
        Obtiene los metadatos de un archivo.
        """
        info = {
            "artista": "",
            "album": "",
            "titulo": "",
            "año": "",
            "genero": "",
            "numero": "",
            "archivo": str(file_path.name)
        }

        if not MUTAGEN_AVAILABLE:
            return info

        try:
            audio = File(file_path)
            if audio is None or not hasattr(audio, 'tags'):
                return info

            tags = audio.tags
            if not tags:
                return info

            # Título
            if 'TIT2' in tags:
                info["titulo"] = str(tags['TIT2'])
            # Artista
            if 'TPE1' in tags:
                info["artista"] = str(tags['TPE1'])
            # Álbum
            if 'TALB' in tags:
                info["album"] = str(tags['TALB'])
            # Año
            if 'TDRC' in tags:
                info["año"] = str(tags['TDRC'])[:4]
            # Género
            if 'TCON' in tags:
                info["genero"] = str(tags['TCON'])
            # Número de pista
            if 'TRCK' in tags:
                info["numero"] = str(tags['TRCK']).split('/')[0]

        except Exception:
            pass

        return info

    @staticmethod
    def save_metadata(file_path: Path, metadata: Dict) -> bool:
        """
        Guarda metadatos en un archivo.
        """
        if not MUTAGEN_AVAILABLE:
            return False

        try:
            audio = File(file_path)
            if audio is None:
                return False

            # Crear tags si no existen
            if not hasattr(audio, 'tags') or audio.tags is None:
                audio.add_tags()

            tags = audio.tags

            # Guardar cada campo
            if metadata.get("titulo"):
                tags['TIT2'] = TIT2(encoding=3, text=metadata["titulo"])
            if metadata.get("artista"):
                tags['TPE1'] = TPE1(encoding=3, text=metadata["artista"])
            if metadata.get("album"):
                tags['TALB'] = TALB(encoding=3, text=metadata["album"])
            if metadata.get("año"):
                tags['TDRC'] = TDRC(encoding=3, text=metadata["año"])
            if metadata.get("genero"):
                tags['TCON'] = TCON(encoding=3, text=metadata["genero"])
            if metadata.get("numero"):
                tags['TRCK'] = TRCK(encoding=3, text=metadata["numero"])

            audio.save()
            return True

        except Exception:
            return False

    @staticmethod
    def check_completeness(metadata: Dict) -> Tuple[bool, List[str]]:
        """
        Verifica si un archivo tiene todos los metadatos necesarios.
        """
        missing = []
        for field in MetadataManager.REQUIRED_FIELDS:
            if not metadata.get(field, "").strip():
                missing.append(field)

        return len(missing) == 0, missing

    @staticmethod
    def scan_folder(
        folder: Path,
        search_subfolders: bool = True
    ) -> List[Dict]:
        """
        Escanea una carpeta y devuelve metadatos de todos los archivos de música.
        """
        results = []
        music_extensions = {
            '.mp3', '.flac', '.wav', '.aac', '.m4a',
            '.ogg', '.wma', '.opus', '.aiff', '.alac'
        }

        if search_subfolders:
            iterator = folder.rglob("*")
        else:
            iterator = folder.glob("*")

        for item in iterator:
            if item.is_file() and item.suffix.lower() in music_extensions:
                metadata = MetadataManager.get_metadata(item)
                metadata["ruta"] = str(item)
                metadata["extension"] = item.suffix
                complete, missing = MetadataManager.check_completeness(metadata)
                metadata["completo"] = complete
                metadata["faltan"] = missing
                results.append(metadata)

        return results