## Paste Images As WebP - configuration

* `avoid_upscaling` - Don't resize an image when its original size is less than requested.
* `bulk_convert_fields` - List of fields where the add-on looks for images when bulk-converting.
* `bulk_reconvert` - When bulk-converting, reconvert images that are already in the desired format.
* `copy_paste` - Convert images when you copy-paste them.
* `cwebp_args` - Extra [cwebp arguments](https://www.unix.com/man-page/debian/1/cwebp/).
  They are applied on each call to `cwebp`.
* `ffmpeg_args` - Extra [ffmpeg arguments](https://ffmpeg.org/ffmpeg.html).
  They are applied on each call to `ffmpeg`.
* `drag_and_drop` - Convert images on drag and drop.
* `image_height` - Desired height.
* `image_width` - Desired width.
* `image_format` - Desired format.
* `image_quality` - Compression factor between `0` and `100`. `0` produces the worst quality but the smallest file size.
* `max_image_height` - Limit for the height slider.
* `max_image_width` - Limit for the width slider.
* `shortcut` - Define a keyboard shortcut for pasting images in the configured `image_format`.
* `show_context_menu_entry` - Add an entry to the editor context menu.
* `show_editor_button` - Add a button to the editor toolbar.
* `show_settings` - When to show the settings dialog.
    * `always` - Every time you try to insert a converted image.
    * `toolbar` - When the toolbar button is clicked.
    * `paste` - When you paste an image.
    * `drag_and_drop` - On drag-and-drop (if enabled).
    * `never` - Only when you press `Tools > WebP settings`.
* `filename_pattern_num` - Used internally.
* `tooltip_duration_seconds` - Duration of tooltips.
* `preserve_original_filenames` - If an image is already named, reuse that name.
  Works when dragging an image from a GUI file manager, e.g. [Thunar](https://wiki.archlinux.org/title/Thunar).

If one of the dimensions is set to `0`, images will be resized
preserving the aspect ratio.
If both `width` and `height` are `0`, no resizing is performed (not recommended).

****

If you enjoy this add-on, please consider supporting my work by
**[making a donation](https://tatsumoto.neocities.org/blog/donating-to-tatsumoto.html)**.
Thank you so much!
