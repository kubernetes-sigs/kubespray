data "oci_objectstorage_namespace" "ci" {
  compartment_id = var.compartment_id
}

resource "oci_core_vcn" "ci" {
  compartment_id = var.compartment_id
  display_name   = "${var.cluster_name}-vcn"
  dns_label      = "kubesprayci"
  cidr_blocks    = ["10.42.0.0/16"]
  is_ipv6enabled = true
}

resource "oci_core_internet_gateway" "ci" {
  compartment_id = var.compartment_id
  display_name   = "${var.cluster_name}-internet"
  vcn_id         = oci_core_vcn.ci.id
  enabled        = true
}

resource "oci_core_nat_gateway" "ci" {
  compartment_id = var.compartment_id
  display_name   = "${var.cluster_name}-nat"
  vcn_id         = oci_core_vcn.ci.id
}

resource "oci_core_route_table" "endpoint" {
  compartment_id = var.compartment_id
  display_name   = "${var.cluster_name}-endpoint-routes"
  vcn_id         = oci_core_vcn.ci.id

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.ci.id
  }

  route_rules {
    destination       = "::/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.ci.id
  }
}

resource "oci_core_route_table" "workers" {
  compartment_id = var.compartment_id
  display_name   = "${var.cluster_name}-worker-routes"
  vcn_id         = oci_core_vcn.ci.id

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_nat_gateway.ci.id
  }

  route_rules {
    destination       = "::/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.ci.id
  }
}

resource "oci_core_security_list" "endpoint" {
  compartment_id = var.compartment_id
  display_name   = "${var.cluster_name}-endpoint-security"
  vcn_id         = oci_core_vcn.ci.id

  ingress_security_rules {
    protocol = "all"
    source   = "10.42.0.0/16"
  }

  ingress_security_rules {
    protocol = "all"
    source   = oci_core_vcn.ci.ipv6cidr_blocks[0]
  }

  dynamic "ingress_security_rules" {
    for_each = var.api_allowed_ipv4_cidrs
    content {
      protocol = "6"
      source   = ingress_security_rules.value
      tcp_options {
        min = 6443
        max = 6443
      }
    }
  }

  dynamic "ingress_security_rules" {
    for_each = var.api_allowed_ipv6_cidrs
    content {
      protocol = "6"
      source   = ingress_security_rules.value
      tcp_options {
        min = 6443
        max = 6443
      }
    }
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }

  egress_security_rules {
    protocol    = "all"
    destination = "::/0"
  }
}

resource "oci_core_security_list" "workers" {
  compartment_id = var.compartment_id
  display_name   = "${var.cluster_name}-worker-security"
  vcn_id         = oci_core_vcn.ci.id

  ingress_security_rules {
    protocol = "all"
    source   = "10.42.0.0/16"
  }

  ingress_security_rules {
    protocol = "all"
    source   = oci_core_vcn.ci.ipv6cidr_blocks[0]
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }

  egress_security_rules {
    protocol    = "all"
    destination = "::/0"
  }
}

resource "oci_core_subnet" "endpoint" {
  compartment_id             = var.compartment_id
  display_name               = "${var.cluster_name}-endpoint"
  dns_label                  = "endpoint"
  vcn_id                     = oci_core_vcn.ci.id
  cidr_block                 = "10.42.0.0/24"
  ipv6cidr_block             = cidrsubnet(oci_core_vcn.ci.ipv6cidr_blocks[0], 8, 0)
  prohibit_public_ip_on_vnic = false
  route_table_id             = oci_core_route_table.endpoint.id
  security_list_ids          = [oci_core_security_list.endpoint.id]
}

resource "oci_core_subnet" "workers" {
  compartment_id             = var.compartment_id
  display_name               = "${var.cluster_name}-workers"
  dns_label                  = "workers"
  vcn_id                     = oci_core_vcn.ci.id
  cidr_block                 = "10.42.4.0/22"
  ipv6cidr_block             = cidrsubnet(oci_core_vcn.ci.ipv6cidr_blocks[0], 8, 1)
  prohibit_public_ip_on_vnic = false
  route_table_id             = oci_core_route_table.workers.id
  security_list_ids          = [oci_core_security_list.workers.id]
}

resource "oci_containerengine_cluster" "ci" {
  compartment_id     = var.compartment_id
  kubernetes_version = var.kubernetes_version
  name               = var.cluster_name
  type               = "ENHANCED_CLUSTER"
  vcn_id             = oci_core_vcn.ci.id

  cluster_pod_network_options {
    cni_type = "OCI_VCN_IP_NATIVE"
  }

  endpoint_config {
    is_public_ip_enabled = true
    subnet_id            = oci_core_subnet.endpoint.id
  }

  options {
    ip_families           = ["IPv4", "IPv6"]
    service_lb_subnet_ids = [oci_core_subnet.endpoint.id]
  }
}

resource "oci_containerengine_node_pool" "always_on" {
  compartment_id     = var.compartment_id
  cluster_id         = oci_containerengine_cluster.ci.id
  kubernetes_version = var.kubernetes_version
  name               = "${var.cluster_name}-always-on"
  node_shape         = var.node_shape

  node_config_details {
    size = 1
    placement_configs {
      availability_domain = var.availability_domain
      subnet_id           = oci_core_subnet.workers.id
    }
    node_pool_pod_network_option_details {
      cni_type       = "OCI_VCN_IP_NATIVE"
      pod_subnet_ids = [oci_core_subnet.workers.id]
    }
  }

  node_source_details {
    source_type             = "IMAGE"
    image_id                = var.node_image_id
    boot_volume_size_in_gbs = 100
  }
}

resource "oci_containerengine_node_pool" "on_demand" {
  compartment_id     = var.compartment_id
  cluster_id         = oci_containerengine_cluster.ci.id
  kubernetes_version = var.kubernetes_version
  name               = "${var.cluster_name}-on-demand"
  node_shape         = var.node_shape

  node_config_details {
    size = var.on_demand_nodes
    placement_configs {
      availability_domain = var.availability_domain
      subnet_id           = oci_core_subnet.workers.id
    }
    node_pool_pod_network_option_details {
      cni_type       = "OCI_VCN_IP_NATIVE"
      pod_subnet_ids = [oci_core_subnet.workers.id]
    }
  }

  node_source_details {
    source_type             = "IMAGE"
    image_id                = var.node_image_id
    boot_volume_size_in_gbs = 100
  }
}

resource "oci_objectstorage_bucket" "artifacts" {
  compartment_id = var.compartment_id
  namespace      = data.oci_objectstorage_namespace.ci.namespace
  name           = var.artifact_bucket_name
  access_type    = "NoPublicAccess"
  storage_tier   = "Standard"
  versioning     = "Enabled"
}
