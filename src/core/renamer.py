"""
Servicio para renombrar archivos en masa.
"""
import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional


class FileRenamer:
    """Servicio para renombrar archivos en masa."""

    def __init__(self):
        self.preview_files: List[Tuple[Path, str]] = []
        self.renamed_files: List[Tuple[Path, Path]] = []
        self.errors: List[Tuple[Path, str]] = []
        self.cancel_requested = False
        self.is_running = False

    def get_preview(
        self,
        source_dir: Path,
        include_subfolders: bool = True,
        extensions: Optional[List[str]] = None,
        base_name: str = "",  # <--- NUEVO
        prefix: str = "",
        suffix: str = "",
        numbering: bool = False,
        number_start: int = 1,
        number_digits: int = 2,
        replace_from: str = "",
        replace_to: str = "",
        use_date: bool = False,
        date_format: str = "%Y-%m-%d",
        lowercase: bool = False,
        uppercase: bool = False,
        remove_spaces: bool = False
    ) -> List[Tuple[Path, str]]:
        """
        Genera una vista previa de cómo quedarán los nombres.
        """
        self.preview_files = []
        
        files = self._get_files(source_dir, include_subfolders, extensions)
        
        if not files:
            return []
        
        counter = number_start
        
        for file_path in files:
            stem = file_path.stem
            ext = file_path.suffix
            
            # ----- SI HAY NOMBRE BASE, SE USA EN LUGAR DEL ORIGINAL -----
            if base_name:
                new_name = base_name
            else:
                new_name = stem
            
            # 1. Reemplazar texto (solo si NO hay nombre base)
            if not base_name and replace_from and replace_to:
                new_name = new_name.replace(replace_from, replace_to)
            
            # 2. Eliminar espacios
            if remove_spaces:
                new_name = new_name.replace(" ", "_")
                new_name = re.sub(r'_+', '_', new_name)
            
            # 3. Añadir fecha
            if use_date:
                try:
                    mtime = file_path.stat().st_mtime
                    date_str = datetime.fromtimestamp(mtime).strftime(date_format)
                    new_name = f"{date_str}_{new_name}"
                except:
                    pass
            
            # 4. Añadir numeración
            if numbering:
                num_str = str(counter).zfill(number_digits)
                new_name = f"{new_name}_{num_str}"
                counter += 1
            
            # 5. Añadir prefijo (si hay base_name, el prefijo va ANTES)
            if prefix:
                new_name = f"{prefix}{new_name}"
            
            # 6. Añadir sufijo (si hay base_name, el sufijo va DESPUÉS)
            if suffix:
                new_name = f"{new_name}{suffix}"
            
            # 7. Mayúsculas/minúsculas
            if lowercase:
                new_name = new_name.lower()
            elif uppercase:
                new_name = new_name.upper()
            
            # 8. Limpiar caracteres especiales
            new_name = re.sub(r'[<>:"/\\|?*]', '_', new_name)
            
            final_name = f"{new_name}{ext}"
            self.preview_files.append((file_path, final_name))
        
        return self.preview_files

    def rename_files(
        self,
        source_dir: Path,
        include_subfolders: bool = True,
        extensions: Optional[List[str]] = None,
        base_name: str = "",
        prefix: str = "",
        suffix: str = "",
        numbering: bool = False,
        number_start: int = 1,
        number_digits: int = 2,
        replace_from: str = "",
        replace_to: str = "",
        use_date: bool = False,
        date_format: str = "%Y-%m-%d",
        lowercase: bool = False,
        uppercase: bool = False,
        remove_spaces: bool = False,
        progress_callback=None
    ) -> Dict:
        """Ejecuta el renombrado."""
        self.cancel_requested = False
        self.is_running = True
        self.renamed_files = []
        self.errors = []

        try:
            preview = self.get_preview(
                source_dir=source_dir,
                include_subfolders=include_subfolders,
                extensions=extensions,
                base_name=base_name,
                prefix=prefix,
                suffix=suffix,
                numbering=numbering,
                number_start=number_start,
                number_digits=number_digits,
                replace_from=replace_from,
                replace_to=replace_to,
                use_date=use_date,
                date_format=date_format,
                lowercase=lowercase,
                uppercase=uppercase,
                remove_spaces=remove_spaces
            )

            total = len(preview)
            processed = 0

            if progress_callback:
                progress_callback(0, total)

            for file_path, new_name in preview:
                if self.cancel_requested:
                    self.is_running = False
                    return {
                        "processed": processed,
                        "errors": len(self.errors),
                        "cancelled": True,
                        "total": total
                    }

                if file_path.name == new_name:
                    processed += 1
                    if progress_callback:
                        progress_callback(processed, total)
                    continue

                try:
                    new_path = file_path.parent / new_name

                    if new_path.exists():
                        counter = 1
                        stem = new_path.stem
                        ext = new_path.suffix
                        while new_path.exists():
                            new_name = f"{stem}_{counter}{ext}"
                            new_path = file_path.parent / new_name
                            counter += 1

                    file_path.rename(new_path)
                    self.renamed_files.append((file_path, new_path))

                except Exception as e:
                    self.errors.append((file_path, str(e)))

                processed += 1

                if progress_callback:
                    progress_callback(processed, total)

            self.is_running = False
            return {
                "processed": len(self.renamed_files),
                "errors": len(self.errors),
                "cancelled": False,
                "total": total,
                "files": self.renamed_files,
                "error_details": self.errors
            }

        except Exception as e:
            self.is_running = False
            raise e

    def cancel(self):
        """Solicita la cancelación."""
        self.cancel_requested = True

    def _get_files(
        self,
        source_dir: Path,
        include_subfolders: bool,
        extensions: Optional[List[str]]
    ) -> List[Path]:
        """Obtiene lista de archivos según criterios."""
        files = []
        
        if include_subfolders:
            iterator = source_dir.rglob("*")
        else:
            iterator = source_dir.glob("*")
        
        # Extensiones permitidas
        ext_set = set(extensions) if extensions else None
        ext_set = {e.lower() if not e.startswith('.') else e.lower() for e in (ext_set or [])}
        
        for item in iterator:
            if item.is_file():
                if ext_set:
                    ext = item.suffix.lower()
                    if ext not in ext_set:
                        continue
                files.append(item)
        
        return files

    def reset(self):
        """Reinicia el estado."""
        self.preview_files = []
        self.renamed_files = []
        self.errors = []
        self.cancel_requested = False
        self.is_running = False
