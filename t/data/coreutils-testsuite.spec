#
# spec file for package coreutils-testsuite
#
# Copyright (c) 2017 SUSE LINUX GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/
#


Name:           coreutils-testsuite
Summary:        GNU Core Utilities
License:        GPL-3.0+
Group:          System/Base
Url:            http://www.gnu.org/software/coreutils/
Version:        8.28
Release:        0

#################################################################
#################################################################
###                ! ! ! R E M I N D E R ! ! !                ###
#################################################################
###    Please call "./pre_checkin.sh" prior to submitting.    ###
###    (This will regenerate coreutils-testsuite.spec)        ###
#################################################################
#################################################################

BuildRequires:  automake
BuildRequires:  gmp-devel
BuildRequires:  libacl-devel
BuildRequires:  libattr-devel
BuildRequires:  libcap-devel
BuildRequires:  libselinux-devel
BuildRequires:  makeinfo
BuildRequires:  perl
BuildRequires:  suse-module-tools
BuildRequires:  xz
%if %{suse_version} > 1320
BuildRequires:  gcc-PIE
%endif
%if "%{name}" == "coreutils-testsuite"
BuildRequires:  acl
BuildRequires:  gdb
BuildRequires:  perl-Expect
BuildRequires:  python-pyinotify
BuildRequires:  strace
BuildRequires:  timezone
# Some tests need the 'bin' user.
BuildRequires:  user(bin)
%ifarch %ix86 x86_64 ppc ppc64 s390x armv7l armv7hl
BuildRequires:  valgrind
%endif
%endif

%if "%{name}" == "coreutils"
Provides:       fileutils = %{version}
Provides:       mktemp = %{version}
Provides:       sh-utils = %{version}
Provides:       stat = %{version}
Provides:       textutils = %{version}
%endif

%if "%{name}" == "coreutils"
Recommends:     %{name}-lang = %version
%endif

# this will create a cycle, broken up randomly - coreutils is just
# too core to have other prerequisites.
#PreReq:         permissions
PreReq:         %{install_info_prereq}

BuildRoot:      %{_tmppath}/%{name}-%{version}-build

#Git-Web:	http://git.savannah.gnu.org/gitweb/?p=coreutils.git
#Git-Clone:	git://git.sv.gnu.org/coreutils
%if "%{name}" == "coreutils"
# For upgrading you now just need to increase the version, remove the old
# tarballs, then run osc service localrun download_files, osc addremove,
# osc vc and osc ci and you are done.
Source0:        https://ftp.gnu.org/gnu/%{name}/%{name}-%{version}.tar.xz
Source1:        https://ftp.gnu.org/gnu/%{name}/%{name}-%{version}.tar.xz.sig
Source2:        https://savannah.gnu.org/project/memberlist-gpgkeys.php?group=%{name}&download=1&file=./%{name}.keyring
%else
# In "coreutils-testsuite", we use the version controlled file from "coreutils".
# otherwise that file would be downloaded twice during the above mentioned
# upgrade procedure.
Source0:        coreutils-%{version}.tar.xz
Source1:        coreutils-%{version}.tar.xz.sig
Source2:        coreutils.keyring
%endif

Source3:        baselibs.conf

Patch1:         coreutils-remove_hostname_documentation.patch
Patch3:         coreutils-remove_kill_documentation.patch
Patch4:         coreutils-i18n.patch
Patch8:         coreutils-sysinfo.patch
Patch16:        coreutils-invalid-ids.patch

# OBS / RPMLINT require /usr/bin/timeout to be built with the -fpie option.
Patch100:       coreutils-build-timeout-as-pie.patch

# There is no network in the build root so make the test succeed
Patch112:       coreutils-getaddrinfo.patch

# Assorted fixes
Patch113:       coreutils-misc.patch

# Skip 2 valgrind'ed sort tests on ppc/ppc64 which would fail due to
# a glibc issue in mkstemp.
Patch300:       coreutils-skip-some-sort-tests-on-ppc.patch

%ifarch %ix86 x86_64 ppc ppc64
Patch301:       coreutils-skip-gnulib-test-tls.patch
%endif

# tests: shorten extreme-expensive factor tests
Patch303:       coreutils-tests-shorten-extreme-factor-tests.patch

Patch500:       coreutils-disable_tests.patch
Patch501:       coreutils-test_without_valgrind.patch

