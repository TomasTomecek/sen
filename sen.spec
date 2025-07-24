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
BuildRequires:  python3-pip
BuildRequires:  python3-wheel
%generate_buildrequires
%pyproject_buildrequires


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
%pyproject_wheel


%install
%pyproject_install

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
%autochangelog

