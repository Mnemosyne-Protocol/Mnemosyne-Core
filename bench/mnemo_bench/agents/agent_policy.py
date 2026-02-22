class AgentPolicy:
    name = "Agent_Policy"
    @staticmethod
    def verify(frame_metadata, memory_snapshot):
        if frame_metadata.get("policy_score", 1.0) >= 0.90:
            return True, "PASS"
        return False, "FAIL (Policy violation)"
