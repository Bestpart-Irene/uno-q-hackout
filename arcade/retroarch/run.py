"""Run on UNO Q Linux under run.sh's private Xvfb display."""

import argparse
from contextlib import suppress
import json
from pathlib import Path
import signal
import subprocess
import time

from arduino.router_bridge import Bridge
from Xlib import X, XK, display, error
from Xlib.ext import xtest

from controls import keys_for
from video import HEIGHT, WIDTH, Tiles, from_bgrx


def stop(*_):
    raise KeyboardInterrupt


class Keyboard:
    def __init__(self, connection):
        self.connection = connection
        self.held = set()

    def update(self, desired):
        for names, event in ((self.held - desired, X.KeyRelease), (desired - self.held, X.KeyPress)):
            for name in sorted(names):
                code = self.connection.keysym_to_keycode(XK.string_to_keysym(name))
                if not code:
                    raise RuntimeError(f"No X keycode for {name}")
                xtest.fake_input(self.connection, event, code)
        self.connection.sync()
        self.held = set(desired)


def run(core=None, content=None):
    connection = display.Display()
    root = connection.screen().root
    geometry = root.get_geometry()
    if (geometry.width, geometry.height, geometry.depth) != (WIDTH, HEIGHT, 24):
        raise RuntimeError("Use run.sh to create the private 160x120x24 Xvfb display")
    info = connection.display.info
    if info.image_byte_order != X.LSBFirst or not any(
            f.depth == 24 and f.bits_per_pixel == 32 for f in info.pixmap_formats):
        raise RuntimeError("Expected little-endian Xvfb with 32-bit storage for depth 24")
    if not connection.has_extension("XTEST"):
        raise RuntimeError("Xvfb must provide the XTEST input extension")
    connection.change_keyboard_control(auto_repeat_mode=X.AutoRepeatModeOff)
    keyboard = Keyboard(connection)
    bridge = Bridge()
    session = 0
    process = None
    try:
        if not bridge.connect(timeout=5):
            raise RuntimeError("Arduino Router unavailable; run the updated Arcade App Lab app first")
        session = bridge.call("arcade_video_begin", timeout=5)
        if type(session) is not int or session <= 0:
            raise RuntimeError("The TFT is already owned by another stream; stop it and retry")
        command = ["retroarch", "--config", str(Path(__file__).with_name("retroarch.cfg"))]
        if core:
            command += ["-L", str(Path(core).resolve())]
            if content:
                command.append(str(Path(content).resolve()))
        else:
            command.append("--menu")
        process = subprocess.Popen(command)
        # No window manager is needed; focus RetroArch's window once it appears.
        deadline = time.monotonic() + 5
        while True:
            windows = [w for w in root.query_tree().children if w.get_attributes().map_state == X.IsViewable]
            if windows:
                windows[-1].set_input_focus(X.RevertToParent, X.CurrentTime)
                connection.sync()
                break
            if process.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError("RetroArch did not create its window; inspect its log above")
            bridge.call("arcade_video_poll", session, timeout=0.75)
            time.sleep(0.05)
        tiles = Tiles()
        frame = None
        capture_at = report_at = time.monotonic()
        sent = 0
        rpc_time = 0.0
        calls = 0
        while process.poll() is None:
            now = time.monotonic()
            if frame is None or now >= capture_at:
                frame = from_bgrx(root.get_image(0, 0, WIDTH, HEIGHT, X.ZPixmap, 0xFFFFFFFF).data)
                capture_at = now + 0.1
            changed = tiles.next_changed(frame)
            start = time.monotonic()
            if changed:
                index, raw, payload = changed
                reply = bridge.call("arcade_video_tile", session, index, payload, timeout=0.75)
            else:
                reply = bridge.call("arcade_video_poll", session, timeout=0.75)
            inputs = json.loads(reply)
            if inputs.get("video") != session:
                raise RuntimeError("TFT stream expired; restart the launcher")
            keyboard.update(keys_for(inputs))
            if changed:
                index, raw, _ = changed
                tiles.sent[index] = raw  # Cache only acknowledged pixels.
                sent += 1
            rpc_time += time.monotonic() - start
            calls += 1
            if now - report_at >= 5:
                print(f"TFT: {sent / (now - report_at):.1f} tiles/s; "
                      f"mean control/RPC cycle {1000 * rpc_time / calls:.0f} ms", flush=True)
                report_at, sent, rpc_time, calls = now, 0, 0.0, 0
            if not changed:
                time.sleep(0.03)
        if process.returncode:
            raise RuntimeError(f"RetroArch exited with status {process.returncode}")
    finally:
        try:
            with suppress(error.ConnectionClosedError):
                keyboard.update(set())
        finally:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            if session:
                try:
                    bridge.call("arcade_video_end", session, timeout=0.75)
                except Exception:
                    pass  # The MCU lease expires even if the connection is gone.
            bridge.disconnect()
            with suppress(error.ConnectionClosedError):
                connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RetroArch on the supplied UNO Q TFT")
    parser.add_argument("--core", help="Path to a software-rendered libretro core (.so)")
    parser.add_argument("--content", help="Path to your game/content, if the core requires it")
    args = parser.parse_args()
    if args.content and not args.core:
        parser.error("--content requires --core")
    signal.signal(signal.SIGTERM, stop)
    try:
        run(args.core, args.content)
    except KeyboardInterrupt:
        pass
