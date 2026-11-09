"""LunaPath - Android app: Kivy + Flask + HTML interface.

Flask serves index.html and the API, Kivy runs everything on Android and opens a WebView.
Bluetooth (classic SPP, HC-05) works through pyjnius.
"""
import os
import threading

from flask import Flask, jsonify, request, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=None)

try:
    from jnius import autoclass
    ANDROID = True
except ImportError:
    ANDROID = False

SPP_UUID = "00001101-0000-1000-8000-00805F9B34FB"


class RoverLink:
    def __init__(self):
        self.socket = None
        self.out = None
        self.inp = None
        self.connected = False
        self.lines = []
        self.lock = threading.Lock()
        self.error = ""

    def devices(self):
        if not ANDROID:
            return []
        BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
        adapter = BluetoothAdapter.getDefaultAdapter()
        if adapter is None:
            return []
        result = []
        for d in adapter.getBondedDevices().toArray():
            result.append({"name": d.getName(), "address": d.getAddress()})
        return result

    def connect(self, address):
        if not ANDROID:
            raise RuntimeError("Bluetooth is only available on Android")
        BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
        UUID = autoclass("java.util.UUID")
        adapter = BluetoothAdapter.getDefaultAdapter()
        device = adapter.getRemoteDevice(address)
        sock = device.createRfcommSocketToServiceRecord(UUID.fromString(SPP_UUID))
        adapter.cancelDiscovery()
        try:
            sock.connect()
        except Exception:
            # a failed socket left open makes the next attempt to the HC-05 fail too
            try:
                sock.close()
            except Exception:
                pass
            raise
        self.socket = sock
        self.out = sock.getOutputStream()
        self.inp = sock.getInputStream()
        self.connected = True
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        buf = bytearray()
        while self.connected:
            try:
                b = self.inp.read()
            except Exception:
                break
            if b < 0:
                break
            if b == 10:
                line = buf.decode("utf-8", "ignore").strip()
                buf.clear()
                if line:
                    with self.lock:
                        self.lines.append(line)
            else:
                buf.append(b)
        self.connected = False

    def send(self, cmd):
        if not self.connected:
            raise RuntimeError("not connected")
        self.out.write(ord(cmd[0]))
        self.out.flush()

    def poll(self):
        with self.lock:
            lines, self.lines = self.lines, []
        return lines


link = RoverLink()


@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")


@app.route("/api/status")
def status():
    return jsonify(connected=link.connected, android=ANDROID)


@app.route("/api/devices")
def devices():
    try:
        return jsonify(devices=link.devices())
    except Exception as e:
        return jsonify(devices=[], error=str(e))


@app.route("/api/connect", methods=["POST"])
def connect():
    address = (request.get_json(silent=True) or {}).get("address", "")
    try:
        link.connect(address)
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(ok=False, error=str(e))


@app.route("/api/send", methods=["POST"])
def send():
    cmd = (request.get_json(silent=True) or {}).get("cmd", "")
    try:
        link.send(cmd)
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(ok=False, error=str(e))


@app.route("/api/poll")
def poll():
    return jsonify(lines=link.poll(), connected=link.connected)


def run_server():
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


if ANDROID:
    from android.runnable import run_on_ui_thread

    @run_on_ui_thread
    def create_webview():
        WebView = autoclass("android.webkit.WebView")
        WebViewClient = autoclass("android.webkit.WebViewClient")
        LayoutParams = autoclass("android.view.ViewGroup$LayoutParams")
        activity = autoclass("org.kivy.android.PythonActivity").mActivity
        webview = WebView(activity)
        settings = webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setDomStorageEnabled(True)
        webview.setWebViewClient(WebViewClient())
        activity.addContentView(webview, LayoutParams(-1, -1))
        webview.loadUrl("http://127.0.0.1:5000")


from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label


class LunaPathApp(App):
    def build(self):
        threading.Thread(target=run_server, daemon=True).start()
        if ANDROID:
            from android.permissions import request_permissions
            request_permissions([
                "android.permission.BLUETOOTH_CONNECT",
                "android.permission.BLUETOOTH_SCAN",
                "android.permission.ACCESS_FINE_LOCATION",
            ])
            Clock.schedule_once(lambda dt: create_webview(), 2)
        return Label(text="LunaPath")


if __name__ == "__main__":
    LunaPathApp().run()
