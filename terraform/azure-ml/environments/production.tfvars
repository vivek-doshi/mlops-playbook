environment    = "production"
location       = "eastus"
location_short = "eus"
model_name     = "fraud-detection"
cost_center    = "ml-platform"
team           = "ml-platform-team"

# Private endpoints only in production.
allow_public_network_access = false

cpu_cluster_vm_size   = "Standard_D8s_v5"
cpu_cluster_max_nodes = 8

# H100 NDv5 for production training — requires support-ticket quota increase.
# Allow 1–4 weeks lead time. See ADR-ML-006 Consequences — Neutral.
gpu_cluster_vm_size     = "Standard_ND96isr_H100_v5"
gpu_cluster_vm_priority = "Dedicated"
gpu_cluster_max_nodes   = 4

# H100 NVL for production inference — single-GPU, highest throughput per $ for LLM serving.
gpu_inference_vm_size   = "Standard_NC40ads_H100_v5"
gpu_inference_max_nodes = 4

# Geo-replicate ACR to westeurope for low-latency image pulls from EU compute.
acr_georeplica_location = "westeurope"
