# Offline environment

In case your servers don't have access to the internet directly (for example
when deploying on premises with security constraints), you need to get the
following artifacts in advance from another environment where has access to the internet.

* Some static files (zips and binaries)
* OS packages (rpm/deb files)
* Container images used by Kubespray. Exhaustive list depends on your setup
* [Optional] Python packages used by Kubespray (only required if your OS doesn't provide all python packages/versions
  listed in `requirements.txt`)
* [Optional] Helm chart files (only required if `helm_enabled=true`)

Then you need to setup the following services on your offline environment:

* an HTTP reverse proxy/cache/mirror to serve some static files (zips and binaries)
* an internal Yum/Deb repository for OS packages
* an internal container image registry that need to be populated with all container images used by Kubespray
* [Optional] an internal PyPi server for python packages used by Kubespray
* [Optional] an internal Helm registry for Helm chart files

You can get artifact lists with [generate_list.sh](/contrib/offline/generate_list.sh) script.
In addition, you can find some tools for offline deployment under [contrib/offline](/contrib/offline/README.md).

## Tip: use the original domains as top directories in the files_repo, i.e `github.com/`, `dl.k8s.io/`, `storage.googleapis.com/`, `get.helm.sh/`

## Tip: for Cilium ensure to mirror <https://helm.cilium.io/index.yaml> and the chart cilium-1.18.2.tgz in files_repo

## Access Control

### Note: access controlled files_repo

To specify a username and password for "{{ files_repo }}", used to download the binaries, you can use url-encoding. Be aware that the Boolean `unsafe_show_logs` will show these credentials when `roles/download/tasks/download_file.yml` runs the task "Download_file | Show url of file to download". You can disable that Boolean in a job-template when running AWX/AAP/Semaphore.

```yaml
files_repo_host: example.com
files_repo_path: /repo
files_repo_user: download
files_repo_pass: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          61663232643236353864663038616361373739613338623338656434386662363539613462626661
          6435333438313034346164313631303534346564316361370a306661393232626364376436386439
          64653965663965356137333436616536643132336630313235333232336661373761643766356366
          6232353233386534380a373262313634613833623537626132633033373064336261383166323230
          3164
files_repo: "https://{{ files_repo_user ~ ':' ~ files_repo_pass ~ '@' ~ files_repo_host ~ files_repo_path }}"
```

### Note: access controlled registry

Specify a "{{ registry_user }}" and "{{ registry_pass }}" for "{{ registry_addr }}",
These are used to download the container images. Ensure to encrypt the password (if used) with ansible-vault.

```yaml
registry_pass: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          61663232643236353864663038616361373739613338623338656434386662363539613462626661
          6435333438313034346164313631303534346564316361370a306661393232626364376436386439
          64653965663965356137333436616536643132336630313235333232336661373761643766356366
          6232353233386534380a373262313634613833623537626132633033373064336261383166323230
          3164
```

To enable Containerd **2+** to access the private registry:

```yaml

containerd_registries_mirrors:
  - prefix: docker.io
    mirrors:
      - host: https://registry-1.docker.io
        capabilities: ["pull", "resolve"]
        skip_verify: false
  - prefix: "{{ registry_addr }}"
    mirrors:
      - host: "https://{{ registry_addr }}"
        capabilities: ["pull", "resolve"]
        skip_verify: false
        header:
          Authorization: ["Basic {{ (registry_user + ':' + registry_pass) | b64encode }}"]
```

To enable Containerd **1.7** to access the private registry:

```yaml
containerd_registry_auth:
  - registry: "{{ registry_host }}"
    username: "{{ registry_user }}"
    password: "{{ registry_pass }}"
```

## Configure Inventory

Once all artifacts are accessible from your internal network, **adjust** the following variables
in [your inventory](/inventory/sample/group_vars/all/offline.yml) to match your environment:

