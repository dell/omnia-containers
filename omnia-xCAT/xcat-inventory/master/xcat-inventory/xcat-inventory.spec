Summary: xCAT Inventory
Name: xcat-inventory
Version: %{?version:%{version}}%{!?version:%(cat Version)}
Release: %{?release:%{release}}%{!?release:snap%(date +"%Y%m%d%H%M")}
Epoch: 1
License: EPL
Group: Applications/System
Source: xcat-inventory-%{version}.tar.gz
Packager: IBM Corp.
Vendor: IBM Corp.
Distribution: %{?_distribution:%{_distribution}}%{!?_distribution:%{_vendor}}
Prefix: /opt/xcat
BuildRoot: /var/tmp/%{name}-%{version}-%{release}-root
%if 0%{?rhel} >= 8
Requires: python2-psycopg2 python2-sqlalchemy >= 0.8.0 python2-PyMySQL python2-pyyaml python2-six python2-jinja2 git
%else
Requires: python-psycopg2 python-sqlalchemy >= 0.8.0 MySQL-python PyYAML python-six python-jinja2 git
%endif

%ifos linux
BuildArch: noarch
%endif

%description

%prep
%setup -q -n xcat-inventory

%build
VERINFO=%{version}' (git commit '%{gitcommit}')'
sed -i s/\#VERSION_SUBSTITUTE\#/"$VERINFO"/g $RPM_BUILD_DIR/$RPM_PACKAGE_NAME/xcclient/inventory/shell.py

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/%{prefix}/bin
install -d $RPM_BUILD_ROOT/%{prefix}/lib/python/xcclient
install -d $RPM_BUILD_ROOT/%{prefix}/lib/python/xcclient/inventory
install -d $RPM_BUILD_ROOT/%{prefix}/lib/python/xcclient/inventory/schema
install -d $RPM_BUILD_ROOT/%{prefix}/share/xcat/inventory_templates
install -d $RPM_BUILD_ROOT/etc
install -d $RPM_BUILD_ROOT/etc/xcat

install -m755 cli/* $RPM_BUILD_ROOT/%{prefix}/bin
install -m644 xcclient/*.py $RPM_BUILD_ROOT/%{prefix}/lib/python/xcclient
install -m644 xcclient/inventory/*.py $RPM_BUILD_ROOT/%{prefix}/lib/python/xcclient/inventory
install -m644 xcclient/inventory/inventory.cfg $RPM_BUILD_ROOT/etc/xcat
cp -a xcclient/inventory/schema/* $RPM_BUILD_ROOT/%{prefix}/lib/python/xcclient/inventory/schema
cp -a templates/* $RPM_BUILD_ROOT/%{prefix}/share/xcat/inventory_templates   

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)

%{prefix}
%config(noreplace) /etc/xcat/inventory.cfg
%changelog

%post

%preun

