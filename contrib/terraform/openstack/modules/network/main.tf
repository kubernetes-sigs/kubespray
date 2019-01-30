resource "openstack_networking_router_v2" "k8s" {
  name                = "${var.cluster_name}-router"
  count               = "${var.use_neutron}"
  admin_state_up      = "true"
  external_network_id = "${var.external_net}"
}

resource "openstack_networking_network_v2" "k8s" {
  name           = "${var.network_name}"
  count          = "${var.use_neutron}"
  admin_state_up = "true"
}

resource "openstack_networking_subnet_v2" "k8s" {
  name            = "${var.cluster_name}-internal-network"
  count           = "${var.use_neutron}"
  network_id      = "${openstack_networking_network_v2.k8s.id}"
  cidr            = "${var.subnet_cidr}"
  ip_version      = 4
  dns_nameservers = "${var.dns_nameservers}"
}

resource "openstack_networking_router_interface_v2" "k8s" {
  count     = "${var.use_neutron}"
  router_id = "${openstack_networking_router_v2.k8s.id}"
  subnet_id = "${openstack_networking_subnet_v2.k8s.id}"
}

data "openstack_networking_network_v2" "bastion_network" {
  count      = "${var.use_neutron}"
  name       = "${(var.bastion_network_name != var.network_name) ? var.bastion_network_name : openstack_networking_network_v2.k8s.name}"
  depends_on = ["openstack_networking_subnet_v2.k8s"]
}

data "openstack_networking_subnet_v2" "bastion_ntwk_subnets" {
  count      = "${var.use_neutron}"
  network_id = "${element(data.openstack_networking_network_v2.bastion_network.*.id, 0)}"
}

data "openstack_networking_subnet_v2" "k8s_ntwk_subnets" {
  count      = "${var.use_neutron}"
  network_id = "${openstack_networking_network_v2.k8s.id}"
  depends_on = ["openstack_networking_subnet_v2.k8s"]
}

resource "openstack_networking_router_interface_v2" "k8s_router_interface_to_bastion" {
  count     = "${(var.use_neutron && (var.bastion_network_name != var.network_name)) ? 1 : 0}"
  router_id = "${openstack_networking_router_v2.k8s.id}"
  subnet_id = "${element(data.openstack_networking_subnet_v2.bastion_ntwk_subnets.*.id, 0)}"
}

resource "openstack_networking_router_route_v2" "k8s_router_extra_routes" {
  count            = "${(!var.use_neutron) ? 0 : length(keys(var.network_router_extra_routes))}"
  depends_on       = ["openstack_networking_router_interface_v2.k8s"]
  router_id        = "${openstack_networking_router_v2.k8s.id}"
  destination_cidr = "${element(keys(var.network_router_extra_routes), count.index)}"
  next_hop         = "${lookup(var.network_router_extra_routes, element(keys(var.network_router_extra_routes), count.index))}"
}

resource "openstack_networking_subnet_route_v2" "bastion_subnet_extra_routes" {
  count            = "${(!var.use_neutron) ? 0 : length(keys(var.bastion_subnet_extra_routes))}"
  subnet_id        = "${element(data.openstack_networking_subnet_v2.bastion_ntwk_subnets.*.id, 0)}"
  destination_cidr = "${element(keys(var.bastion_subnet_extra_routes), count.index)}"
  next_hop         = "${lookup(var.bastion_subnet_extra_routes, element(keys(var.bastion_subnet_extra_routes), count.index))}"
}
