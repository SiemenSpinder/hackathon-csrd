from typing import Any, Dict, List, Optional, TypedDict, Literal


# =========================
# CORE TYPES
# =========================

ESRSCode = Literal[
    "E2-1", "E2-2", "E2-3", "E2-4", "E2-5", "E2-6",
    "E3-1", "E3-2", "E3-3", "E3-4", "E3-5",
    "E4-1", "E4-2", "E4-3", "E4-4", "E4-5", "E4-6",
    "E5-1", "E5-2", "E5-3", "E5-4", "E5-5", "E5-6"
]

ESRSStandardCode = Literal["E2", "E3", "E4", "E5"]


class DisclosureDefinition(TypedDict):
    code: ESRSCode
    title: str
    description: str
    standard: ESRSStandardCode


class StandardDefinition(TypedDict):
    code: ESRSStandardCode
    name: str
    purpose: str


# =========================
# STANDARDS (E2–E5)
# =========================

ESRS_STANDARDS: Dict[ESRSStandardCode, StandardDefinition] = {
    "E2": {
        "code": "E2",
        "name": "Pollution",
        "purpose": "Manage and disclose emissions and pollution to air, water, and soil, including hazardous substances."
    },
    "E3": {
        "code": "E3",
        "name": "Water and Marine Resources",
        "purpose": "Disclose water usage, wastewater impacts, and effects on marine ecosystems."
    },
    "E4": {
        "code": "E4",
        "name": "Biodiversity and Ecosystems",
        "purpose": "Report impacts, dependencies, and actions related to biodiversity and ecosystem services."
    },
    "E5": {
        "code": "E5",
        "name": "Resource Use and Circular Economy",
        "purpose": "Disclose material use, waste, and circular economy practices."
    }
}


# =========================
# DISCLOSURES (E2)
# =========================

E2_DISCLOSURES: Dict[ESRSCode, DisclosureDefinition] = {
    "E2-1": {
        "code": "E2-1",
        "title": "Policies on pollution",
        "description": "Policies for prevention, control and remediation of pollution across air, water and soil.",
        "standard": "E2"
    },
    "E2-2": {
        "code": "E2-2",
        "title": "Actions and resources for pollution",
        "description": "Actions and financial/operational resources allocated to pollution prevention and reduction.",
        "standard": "E2"
    },
    "E2-3": {
        "code": "E2-3",
        "title": "Pollution targets",
        "description": "Quantified targets for reducing emissions to air, water and soil.",
        "standard": "E2"
    },
    "E2-4": {
        "code": "E2-4",
        "title": "Pollution of air, water and soil",
        "description": "Quantitative emissions to air, water and soil (e.g. NOx, SOx, PFAS, heavy metals).",
        "standard": "E2"
    },
    "E2-5": {
        "code": "E2-5",
        "title": "Substances of concern",
        "description": "Use, production or release of hazardous and SVHC substances and substitution measures.",
        "standard": "E2"
    },
    "E2-6": {
        "code": "E2-6",
        "title": "Financial effects from pollution risks and opportunities",
        "description": "Expected financial impacts from pollution-related risks and opportunities.",
        "standard": "E2"
    }
}


# =========================
# DISCLOSURES (E3)
# =========================

E3_DISCLOSURES: Dict[ESRSCode, DisclosureDefinition] = {
    "E3-1": {
        "code": "E3-1",
        "title": "Water and marine resources policies",
        "description": "Policies for sustainable water management and marine ecosystem protection.",
        "standard": "E3"
    },
    "E3-2": {
        "code": "E3-2",
        "title": "Water-related actions and resources",
        "description": "Actions and investments to reduce water use and prevent water pollution.",
        "standard": "E3"
    },
    "E3-3": {
        "code": "E3-3",
        "title": "Water targets",
        "description": "Quantified targets for water withdrawal, reuse, and wastewater quality.",
        "standard": "E3"
    },
    "E3-4": {
        "code": "E3-4",
        "title": "Water withdrawal and consumption",
        "description": "Total water withdrawal and consumption by source and region, including water-stressed areas.",
        "standard": "E3"
    },
    "E3-5": {
        "code": "E3-5",
        "title": "Financial effects from water risks",
        "description": "Financial impacts from physical and regulatory water-related risks.",
        "standard": "E3"
    }
}


# =========================
# DISCLOSURES (E4)
# =========================

