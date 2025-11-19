# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os
import tempfile
from unittest.mock import Mock, patch

import pytest
from anki.notes import NoteId

from media_converter.bulk_convert.convert_result import ConvertResult
from media_converter.bulk_convert.convert_task import (
    ConvertTask,
    TaskCanceledByUserException,
    cancel_all_remaining_futures,
)
from media_converter.bulk_convert.runnable import ConvertRunnable
from media_converter.config import MediaConverterConfig
from media_converter.file_converters.common import LocalFile
from media_converter.file_converters.file_converter import FileConverter
from media_converter.file_converters.find_media import FindMedia
from media_converter.utils.file_paths_factory import FilePathFactory


def test_convert_result_has_results() -> None:
    """Test that has_results() returns True when there are converted or failed files."""
    result = ConvertResult()

    # Initially should be False
    assert result.has_results() is False

    # Should be True after adding a converted file
    result.add_converted(LocalFile.image("test.jpg"), "test.webp")
    assert result.has_results() is True

    # Reset and test with failed file
    result = ConvertResult()
    result.add_failed(LocalFile.image("test2.jpg"), Exception("test error"))
    assert result.has_results() is True


def test_convert_result_converted_and_failed_properties() -> None:
    """Test that converted and failed properties work correctly."""
    result = ConvertResult()

    # Add a converted file
    original_file = LocalFile.image("test.jpg")
    result.add_converted(original_file, "test.webp")

    # Add a failed file
    failed_file = LocalFile.image("test2.jpg")
    test_exception = Exception("test error")
    result.add_failed(failed_file, test_exception)

    # Check converted property
    assert len(result.converted) == 1
    assert original_file in result.converted
    assert result.converted[original_file] == "test.webp"

    # Check failed property
    assert len(result.failed) == 1
    assert failed_file in result.failed
    assert result.failed[failed_file] == test_exception


def test_cancel_all_remaining_futures() -> None:
    """Test that cancel_all_remaining_futures cancels pending futures."""
    # Create mock futures
    future1 = Mock()
    future1.done.return_value = False
    future2 = Mock()
    future2.done.return_value = True  # Already done, should not be canceled
    future3 = Mock()
    future3.done.return_value = False

    future_to_file = {
        future1: LocalFile.image("test1.jpg"),
        future2: LocalFile.image("test2.jpg"),
        future3: LocalFile.image("test3.jpg"),
    }

    cancel_all_remaining_futures(future_to_file)

    # Only the non-done futures should be canceled
    future1.cancel.assert_called_once()
    future2.cancel.assert_not_called()
    future3.cancel.assert_called_once()


def test_convert_task_initialization(no_anki_config: MediaConverterConfig) -> None:
    """Test that ConvertTask initializes correctly."""
    mock_browser = Mock()
    note_ids = [NoteId(1), NoteId(2), NoteId(3)]
    selected_fields = ["Front", "Back"]

    with patch.object(ConvertTask, "_find_files_to_convert_and_notes", return_value={}):
        task = ConvertTask(mock_browser, note_ids, selected_fields, no_anki_config)

        assert task._browser == mock_browser
        assert task._selected_fields == selected_fields
        assert task._canceled is False


def test_convert_task_set_canceled(no_anki_config: MediaConverterConfig) -> None:
    """Test that set_canceled sets the canceled flag."""
    mock_browser = Mock()
    note_ids = [NoteId(1), NoteId(2), NoteId(3)]
    selected_fields = ["Front", "Back"]

    with patch.object(ConvertTask, "_find_files_to_convert_and_notes", return_value={}):
        task = ConvertTask(mock_browser, note_ids, selected_fields, no_anki_config)

        assert task._canceled is False
        task.set_canceled()
        assert task._canceled is True


def test_convert_task_size(no_anki_config: MediaConverterConfig) -> None:
    """Test that size property returns the correct count."""
    mock_browser = Mock()
    note_ids = [NoteId(1), NoteId(2), NoteId(3)]
    selected_fields = ["Front", "Back"]

    # Mock the _to_convert dictionary with 3 items
    to_convert = {
        LocalFile.image("test1.jpg"): {},
        LocalFile.image("test2.jpg"): {},
        LocalFile.image("test3.jpg"): {},
    }

    with patch.object(ConvertTask, "_find_files_to_convert_and_notes", return_value=to_convert):
        task = ConvertTask(mock_browser, note_ids, selected_fields, no_anki_config)

        assert task.size == 3


