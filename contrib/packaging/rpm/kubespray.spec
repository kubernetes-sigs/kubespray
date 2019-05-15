%global srcname kubespray

%{!?upstream_version: %global upstream_version %{version}%{?milestone}}

Name:           kubespray
Version:        master
Release:        %(git describe | sed -r 's/v(\S+-?)-(\S+)-(\S+)/\1.dev\2+\3/')
Summary:        Ansible modules for installing Kubernetes

Group:          System Environment/Libraries
License:        ASL 2.0
Url:            https://github.com/kubernetes-incubator/kubespray
Source0:        https://github.com/kubernetes-incubator/kubespray/archive/%{upstream_version}.tar.gz#/%{name}-%{release}.tar.gz

BuildArch:      noarch
BuildRequires:  git
BuildRequires:  python2
BuildRequires:  python2-devel
BuildRequires:  python2-setuptools
BuildRequires:  python-d2to1
BuildRequires:  python2-pbr

Requires: ansible >= 2.5.0
Requires: python-jinja2 >= 2.10
Requires: python-netaddr
Requires: python-pbr

%description

Ansible-kubespray is a set of Ansible modules and playbooks for
installing a Kubernetes cluster. If you have questions, join us
on the https://slack.k8s.io, channel '#kubespray'.

%prep
%autosetup -n %{name}-%{upstream_version} -S git


%build
export PBR_VERSION=%{release}
%{__python2} setup.py build bdist_rpm


%install
export PBR_VERSION=%{release}
export SKIP_PIP_INSTALL=1
%{__python2} setup.py install --skip-build --root %{buildroot} bdist_rpm


%files
%doc %{_docdir}/%{name}/README.md
%doc %{_docdir}/%{name}/inventory/sample/hosts.ini
%config %{_sysconfdir}/%{name}/ansible.cfg
%config %{_sysconfdir}/%{name}/inventory/sample/group_vars/all.yml
%config %{_sysconfdir}/%{name}/inventory/sample/group_vars/k8s-cluster.yml
%license %{_docdir}/%{name}/LICENSE
%{python2_sitelib}/%{srcname}-%{release}-py%{python2_version}.egg-info
%{_datarootdir}/%{name}/roles/
%{_datarootdir}/%{name}/playbooks/
%defattr(-,root,root)


%changelog
