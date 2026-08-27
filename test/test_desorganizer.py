"""
Tests para el desorganizador de archivos.
"""
import tempfile
from pathlib import Path
import pytest

from src.core.desorganizer import Desorganizer
from src.core.organizer import PhotoVideoOrganizer


@pytest.fixture
def organized_files():
    """Crea una estructura organizada de prueba."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / "source"
        source.mkdir()
        
        # Crear archivos de prueba
        (source / "foto1.jpg").write_text("fake photo")
        (source / "foto2.png").write_text("fake photo2")
        (source / "video1.mp4").write_text("fake video")
        (source / "documento.txt").write_text("fake doc")
        
        # Organizar primero
        dest = Path(tmpdir) / "dest"
        organizer = PhotoVideoOrganizer()
        organizer.organize(source, dest)
        
        yield dest


def test_desorganize_all_files(organized_files):
    """Test que desorganiza todos los archivos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / "output"
        desorganizer = Desorganizer()
        
        summary = desorganizer.desorganize(organized_files, dest)
        
        # Verificar que se procesaron 3 archivos (2 fotos + 1 video)
        assert summary["processed"] == 3
        assert summary["errors"] == 0
        
        # Verificar que los archivos están en la carpeta destino
        files = list(dest.glob("*"))
        assert len(files) == 3


def test_desorganize_with_subfolders(organized_files):
    """Test que desorganiza incluyendo subcarpetas."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / "output"
        desorganizer = Desorganizer()
        
        summary = desorganizer.desorganize(
            organized_files, 
            dest,
            search_subfolders=True
        )
        
        assert summary["processed"] == 3