import json
from pathlib import Path


class Config:
    """Configuración global de la aplicación"""

    def __init__(self):
        self.config_dir = Path.home() / ".organizador_pro"
        self.config_file = self.config_dir / "settings.json"
        self.categories_file = self.config_dir / "categories.json"

        # Crear directorio de configuración si no existe
        self.config_dir.mkdir(exist_ok=True)

        # Configuración por defecto
        self.defaults = {
            "language": "es",
            "theme": "light",
            "default_operation": "mover",
            "use_metadata": True,
            "include_subfolders": False,
            "handle_duplicates": "rename",
            "unknown_files": "ignore",
            "date_priority": ["exif", "modified", "created"],
            "keep_empty_folders": False,
            "log_level": "INFO",
            "max_file_size": 0,
            # ← NUEVO
            "active_categories": ["fotos", "videos", "documentos", "comprimidos"]
        }

        self.load()

    def load(self):
        """Cargar configuración desde archivo"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except BaseException:
                self.data = self.defaults.copy()
        else:
            self.data = self.defaults.copy()
            self.save()

    def save(self):
        """Guardar configuración"""
        self.config_file.parent.mkdir(exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get(self, key, default=None):
        """Obtener un valor de configuración"""
        return self.data.get(key, default or self.defaults.get(key))

    def set(self, key, value):
        """Establecer un valor de configuración"""
        self.data[key] = value
        self.save()

    def get_categories(self):
        """Obtener categorías personalizadas"""
        if self.categories_file.exists():
            try:
                with open(self.categories_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except BaseException:
                return self.default_categories()
        return self.default_categories()

    def get_active_categories(self):
        """Obtener lista de categorías activas"""
        return self.get(
            "active_categories", [
                "fotos", "videos", "documentos", "comprimidos"])

    def set_active_categories(self, categories):
        """Establecer categorías activas"""
        self.set("active_categories", categories)

    def default_categories(self):
        """Categorías por defecto"""
        return {
            "fotos": {
                "extensions": [
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".gif",
                    ".bmp",
                    ".tiff",
                    ".tif",
                    ".webp",
                    ".heic",
                    ".heif",
                    ".raw",
                    ".cr2",
                    ".nef",
                    ".arw"],
                "folder": "Fotos",
                "priority": 1,
                "metadata": True},
            "videos": {
                "extensions": [
                    ".mp4",
                    ".avi",
                    ".mkv",
                    ".mov",
                    ".wmv",
                    ".flv",
                    ".webm",
                    ".m4v",
                    ".mpg",
                    ".mpeg",
                    ".3gp",
                    ".mts",
                    ".m2ts"],
                "folder": "Videos",
                "priority": 2,
                "metadata": True},
            "audio": {
                "extensions": [
                    ".mp3",
                    ".wav",
                    ".flac",
                    ".aac",
                    ".ogg",
                    ".wma",
                    ".m4a"],
                "folder": "Audio",
                "priority": 3,
                "metadata": True},
            "documentos": {
                "extensions": [
                    ".pdf",
                    ".docx",
                    ".doc",
                    ".txt",
                    ".xlsx",
                    ".xls",
                    ".pptx",
                    ".ppt",
                    ".odt",
                    ".rtf",
                    ".csv"],
                "folder": "Documentos",
                "priority": 4,
                "metadata": False},
            "comprimidos": {
                "extensions": [
                    ".zip",
                    ".rar",
                    ".7z",
                    ".tar",
                    ".gz",
                    ".bz2"],
                "folder": "Comprimidos",
                "priority": 5,
                "metadata": False},
            "ejecutables": {
                "extensions": [
                    ".exe",
                    ".msi",
                    ".bat",
                    ".cmd",
                    ".sh"],
                "folder": "Ejecutables",
                "priority": 6,
                "metadata": False},
            "codigo": {
                "extensions": [
                    ".py",
                    ".js",
                    ".html",
                    ".css",
                    ".java",
                    ".cpp",
                    ".c",
                    ".php",
                    ".json",
                    ".xml",
                    ".yaml",
                    ".yml"],
                "folder": "Código",
                "priority": 7,
                "metadata": False}}


# Instancia global
config = Config()
