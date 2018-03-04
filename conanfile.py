#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment, tools
import os


class FDKAACConan(ConanFile):
    name = "libfdk_aac"
    version = "0.1.5"
    url = "https://github.com/bincrafters/conan-libfdk_aac"
    description = "A standalone library of the Fraunhofer FDK AAC code from Android"
    license = "https://github.com/mstorsjo/fdk-aac/blob/master/NOTICE"
    exports_sources = ["CMakeLists.txt", "LICENSE"]
    settings = "os", "arch", "compiler", "build_type"
    homepage = "https://sourceforge.net/projects/opencore-amr/"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = "shared=False", "fPIC=True"

    @property
    def is_mingw(self):
        return self.settings.compiler == 'gcc' and self.settings.os == 'Windows'

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def system_requirements(self):
        if self.settings.os == "Linux" and tools.os_info.is_linux:
            if tools.os_info.with_apt:
                installer = tools.SystemPackageTool()
                packages = ['autoconf', 'automake', 'libtool-bin']
                for package in packages:
                    installer.install(package)

    def source(self):
        source_url = "https://github.com/mstorsjo/fdk-aac/archive/v%s.tar.gz" % self.version
        tools.get(source_url)
        extracted_dir = "fdk-aac-" + self.version
        os.rename(extracted_dir, "sources")

    def build_vs(self):
        with tools.chdir('sources'):
            with tools.vcvars(self.settings, force=True):
                with tools.remove_from_path('mkdir'):
                    tools.replace_in_file('Makefile.vc',
                                          'CFLAGS   = /nologo /W3 /Ox /MT',
                                          'CFLAGS   = /nologo /W3 /Ox /%s' % str(self.settings.compiler.runtime))
                    self.run('nmake -f Makefile.vc')
                    self.run('nmake -f Makefile.vc prefix="%s" install' % os.path.abspath(self.package_folder))

    def build_configure(self):
        with tools.chdir('sources'):
            win_bash = self.is_mingw
            prefix = os.path.abspath(self.package_folder)
            if self.is_mingw:
                prefix = tools.unix_path(prefix, tools.MSYS2)
            args = ['--prefix=%s' % prefix]
            if self.options.shared:
                args.extend(['--disable-static', '--enable-shared'])
            else:
                args.extend(['--disable-shared', '--enable-static'])
            if self.settings.os != 'Windows' and self.options.fPIC:
                args.append('--with-pic')
            env_build = AutoToolsBuildEnvironment(self, win_bash=win_bash)
            self.run('autoreconf -fiv', win_bash=win_bash)
            env_build.configure(args=args)
            env_build.make()
            env_build.make(args=['install'])

    def build(self):
        if self.settings.compiler == 'Visual Studio':
            self.build_vs()
        elif self.is_mingw:
            msys_bin = self.deps_env_info['msys2_installer'].MSYS_BIN
            with tools.environment_append({'PATH': [msys_bin],
                                           'CONAN_BASH_PATH': os.path.join(msys_bin, 'bash.exe')}):
                self.build_configure()
        else:
            self.build_configure()

    def package(self):
        self.copy(pattern="NOTICE", src='sources', dst="licenses")

    def package_info(self):
        if self.settings.compiler == 'Visual Studio' and self.options.shared:
            self.cpp_info.libs = ['fdk-aac.dll.lib']
        else:
            self.cpp_info.libs = ['fdk-aac']