def test_convert_task_already_converted_check(no_anki_config: MediaConverterConfig) -> None:
    """Test that calling the task twice raises RuntimeError."""
    mock_browser = Mock()
    note_ids = [NoteId(1), NoteId(2), NoteId(3)]
    selected_fields = ["Front", "Back"]

    with patch.object(ConvertTask, "_find_files_to_convert_and_notes", return_value={}):
        task = ConvertTask(mock_browser, note_ids, selected_fields, no_anki_config)

        # Add a result to make it "dirty"
        task._result.add_converted(LocalFile.image("test.jpg"), "test.webp")

        # Calling it should raise RuntimeError
        with pytest.raises(RuntimeError, match="Already converted"):
            list(task())


def test_convert_stored_file_canceled(no_anki_config: MediaConverterConfig) -> None:
    """Test that _convert_stored_file raises TaskCanceledByUserException when canceled."""
    mock_browser = Mock()
    note_ids = [NoteId(1), NoteId(2), NoteId(3)]
    selected_fields = ["Front", "Back"]

    with patch.object(ConvertTask, "_find_files_to_convert_and_notes", return_value={}):
        task = ConvertTask(mock_browser, note_ids, selected_fields, no_anki_config)
        task.set_canceled()

        with pytest.raises(TaskCanceledByUserException):
            task._convert_stored_file(LocalFile.image("test.jpg"))


def test_convert_runnable_set_canceled() -> None:
    """Test that ConvertRunnable set_canceled delegates to task."""
    mock_task = Mock()
    mock_signals = Mock()

    runnable = ConvertRunnable(mock_task, mock_signals)

    runnable.set_canceled()

    mock_task.set_canceled.assert_called_once()


def test_convert_runnable_run() -> None:
    """Test that ConvertRunnable run method works correctly."""
    mock_task = Mock()
    mock_task.return_value = [1, 2, 3]  # Simulate progress values
    mock_signals = Mock()

    runnable = ConvertRunnable(mock_task, mock_signals)

    runnable.run()

    # Check that progress was emitted correctly
    mock_signals.update_progress.emit.assert_any_call(0)  # Initial call
    mock_signals.update_progress.emit.assert_any_call(1)  # First progress
    mock_signals.update_progress.emit.assert_any_call(2)  # Second progress
    mock_signals.update_progress.emit.assert_any_call(3)  # Third progress
    mock_signals.task_done.emit.assert_called_once()


def test_find_media_functionality(no_anki_config: MediaConverterConfig) -> None:
    """Test that FindMedia can find convertible images in HTML content."""

    # Create a FindMedia instance with the config
    finder = FindMedia(no_anki_config)

    # Test HTML with sample images
    html_content = '<img src="sample01.png"> Some text <img src="sample02.jpg">'

    # Find convertible images
    convertible_images = list(finder.find_convertible_images(html_content))

    # Both images should be found as convertible (they're not in the excluded list)
    assert frozenset(convertible_images) == frozenset(["sample01.png", "sample02.jpg"])


def test_file_path_factory_functionality(no_anki_config: MediaConverterConfig) -> None:
    """Test that FilePathFactory can generate target extensions correctly."""

    # Create a FilePathFactory instance
    fpf = FilePathFactory(note=None, editor=None, config=no_anki_config)

    # Test target extensions
    assert fpf.get_target_extension(LocalFile.image("test.jpg")) == ".webp"
    assert fpf.get_target_extension(LocalFile.image("test.png")) == ".webp"
    assert fpf.get_target_extension(LocalFile.audio("test.mp3")) == ".ogg"
    assert fpf.get_target_extension(LocalFile.audio("test.wav")) == ".ogg"


def test_convert_result_accumulation() -> None:
    """Test that ConvertResult properly accumulates converted and failed files."""

    result = ConvertResult()

    # Add some converted files
    result.add_converted(LocalFile.image("test1.jpg"), "test1.webp")
    result.add_converted(LocalFile.image("test2.png"), "test2.webp")

    # Add some failed files
    exception1 = Exception("Conversion failed")
    exception2 = FileNotFoundError("File not found")
    result.add_failed(LocalFile.image("test3.jpg"), exception1)
    result.add_failed(LocalFile.audio("test4.mp3"), exception2)

    # Check that all files are properly tracked
    assert frozenset(result.converted) == frozenset([LocalFile.image("test1.jpg"), LocalFile.image("test2.png")])
    assert frozenset(result.failed) == frozenset([LocalFile.audio("test4.mp3"), LocalFile.image("test3.jpg")])
    assert len(result.failed) == 2
    assert result.has_results() is True

    # Check specific entries
    assert LocalFile.image("test1.jpg") in result.converted
    assert result.converted[LocalFile.image("test1.jpg")] == "test1.webp"
    assert LocalFile.image("test3.jpg") in result.failed
    assert result.failed[LocalFile.image("test3.jpg")] == exception1


