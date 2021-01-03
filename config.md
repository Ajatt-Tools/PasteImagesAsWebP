## Paste Images As WebP - configuration

* `drag_and_drop` - Convert images to webp on drag and drop
* `image_height` - Desired height
* `image_width` - Desired width
* `image_quality` - Compression factor between `0` and `100`. `0` produces the worst quality.
* `shortcut` - Define a keyboard shortcut for pasting images as webp
* `show_context_menu_entry` - Add an entry to the editor context menu
* `show_editor_button` - Add a button to the editor toolbar
* `show_settings` - When to show the settings dialog:
    * `always` - Every time you paste a new image
    * `toolbar` - When the toolbar button is pressed
    * `drag_and_drop` - On drag-and-drop (if enabled)
    * `never` - Only when you press `Tools > WebP settings`

If one of the dimensions is set to `0`, images will be resized
preserving the aspect ratio.
If both `width` and `height` are `0`, no resizing is performed (not recommended).

****

If you enjoy this add-on, please consider supporting my work by
**[pledging your support on Patreon](https://www.patreon.com/tatsumoto_ren)**.
Thank you so much!
