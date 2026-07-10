from fixlot.memory.store import SessionMemory, ProjectMemory


def retrieve_relevant_memory(project: ProjectMemory, session: SessionMemory, query: str) -> str:
    parts = []

    known_errors = project.load("known_error")
    if known_errors:
        parts.append(f"Known error patterns: {known_errors}")

    conventions = project.load("convention")
    if conventions:
        parts.append(f"Project conventions: {conventions}")

    return "\n".join(parts) if parts else ""