[buildozer]
android.accept_license = yes

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
requirements = python3==3.10.12,pygame==2.1.3
p4a.bootstrap = sdl2
orientation = landscape
fullscreen = 1
android.minapi = 21
android.archs = arm64-v8a
android.api = 33
android.ndk = 25b
icon.filename = %(source.dir)s/assets/icon.png
android.manifest.application_attributes = android:appCategory='game'
android.debuggable = False
android.permissions = READ_EXTERNAL_STORAGE
requirements.pip_options = --timeout=1200
