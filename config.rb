# vagrant/config.rb — Lokale Testkonfiguration für graceful_rolling Upgrade-Tests
#
# Topologie:
#   k8s-1, k8s-2, k8s-3  →  control-plane + etcd  (3 Nodes, etcd-Quorum: toleriert 1 Ausfall)
#   k8s-4, k8s-5, k8s-6  →  Worker-Nodes           (dediziert, kein CP)
#
# Upgrade-Testplan:
#   1. vagrant up                              → Cluster auf v1.34.4 installieren
#   2. vagrant snapshot save pre-upgrade      → Snapshot sichern
#   3. Test A — graceful_rolling (neu):
#        ./tests/scripts/monitor-upgrade.sh &
#        ansible-playbook playbooks/upgrade_cluster.yml \
#          -i .vagrant/provisioners/ansible/inventory \
#          -e kube_version=v1.35.1 -vv
#   4. vagrant snapshot restore pre-upgrade
#   5. Test B — linear (alt):
#        ./tests/scripts/monitor-upgrade.sh &
#        ansible-playbook playbooks/upgrade_cluster.yml \
#          -i .vagrant/provisioners/ansible/inventory \
#          -e kube_version=v1.35.1 -e upgrade_strategy=linear -vv
#
# RAM-Bedarf: 6 × 3 GB ≈ 18 GB (von ~60 GB verfügbar)

# ── VM-Größe ──────────────────────────────────────────────────────────────────
$num_instances        = 6
$instance_name_prefix = "k8s"
$vm_memory            = 3096    # MB pro VM
$vm_cpus              = 2
$os                   = "ubuntu2404"

# ── Cluster-Topologie ─────────────────────────────────────────────────────────
# Control-Plane + etcd: k8s-1 bis k8s-3
# 3 etcd-Nodes = Quorum bei 1 ausgefallenen Node (floor(3/2)+1 = 2 müssen erreichbar sein)
$first_control_plane      = 1
$control_plane_instances  = 3
$first_etcd               = 1
$etcd_instances           = 3

# Worker: k8s-4 bis k8s-6
# $kube_node_instances = $num_instances - $first_node + 1 = 6 - 4 + 1 = 3
$first_node               = 4

# ── Netzwerk ──────────────────────────────────────────────────────────────────
$network_plugin = "calico"
$subnet         = "172.18.8"

# ── Download-Cache ────────────────────────────────────────────────────────────
# Alle Binaries + Container-Images einmal auf k8s-1 laden und verteilen.
# Folgeprovisionierungen nutzen den lokalen Cache.
$download_run_once    = "True"
$download_force_cache = "False"

# ── Ansible Extra-Vars ────────────────────────────────────────────────────────
# kube_version = Installations-Version des initialen Clusters.
# Die Upgrade-Zielversion wird beim Upgrade per -e kube_version=v1.35.1 gesetzt.
$extra_vars = {
  kube_version: "v1.34.4",

  # graceful_rolling: 2 Worker gleichzeitig — Sliding Window klar sichtbar:
  # W4 + W5 starten, W4 fertig → W6 startet sofort ohne auf W5 zu warten.
  upgrade_node_concurrency: 2,

  # Control-Plane sequenziell: etcd-Quorum (2 von 3) bleibt während des Upgrades erhalten.
  upgrade_control_plane_concurrency: 1,
}