# ================================================
%description
These are the GNU core utilities.  This package is the union of
the GNU fileutils, sh-utils, and textutils packages.

  [ arch b2sum base32 base64 basename cat chcon chgrp chmod chown chroot cksum
  comm cp csplit cut date dd df dir dircolors dirname du echo env expand expr
  factor false fmt fold groups head hostid id install join
  link ln logname ls md5sum mkdir mkfifo mknod mktemp mv nice nl nohup
  nproc numfmt od paste pathchk pinky pr printenv printf ptx pwd readlink
  realpath rm rmdir runcon seq sha1sum sha224sum sha256sum sha384sum sha512sum
  shred shuf sleep sort split stat stdbuf stty sum sync tac tail tee test
  timeout touch tr true truncate tsort tty uname unexpand uniq unlink
  uptime users vdir wc who whoami yes

# ================================================
%lang_package
%prep
%setup -q -n coreutils-%{version}
%patch4
%patch1
%patch3
%patch8
%patch16
#
%if %{suse_version} <= 1320
%patch100
%endif
%patch112
%patch113

%patch300

%ifarch %ix86 x86_64 ppc ppc64
%patch301
%endif

%patch303
%patch500
%patch501

#???## We need to statically link to gmp, otherwise we have a build loop
#???#sed -i s,'$(LIB_GMP)',%%{_libdir}/libgmp.a,g Makefile.in

# ================================================
%build
%if 0%{suse_version} >= 1200
AUTOPOINT=true autoreconf -fi
%endif
export CFLAGS="%optflags"
%configure --libexecdir=%{_libdir} \
           --enable-install-program=arch \
           DEFAULT_POSIX2_VERSION=200112 \
           alternative=199209

make -C po update-po

# Regenerate manpages
touch man/*.x

make all %{?_smp_mflags} V=1

# ================================================
%check
%if "%{name}" == "coreutils-testsuite"
  # Make our multi-byte test for sort executable
  chmod a+x tests/misc/sort-mb-tests.sh
  # Avoid parallel make, because otherwise some timeout based tests like
  # rm/ext3-perf may fail due to high CPU or IO load.
  make check-very-expensive \
    && install -d -m 755 %{buildroot}%{_docdir}/%{name} \
    && xz -c tests/test-suite.log \
         > %{buildroot}%{_docdir}/%{name}/test-suite.log.xz
%endif

# ================================================
%install
%if "%{name}" == "coreutils"
make install DESTDIR="%buildroot" pkglibexecdir=%{_libdir}/%{name}

# remove kill - we use that from util-linux.
rm -v %{buildroot}%{_bindir}/kill
rm -v %{buildroot}/%{_mandir}/man1/kill.1

#UsrMerge
install -d %{buildroot}/bin
for i in arch basename cat chgrp chmod chown cp date dd df echo \
  false ln ls mkdir mknod mktemp mv pwd rm rmdir sleep sort stat \
  stty sync touch true uname readlink md5sum
do
  ln -sf %{_bindir}/$i %{buildroot}/bin/$i
done
#EndUsrMerge
echo '.so man1/test.1' > %{buildroot}/%{_mandir}/man1/\[.1
%find_lang coreutils
%endif

# ================================================
%post
%if "%{name}" == "coreutils"
%install_info --info-dir=%{_infodir} %{_infodir}/coreutils.info.gz
%{?regenerate_initrd_post}
%endif

# ================================================
%posttrans
%if "%{name}" == "coreutils"
%{?regenerate_initrd_posttrans}
%endif

# ================================================
%postun
%if "%{name}" == "coreutils"
%install_info_delete --info-dir=%{_infodir} %{_infodir}/coreutils.info.gz
%endif

# ================================================
%files
%if "%{name}" == "coreutils"

%defattr(-,root,root)
%doc COPYING NEWS README THANKS
%{_bindir}/*
#UsrMerge
/bin/*
#EndUsrMerge
%{_libdir}/%{name}
%doc %{_infodir}/coreutils.info*.gz
%doc %{_mandir}/man1/*.1.gz
%dir %{_datadir}/locale/*/LC_TIME

%files lang -f coreutils.lang
%defattr(-,root,root)

%else

# test-suite
%dir %{_docdir}/%{name}
%doc %{_docdir}/%{name}/test-suite.log.xz

%endif

# ================================================

%changelog
