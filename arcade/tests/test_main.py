import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch


PYTHON = Path(__file__).resolve().parents[1] / "python"
INPUTS = {"connected": 7, "buttons": 1, "x": 0, "y": 0,
          "ax": 50, "ay": -75, "az": 1034, "video": 0}


class PreviewLoopTests(unittest.TestCase):
    def setUp(self):
        self.bridge = Mock()
        self.output = self.enterContext(patch("builtins.print"))
        app_utils = SimpleNamespace(App=Mock(), Bridge=self.bridge)
        with patch.dict(sys.modules, {"arduino.app_utils": app_utils}), \
                patch.object(sys, "path", [str(PYTHON), *sys.path]):
            self.loop = runpy.run_path(str(PYTHON / "main.py"))["loop"]
        self.sleep = Mock()
        self.loop.__globals__["time"] = SimpleNamespace(sleep=self.sleep)
        self.output.reset_mock()

    def test_json_text_and_bytes_draw_calibrated_frame(self):
        text = json.dumps(INPUTS)
        for response in (text, text.encode(), bytearray(text.encode())):
            with self.subTest(response_type=type(response).__name__):
                self.bridge.reset_mock()
                self.bridge.call.return_value = response
                self.loop()
                self.assertEqual(self.bridge.call.call_args_list, [
                    call("arcade_read_inputs"),
                    call("arcade_draw_frame", 240, 234, 1, 0, 0, 0, 7),
                ])
                self.output.assert_not_called()

    def test_invalid_responses_do_not_draw_and_next_read_can_recover(self):
        for response in (None, 7, {}, [], "not JSON", "[]", "{}",
                         json.dumps({**INPUTS, "x": 999})):
            with self.subTest(response=response):
                self.bridge.reset_mock()
                self.bridge.call.return_value = response
                self.loop()
                self.bridge.call.assert_called_once_with("arcade_read_inputs")
                self.sleep.assert_called_with(1)
                self.assertTrue(self.output.call_args.args[0].startswith(
                    "Arcade connection/input error:"))
                self.bridge.call.return_value = json.dumps(INPUTS)
                self.loop()
                self.bridge.call.assert_called_with(
                    "arcade_draw_frame", 240, 234, 1, 0, 0, 0, 7)

    def test_video_owner_suspends_preview(self):
        self.bridge.call.return_value = json.dumps({**INPUTS, "video": 1})
        self.loop()
        self.bridge.call.assert_called_once_with("arcade_read_inputs")
        self.sleep.assert_called_once_with(0.5)
        self.output.assert_not_called()


if __name__ == "__main__":
    unittest.main()
