#!/bin/bash

pkg_file="ovis-ldms.tar.gz"

echo "Install epel-release"
dnf install -y epel-release
dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm

# Doxygen
dnf config-manager -y --set-enabled powertools

echo "Update"
dnf update -y

echo "Install packages"
dnf install -y \
    autoconf \
    automake \
    bison \
    bzip2 \
    curl \
    doxygen \
    flex \
    gcc \
    gettext \
    git \
    gcc-c++ \
    gzip \
    hostname \
    jansson-devel \
    jansson \
    jq \
    libcurl-devel \
    libibverbs \
    libpfm-devel \
    librdkafka \
    librdmacm \
    less \
    libtool \
    m4 \
    make \
    openssl \
    openssl-devel \
    openssl-libs \
    papi-devel \
    pkg-config \
    python3-pyverbs \
    python3 \
    python3-docutils \
    python3-pip \
    python3-pycurl \
    python3-devel \
    python3-distutils-extra \
    python3-Cython \
    platform-python-devel \
    python3-docutils \
    python3-pip \
    rpm-build \
    rsync \
    rubygems \
    ruby \
    ruby-devel \
    tree \
    vim \
    wget \
    which

#--------------------------------
# CLEAN
#--------------------------------
echo "[>>] Clean previous install"
if [ -f "$pkg_file" ]; then
  rm -rf "$pkg_file"
fi
if [ -f "*.rpm" ]; then
  rm -rf "*.rpm"
fi
find ./ -name "*.deb" -delete
for i in \
  /app \
  /opt/ovis-ldms \
  /app/etc/ldms \
  /app/etc/systemd/system/ldmsd.kokkos.service \
  /app/etc/systemd/system/ldmsd.aggregator.service \
  /app/etc/systemd/system/ldmsd.sampler.service \
  lib/etc/ld.so.conf.d/ovis-ld-so.conf \
  $pkg_file \
; do
  if [ -e "$i" ]; then
    echo "[>>]  Delete $i"
    rm -rf "$i"
  fi
done
echo "[>>] Remove old rpm and tar.gz"
rm -rf ovis-ldms.{rpm,tar.gz}
if [ -d "/build/libserde" ]; then
    rm -rf "/build/libserde"
fi
echo "[>>] Clean source tree"
rm -rf .version
make uninstall
make distclean
make clean
make maintainer-clean
echo "[>>] Clean isn't clean. Remove any file with an .in file"
find ./ -name "*.in" |(while read FOO; do base="$(echo $FOO |sed 's/\.in$//g')"; echo "Remove $base"; rm -rf  "$base"; done; )
find ./ -name "*.cache" -delete

#--------------------------------
# BUILD 
#--------------------------------
echo "[>>] Get in source dir"
#popd
#rpm -i datacenter-gpu-manager-2.2.3-1-x86_64.rpm 
set -xe
echo "#define DCGM_PUBLIC_API" >> "/usr/include/dcgm_api_export.h"
echo "[--] Build ldms"
echo "[>>] autoreconf"
autoreconf --install
echo "[>>] autogen"
./autogen.sh
echo "[>>] configure"
../scripts/configure.sh
echo "[>>] make"
make -j 10
echo "[>>] make install"
make install
echo "[>>] Find python3 site packages"

PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PYTHON_SITE_PKGS="$(python3 -m site --user-site)"
echo "PYTHON_VERSION=$PYTHON_VERSION"
echo "PYTHON_SITE_PKGS=$PYTHON_SITE_PKGS"

#--------------------------------
# ASSEBLE PACKAGE TREE
#--------------------------------
echo "[>>] Make package tree staging area: /app"
mkdir -p \
  /app/etc/profile.d \
  /app/etc/sysconfig \
  /app/lib/systemd/system \
  /app/opt \
  /app/${PYTHON_SITE_PKGS} \
  /app/usr/share
echo "[>>] Stage /usr/share/man"
mv /opt/ovis-ldms/share/man /app/usr/share/
echo "[>>] Stage /opt/ovis-ldms"
mv /opt/ovis-ldms /app/opt/
rsync -a /app/opt/ovis-ldms/share/doc/ovis-ldms/sample_init_scripts/opt/etc/systemd /app/opt/ovis-ldms/etc/
rsync -a /app/opt/ovis-ldms/share/doc/ovis-ldms/sample_init_scripts/opt/etc/ldms /app/opt/ovis-ldms/etc/
echo "[>>] Stage /etc"
ln -s /opt/ovis-ldms/etc/profile.d/set-ovis-variables.sh /app/etc/profile.d/set-ovis-variables.sh
echo "[>>] Stage /lib/systemd/system"
ln -s /opt/ovis-ldms/etc/systemd/system/nersc-ldmsd.sampler.service /app/lib/systemd/system/nersc-ldmsd.sampler.service
echo "[>>] Stage ${PYTHON_SITE_PKGS}"
ln -s /opt/ovis-ldms/lib/${PYTHON_VERSION}/ldmsd /app/${PYTHON_SITE_PKGS}/
ln -s /opt/ovis-ldms/lib/${PYTHON_VERSION}/ovis_ldms /app/${PYTHON_SITE_PKGS}/

#--------------------------------
# PACKAGE
#--------------------------------
echo "[>>] Bundle"
ls -tlr /app
tar -C /app -czvpf "$pkg_file" .

echo "[>>] Build Product"
du -sh $pkg_file

echo "[>>] install fpm"

# Workaround due pleaserun hard dependency on ruby-3.0
# REF: https://github.com/jordansissel/fpm/issues/2048
cat > gems.rb <<'EOF'
gem 'dotenv', '= 2.8.1'
gem 'fpm', '= 1.15.1'
EOF

gem install --no-document --file gems.rb 

fpm --version
echo "[>>] Build RPM with fpm"
fpm \
--input-type tar \
--output-type rpm \
--name ovis-ldms \
--version $(cat .version) \
--iteration 1 \
--depends bash \
--depends python3-Cython \
--depends python3-devel \
--directories=/opt/ovis-ldms \
--post-uninstall ../scripts/rpm_postuninstall.txt \
--license "GPLv2 or BSD" \
--rpm-group root \
--description "This package provides the LDMS commands and libraries.\n* ldmsd: the LDMS daemon, which can run as sampler or aggregator (or both).\n* ldms_ls: the tool to list metric information of an ldmsd.\n* ldmsctl: the tool to control an ldmsd." \
--rpm-summary "LDMS - Lighweight Distributed Metric Service" \
--package ovis-ldms-$(cat .version).x86_64.rpm \
$pkg_file

echo "[>>] List rpm created"
ls -tlr *tar.gz *.rpm
echo "[>>] List files in rpm"
rpm -qlp "ovis-ldms-$(cat .version).x86_64.rpm"
echo "[>>] Show rpm scripts"
rpm -qp --scripts "ovis-ldms-$(cat .version).x86_64.rpm"
echo "[>>] Show rpm info"
rpm -qi "ovis-ldms-$(cat .version).x86_64.rpm"
echo "[--] Success"

