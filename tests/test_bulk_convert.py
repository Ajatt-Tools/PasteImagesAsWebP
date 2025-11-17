# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from unittest.mock import Mock, patch

import pytest
from anki.notes import NoteId

from media_converter.bulk_convert.convert_result import ConvertResult
from media_converter.bulk_convert.convert_task import (
    ConvertTask,
    TaskCanceledByUserException, cancel_all_remaining_futures,
)
from media_converter.bulk_convert.runnable import ConvertRunnable
from media_converter.config import MediaConverterConfig
from media_converter.file_converters.common import LocalFile


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
