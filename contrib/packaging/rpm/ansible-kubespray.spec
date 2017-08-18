%global srcname ansible_kubespray

%{!?upstream_version: %global upstream_version %{version}%{?milestone}}

Name:           ansible-kubespray
Version:        XXX
Release:        XXX
Summary:        Ansible modules for installing Kubernetes

Group:          System Environment/Libraries
License:        ASL 2.0
Vendor:         Kubespray <smainklh@gmail.com>
Url:            https://github.com/kubernetes-incubator/kubespray
Source0:        https://github.com/kubernetes-incubator/kubespray/archive/%{upstream_version}.tar.gz

BuildArch:      noarch
BuildRequires:  git
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
BuildRequires:  python-d2to1
BuildRequires:  python-pbr

Requires: ansible
Requires: python-jinja2
Requires: python-netaddr

%description

Ansible-kubespray is a set of Ansible modules and playbooks for
installing a Kubernetes cluster. If you have questions, join us
on the https://slack.k8s.io, channel '#kubespray'.

%prep
%autosetup -n %{name}-%{upstream_version} -S git


%build
%{__python2} setup.py build


%install
export PBR_VERSION=%{version}
export SKIP_PIP_INSTALL=1
%{__python2} setup.py install --skip-build --root %{buildroot}


%files
%doc README.md
%doc inventory/inventory.example
%config /etc/kubespray/ansible.cfg
%config /etc/kubespray/inventory/group_vars/all.yml
%config /etc/kubespray/inventory/group_vars/k8s-cluster.yml
%license LICENSE
%{python2_sitelib}/%{srcname}-%{version}-py%{python2_version}.egg-info
/usr/local/share/kubespray/roles/
/usr/local/share/kubespray/playbooks/
%defattr(-,root,root)


%changelog