def test_convert_task_cancellation_behavior(no_anki_config: MediaConverterConfig) -> None:
    """Test that ConvertTask properly handles cancellation."""

    # Mock the file finding to return no files (so we don't need real notes)
    with patch.object(ConvertTask, "_find_files_to_convert_and_notes", return_value={}):
        task = ConvertTask(Mock(), [], [], no_anki_config)

        # Initially should not be canceled
        assert task._canceled is False

        # After setting canceled, should be canceled
        task.set_canceled()
        assert task._canceled is True


def test_convert_task_progress_reporting(no_anki_config: MediaConverterConfig) -> None:
    """Test that ConvertTask properly reports progress."""

    # Mock the file finding to return some files
    mock_files = {
        LocalFile.image("sample01.png"): {},
        LocalFile.image("sample02.jpg"): {},
    }

    with patch.object(ConvertTask, "_find_files_to_convert_and_notes", return_value=mock_files):
        with patch.object(ConvertTask, "_convert_stored_file", return_value="converted_file.webp"):
            task = ConvertTask(Mock(), [], [], no_anki_config)

            # Check that size is correct
            assert task.size == 2

            # Check progress reporting (this would normally be an iterable)
            progress_values = list(task())

            # Should have reported progress for each file
            assert len(progress_values) == 2


def test_real_image_conversion(no_anki_config: MediaConverterConfig) -> None:
    """Test real image conversion using sample images."""
    # Get the path to the sample images
    sample_dir = os.path.join(os.path.dirname(__file__), "collection.media")
    sample_png = os.path.join(sample_dir, "sample01.png")
    sample_jpg = os.path.join(sample_dir, "sample02.jpg")

    # Check that the sample files exist
    assert os.path.exists(sample_png), f"Sample PNG file not found at {sample_png}"
    assert os.path.exists(sample_jpg), f"Sample JPG file not found at {sample_jpg}"

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test PNG to WebP conversion
        output_png_webp = os.path.join(temp_dir, "sample01.webp")
        converter_png = FileConverter(sample_png, output_png_webp, no_anki_config)
        converter_png.convert()

        # Check that the output file was created
        assert os.path.exists(output_png_webp), f"Output PNG WebP file not created at {output_png_webp}"
        assert os.path.getsize(output_png_webp) > 0, "Output PNG WebP file is empty"

        # Test JPG to WebP conversion
        output_jpg_webp = os.path.join(temp_dir, "sample02.webp")
        converter_jpg = FileConverter(sample_jpg, output_jpg_webp, no_anki_config)
        converter_jpg.convert()

        # Check that the output file was created
        assert os.path.exists(output_jpg_webp), f"Output JPG WebP file not created at {output_jpg_webp}"
        assert os.path.getsize(output_jpg_webp) > 0, "Output JPG WebP file is empty"


def test_convert_task_call_with_real_images(no_anki_config: MediaConverterConfig) -> None:
    """Test that ConvertTask.__call__ works properly with real images from the tests directory."""
    from unittest.mock import MagicMock

    from anki.notes import Note

    from media_converter.bulk_convert.convert_task import ConvertTask
    from media_converter.file_converters.common import LocalFile

    # Mock the Anki environment
    mock_browser = MagicMock()
    mock_browser.editor = MagicMock()

    # Mock the note finding to return notes that reference our sample images
    mock_note = MagicMock(spec=Note)
    mock_note.id = NoteId(1)
    mock_note.keys.return_value = ["Front", "Back"]

    # Mock the file finding to return some files
    mock_files = {
        LocalFile.image("sample01.png"): {NoteId(1): mock_note},
        LocalFile.image("sample02.jpg"): {NoteId(1): mock_note},
    }

    with patch.object(ConvertTask, "_find_files_to_convert_and_notes", return_value=mock_files):
        with patch("media_converter.bulk_convert.convert_task.InternalFileConverter") as mock_converter_class:
            # Mock the converter to simulate successful conversion
            mock_converter_instance = MagicMock()
            mock_converter_instance.new_filename = "converted_sample01.webp"
            mock_converter_instance.convert_internal.return_value = None
            mock_converter_class.return_value = mock_converter_instance

            # Create a ConvertTask with our mock browser and note IDs
            task = ConvertTask(mock_browser, [NoteId(1)], ["Front", "Back"], no_anki_config)

            # Execute the task
            progress_values = list(task())

            # Verify that progress was reported
            assert len(progress_values) == 2  # Should have progress for 2 files

            # Verify that the converter was called
            assert mock_converter_class.called

            # Verify that the result has been recorded
            assert task._result.has_results() is True
