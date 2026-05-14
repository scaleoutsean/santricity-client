#!/usr/bin/env python3
import argparse
import sys
import urllib3

try:
    from kubernetes import client, config
except ImportError:
    print("Error: The 'kubernetes' package is not installed.")
    print("Please install it running: pip install kubernetes")
    sys.exit(1)

from santricity_client import SANtricityClient
from santricity_client.auth.basic import BasicAuth

# Suppress insecure request warnings if verify_ssl is false
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    parser = argparse.ArgumentParser(description="Map Kubernetes PVCs to SANtricity Volumes and find orphans.")
    parser.add_argument("--base-url", required=True, help="SANtricity API base URL (e.g., https://1.2.3.4:8443/devmgr/v2)")
    parser.add_argument("--user", required=True, help="SANtricity username for basic auth")
    parser.add_argument("--password", required=True, help="SANtricity password for basic auth")
    parser.add_argument("--verify", action="store_true", default=False, help="Verify SSL")
    args = parser.parse_args()

    # 1. Load Kubernetes Configuration
    try:
        config.load_kube_config()
    except Exception as e:
        print(f"Failed to load Kubeconfig: {e}")
        sys.exit(1)

    v1 = client.CoreV1Api()

    print("Querying Kubernetes PVCs and PVs...")
    try:
        pvcs = v1.list_persistent_volume_claim_for_all_namespaces().items
        pvs = v1.list_persistent_volume().items
    except Exception as e:
        print(f"Failed to communicate with Kubernetes API: {e}")
        sys.exit(1)

    # Fast access map for PVs
    pv_map = {pv.metadata.name: pv for pv in pvs}
    
    # Store K8s metadata keyed by CSI volume_handle (which maps to array Volume ID/Name)
    k8s_volumes = {}

    # Map bound PVCs to their PVs
    for pvc in pvcs:
        pv_name = pvc.spec.volume_name
        if pv_name and pv_name in pv_map:
            pv = pv_map[pv_name]
            if pv.spec and pv.spec.csi:
                vol_handle = pv.spec.csi.volume_handle
                k8s_volumes[vol_handle] = {
                    "pvc_name": pvc.metadata.name,
                    "namespace": pvc.metadata.namespace,
                    "pv_name": pv_name,
                    "status": "Bound"
                }

    # Catch remaining PVs that are Released/Retained (no active PVC)
    for pv in pvs:
        if pv.spec and pv.spec.csi:
            vol_handle = pv.spec.csi.volume_handle
            if vol_handle not in k8s_volumes:
                k8s_volumes[vol_handle] = {
                    "pvc_name": "<None>",
                    "namespace": "<None>",
                    "pv_name": pv.metadata.name,
                    "status": "Retained/Orphaned in K8s"
                }

    # 2. Extract SANtricity volumes
    print("Querying SANtricity Array Volumes...")
    sc = SANtricityClient(
        base_url=args.base_url,
        auth_strategy=BasicAuth(args.user, args.password),
        verify_ssl=args.verify
    )
    
    try:
        arr_volumes = sc.volumes.list()
    except Exception as e:
        print(f"Failed to fetch volumes from SANtricity API: {e}")
        sys.exit(1)

    # 3. Correlate and Print
    print("\n{:<15} | {:<25} | {:<40} | {:<25} | {:<20}".format(
        "Namespace", "PVC Name", "PV Name", "SANtricity Volume", "Status"
    ))
    print("-" * 135)
    
    matched_k8s_handles = set()

    for vol in arr_volumes:
        vol_name = vol.get("name", "Unknown")
        vol_id = vol.get("id", "")
        vol_wwn = vol.get("volumeWwn", "")
        
        # Check if the CSI Volume Handle contains the Array ID, Name, or WWN
        match_handle = None
        for k8s_handle in k8s_volumes.keys():
             if (vol_id and vol_id in k8s_handle) or (vol_wwn and vol_wwn in k8s_handle) or (vol_name == k8s_handle):
                 match_handle = k8s_handle
                 break
                
        if match_handle:
            meta = k8s_volumes[match_handle]
            matched_k8s_handles.add(match_handle)
            print("{:<15} | {:<25} | {:<40} | {:<25} | {:<20}".format(
                meta["namespace"], meta["pvc_name"], meta["pv_name"], vol_name, meta["status"]
            ))
        else:
            # If a SANtricity volume starts with a likely CSI prefix but isn't in K8s, it's an array-side orphan
            # You might need to adjust this prefix ("pvc-") depending on what your specific CSI driver names volumes!
            if vol_name.startswith("pvc-") or vol_name.startswith("csi_"):
                print("{:<15} | {:<25} | {:<40} | {:<25} | {:<20}".format(
                    "<None>", "<None>", "<None>", vol_name, "Orphaned on Array!"
                ))
            # Else, it's just a regular non-k8s array volume (boot luns, VMFS, etc.), so we skip logging it to keep the table clean.

    # 4. Check for Kubernetes PVs that point to a Volume Handle that DOES NOT exist on SANtricity
    for handle, meta in k8s_volumes.items():
        if handle not in matched_k8s_handles:
             print("{:<15} | {:<25} | {:<40} | {:<25} | {:<20}".format(
                meta["namespace"], meta["pvc_name"], meta["pv_name"], handle, "Missing from Array!"
            ))


if __name__ == "__main__":
    main()
