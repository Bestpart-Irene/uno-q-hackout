import json
import time

from arduino.app_utils import App, Bridge
from preview import frame_values


def loop():
    try:
        response = Bridge.call("arcade_read_inputs")
        if not isinstance(response, (str, bytes, bytearray)):
            raise TypeError("Expected JSON text from arcade_read_inputs")
        inputs = json.loads(response)
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
