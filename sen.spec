%global srcname sen
%global sum Terminal User Interface for docker engine


# enable tests by default, disable with --without tests
%bcond_without tests


Name:           %{srcname}
Version:        0.8.0
Release:        1%{?dist}
Summary:        %{sum}

License:        MIT
URL:            http://pypi.python.org/pypi/%{srcname}
Source0:        https://files.pythonhosted.org/packages/source/s/%{srcname}/%{srcname}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python3-%{srcname}
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools


%description
sen enables you to manage your containers and images interactively directly
from command line. Interface is similar to htop, alot or tig.


%package -n python3-%{srcname}
Requires:       python3-urwid
Requires:       python3-urwidtrees
Requires:       python3-docker
%if %{with tests}
BuildRequires:  python3-pytest
BuildRequires:  python3-flexmock
BuildRequires:  python3-urwid
BuildRequires:  python3-urwidtrees
BuildRequires:  python3-docker
%endif  # tests

Summary:        %{sum}
%{?python_provide:%python_provide python3-%{srcname}}

%description -n python3-%{srcname}
sen enables you to manage your containers and images interactively directly
from command line. Interface is similar to htop, alot or tig.


%prep
%autosetup -n %{srcname}-%{version}
sed -i 1d sen/cli.py


%build
%py3_build


%install
%py3_install

%check
%if %{with tests}
py.test-%{python3_version} -vv tests || :
%endif  # tests


%files
%license LICENSE
%{_bindir}/sen
%doc README.md

%files -n python3-%{srcname}
%license LICENSE
%{python3_sitelib}/*


%changelog
* Wed Nov 20 2024 Tomas Tomecek <ttomecek@redhat.com> - 0.8.0-1
- 0.8.0 upstream release

* Wed Apr 12 2023 Tomas Tomecek <ttomecek@redhat.com> - 0.7.0-1
- 0.7.0 upstream release

* Mon Nov 01 2021 Tomas Tomecek <ttomecek@redhat.com> - 0.6.2-1
- 0.6.2 upstream release

* Mon Mar 04 2019 Tomas Tomecek <ttomecek@redhat.com> - 0.6.1-1
- New upstream release 0.6.1

* Sat Feb 02 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.6.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Sat Jul 14 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.6.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Tue Jun 19 2018 Miro Hrončok <mhroncok@redhat.com> - 0.6.0-2
- Rebuilt for Python 3.7

* Thu Mar 22 2018 Tomas Tomecek <ttomecek@redhat.com> - 0.6.0-1
- New upstream release 0.6.0

* Fri Feb 09 2018 Fedora Release Engineering <releng@fedoraproject.org> - 0.5.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Thu Jul 27 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.5.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Mon Mar 27 2017 Tomas Tomecek <ttomecek@redhat.com> - 0.5.1-1
- new upstream release: 0.5.1

* Sat Feb 11 2017 Fedora Release Engineering <releng@fedoraproject.org> - 0.5.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Thu Jan 12 2017 Tomas Tomecek <ttomecek@redhat.com> - 0.5.0-1
- new upstream release: 0.5.0

* Mon Dec 19 2016 Miro Hrončok <mhroncok@redhat.com> - 0.4.0-2
- Rebuild for Python 3.6

* Tue Aug 09 2016 Tomas Tomecek <ttomecek@redhat.com> - 0.4.0-1
- new upstream release: 0.4.0

* Tue Jul 19 2016 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.3.0-2
- https://fedoraproject.org/wiki/Changes/Automatic_Provides_for_Python_RPM_Packages

* Thu May 05 2016 Tomas Tomecek <ttomecek@redhat.com> - 0.3.0-1
- new upstream release: 0.3.0

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Dec 10 2015 Tomas Tomecek <ttomecek@redhat.com> - 0.1.1-1
- initial build

