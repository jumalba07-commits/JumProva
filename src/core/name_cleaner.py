"""
Limpieza y estandarización de nombres de archivos.
"""
import re
from pathlib import Path
from typing import List, Dict, Tuple


class NameCleaner:
    """Limpia y estandariza nombres de archivos de música."""

    @staticmethod
    def clean_name(
        filename: str,
        remove_track_numbers: bool = True,
        remove_brackets: bool = True,
        remove_parentheses: bool = True,
        remove_words: List[str] = None,
        custom_text: str = "",
        format_output: bool = True
    ) -> str:
        """
        Limpia un nombre de archivo.
        """
        name = filename
        original_name = name

        # 1. Eliminar números de pista (01 -, 01., 01_, etc.)
        if remove_track_numbers:
            name = re.sub(r'^\d+\s*[-._]\s*', '', name)
            name = re.sub(r'^\d+\s+', '', name)

        # 2. Eliminar texto entre corchetes [ ... ]
        if remove_brackets:
            name = re.sub(r'\[[^\]]*\]', '', name)

        # 3. Eliminar texto entre paréntesis ( ... )
        if remove_parentheses:
            name = re.sub(r'\([^)]*\)', '', name)

        # 4. Eliminar palabras específicas
        if remove_words:
            for word in remove_words:
                pattern = re.compile(rf'\s*{re.escape(word)}\s*', re.IGNORECASE)
                name = pattern.sub(' ', name)

        # 5. Eliminar texto personalizado
        if custom_text:
            pattern = re.compile(rf'\s*{re.escape(custom_text)}\s*', re.IGNORECASE)
            name = pattern.sub(' ', name)

        # 6. Limpiar espacios múltiples
        name = re.sub(r'\s+', ' ', name).strip()

        # 7. Si está vacío, usar el original
        if not name:
            name = original_name

        return name

    @staticmethod
    def extract_artist_title(filename: str) -> Tuple[str, str]:
        """
        Intenta extraer Artista y Título de un nombre de archivo.
        """
        # Limpiar primero
        cleaned = NameCleaner.clean_name(
            filename,
            remove_track_numbers=True,
            remove_brackets=True,
            remove_parentheses=True
        )

        # Intentar patrón "Artista - Título"
        if ' - ' in cleaned:
            parts = cleaned.split(' - ', 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()

        # Si no hay separador, usar el nombre como título
        return "", cleaned

    @staticmethod
    def rename_files(
        files: List[Path],
        format_output: bool = True,
        remove_track_numbers: bool = True,
        remove_brackets: bool = True,
        remove_parentheses: bool = True,
        remove_words: List[str] = None,
        custom_text: str = "",
        progress_callback=None
    ) -> Dict:
        """
        Renombra archivos según las reglas de limpieza.
        """
        renamed = []
        errors = []
        total = len(files)
        processed = 0

        if progress_callback:
            progress_callback(0, total)

        for file_path in files:
            try:
                # Limpiar nombre
                new_name = NameCleaner.clean_name(
                    file_path.stem,
                    remove_track_numbers=remove_track_numbers,
                    remove_brackets=remove_brackets,
                    remove_parentheses=remove_parentheses,
                    remove_words=remove_words,
                    custom_text=custom_text,
                    format_output=format_output
                )

                # Añadir extensión
                new_name = f"{new_name}{file_path.suffix}"

                # Si el nombre cambia, renombrar
                if new_name != file_path.name:
                    new_path = file_path.parent / new_name

                    # Si ya existe, añadir sufijo
                    if new_path.exists():
                        counter = 1
                        stem = new_path.stem
                        ext = new_path.suffix
                        while new_path.exists():
                            new_name = f"{stem}_{counter}{ext}"
                            new_path = file_path.parent / new_name
                            counter += 1

                    file_path.rename(new_path)
                    renamed.append((file_path, new_path))

                processed += 1

                if progress_callback:
                    progress_callback(processed, total)

            except Exception as e:
                errors.append((file_path, str(e)))
                processed += 1

                if progress_callback:
                    progress_callback(processed, total)

        return {
            "renamed": len(renamed),
            "errors": len(errors),
            "details": renamed,
            "error_details": errors
        }