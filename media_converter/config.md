## AJT Media Converter &mdash; edit config

Here you can edit the config file.
You must know what you're doing.
Anki needs to be restarted for changes to be applied.
To restore default settings, click the **"Restore Defaults"** button.

If you have any questions,
ask other users in the [user group](https://tatsumoto.neocities.org/blog/join-our-community.html).

**Notes:**

- The add-on does not preserve transparency by default because `blend_alpha` is set to white.
- When batch converting, it is not recommended to enable `delete_original_file_on_convert`.
- If you have video files in your collection, exclude them using `excluded_image_containers`.
- Common video containers (`mp4`, `mkv`) are excluded by default.

****

* `avoid_upscaling` - Don't resize an image when its original size is less than requested.
* `bulk_convert_fields` - List of fields where the add-on looks for images when bulk-converting.
* `bulk_reconvert` - When bulk-converting, reconvert images that are already in the desired format.
* `delete_original_file_on_convert` - Delete the original file after conversion.
* `copy_paste` - Convert images when you copy-paste them.
* `convert_on_note_add` - Convert media when new notes are created, e.g. by AnkiConnect.
* `cwebp_args` - Extra [cwebp arguments](https://developers.google.com/speed/webp/docs/cwebp#options).
  They are applied on each call to `cwebp`.
* `ffmpeg_args` - Extra [ffmpeg arguments](https://ffmpeg.org/ffmpeg.html).
  They are applied on each call to `ffmpeg`.
* `drag_and_drop` - Convert images on drag and drop.
* `image_height` - Desired height.
* `image_width` - Desired width.
* `image_format` - Desired format ("avif" or "webp").
* `excluded_image_containers` - A comma-separated list of file formats (extensions without the dot)
  to skip from image conversion.
* `excluded_audio_containers` - A comma-separated list of file formats (extensions without the dot)
  to skip from audio conversion.
* `image_quality` - Compression factor between `0` and `100`.
  `0` produces the worst quality but the smallest file size.
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
* `saved_presets` - Used internally. Saved settings dialog presets.
* `tooltip_duration_seconds` - Duration of tooltips.
* `preserve_original_filenames` - If an image is already named, reuse that name.
  Works when dragging an image from a GUI file manager, e.g. [Thunar](https://wiki.archlinux.org/title/Thunar).
* `custom_name_field` - Name of a note field whose content is used to name converted files.
* `enable_audio_conversion` - Enable/disable conversion of audio files to `opus`.
* `enable_image_conversion` - Enable/disable conversion of image files to `webp` or `avif`
  based on the selected image format.
* `ffmpeg_audio_args` - Extra [ffmpeg arguments](https://ffmpeg.org/ffmpeg.html) for audio.
    * `-b:a` - Audio bitrate. Default "64k".
      [About opus bitrates](https://wiki.xiph.org/Opus_Recommended_Settings).
* `ffmpeg_audio_bitrate` - Audio bitrate in kbit/s for audio conversion.
* `audio_container` - Container (file extension name) for opus files ("opus" or "ogg").

If one of the dimensions is set to `0`, images will be resized
preserving the aspect ratio.
If both `width` and `height` are `0`, no resizing is performed (not recommended).

****

If you enjoy this add-on, please consider supporting my work by
**[making a donation](https://tatsumoto.neocities.org/blog/donating-to-tatsumoto.html)**.
Thank you so much!
