class AgentStyle:
    name = "Agent_Style"
    @staticmethod
    def verify(frame_metadata, memory_snapshot):
        if frame_metadata.get("style_score", 1.0) >= 0.85:
            return True, "PASS"
        return False, "FAIL (Scar missing)"
