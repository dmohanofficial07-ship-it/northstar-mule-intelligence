from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_current_user
from ..models import User
from ..seed_data import GRAPH_EDGES, GRAPH_NODES
from ..services.integrations import integrations

router = APIRouter(prefix="/investigations", tags=["investigations"])


def read_neo4j_network(case_ref: str) -> tuple[list[dict], list[dict]] | None:
    if not integrations.neo4j:
        return None
    try:
        with integrations.neo4j.session() as session:
            record = session.run(
                "MATCH (a:Entity)-[r:LINKED_TO {case_ref: $case_ref}]->(b:Entity) "
                "RETURN collect(DISTINCT properties(a)) + collect(DISTINCT properties(b)) AS nodes, "
                "collect({source: a.id, target: b.id, type: r.kind, amount: r.amount}) AS edges",
                case_ref=case_ref,
            ).single()
            if not record:
                return None
            unique_nodes = {node["id"]: dict(node) for node in record["nodes"]}
            return list(unique_nodes.values()), [dict(edge) for edge in record["edges"]]
    except Exception:
        return None


@router.get("/{case_ref}/network")
def investigation_network(case_ref: str, _: User = Depends(get_current_user)) -> dict:
    if case_ref != "MULE-2048":
        raise HTTPException(status_code=404, detail="Investigation network not found")
    graph = read_neo4j_network(case_ref)
    nodes, edges = graph if graph else (GRAPH_NODES, GRAPH_EDGES)
    return {
        "case_ref": case_ref,
        "title": "Connected entity investigation",
        "risk_score": 94,
        "risk_level": "critical",
        "linked_value": 860000,
        "trace": {"amount": 594000, "duration_minutes": 18, "entity_count": 7, "destination": "Orion Exports"},
        "source": "neo4j" if graph else "seeded-fallback",
        "nodes": nodes,
        "edges": edges,
    }
