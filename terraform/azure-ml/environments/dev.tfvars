environment    = "dev"
location       = "eastus"
location_short = "eus"
model_name     = "fraud-detection"
cost_center    = "ml-platform"
team           = "ml-platform-team"

allow_public_network_access = true

cpu_cluster_vm_size   = "Standard_DS3_v2"
cpu_cluster_max_nodes = 2

gpu_cluster_vm_size     = "Standard_NC24ads_A100_v4"
gpu_cluster_vm_priority = "LowPriority"
gpu_cluster_max_nodes   = 1

gpu_inference_vm_size   = "Standard_NC24ads_A100_v4"
gpu_inference_max_nodes = 1

acr_georeplica_location = null
