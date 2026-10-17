import json
import time

from arduino.app_utils import App, Bridge
from preview import frame_values


def loop():
    try:
        inputs = json.loads(Bridge.call("arcade_read_inputs"))
        if inputs.get("video", 0):
            time.sleep(0.5)
            return
        Bridge.call("arcade_draw_frame", *frame_values(inputs))
    except Exception as error:
        # Without fresh frames the MCU clears the preview after 1.5 seconds.
        print(f"Arcade connection/input error: {error}")
        time.sleep(1)
        return
    time.sleep(0.1)


print("Move the joystick, press A/B/C or the stick, and gently tilt the console.")
App.run(user_loop=loop)
