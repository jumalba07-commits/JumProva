"""
Parseo de metadatos y nombres de archivos de música.
"""
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    from mutagen import File
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TRCK
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


class MusicParser:
    """Extrae información de archivos de música."""

    # Patrones para nombres de archivo
    PATTERNS = [
        # Artista - Título
        re.compile(r'^(?P<artista>.+?)\s*-\s*(?P<titulo>.+?)(?:\s*\((?P<año>\d{4})\))?$'),
        # Artista - Álbum - Título
        re.compile(r'^(?P<artista>.+?)\s*-\s*(?P<album>.+?)\s*-\s*(?P<titulo>.+?)$'),
        # Número - Título
        re.compile(r'^(?P<numero>\d+)\s*[-_]\s*(?P<titulo>.+?)$'),
        # Artista - Año - Título
        re.compile(r'^(?P<artista>.+?)\s*-\s*(?P<año>\d{4})\s*-\s*(?P<titulo>.+?)$'),
        # Título (Año)
        re.compile(r'^(?P<titulo>.+?)\s*\((?P<año>\d{4})\)$'),
        # Artista - Título (con extensión)
        re.compile(r'^(?P<artista>.+?)\s*[-_]\s*(?P<titulo>.+?)$'),
    ]

    @staticmethod
    def extract_metadata(file_path: Path) -> Optional[Dict]:
        """
        Extrae metadatos del archivo usando mutagen.
        """
        if not MUTAGEN_AVAILABLE:
            return None

        try:
            audio = File(file_path)
            if audio is None:
                return None

            info = {
                "artista": None,
                "album": None,
                "titulo": None,
                "año": None,
                "numero": None
            }

            # Intentar extraer ID3
            if hasattr(audio, 'tags'):
                tags = audio.tags
                if tags:
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
                    # Número de pista
                    if 'TRCK' in tags:
                        info["numero"] = str(tags['TRCK']).split('/')[0]
                    # Genero
                    if 'TCON' in tags:  # Género en ID3
                        info["genero"] = str(tags['TCON'])

            # Si no se encontraron metadatos, intentar con propiedades del archivo
            if not any(info.values()):
                return None

            return info

        except Exception:
            return None

    @staticmethod
    def parse_filename(file_path: Path) -> Dict:
        """
        Extrae información del nombre del archivo.
        """
        name = file_path.stem  # Sin extensión
        info = {
            "artista": None,
            "album": None,
            "titulo": None,
            "año": None,
            "numero": None
        }

        # Probar cada patrón
        for pattern in MusicParser.PATTERNS:
            match = pattern.match(name)
            if match:
                for key, value in match.groupdict().items():
                    if value and not info.get(key):
                        info[key] = value.strip()
                break

        # Si no hay título, usar el nombre completo
        if not info.get("titulo"):
            info["titulo"] = name

        return info

    @staticmethod
    def extract_info(file_path: Path, use_metadata: bool = True) -> Dict:
        """
        Extrae toda la información posible del archivo.
        """
        info = {
            "artista": "Sin Artista",
            "album": None,
            "titulo": None,
            "año": None,
            "numero": None
        }

        # 1. Intentar metadatos (prioridad alta)
        if use_metadata:
            metadata = MusicParser.extract_metadata(file_path)
            if metadata and any(metadata.values()):
                for key in info:
                    if metadata.get(key):
                        info[key] = metadata[key]

        # 2. Si faltan datos, intentar por nombre
        if not info.get("titulo") or info.get("artista") == "Sin Artista":
            filename_info = MusicParser.parse_filename(file_path)
            for key in filename_info:
                if filename_info.get(key) and not info.get(key):
                    info[key] = filename_info[key]

        # 3. Limpiar
        if info.get("artista") == "Sin Artista" and not info.get("titulo"):
            info["titulo"] = file_path.stem

        return info

    @staticmethod
    def get_destination_path(base_dir: Path, info: Dict, order: str = "año_album_artista") -> Path:
        """
        Genera la ruta de destino según la información extraída y el orden elegido.
        Siempre crea la carpeta base "Música".
        """
        artista = info.get("artista", "Sin Artista")
        album = info.get("album")
        año = info.get("año")
        genero = info.get("genero")

        # Limpiar nombres
        artista = MusicParser._clean_name(artista)
        if album:
            album = MusicParser._clean_name(album)

        # Carpeta base SIEMPRE "Música"
        path = base_dir / "Música"

        # Construir partes según el orden
        parts = []

        if order == "año_album_artista":
            if año:
                parts.append(año)
            if album:
                parts.append(album)
            parts.append(artista)

        elif order == "artista_año_album":
            parts.append(artista)
            if año:
                parts.append(año)
            if album:
                parts.append(album)

        elif order == "album_artista":
            if album:
                parts.append(album)
            parts.append(artista)

        elif order == "año_genero":
            if año:
                parts.append(año)
            if genero:
                parts.append(genero)
            else:
                parts.append("Sin Género")

        # Si no hay partes, devolver Música/Sin Artista
        if not parts:
            return path / "Sin Artista"

        # Añadir partes a la ruta
        for part in parts:
            path = path / part

        return path

    @staticmethod
    def _clean_name(name: str) -> str:
        """
        Limpia un nombre para usarlo como nombre de carpeta.
        """
        if not name:
            return "Desconocido"

        # Eliminar caracteres inválidos para carpetas
        invalid_chars = r'[<>:"/\\|?*]'
        cleaned = re.sub(invalid_chars, '_', name)
        # Eliminar espacios al inicio/final
        cleaned = cleaned.strip()
        # Reemplazar múltiples espacios por uno
        cleaned = re.sub(r'\s+', ' ', cleaned)

        return cleaned if cleaned else "Desconocido"
