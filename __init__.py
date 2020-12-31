import json
import subprocess
import time
from distutils.spawn import find_executable
from tempfile import mkstemp
from typing import Any

from anki.hooks import addHook
from aqt import mw
from aqt.editor import Editor, EditorWebView
from aqt.qt import *

addon_path = os.path.dirname(__file__)


######################################################################
# Utils
######################################################################

def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func

    return decorate


class Conf:
    dict = mw.addonManager.getConfig(__name__) or dict()

    @classmethod
    def get(cls, key, default: Any = False):
        return cls.dict.get(key, default)


def find_cwebp():
    exe = find_executable('cwebp')
    if exe is None:
        # https://developers.google.com/speed/webp/download
        support_dir = "support"
        if isWin:
            exe = os.path.join(addon_path, support_dir, "cwebp.exe")
        else:
            exe = os.path.join(addon_path, support_dir, "cwebp")
            os.chmod(exe, 0o755)
    return exe


def apply_resize_args(args):
    width = Conf.get('width', 0)
    height = Conf.get('height', 200)
    if not (width == 0 and height == 0):
        print(f"image will be resized to {width}x{height}")
        args.extend(['-resize', width, height])
    return args


@static_vars(cwebp=find_cwebp())
def convert_file(source_path, destination_path):
    args = [
        convert_file.cwebp,
        source_path,
        '-short',
        '-mt',
        '-pass', '10',
        '-af',
        '-blend_alpha', '0xffffff',
        '-m', '6',
        '-q', '33',
        '-o', destination_path
    ]
    args = apply_resize_args(args)

    try:
        subprocess.check_output(args)
    except subprocess.CalledProcessError as ex:
        print(f"cwebp failed.")
        print(f"\texit code = {ex.returncode}")
        print(f"\toutput = {ex.output}")
        return False
    return True


def insert_webp(editor: Editor):
    mime: QMimeData = editor.mw.app.clipboard().mimeData()

    if not mime.hasImage():
        return

    fd, tmp_filepath = mkstemp()

    image: QImage = mime.imageData()
    if image.save(tmp_filepath, 'png') is True:
        out_filename: str = str(int(time.time())) + '.webp'
        out_filepath: str = os.path.join(mw.col.media.dir(), out_filename)
        if convert_file(tmp_filepath, out_filepath):
            image_html = f'<img src="{out_filename}">'
            editor.web.eval("""setFormat("insertHtml", %s);""" % json.dumps(image_html))  # calls document.execCommand
    os.close(fd)
    os.remove(tmp_filepath)


def key_to_str(shortcut: str) -> str:
    return QKeySequence(shortcut).toString(QKeySequence.NativeText)


######################################################################
# Main
######################################################################


def setup_menus():
    shortcut: str = Conf.get("shortcut", "")
    action_tooltip: str = "Paste as webp"
    if shortcut:
        action_tooltip += f" ({key_to_str(shortcut)})"

    if Conf.get("context_menu_entry") is True:
        def add_context_menu_item(webview: EditorWebView, menu: QMenu):
            editor = webview.editor
            a: QAction = menu.addAction(action_tooltip)
            a.triggered.connect(lambda _, e=editor: insert_webp(e))

        addHook('EditorWebView.contextMenuEvent', add_context_menu_item)

    if Conf.get("show_editor_button") is True:
        def add_editor_button(buttons, editor):
            b = editor.addButton(
                os.path.join(addon_path, "webp_icon.png"),
                "paste_webp_button",
                lambda e=editor: insert_webp(e),
                tip=action_tooltip,
                keys=shortcut
            )
            buttons.extend([b])
            return buttons

        addHook("setupEditorButtons", add_editor_button)

    elif shortcut:
        def add_editor_shortcut(cuts, self):
            cuts.append((shortcut, lambda e=self: insert_webp(e)))

        addHook("setupEditorShortcuts", add_editor_shortcut)


setup_menus()
