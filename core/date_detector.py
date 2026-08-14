import os
from datetime import datetime
from pathlib import Path
from config.settings import config

class DateDetector:
    """Detecta la fecha de creación/captura de un archivo"""
    
    def __init__(self):
        self.priority = config.get("date_priority", ["exif", "modified", "created"])
        self.exif_available = False
        
        # Intentar importar PIL
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            self.Image = Image
            self.TAGS = TAGS
            self.exif_available = True
        except ImportError:
            self.exif_available = False
    
    def get_date(self, file_path, use_metadata=True):
        """Obtiene la fecha del archivo según la prioridad configurada"""
        file_path = Path(file_path)
        
        date = None
        
        # Intentar diferentes métodos según prioridad
        for method in self.priority:
            if method == "exif" and use_metadata:
                date = self._get_exif_date(file_path)
            elif method == "modified":
                date = self._get_modified_date(file_path)
            elif method == "created":
                date = self._get_created_date(file_path)
            
            if date:
                return date
        
        # Si todo falla, usar fecha actual
        return datetime.now()
    
    def _get_exif_date(self, file_path):
        """Extraer fecha de metadatos EXIF"""
        if not self.exif_available:
            return None
        
        try:
            image = self.Image.open(file_path)
            exifdata = image._getexif()
            
            if exifdata:
                for tag_id, value in exifdata.items():
                    tag = self.TAGS.get(tag_id, tag_id)
                    if tag == "DateTimeOriginal":
                        try:
                            return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        except:
                            pass
                    elif tag == "DateTimeDigitized":
                        try:
                            return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        except:
                            pass
                    elif tag == "DateTime":
                        try:
                            return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
                        except:
                            pass
        except:
            pass
        
        return None
    
    def _get_modified_date(self, file_path):
        """Obtener fecha de modificación del sistema"""
        try:
            timestamp = os.path.getmtime(file_path)
            return datetime.fromtimestamp(timestamp)
        except:
            return None
    
    def _get_created_date(self, file_path):
        """Obtener fecha de creación del sistema"""
        try:
            timestamp = os.path.getctime(file_path)
            return datetime.fromtimestamp(timestamp)
        except:
            return None
    
    def extract_date_components(self, date):
        """Extraer año, mes y día de una fecha"""
        return {
            "year": date.year,
            "month": date.month,
            "day": date.day,
            "month_name": self._get_month_name(date.month),
            "date": date
        }
    
    def _get_month_name(self, month):
        """Obtener nombre del mes en español"""
        months = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        return months.get(month, "Desconocido")