"""
Tests para el organizador de archivos.
"""
import tempfile
from datetime import datetime
from pathlib import Path
import pytest

from src.core.organizer import PhotoVideoOrganizer


@pytest.fixture
def sample_files():
    """Crea archivos de prueba en un directorio temporal."""
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / "source"
        source.mkdir()
        
        # Crear archivos de prueba
        (source / "photo1.jpg").write_text("fake photo")
        (source / "video1.mp4").write_text("fake video")
        (source / "document.txt").write_text("fake doc")
        
        yield source


def test_organize_photos_and_videos(sample_files):
    """Test básico de organización."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / "dest"
        organizer = PhotoVideoOrganizer()
        
        summary = organizer.organize(sample_files, dest)
        
        assert summary["processed"] == 2
        assert summary["errors"] == 0
        
        # Verificar que se crearon las carpetas correctas
        assert (dest / "Fotos").exists()
        assert (dest / "Videos").exists()


def test_organize_only_photos(sample_files):
    """Test organizando solo fotos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / "dest"
        organizer = PhotoVideoOrganizer()
        
        summary = organizer.organize(
            sample_files, dest, organize_photos=True, organize_videos=False
        )
        
        assert summary["processed"] == 1
        assert (dest / "Fotos").exists()
        assert not (dest / "Videos").exists()