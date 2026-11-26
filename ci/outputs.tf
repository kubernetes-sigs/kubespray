output "cluster_id" {
  description = "OCID of the new OKE cluster."
  value       = oci_containerengine_cluster.ci.id
}

output "always_on_node_pool_id" {
  description = "OCID of the one-node baseline pool."
  value       = oci_containerengine_node_pool.always_on.id
}

output "on_demand_node_pool_id" {
  description = "OCID of the zero-to-four-node capacity pool."
  value       = oci_containerengine_node_pool.on_demand.id
}

output "artifact_bucket_name" {
  description = "Private Object Storage bucket for CI artifacts."
  value       = oci_objectstorage_bucket.artifacts.name
}
