resource "openstack_lb_loadbalancer_v2" "k8s_lb" {
  count             = var.k8s_master_loadbalancer_enabled ? 1 : 0
  name              = "${var.cluster_name}-api-loadbalancer"
  vip_subnet_id     = var.subnet_id
}

resource "openstack_lb_listener_v2" "api_listener"{
  count             = var.k8s_master_loadbalancer_enabled ? 1 : 0
  name              = "api-listener"
  protocol          = "TCP"
  protocol_port     = var.k8s_master_loadbalancer_listener_port
  loadbalancer_id   = openstack_lb_loadbalancer_v2.k8s_lb[0].id
  depends_on        = [ openstack_lb_loadbalancer_v2.k8s_lb ]
}

resource "openstack_lb_pool_v2" "api_pool" {
  count             = var.k8s_master_loadbalancer_enabled ? 1 : 0
  name              = "api-pool"
  protocol          = "TCP"
  lb_method         = "ROUND_ROBIN"
  listener_id       = openstack_lb_listener_v2.api_listener[0].id
  depends_on        = [ openstack_lb_listener_v2.api_listener ]
}

resource "openstack_lb_member_v2" "lb_member" {
  count             = var.k8s_master_loadbalancer_enabled ? length(var.k8s_master_ips) : 0
  name              = var.k8s_master_ips[count.index].name
  pool_id           = openstack_lb_pool_v2.api_pool[0].id
  address           = var.k8s_master_ips[count.index].access_ip_v4
  protocol_port     = var.k8s_master_loadbalancer_server_port
  depends_on        = [ openstack_lb_pool_v2.api_pool ]
}

resource "openstack_lb_monitor_v2" "monitor" {
  count       = var.k8s_master_loadbalancer_enabled ? 1 : 0
  name        = "Api Monitor"
  pool_id     = openstack_lb_pool_v2.api_pool[0].id
  type        = "TCP"
  delay       = 10
  timeout     = 5
  max_retries = 5
}

resource "openstack_networking_floatingip_v2" "floatip_1" {
  count = var.k8s_master_loadbalancer_enabled && var.k8s_master_loadbalancer_public_ip == "" ? 1 : 0
  pool = var.floatingip_pool
}

resource "openstack_networking_floatingip_associate_v2" "public_ip" {
  count             = var.k8s_master_loadbalancer_enabled ? 1 : 0
  floating_ip       = var.k8s_master_loadbalancer_public_ip != "" ? var.k8s_master_loadbalancer_public_ip : openstack_networking_floatingip_v2.floatip_1[0].address
  port_id           = openstack_lb_loadbalancer_v2.k8s_lb[0].vip_port_id
  depends_on        = [ openstack_lb_loadbalancer_v2.k8s_lb ]
}
