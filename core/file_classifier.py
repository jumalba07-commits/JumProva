from pathlib import Path
from config.settings import config


class FileClassifier:
    """Clasifica archivos por tipo usando extensiones y contenido"""

    def __init__(self):
        self.categories = config.get_categories()
        self.active_categories = config.get_active_categories()
        self.cache = {}

    def classify(self, file_path):
        """Clasifica un archivo y devuelve su categoría (solo si está activa)"""
        file_path = Path(file_path)

        # Verificar caché
        cache_key = str(file_path)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Obtener extensión
        extension = file_path.suffix.lower()

        # Si no tiene extensión
        if not extension:
            result = self._classify_by_content(file_path)
            if result:
                self.cache[cache_key] = result
                return result
            result = self._get_default_category()
            self.cache[cache_key] = result
            return result

        # Buscar en categorías por extensión (SOLO LAS ACTIVAS)
        for category_name, category_data in self.categories.items():
            # Verificar si la categoría está activa
            if category_name not in self.active_categories:
                continue

            if extension in category_data.get("extensions", []):
                result = {
                    "name": category_name,
                    "folder": category_data["folder"],
                    "priority": category_data.get("priority", 999),
                    "use_metadata": category_data.get("metadata", False)
                }
                self.cache[cache_key] = result
                return result

        # Si no se encontró en categorías activas
        result = self._classify_by_content(file_path)
        if result:
            self.cache[cache_key] = result
            return result

        # Categoría "otros" (siempre activa)
        result = self._get_default_category()
        self.cache[cache_key] = result
        return result

    def _classify_by_content(self, file_path):
        """Clasificar por contenido (MIME type, cabeceras)"""
        try:
            import magic
            mime_type = magic.from_file(str(file_path), mime=True)

            # Mapeo de MIME types a categorías (solo activas)
            mime_map = {
                "image": "fotos",
                "video": "videos",
                "audio": "audio",
                "text": "documentos",
                "application/pdf": "documentos",
                "application/zip": "comprimidos",
                "application/x-rar": "comprimidos"
            }

            for mime_prefix, category in mime_map.items():
                # Verificar si la categoría está activa
                if category not in self.active_categories:
                    continue

                if mime_type.startswith(mime_prefix):
                    category_data = self.categories.get(category)
                    if category_data:
                        return {
                            "name": category,
                            "folder": category_data["folder"],
                            "priority": category_data.get(
                                "priority",
                                999),
                            "use_metadata": category_data.get(
                                "metadata",
                                False)}
        except ImportError:
            pass

        return None

    def _get_default_category(self):
        """Obtener categoría por defecto (Otros) - SIEMPRE ACTIVA"""
        return {
            "name": "otros",
            "folder": "Otros",
            "priority": 999,
            "use_metadata": False
        }

    def get_active_categories(self):
        """Obtener lista de categorías activas"""
        return self.active_categories

    def set_active_categories(self, categories):
        """Establecer categorías activas"""
        self.active_categories = categories
        config.set_active_categories(categories)
        self.cache = {}  # Limpiar caché

    def get_all_categories(self):
        """Obtener todas las categorías (activas e inactivas)"""
        return self.categories

    def add_category(
            self,
            name,
            extensions,
            folder,
            priority=999,
            use_metadata=False):
        """Añadir una nueva categoría personalizada"""
        self.categories[name] = {
            "extensions": extensions,
            "folder": folder,
            "priority": priority,
            "metadata": use_metadata
        }
        # Guardar en archivo de configuración
        import json
        config.categories_file.parent.mkdir(exist_ok=True)
        with open(config.categories_file, 'w', encoding='utf-8') as f:
            json.dump(self.categories, f, indent=4, ensure_ascii=False)
