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
requirements = python3,pygame-ce
p4a.bootstrap = sdl2
orientation = landscape
fullscreen = 1
# 【必改1】NDK25b最低兼容API24，21会底层链接异常、Python虚拟机卡死
android.minapi = 24
android.archs = arm64-v8a
android.api = 33
android.ndk = 25b
icon.filename = %(source.dir)s/assets/icon.png
android.manifest.application_attributes = android:appCategory="game"
# 可选：调试时开True，打包发布再切False，不强制改
android.debuggable = False
# 【必改2】只给读权限不够，Python初始化要写缓存文件，缺少直接卡死
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
requirements.pip_options = --timeout=1200
android.accept_sdk_license = True
