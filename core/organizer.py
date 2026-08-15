from pathlib import Path
from core.file_classifier import FileClassifier
from core.date_detector import DateDetector
from core.file_handler import FileHandler
from config.settings import config


class Organizer:
    """Lógica principal de organización"""

    def __init__(self):
        self.classifier = FileClassifier()
        self.date_detector = DateDetector()
        self.file_handler = FileHandler()

        # Conectar el log del file_handler
        self.file_handler.set_log_callback(self._log_from_handler)

        self.callbacks = {
            "on_start": None,
            "on_progress": None,
            "on_file_processed": None,
            "on_complete": None,
            "on_error": None,
            "on_cancel": None,
            "on_log": None  # Nuevo callback para logs
        }

        # Configuración
        self.use_metadata = config.get("use_metadata", True)
        self.include_subfolders = config.get("include_subfolders", False)
        self.handle_unknown = config.get("unknown_files", "ignore")

        # Control de cancelación
        self.cancel_requested = False

    def _log_from_handler(self, message):
        """Recibir logs del file_handler y pasarlos a la interfaz"""
        if self.callbacks["on_log"]:
            self.callbacks["on_log"](message)

    def register_callback(self, event, callback):
        """Registrar callbacks para eventos"""
        if event in self.callbacks:
            self.callbacks[event] = callback

    def cancel(self):
        """Solicitar cancelación del proceso"""
        self.cancel_requested = True
        if self.callbacks["on_cancel"]:
            self.callbacks["on_cancel"]()

    def organize(self, source_dir, dest_dir, operation="move"):
        """Organizar archivos de source_dir a dest_dir"""
        self.cancel_requested = False

        source_dir = Path(source_dir)
        dest_dir = Path(dest_dir)

        # Resetear estadísticas
        self.file_handler.reset_stats()

        # Obtener lista de archivos
        if self.callbacks["on_log"]:
            self.callbacks["on_log"]("🔍 Escaneando archivos...")

        files = self._get_files(source_dir)

        if not files:
            if self.callbacks["on_log"]:
                self.callbacks["on_log"](
                    "⚠️ No se encontraron archivos para organizar")
            return {"error": "No se encontraron archivos para organizar"}

        if self.callbacks["on_log"]:
            self.callbacks["on_log"](f"📊 Encontrados {len(files)} archivos")
            self.callbacks["on_log"]("=" * 50)

        # Notificar inicio
        if self.callbacks["on_start"]:
            self.callbacks["on_start"](len(files))

        # Procesar cada archivo
        processed = 0
        for file_path in files:
            # Verificar cancelación
            if self.cancel_requested:
                if self.callbacks["on_log"]:
                    self.callbacks["on_log"](
                        "🛑 Proceso cancelado por el usuario")
                if self.callbacks["on_complete"]:
                    stats = self.file_handler.get_stats()
                    stats["cancelled"] = True
                    stats["processed"] = processed
                    self.callbacks["on_complete"](stats)
                return {"cancelled": True, "processed": processed}

            processed += 1
            try:
                if self.callbacks["on_log"]:
                    self.callbacks["on_log"](
                        f"\n📄 [{processed}/{len(files)}] {file_path.name}")

                # Clasificar archivo
                category = self.classifier.classify(file_path)
                if self.callbacks["on_log"]:
                    self.callbacks["on_log"](
                        f"   📂 Categoría: {category['folder']}")

                # Si es "otros" y la configuración es ignorar
                if category["name"] == "otros" and self.handle_unknown == "ignore":
                    if self.callbacks["on_file_processed"]:
                        self.callbacks["on_file_processed"](
                            file_path, "ignored", "Archivo desconocido ignorado")
                    if self.callbacks["on_log"]:
                        self.callbacks["on_log"](
                            "   ⏭️ Archivo ignorado (categoría desconocida)")
                    continue

                # Obtener fecha
                use_metadata = category.get(
                    "use_metadata", False) and self.use_metadata
                date = self.date_detector.get_date(file_path, use_metadata)

                # Extraer componentes de fecha
                date_components = self.date_detector.extract_date_components(
                    date)
                if self.callbacks["on_log"]:
                    self.callbacks["on_log"](
                        f"   📅 Fecha: {
                            date_components['year']}/{
                            date_components['month']:02d}-{
                            date_components['month_name']}/{
                            date_components['day']:02d}")

                # Construir ruta destino
                dest_path = self._build_dest_path(
                    dest_dir,
                    category["folder"],
                    date_components,
                    file_path
                )

                # Mover o copiar archivo
                self.file_handler.move_file(file_path, dest_path, operation)

                # Notificar progreso
                if self.callbacks["on_file_processed"]:
                    self.callbacks["on_file_processed"](
                        file_path, "processed", f"→ {
                            category['folder']}/{
                            date_components['year']}/{
                            date_components['month']:02d}-{
                            date_components['month_name']}/{
                            date_components['day']:02d}")

                if self.callbacks["on_progress"]:
                    progress = (processed / len(files)) * 100
                    self.callbacks["on_progress"](
                        progress, f"Procesando: {file_path.name}")

            except Exception as e:
                if self.callbacks["on_error"]:
                    self.callbacks["on_error"](str(e), file_path)
                if self.callbacks["on_log"]:
                    self.callbacks["on_log"](f"   ❌ Error: {str(e)}")
                continue

        # Notificar completado
        if self.callbacks["on_log"]:
            self.callbacks["on_log"]("\n" + "=" * 50)
            self.callbacks["on_log"]("✅ PROCESO COMPLETADO")

        if self.callbacks["on_complete"]:
            stats = self.file_handler.get_stats()
            stats["cancelled"] = False
            stats["processed"] = processed
            self.callbacks["on_complete"](stats)

        return self.file_handler.get_stats()

    def _get_files(self, directory):
        """Obtener lista de archivos (recursivo según configuración)"""
        directory = Path(directory)

        if self.include_subfolders:
            return [f for f in directory.rglob("*") if f.is_file()]
        else:
            return [f for f in directory.iterdir() if f.is_file()]

    def _build_dest_path(
            self,
            dest_dir,
            category_folder,
            date_components,
            file_path):
        """Construir la ruta de destino con estructura año/mes/día"""
        dest_dir = Path(dest_dir)
        year = date_components["year"]
        month_num = date_components["month"]
        month_name = date_components["month_name"]
        day = date_components["day"]

        # Si es audio, usar la opción de organización por metadatos
        if category_folder.lower() == "audio":
            audio_organize = config.get("audio_organize", "año")

            try:
                import mutagen
                audio = mutagen.File(str(file_path))
                if audio and hasattr(audio, 'tags') and audio.tags is not None:
                    if audio_organize == "artista" and 'TPE1' in audio.tags:
                        artista = str(audio.tags['TPE1']).strip()
                        if artista:
                            # Estructura: Destino/Audio/Artista/Año/Mes/Día/
                            dest_path = dest_dir / category_folder / artista / \
                                str(year) / f"{month_num:02d}-{month_name}" / f"{day:02d}"
                            dest_path = dest_path / file_path.name
                            return dest_path

                    elif audio_organize == "genero" and 'TCON' in audio.tags:
                        genero = str(audio.tags['TCON']).strip()
                        if genero:
                            dest_path = dest_dir / category_folder / genero / \
                                str(year) / f"{month_num:02d}-{month_name}" / f"{day:02d}"
                            dest_path = dest_path / file_path.name
                            return dest_path
            except BaseException:
                pass

        # Estructura estándar: Destino/Categoría/Año/MM-Mes/DD/
        dest_path = dest_dir / category_folder / \
            str(year) / f"{month_num:02d}-{month_name}" / f"{day:02d}"
        dest_path = dest_path / file_path.name

        return dest_path
