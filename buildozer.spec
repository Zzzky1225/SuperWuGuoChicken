[app]
title = 超级吴国鸡跑酷
package.name = wuguoji
package.domain = com.chaoji
version = 1.0
android.versioncode = 1
android.strip_libs = True
android.compression_level = 9
source.dir = .
source.include_exts = py,png,jpg,wav,ttf
source.include_patterns = assets/*
requirements = python3,pygame_ce
p4a.bootstrap = sdl2
p4a.hostpython_version = "3.10"
p4a.python_version = "3.10"
p4a.allow_prebuilt_host_extensions = False
orientation = landscape
fullscreen = 1
android.minapi = 24
android.archs = arm64-v8a
android.api = 33
android.ndk = 25b
icon.filename = %(source.dir)s/assets/icon.png
android.manifest.application_attributes = android:appCategory="game"
android.debuggable = False
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
requirements.pip_options = --timeout=1200 --no-cache-dir
android.accept_sdk_license = True
