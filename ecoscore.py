"""EcoScore calculation for products and predicted waste classes."""

from __future__ import annotations

from dataclasses import dataclass

from app.mapping import SortInstruction, classify_from_text_or_material, infer_material_from_text


@dataclass(frozen=True)
class EcoScore:
    score: int
    recyclability: str
    risk_level: str
    advice: str
    alternative: str


MATERIAL_PROFILES = {
    "glass": EcoScore(
        score=86,
        recyclability="Tres bonne recyclabilite si le verre est propre et depose dans la filiere dediee.",
        risk_level="Risque faible",
        advice="Preferer les contenants reutilisables ou consignables quand ils existent.",
        alternative="Bouteille en verre consignee ou contenant rechargeable.",
    ),
    "metal": EcoScore(
        score=78,
        recyclability="Bonne recyclabilite, surtout pour aluminium et acier correctement tries.",
        risk_level="Risque modere",
        advice="Eviter les produits multi-matieres difficiles a separer.",
        alternative="Produit durable, rechargeable ou vendu en vrac.",
    ),
    "cardboard": EcoScore(
        score=74,
        recyclability="Bonne recyclabilite si le carton est sec, propre et non plastifie.",
        risk_level="Risque faible a modere",
        advice="Aplatir le carton et eviter les emballages suremballes.",
        alternative="Produit avec emballage minimal ou carton recycle.",
    ),
    "paper": EcoScore(
        score=72,
        recyclability="Bonne recyclabilite pour les papiers propres et non souilles.",
        risk_level="Risque faible",
        advice="Limiter l'impression et privilegier papier recycle ou reutilisable.",
        alternative="Version numerique ou papier recycle certifie.",
    ),
    "plastic": EcoScore(
        score=58,
        recyclability="Recyclabilite variable selon le plastique, la couleur et la proprete.",
        risk_level="Risque environnemental eleve",
        advice="Reduire l'usage unique, vider le contenant et le deposer dans la poubelle jaune.",
        alternative="Contenant reutilisable, recharge ou verre consigne.",
    ),
    "trash": EcoScore(
        score=24,
        recyclability="Faible recyclabilite dans les filieres classiques.",
        risk_level="Risque eleve",
        advice="Eviter ce type de dechet quand une option reutilisable ou recyclable existe.",
        alternative="Produit lavable, rechargeable ou recyclable.",
    ),
}


INSTRUCTION_PROFILES = {
    "electronic": EcoScore(
        score=42,
        recyclability="Recyclabilite possible uniquement en point de collecte D3E.",
        risk_level="Risque eleve si jete avec les dechets ordinaires",
        advice="Ne jamais jeter avec les ordures menageres : rapporter en boutique ou point D3E.",
        alternative="Produit reparable, reconditionne ou avec batterie remplacable.",
    ),
    "black": MATERIAL_PROFILES["trash"],
}


def compute_ecoscore(
    product_name: str,
    material: str | None,
    instruction: SortInstruction | None = None,
) -> EcoScore:
    """Return a pragmatic environmental score for a product/material pair."""

    selected_instruction = instruction or classify_from_text_or_material(product_name, material)
    if selected_instruction.code in INSTRUCTION_PROFILES:
        return INSTRUCTION_PROFILES[selected_instruction.code]

    selected_material = material or selected_instruction.material or infer_material_from_text(product_name)
    profile = MATERIAL_PROFILES.get((selected_material or "").casefold(), MATERIAL_PROFILES["trash"])
    score = profile.score

    normalized = product_name.casefold()
    if "reutilisable" in normalized or "recharge" in normalized or "rechargeable" in normalized:
        score = min(100, score + 8)
    if "jetable" in normalized or "usage unique" in normalized:
        score = max(0, score - 12)

    return EcoScore(
        score=score,
        recyclability=profile.recyclability,
        risk_level=profile.risk_level,
        advice=profile.advice,
        alternative=profile.alternative,
    )
