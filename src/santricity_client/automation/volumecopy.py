"""
Automation wrapper for dynamically managing Volume Copy workloads.
"""

from __future__ import annotations

import logging
from typing import Any

from santricity_client.client import SANtricityClient

logger = logging.getLogger(__name__)

class VolumeCopyAutomation:
    """Intelligent workload-aware automation for SANtricity Volume Copies."""

    def __init__(self, client: SANtricityClient):
        self._client = client

    def get_system_load(self) -> dict[str, float]:
        """
        Polls the array for current load metrics (IOPS, CPU, etc.).
        This is a stub that needs to parse /analysed-performance or similar endpoints.
        """
        self._client.request("GET", "/analysed-system-statistics")
        logger.debug("Polling array performance metrics...")
        
        try:
            stats = self._client.request("GET", "/analysed-system-statistics", system_scope=True)
            if isinstance(stats, dict):
                return {
                    "controller_cpu_percent": float(stats.get("cpuAvgUtilization", 0.0) * 100),  # Example mapping
                    "overall_iops": float(stats.get("combinedIOps", 0.0)),
                    "overall_throughput_mbps": float(stats.get("combinedThroughput", 0.0)),
                    "max_possible_iops": float(stats.get("maxPossibleIopsUnderCurrentLoad", 0.0))
                }
        except Exception as e:
            logger.warning(f"Failed to fetch real system performance stats: {e}")

        # Fallback payload
        return {
            "controller_cpu_percent": 0.0,
            "overall_iops": 0.0,
            "overall_throughput_mbps": 0.0
        }

    def cleanup_completed_copies(self) -> None:
        """
        Scans for volume copies that have completed (or failed) and deletes them,
        which automatically cleans up their ephemeral snapshot repository groups
        if `retainRepositories=False` is used.
        """
        all_copies = self._client.volumes.list_copies()
        if not all_copies:
            return

        for job in all_copies:
            status = job.get("status")
            if status in ("complete", "failed"):
                job_ref = job.get("volcopyRef")
                logger.info(f"Cleaning up {status} volume copy job: {job_ref}")
                try:
                    self._client.volumes.delete_copy(job_ref, retain_repositories=False)
                    logger.info(f"Successfully removed job {job_ref} and its temporary resources.")
                except Exception as e:
                    logger.error(f"Error cleaning up volume copy job {job_ref}: {e}")

    def evaluate_and_adjust_copies(self, max_cpu_threshold: float = 70.0, max_size_bytes: int = 64 * 1024**3) -> None:
        """
        Pragmatic volume copy adjustment:
        - Default to 'priority2' (Medium).
        - If CPU < 70% AND Source Volume Capacity < 64 GiB, elevate to 'priority3' (High).
        - Automatically cleans up completed or failed copies.
        """
        self.cleanup_completed_copies()

        active_copies = self._client.volumes.list_copies()
        # Filter only active ones after cleanup
        active_copies = [j for j in active_copies if j.get("status") not in ("complete", "failed")]
        
        if not active_copies:
            logger.info("No active volume copies to manage.")
            return

        metrics = self.get_system_load()
        cpu_load = metrics.get("controller_cpu_percent", 0.0)

        for job in active_copies:
            job_ref = job.get("volcopyRef")
            current_priority = job.get("copyPriority")
            source_id = job.get("sourceVolume")
            
            try:
                # Look up source volume size
                source_vol = self._client.volumes.get(source_id)
                vol_capacity = int(source_vol.get("capacity", 0))
            except Exception as e:
                logger.warning(f"Could not retrieve source volume {source_id} for job {job_ref}: {e}")
                continue

            # Evaluate pragmatic conditions
            desired_priority = "priority2"
            if cpu_load < max_cpu_threshold and vol_capacity < max_size_bytes:
                desired_priority = "priority3"
            
            if current_priority != desired_priority:
                logger.info(f"Adjusting job {job_ref} from {current_priority} to {desired_priority} "
                            f"(CPU: {cpu_load}%, VolSize: {vol_capacity / 1024**3:.2f} GiB)")
                try:
                    self._client.volumes.update_copy(job_ref, priority=desired_priority)
                except Exception as e:
                    logger.error(f"Failed to update job {job_ref}: {e}")
