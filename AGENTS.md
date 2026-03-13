# AGENTS.md — Kubespray Codebase Guide for AI Agents

Kubespray deploys production-ready Kubernetes clusters using Ansible.

- **Repo**: <https://github.com/kubernetes-sigs/kubespray>
- **Docs**: <https://kubespray.io>
- See [README.md](README.md) for supported platforms, components, and quick start
- See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, linting, testing, and PR workflow

## Directory Layout

```
.
├── cluster.yml                  # Top-level entry point
├── upgrade_cluster.yml          # Cluster upgrade
├── scale.yml                    # Scale nodes
├── remove-node.yml              # Remove node
├── playbooks/                   # Core playbooks
├── roles/                       # Ansible roles (bulk of logic)
│   ├── kubespray_defaults/      #   Default variables & checksums
│   ├── kubernetes/              #   control-plane, node, kubeadm, client, preinstall
│   ├── kubernetes-apps/         #   Cluster add-ons
│   ├── network_plugin/          #   CNI plugins (calico, cilium, flannel, ...)
│   ├── container-engine/        #   CRI runtimes (containerd, cri-o, docker)
│   ├── etcd/                    #   etcd cluster
│   ├── download/                #   Binary & image downloads
│   └── ...
├── inventory/sample/            # Sample inventory & group_vars
├── contrib/                     # Terraform, offline, OS services
├── docs/                        # Documentation
├── tests/                       # Molecule, CI configs
├── scripts/                     # Helper scripts
├── library/                     # Custom Ansible modules
└── .pre-commit-config.yaml      # Linting hooks
```

## Key Entry Points

| File | Purpose |
|------|---------|
| `roles/kubespray_defaults/defaults/main/main.yml` | Core default variables (`kube_version`, `container_manager`, `kube_network_plugin`, ...) |
| `roles/kubespray_defaults/defaults/main/download.yml` | Download URLs, versions, and the `downloads` dict |
| `roles/kubespray_defaults/vars/main/checksums.yml` | Binary checksums (`{arch: {version: sha256}}`, must be version-sorted) |
| `roles/network_plugin/tasks/main.yml` | CNI plugin dispatcher — includes `network_plugin/{{ kube_network_plugin }}` |
| `roles/kubernetes-apps/meta/main.yml` | Add-on wiring — conditional `dependencies` list |
| `playbooks/cluster.yml` | Main deployment orchestration |
| `inventory/sample/group_vars/` | Sample variable overrides |

See [docs/ansible/vars.md](docs/ansible/vars.md) for full variable reference.
See [docs/advanced/downloads.md](docs/advanced/downloads.md) for download mechanism details.

## Variable Precedence

From lowest to highest:

1. `roles/<role>/defaults/main.yml` — role defaults
2. `inventory/<cluster>/group_vars/all/*.yml` — cluster-wide
3. `inventory/<cluster>/group_vars/k8s_cluster/*.yml` — K8s group
4. `inventory/<cluster>/host_vars/<host>.yml` — per-host
5. Extra vars (`-e`) on command line

## Architecture Patterns

### Download & Checksums

All binary/image downloads are centralized in `roles/kubespray_defaults/`:

- **Checksums** (`vars/main/checksums.yml`): `{component}_checksums` maps `{arch: {version: sha256}}`. Versions must be sorted descending (enforced by `check-checksums-sorted` hook).
- **Download vars** (`defaults/main/download.yml`): the `downloads` dict defines `url`, `checksum`, `dest`, `groups` per component.
- **Execution**: `roles/download/tasks/main.yml` iterates `downloads`, calling `download_file.yml` or `download_container.yml`.
- **Auto-updater**: `scripts/component_hash_update/` fetches upstream checksums.

### Adding a New CNI Plugin

`roles/network_plugin/tasks/main.yml` dynamically includes `network_plugin/{{ kube_network_plugin }}`:

1. Create `roles/network_plugin/<name>/` with at least `tasks/main.yml`, `defaults/main.yml`, `meta/main.yml`
2. Add download entries and checksums if the plugin needs binary downloads
3. Users select via `kube_network_plugin: <name>` in their inventory

### Adding a New Add-on

Add-ons are wired via `roles/kubernetes-apps/meta/main.yml` dependencies:

1. Create `roles/kubernetes-apps/<name>/` with `tasks/main.yml`, `defaults/main.yml`
2. Add enable flag in `roles/kubespray_defaults/defaults/main/main.yml`: `<name>_enabled: false`
3. Add dependency in `roles/kubernetes-apps/meta/main.yml`:
   ```yaml
   - role: kubernetes-apps/<name>
     when: <name>_enabled
   ```

### Pre-commit Hooks

The `propagate-ansible-variables` hook auto-updates `README.md` and `Dockerfile` to reflect current default versions. The `check-checksums-sorted` hook enforces version ordering.

## Code Style

- **YAML**: 2-space indent, `---` header, `yamllint --strict`
- **Ansible**: `ansible-lint`, FQCN (`ansible.builtin.*`), templates use `.j2`
- **Shell**: `shellcheck --severity=error`
- **Markdown**: `markdownlint` (excludes `.github/`, `docs/_sidebar.md`)

Always run `pre-commit run -a` before committing.
