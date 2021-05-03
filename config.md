## Paste Images As WebP - configuration

*You have to restart Anki to apply changes to this file.*

****

* `avoid_upscaling` - Don't resize an image when its original size is less than requested.
* `cwebp_args` - Extra cwebp arguments you want to add.
* `copy_paste` - Convert images to webp when you copy-paste them.
* `drag_and_drop` - Convert images to webp on drag and drop.
* `image_height` - Desired height.
* `image_width` - Desired width.
* `image_quality` - Compression factor between `0` and `100`. `0` produces the worst quality.
* `max_image_height` - Limit for the height slider.
* `max_image_width` - Limit for the width slider.
* `shortcut` - Define a keyboard shortcut for pasting images as webp.
* `show_context_menu_entry` - Add an entry to the editor context menu.
* `show_editor_button` - Add a button to the editor toolbar.
* `show_settings` - When to show the settings dialog:
    * `always` - Every time you paste a new image.
    * `menus` - When the toolbar button or the context menu is activated.
    * `drag_and_drop` - On drag-and-drop (if enabled).
    * `never` - Only when you press `Tools > WebP settings`.

If one of the dimensions is set to `0`, images will be resized
preserving the aspect ratio.
If both `width` and `height` are `0`, no resizing is performed (not recommended).

****

If you enjoy this add-on, please consider supporting my work by
**[pledging your support on Patreon](https://www.patreon.com/tatsumoto_ren)**.
Thank you so much!
