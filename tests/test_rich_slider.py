# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import pytest
from aqt.qt import QSignalBlocker, QSlider, Qt

from media_converter.widgets.image_slider_box import ImageSliderBox
from media_converter.widgets.rich_slider import RichSlider


class TestRichSliderControls:
    """Verify synchronization and configuration of the composite controls."""

    @pytest.mark.parametrize(
        "widget_name, value",
        [("slider", 30), ("spinbox", 40)],
        ids=["slider_updates_spinbox", "spinbox_updates_slider"],
    )
    def test_controls_stay_synchronized(self, widget_name: str, value: int) -> None:
        """Changing either control updates the shared RichSlider value."""
        rich_slider = RichSlider("Width", upper_limit=100)
        controls = rich_slider.widgets

        getattr(controls, widget_name).setValue(value)

        assert rich_slider.value == value
        assert controls.slider.value() == value
        assert controls.spinbox.value() == value

    @pytest.mark.parametrize(
        "start, stop, expected_value",
        [(10, 50, 10), (0, 20, 0)],
        ids=["clamps_existing_value", "keeps_zero"],
    )
    def test_set_range_updates_both_controls(self, start: int, stop: int, expected_value: int) -> None:
        """Setting a range applies it to both controls and clamps their value."""
        rich_slider = RichSlider("Width", upper_limit=100)
        rich_slider.set_range(start=start, stop=stop)
        controls = rich_slider.widgets

        assert controls.slider.minimum() == start
        assert controls.spinbox.minimum() == start
        assert controls.slider.maximum() == stop
        assert controls.spinbox.maximum() == stop
        assert rich_slider.value == expected_value

    @pytest.mark.parametrize("limit", [50, 200], ids=["lower_limit", "higher_limit"])
    def test_set_upper_limit_keeps_zero_lower_bound(self, limit: int) -> None:
        """Updating the upper limit retains zero as the controls' lower bound."""
        rich_slider = RichSlider("Width", lower_limit=10, upper_limit=100)
        rich_slider.set_upper_limit(limit)
        controls = rich_slider.widgets

        assert controls.slider.minimum() == 0
        assert controls.spinbox.minimum() == 0
        assert controls.slider.maximum() == limit
        assert controls.spinbox.maximum() == limit

    @pytest.mark.parametrize("step", [1, 10], ids=["single_unit", "ten_units"])
    def test_step_is_applied_to_both_controls(self, step: int) -> None:
        """The configured step controls keyboard and spin-box increments."""
        rich_slider = RichSlider("Width", step=step)
        controls = rich_slider.widgets

        assert controls.slider.singleStep() == step
        assert controls.spinbox.singleStep() == step

    @pytest.mark.parametrize("control_name", ["slider", "spinbox", "unit_label"])
    def test_tooltip_is_applied_to_every_control(self, control_name: str) -> None:
        """The same tooltip is exposed by every RichSlider control."""
        rich_slider = RichSlider("Width")
        tooltip = "Choose a width."
        rich_slider.set_tooltip(tooltip)

        assert getattr(rich_slider.widgets, control_name).toolTip() == tooltip

    def test_title_and_widgets_layout_order(self) -> None:
        """RichSlider exposes its title and controls in layout order."""
        rich_slider = RichSlider("Width", unit="px")
        controls = rich_slider.widgets

        assert rich_slider.title == "Width"
        assert controls._fields == ("slider", "spinbox", "unit_label")
        assert tuple(controls) == (controls.slider, controls.spinbox, controls.unit_label)

    @pytest.mark.parametrize("control_name", ["slider", "spinbox", "unit_label"])
    def test_widgets_property_keeps_live_controls(self, control_name: str) -> None:
        """Fresh property containers expose the same live widget instances."""
        slider = RichSlider("Width")
        first = slider.widgets
        second = slider.widgets
        assert first is not second
        assert getattr(first, control_name) is getattr(second, control_name)


class TestRichSliderValues:
    """Cover value assignment, clamping, and the visible control defaults."""

    @pytest.mark.parametrize(("value", "expected"), [(-1, 10), (10, 10), (35, 35), (50, 50), (101, 50)])
    def test_value_setter(self, value: int, expected: int) -> None:
        """Programmatic assignment clamps and synchronizes both controls."""
        slider = RichSlider("Width", lower_limit=10, upper_limit=50)
        slider.value = value
        assert slider.value == expected
        assert slider.widgets.slider.value() == expected
        assert slider.widgets.spinbox.value() == expected

    @pytest.mark.parametrize(("block_slider", "block_spinbox"), [(True, False), (False, True), (True, True)])
    @pytest.mark.parametrize(("value", "expected"), [(-1, 10), (35, 35), (101, 50)])
    def test_value_setter_with_signals_blocked(
        self, block_slider: bool, block_spinbox: bool, value: int, expected: int
    ) -> None:
        """Assignment synchronizes both controls without relying on signal delivery."""
        slider = RichSlider("Width", lower_limit=10, upper_limit=50)
        controls = slider.widgets
        controls.slider.blockSignals(block_slider)
        controls.spinbox.blockSignals(block_spinbox)
        slider.value = value
        assert controls.slider.value() == expected
        assert controls.spinbox.value() == expected
        assert controls.slider.signalsBlocked() == block_slider
        assert controls.spinbox.signalsBlocked() == block_spinbox

    @pytest.mark.parametrize("value", [10, 30])
    def test_value_setter_repairs_desynchronized_controls(self, value: int) -> None:
        """Reassigning the slider's existing value also repairs a different spin-box value."""
        slider = RichSlider("Width", lower_limit=10, upper_limit=50)
        slider.value = value
        controls = slider.widgets
        # Model a temporary signal-blocked edit without leaving either control's signals blocked.
        with QSignalBlocker(controls.spinbox):
            controls.spinbox.setValue(40)
        assert controls.slider.value() == value
        assert controls.spinbox.value() == 40
        slider.value = value
        assert controls.slider.value() == value
        assert controls.spinbox.value() == value

    @pytest.mark.parametrize("unit", ["px", "%", "kbit/s"])
    def test_control_defaults(self, unit: str) -> None:
        """Expose the requested unit, horizontal orientation, and default keyboard step."""
        controls = RichSlider("Size", unit=unit).widgets
        assert controls.unit_label.text() == unit
        assert controls.slider.orientation() == Qt.Orientation.Horizontal
        assert controls.slider.singleStep() == 5
        assert controls.spinbox.singleStep() == 5

    @pytest.mark.parametrize(("row", "expected_step", "expected_maximum"), [(0, 5, 800), (1, 5, 600), (2, 1, 100)])
    def test_image_slider_steps(self, row: int, expected_step: int, expected_maximum: int) -> None:
        """Quality uses single-percent increments without changing dimension increments."""
        box = ImageSliderBox(max_width=800, max_height=600)
        # Inspect the public layout rather than depending on ImageSliderBox's private slider storage.
        slider = box.layout().itemAtPosition(row, 1).widget()
        assert isinstance(slider, QSlider)
        assert slider.singleStep() == expected_step
        assert slider.maximum() == expected_maximum
