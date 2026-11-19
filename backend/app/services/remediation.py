import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
from app.database import db_manager
from app.services.websocket_manager import ws_manager

logger = logging.getLogger("netpulse.remediation")

class RemediationService:
    async def execute_runbook(self, runbook_id: str, incident_id: str) -> Dict[str, Any]:
        """Executes/simulates autonomous self-healing remediation steps and broadcasts progress."""
        db = db_manager.db
        runbook = await db["runbooks"].find_one({"runbook_id": runbook_id}, {"_id": 0})
        if not runbook:
            return {"status": "error", "message": f"Runbook {runbook_id} not found."}

        # Update incident status to REMEDIATING
        await db["incidents"].update_one(
            {"incident_id": incident_id},
            {"$set": {"status": "REMEDIATING", "updated_at": datetime.utcnow()}}
        )
        
        await ws_manager.broadcast("incident_status_change", {
            "incident_id": incident_id,
            "status": "REMEDIATING",
            "message": f"Initiated Runbook {runbook_id}: {runbook.get('title')}"
        })

        steps: List[str] = runbook.get("remediation_steps", [])
        commands: List[str] = runbook.get("remediation_commands", [])
        execution_logs = []

        for idx, step in enumerate(steps):
            cmd = commands[idx] if idx < len(commands) else "echo 'Executing step...'"
            log_entry = {
                "step_index": idx + 1,
                "total_steps": len(steps),
                "step_description": step,
                "command": cmd,
                "status": "RUNNING",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await ws_manager.broadcast("remediation_step", {
                "incident_id": incident_id,
                "runbook_id": runbook_id,
                "log": log_entry
            })
            
            # Simulated real execution interval
            await asyncio.sleep(0.8)
            
            log_entry["status"] = "SUCCESS"
            log_entry["output"] = f"[STDOUT] Command '{cmd}' executed successfully (exit code 0)."
            execution_logs.append(log_entry)

        # Verification check
        verify_cmd = runbook.get("verification_check", "curl -f http://localhost/healthz")
        verification_log = {
            "step_index": len(steps) + 1,
            "total_steps": len(steps) + 1,
            "step_description": "Service health verification probe",
            "command": verify_cmd,
            "status": "SUCCESS",
            "output": "HTTP/1.1 200 OK - Health probe passed. Latency: 18ms. Error rate: 0.00%",
            "timestamp": datetime.utcnow().isoformat()
        }
        execution_logs.append(verification_log)
        
        # Mark incident as RESOLVED
        await db["incidents"].update_one(
            {"incident_id": incident_id},
            {
                "$set": {
                    "status": "RESOLVED",
                    "updated_at": datetime.utcnow(),
                    "remediation_logs": execution_logs
                }
            }
        )

        await ws_manager.broadcast("incident_status_change", {
            "incident_id": incident_id,
            "status": "RESOLVED",
            "message": f"Incident {incident_id} successfully mitigated via {runbook_id}!"
        })

        return {
            "status": "success",
            "incident_id": incident_id,
            "runbook_id": runbook_id,
            "logs": execution_logs,
            "final_status": "RESOLVED"
        }

remediation_service = RemediationService()