```yaml
# Registry overrides
kube_image_repo: "{{ registry_host }}"
gcr_image_repo: "{{ registry_host }}"
docker_image_repo: "{{ registry_host }}"
quay_image_repo: "{{ registry_host }}"
github_image_repo: "{{ registry_host }}"
github_url: "{{ files_repo }}/github.com"
dl_k8s_io_url: "{{ files_repo }}/dl.k8s.io"
storage_googleapis_url: "{{ files_repo }}/storage.googleapis.com"
get_helm_url: "{{ files_repo }}/get.helm.sh"
local_path_provisioner_helper_image_repo: "{{ registry_host }}/busybox"
# Insecure registries for containerd (see authenticated example above)
containerd_registries_mirrors:
  - prefix: "{{ registry_addr }}"
    mirrors:
      - host: "{{ registry_host }}"
        capabilities: ["pull", "resolve"]
        skip_verify: true

# Cilium
cilium_install_extra_flags: "--repository {{ files_repo }}/helm.cilium.io/"
cilium_extra_values:
  image:
    useDigest: false
  hubble:
    relay:
      image:
        useDigest: false
    ui:
      backend:
        image:
          useDigest: false
      frontend:
        image:
          useDigest: false
  operator:
    image:
      override: "{{ registry_host }}/cilium/operator-generic:v1.18.2"
      useDigest: false
      extension: ""
  certgen:
    image:
      useDigest: false
  envoy:
    image:
      useDigest: false

# CentOS/Redhat/AlmaLinux/Rocky Linux
## Docker / Containerd
docker_rh_repo_base_url: "{{ yum_repo }}/docker-ce/$releasever/$basearch"
docker_rh_repo_gpgkey: "{{ yum_repo }}/docker-ce/gpg"

# Fedora
## Docker
docker_fedora_repo_base_url: "{{ yum_repo }}/docker-ce/{{ ansible_distribution_major_version }}/{{ ansible_architecture }}"
docker_fedora_repo_gpgkey: "{{ yum_repo }}/docker-ce/gpg"
## Containerd
containerd_fedora_repo_base_url: "{{ yum_repo }}/containerd"
containerd_fedora_repo_gpgkey: "{{ yum_repo }}/docker-ce/gpg"

# Debian
## Docker
docker_debian_repo_base_url: "{{ debian_repo }}/docker-ce"
docker_debian_repo_gpgkey: "{{ debian_repo }}/docker-ce/gpg"
## Containerd
containerd_debian_repo_base_url: "{{ ubuntu_repo }}/containerd"
containerd_debian_repo_gpgkey: "{{ ubuntu_repo }}/containerd/gpg"
containerd_debian_repo_repokey: 'YOURREPOKEY'

# Ubuntu
## Docker
docker_ubuntu_repo_base_url: "{{ ubuntu_repo }}/docker-ce"
docker_ubuntu_repo_gpgkey: "{{ ubuntu_repo }}/docker-ce/gpg"
## Containerd
containerd_ubuntu_repo_base_url: "{{ ubuntu_repo }}/containerd"
containerd_ubuntu_repo_gpgkey: "{{ ubuntu_repo }}/containerd/gpg"
containerd_ubuntu_repo_repokey: 'YOURREPOKEY'
```

For the OS specific settings, just define the one matching your OS.
If you use the settings like the one above, you'll need to define in your inventory the following variables:

* `registry_host`: Container image registry. If you _don't_ use the same repository path for the container images that
  the ones defined
  in [kubesprays-defaults's role defaults](https://github.com/kubernetes-sigs/kubespray/blob/master/roles/kubespray_defaults/defaults/main/download.yml)
  , you need to override the `*_image_repo` for these container images. If you want to make your life easier, use the
  same repository path, you won't have to override anything else.
* `registry_addr`: Container image registry, but only have [domain or ip]:[port].
* `files_repo`: HTTP webserver or reverse proxy that is able to serve the files listed above. Path is not important, you
  can store them anywhere as long as it's accessible by kubespray. It's recommended to use `*_version` in the path so
  that you don't need to modify this setting everytime kubespray upgrades one of these components.
* `yum_repo`/`debian_repo`/`ubuntu_repo`: OS package repository depending on your OS, should point to your internal
  repository. Adjust the path accordingly. Used only for Docker/Containerd packages (if needed); other packages might
  be installed from other repositories. You might disable installing packages from other repositories by skipping
  the `system-packages` tag

## Install Kubespray Python Packages

### Recommended way: Kubespray Container Image

The easiest way is to use [kubespray container image](https://quay.io/kubespray/kubespray) as all the required packages
are baked in the image.
Just copy the container image in your private container image registry and you are all set!

### Manual installation

Look at the `requirements.txt` file and check if your OS provides all packages out-of-the-box (Using the OS package
manager). For those missing, you need to either use a proxy that has Internet access (typically from a DMZ) or setup a
PyPi server in your network that will host these packages.

If you're using an HTTP(S) proxy to download your python packages:

```bash
sudo pip install --proxy=https://[username:password@]proxyserver:port -r requirements.txt
```

When using an internal PyPi server:

```bash
# If you host all required packages
pip install -i https://pypiserver/pypi -r requirements.txt

# If you only need the ones missing from the OS package manager
pip install -i https://pypiserver/pypi package_you_miss
```

## Run Kubespray as usual

Once all artifacts are in place and your inventory properly set up, you can run kubespray with the
regular `cluster.yaml` command:

```bash
ansible-playbook -i inventory/my_airgap_cluster/hosts.yaml -b cluster.yml
```

If you use [Kubespray Container Image](#recommended-way:-kubespray-container-image), you can mount your inventory inside
the container:

```bash
docker run --rm -it -v path_to_inventory/my_airgap_cluster:inventory/my_airgap_cluster myprivateregisry.com/kubespray/kubespray:v2.14.0 ansible-playbook -i inventory/my_airgap_cluster/hosts.yaml -b cluster.yml
```