E4_DISCLOSURES: Dict[ESRSCode, DisclosureDefinition] = {
    "E4-1": {
        "code": "E4-1",
        "title": "Biodiversity transition plan",
        "description": "Alignment with EU Biodiversity Strategy 2030 and Global Biodiversity Framework.",
        "standard": "E4"
    },
    "E4-2": {
        "code": "E4-2",
        "title": "Biodiversity policies",
        "description": "Policies to prevent, mitigate and restore biodiversity impacts.",
        "standard": "E4"
    },
    "E4-3": {
        "code": "E4-3",
        "title": "Biodiversity actions and resources",
        "description": "Mitigation hierarchy actions (avoid, reduce, restore, compensate).",
        "standard": "E4"
    },
    "E4-4": {
        "code": "E4-4",
        "title": "Biodiversity targets",
        "description": "Targets for habitat and ecosystem protection and restoration.",
        "standard": "E4"
    },
    "E4-5": {
        "code": "E4-5",
        "title": "Biodiversity impact metrics",
        "description": "Land use, land conversion, habitat impact, and endangered species effects.",
        "standard": "E4"
    },
    "E4-6": {
        "code": "E4-6",
        "title": "Financial effects from biodiversity risks",
        "description": "Financial impacts from ecosystem dependency and biodiversity risks.",
        "standard": "E4"
    }
}


# =========================
# DISCLOSURES (E5)
# =========================

E5_DISCLOSURES: Dict[ESRSCode, DisclosureDefinition] = {
    "E5-1": {
        "code": "E5-1",
        "title": "Resource use policies",
        "description": "Policies to reduce virgin material use and improve circularity.",
        "standard": "E5"
    },
    "E5-2": {
        "code": "E5-2",
        "title": "Circular economy actions",
        "description": "Eco-design, recycling, reuse, and product lifecycle extension measures.",
        "standard": "E5"
    },
    "E5-3": {
        "code": "E5-3",
        "title": "Circular economy targets",
        "description": "Targets for waste reduction, recycling, and secondary material use.",
        "standard": "E5"
    },
    "E5-4": {
        "code": "E5-4",
        "title": "Resource inflows",
        "description": "Total material input including primary and secondary raw materials.",
        "standard": "E5"
    },
    "E5-5": {
        "code": "E5-5",
        "title": "Waste generation and streams",
        "description": "Total waste and treatment methods (recycling, incineration, landfill).",
        "standard": "E5"
    },
    "E5-6": {
        "code": "E5-6",
        "title": "Financial effects from resource risks",
        "description": "Financial impacts from material scarcity and circular economy opportunities.",
        "standard": "E5"
    }
}


# =========================
# MASTER LOOKUP
# =========================

ESRS_DISCLOSURES: Dict[ESRSCode, DisclosureDefinition] = {
    **E2_DISCLOSURES,
    **E3_DISCLOSURES,
    **E4_DISCLOSURES,
    **E5_DISCLOSURES,
}

# =========================
# NTP SCORING WEIGHTS
# Dimensions weighted out of 100, per WWF NAT40 framework:
#   implementation_strategy gets the highest weight.
# =========================

NTP_WEIGHTS = {
    "foundations": 25,
    "metrics_and_targets": 20,
    "implementation_strategy": 30,
    "engagement_strategy": 15,
    "governance": 10,
}

NTP_MATURITY_LABELS = {
    0: "Non-aligned",
    1: "Compliant",
    2: "Coherent",
    3: "Credible",
}


def _compute_total_score(ntp_scoring: Dict[str, Any]) -> float:
    total = 0.0
    for dim, weight in NTP_WEIGHTS.items():
        dim_score = ntp_scoring.get(dim, {}).get("score", 0)
        total += (dim_score / 3) * weight
    return round(total, 1)


def enrich_with_ontology(
    disclosures: List[Any],
    ntp_scoring: Optional[Any] = None,
) -> Dict[str, Any]:
    enriched_disclosures = []
    for d in disclosures:
        code = d.code if hasattr(d, "code") else d["code"]
        definition = ESRS_DISCLOSURES.get(code)
        if definition is None:
            continue
        enriched_disclosures.append({
            "code": code,
            "title": definition["title"],
            "description": definition["description"],
            "standard": definition["standard"],
            "is_present": d.is_present if hasattr(d, "is_present") else d["is_present"],
            "confidence": d.confidence if hasattr(d, "confidence") else d["confidence"],
            "evidence": d.evidence if hasattr(d, "evidence") else d["evidence"],
            "metrics": d.metrics if hasattr(d, "metrics") else d["metrics"],
        })

    result: Dict[str, Any] = {"disclosures": enriched_disclosures}

    if ntp_scoring is not None:
        ntp_dict = ntp_scoring.model_dump() if hasattr(ntp_scoring, "model_dump") else ntp_scoring
        total = _compute_total_score(ntp_dict)

        enriched_ntp: Dict[str, Any] = {}
        for dim, weight in NTP_WEIGHTS.items():
            dim_data = ntp_dict.get(dim, {})
            score = dim_data.get("score", 0)
            enriched_ntp[dim] = {
                "score": score,
                "maturity": NTP_MATURITY_LABELS.get(score, "Unknown"),
                "weight": weight,
                "weighted_contribution": round((score / 3) * weight, 1),
                "rationale": dim_data.get("rationale", ""),
                "evidence": dim_data.get("evidence", []),
            }

        result["ntp_scoring"] = {
            **enriched_ntp,
            "total_score": total,
        }

    return result
