environment    = "staging"
location       = "eastus"
location_short = "eus"
model_name     = "fraud-detection"
cost_center    = "ml-platform"
team           = "ml-platform-team"

# Private endpoints in staging — no public internet access.
allow_public_network_access = false

cpu_cluster_vm_size   = "Standard_DS3_v2"
cpu_cluster_max_nodes = 4

# Dedicated priority in staging: validates production behaviour without preemption risk.
gpu_cluster_vm_size     = "Standard_NC24ads_A100_v4"
gpu_cluster_vm_priority = "Dedicated"
gpu_cluster_max_nodes   = 2

gpu_inference_vm_size   = "Standard_NC24ads_A100_v4"
gpu_inference_max_nodes = 2

acr_georeplica_location = null
