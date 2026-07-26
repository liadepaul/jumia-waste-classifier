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


def test_contenant_en_verre_est_reconnu_malgre_les_mots_intermediaires():
    assert (
        categorie_depuis_texte(produit("Bocal de stockage hermétique en verre"))
        == "vert"
    )
    assert (
        categorie_depuis_texte(produit("Ensemble de quatre bocaux en verre"))
        == "vert"
    )


def test_bouteille_de_boisson_sans_matiere_explicitement_indiquee():
    assert (
        categorie_depuis_texte(produit("Lot de bouteilles d'eau minérale"))
        == "jaune"
    )
    assert (
        categorie_depuis_texte(produit("Bouteille d'eau en verre"))
        == "vert"
    )


def test_shampoing_conditionne_en_flacon_est_un_emballage_jaune():
    assert categorie_depuis_texte(produit("Shampoing à l'huile 400 ml")) == "jaune"
