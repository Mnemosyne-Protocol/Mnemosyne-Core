class AgentGeometry:
    name = "Agent_Geometry"
    @staticmethod
    def verify(frame_metadata, memory_snapshot):
        if frame_metadata.get("geometry_score", 1.0) >= 0.90: return True, "PASS"
        return False, "FAIL (Geometry mismatch)"
