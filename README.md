<p align="center">
<img src="https://user-images.githubusercontent.com/69171671/103569451-35025f00-4ebf-11eb-9ff2-e44aba4183a1.png">
</p>

# Paste Images As WebP
[![Rate on AnkiWeb](https://glutanimate.com/logos/ankiweb-rate.svg)](https://ankiweb.net/shared/info/1151815987)
![GitHub](https://img.shields.io/github/license/Ajatt-Tools/PasteImagesAsWebP)
[![Patreon](https://img.shields.io/badge/support-patreon-orange)](https://www.patreon.com/tatsumoto_ren)
[![Matrix](https://img.shields.io/badge/chat-join-green.svg)](https://tatsumoto-ren.github.io/blog/join-our-community.html)

> An Anki add-on that makes your images small.

We all know that people who don't store their images in
[WebP](https://developers.google.com/speed/webp)
are wasting a lot of disk space.
Not only on their hard drives, but on AnkiWeb as well.
Unfortunately Anki doesn't convert images to WebP when you paste them from elsewhere,
and it takes time to convert and resize images manually.

For the longest time I used a bash script
to automatically convert images in my Anki collection to WebP
until I decided that we simply need an add-on for this.

> WebP lossy images are 25-34% smaller than comparable JPEG images at equivalent SSIM quality index.

Storing images in WebP is a great way to reduce the size of your Anki collection.

## Installation
Install from [AnkiWeb](https://ankiweb.net/shared/info/1151815987), or manually with `git`:

```
$ git clone 'https://github.com/Ajatt-Tools/PasteImagesAsWebP.git' ~/.local/share/Anki2/addons21/PasteImagesAsWebP
```

You also need `cwebp` installed:
```
$ sudo pacman -S libwebp
```

If you're running MacOS:
```
$ brew install webp
```

Or download it from [google.com](https://developers.google.com/speed/webp/download)
and save the `cwebp` executable in `~/.local/share/Anki2/addons21/PasteImagesAsWebP/support/`.
cwebp comes included in the AnkiWeb package.

## Configuration

To configure the add-on select "AJT" > "WebP settings" from the top menu bar.
To view hidden settings open the Anki Add-on Menu
via "Tools" > "Add-ons" and select "PasteImagesAsWebP".
Then click the Config button on the right-side of the screen.

## Usage

Watch video demonstration:

<p align="center"><a href="https://www.youtube.com/watch?v=kEsIykks1WY" target="_blank"><img src="https://user-images.githubusercontent.com/69171671/106127599-97fdb380-6156-11eb-93b0-8f73260cf582.png"></a></p>

After installation images will be automatically converted to `WebP` and resized on pasting or drag-and-dropping.
There's also a button in the Editor toolbar that lets you do the same.

To bulk-convert existing images in your collection, select `Edit` > `Bulk-convert to WebP` in the card browser.

To rename media files on a particular note,
open the Anki Browser, select the note and click on the pencil icon on the toolbar.
A dialog will pop up asking you to enter new filenames.

## Contributions

If you've found a bug or want to extend the add-on, please let us know in the
[Matrix chat](https://tatsumoto-ren.github.io/blog/join-our-community.html).
I'm open to suggestions and pull requests.

My special thanks to all my
[Patreon](https://www.patreon.com/tatsumoto_ren)
supporters for making this project possible.
