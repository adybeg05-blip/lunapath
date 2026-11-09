[app]
title = LunaPath
package.name = lunapath
package.domain = org.lunapath
source.dir = .
source.include_exts = py,png,html
version = 0.1
requirements = python3,kivy,flask,werkzeug,jinja2,markupsafe,itsdangerous,click,blinker,pyjnius,android
orientation = portrait
fullscreen = 0

# Home screen icon: put icon.png (512x512) next to this file and uncomment
# icon.filename = %(source.dir)s/icon.png

android.permissions = INTERNET,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,BLUETOOTH_SCAN,ACCESS_FINE_LOCATION
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True

# The WebView opens plain http://127.0.0.1:5000 (the Flask server inside the app).
# The SDL2 bootstrap does not allow cleartext traffic by default (Android 9+ blocks it),
# so this file adds android:usesCleartextTraffic="true" to the <application> tag.
android.extra_manifest_application_arguments = ./extra_manifest_application_arguments.xml

[buildozer]
log_level = 2
warn_on_root = 1
