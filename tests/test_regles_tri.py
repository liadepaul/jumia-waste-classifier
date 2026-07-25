from app.app import categorie_depuis_texte, est_electronique


def produit(nom: str, categorie_jumia: str = "") -> dict:
    return {
        "nom": nom,
        "mot_cle": "",
        "categorie_jumia": categorie_jumia,
        "image_url": "",
    }


def test_d3e_est_prioritaire():
    assert est_electronique(produit("Smartphone"))
    assert est_electronique(
        produit("Produit sans mot-cle", "telephones-tablettes")
    )


def test_verre_emballage_et_vaisselle_sont_distingues():
    assert categorie_depuis_texte(produit("Bouteille en verre")) == "vert"
    assert categorie_depuis_texte(produit("Verre à boire")) == "marron"


def test_objet_plastique_n_est_pas_un_emballage_jaune():
    assert (
        categorie_depuis_texte(
            produit("Ensemble de gourdes réutilisables en plastique")
        )
        == "marron"
    )
    assert categorie_depuis_texte(produit("Brosse en plastique")) == "marron"


def test_objet_multimatiere_est_residuel():
    assert (
        categorie_depuis_texte(
            produit("Coffre en forme de livre en papier acier et plastique")
        )
        == "marron"
    )


def test_emballages_explicites_restent_jaunes():
    assert categorie_depuis_texte(
        produit("Canette de boisson en aluminium")
    ) == "jaune"
    assert categorie_depuis_texte(
        produit("Bouteille en plastique")
    ) == "jaune"
