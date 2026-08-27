"""
Configuración global de la aplicación.
"""
from pathlib import Path

# Categorías soportadas
PHOTO_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
    '.webp', '.heic', '.heif', '.raw', '.cr2', '.nef', '.arw'
}

VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm',
    '.m4v', '.mpg', '.mpeg', '.3gp', '.3g2', '.mts', '.m2ts'
}

# Carpetas de destino
PHOTOS_FOLDER = "Fotos"
VIDEOS_FOLDER = "Videos"
DOCUMENTS_FOLDER = "Documentos"

# Patrón de organización: destino/Categoría/AÑO/MES/DÍA/
DATE_FORMAT_PATH = "%Y/%m/%d"

# Documentos - TODOS los tipos
DOCUMENT_EXTENSIONS = {
    # Texto
    '.txt', '.rtf', '.md', '.log',
    # PDF
    '.pdf',
    # Word
    '.doc', '.docx', '.odt',
    # Excel
    '.xls', '.xlsx', '.ods', '.csv',
    # PowerPoint
    '.ppt', '.pptx', '.odp',
    # Imágenes (si quieres incluirlas como documentos)
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico',
    # Libros electrónicos
    '.epub', '.mobi', '.azw', '.azw3',
    # Datos
    '.xml', '.json', '.yaml', '.yml', '.toml',
    # Comprimidos
    '.zip', '.rar', '.7z', '.tar', '.gz',
    # Ejecutables
    '.exe', '.msi', '.bat', '.cmd', '.sh',
    # Otros
    '.sql', '.db', '.sqlite',
}


