# 🗂️ JumProva

### Organizador de Archivos Profesional

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![Python](https://img.shields.io/badge/python-3.11%2B-green) ![License](https://img.shields.io/badge/license-MIT-yellow) ![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

---

## 📋 Descripción

**JumProva** es una aplicación de escritorio todo en uno para organizar, limpiar y gestionar tus archivos de forma profesional y sencilla. Diseñada para usuarios que quieren tener **todos sus archivos bajo control**.

---

## ✨ Características principales

### 📁 Organizar
- 📸 **Fotos** → Clasificadas por `AÑO/MES/DÍA/`
- 🎬 **Videos** → Clasificados por `AÑO/MES/DÍA/`
- 📄 **Documentos** → Clasificados por extensión (`PDF/`, `DOCX/`, `XLSX/`, etc.)

### 🔄 Desorganizar
- Revertir cualquier organización realizada por la app
- Soporte para Fotos, Videos, Música y Documentos

### 📝 Renombrar
- Renombrado masivo con:
  - Prefijo / Sufijo
  - Numeración automática
  - Fecha de modificación
  - Reemplazo de texto
  - Minúsculas / Mayúsculas

### 🎵 Música
- Organización por **Artista / Álbum / Año**
- Extracción de metadatos ID3
- Múltiples estructuras de carpetas

### 🏷️ Metadatos
- Escaneo de archivos de música
- Editor de metadatos
- Limpieza de nombres de archivos
- Formato estándar: `Artista - Título.mp3`

### 🧹 Limpieza de Sistema
- 🗑️ Papelera de reciclaje
- 📁 Archivos temporales del sistema
- 🌐 Caché de navegadores
- 🖼️ Miniaturas
- 📄 Archivos vacíos (0 B)
- 📄 Archivos pequeños (< X KB)
- 📦 Archivos grandes (> X MB)
- 📁 Archivos .log antiguos
- 💾 Archivos de respaldo
- ⬇️ Descargas antiguas
- 🔄 Archivos duplicados
- 🗑️ Eliminar carpetas vacías
- 🛡️ **Protección de archivos del sistema**

---

## 🛠️ Tecnologías utilizadas

- 🐍 **Python 3.11+**
- 🖥️ **Tkinter** (GUI nativa)
- 🎵 **Mutagen** (Metadatos de música)
- 🖼️ **Pillow** (Procesamiento de imágenes)

---

## 📦 Instalación y uso

### 🔧 Requisitos
- Python 3.11 o superior
- Windows 10/11 (recomendado)

### 📥 Instalar dependencias

```bash
pip install -r requirements.txt
🚀 Ejecutar desde código fuente
bash
python src/main.py
📦 Compilar a .exe
bash
pyinstaller JumProva.spec --clean
📁 Estructura del proyecto
text
JumProva/
├── src/
│   ├── assets/
│   │   ├── jumprova.ico
│   │   └── jumprova.png
│   ├── gui/
│   │   ├── main_window.py
│   │   ├── organize_tab.py
│   │   ├── desorganize_tab.py
│   │   ├── rename_tab.py
│   │   ├── music_tab.py
│   │   ├── metadata_tab.py
│   │   ├── cleaner_tab.py
│   │   └── about_tab.py
│   ├── core/
│   │   ├── organizer.py
│   │   ├── desorganizer.py
│   │   ├── renamer.py
│   │   ├── music_organizer.py
│   │   ├── music_parser.py
│   │   ├── metadata_manager.py
│   │   ├── name_cleaner.py
│   │   ├── file_handler.py
│   │   └── models.py
│   ├── config/
│   │   └── settings.py
│   └── main.py
├── JumProva.spec
├── requirements.txt
└── README.md
👨‍💻 Autor
Juan José Rivera
📧 jumalba@hotmail.com
🐙 github.com/jumalba07-commits

📅 Versiones
Versión	Fecha	Cambios
1.0.0	2026	Lanzamiento inicial
📝 Licencia
Este proyecto está bajo la licencia MIT.

<div align="center">
Hecho con ❤️ por Juan José Rivera

</div> ```
