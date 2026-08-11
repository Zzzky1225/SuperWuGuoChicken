[buildozer]
pypi_mirror = https://pypi.tuna.tsinghua.edu.cn/simple
android.sdk_mirror = https://mirrors.cloud.tencent.com/AndroidSDK/
android.ndk_mirror = https://mirrors.cloud.tencent.com/AndroidSDK/ndk-bundle/
android.accept_license = yes

[app]
title = 超级吴国鸡跑酷
package.name = wuguoji
package.domain = com.chaoji
version = 1.0
android.versioncode = 1
source.dir = .
source.include_exts = py,png,jpg,wav,ttf
source.include_patterns = assets/*
requirements = python3,pygame,pyjnius
android.bootstrap = sdl2
orientation = landscape
fullscreen = 1
android.minapi = 21
android.archs = arm64-v8a,armeabi-v7a
icon.filename = %(source.dir)s/assets/icon.png
android.manifest.application_attributes = android:appCategory='game'
android.debuggable = True
android.permissions = READ_EXTERNAL_STORAGE
requirements.pip_options = --timeout=1200