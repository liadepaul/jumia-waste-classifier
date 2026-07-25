import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from diagnostic.evaluer_echantillon_groupe import (
    calculer_metriques,
    evaluer_cnn_direct,
    evaluer_hybride,
    matrice_confusion,
    paires_cnn,
    paires_hybride,
    produit_pour_application,
    repartir,
)


def _produit(lien, categorie, nom="Produit", mot_cle="", categorie_jumia=None):
    return {
        "nom": nom,
        "image_url": f"https://ci.jumia.is/{lien}.jpg",
        "prix": "1 000 FCFA",
        "lien": lien,
        "categorie_jumia": categorie_jumia,
        "mot_cle_recherche": mot_cle,
        "categorie_attendue_provisoire": categorie,
        "categorie_validee_manuellement": categorie,
    }


def test_exclusion_des_aucune():
    echantillon = [
        _produit("a", "jaune"),
        _produit("b", "aucune"),
        _produit("c", "gris"),
    ]
    groupes = repartir(echantillon, liens_benchmark=set(), liens_holdout=set())

    assert len(groupes["aucune"]) == 1
    assert len(groupes["classables"]) == 2
    assert all(p["categorie_validee_manuellement"] != "aucune" for p in groupes["classables"])


def test_detection_des_liens_deja_vus():
    echantillon = [
        _produit("deja-dans-benchmark", "jaune"),
        _produit("deja-dans-holdout", "vert"),
        _produit("jamais-vu", "bleu"),
    ]
    groupes = repartir(
        echantillon,
        liens_benchmark={"deja-dans-benchmark"},
        liens_holdout={"deja-dans-holdout"},
    )

    liens_deja_vus = {p["lien"] for p in groupes["deja_vus"]}
    liens_nouveaux = {p["lien"] for p in groupes["nouveaux"]}

    assert liens_deja_vus == {"deja-dans-benchmark", "deja-dans-holdout"}
    assert liens_nouveaux == {"jamais-vu"}
    assert len(groupes["deja_vus"]) + len(groupes["nouveaux"]) == len(groupes["classables"])


def test_ensembles_83_75_70_62_55_sur_echantillon_proportionnel():
    echantillon = []
    for i in range(20):
        echantillon.append(_produit(f"gris-{i}", "gris"))
    for i in range(22):
        echantillon.append(_produit(f"marron-{i}", "marron"))
    for i in range(17):
        echantillon.append(_produit(f"jaune-{i}", "jaune"))
    for i in range(10):
        echantillon.append(_produit(f"bleu-{i}", "bleu"))
    for i in range(6):
        echantillon.append(_produit(f"vert-{i}", "vert"))
    for i in range(8):
        echantillon.append(_produit(f"aucune-{i}", "aucune"))

    assert len(echantillon) == 83

    liens_benchmark = {"gris-0", "gris-1", "gris-2", "marron-0", "marron-1",
                        "marron-2", "marron-3", "jaune-0", "jaune-1", "bleu-0"}
    liens_holdout = {"jaune-2", "vert-0", "vert-1"}

    groupes = repartir(echantillon, liens_benchmark, liens_holdout)

    assert len(groupes["classables"]) == 75
    assert len(groupes["deja_vus"]) == 13
    assert len(groupes["nouveaux"]) == 62

    classables_non_gris = [
        p for p in groupes["classables"]
        if p["categorie_validee_manuellement"] != "gris"
    ]
    assert len(classables_non_gris) == 55


def test_cnn_exclut_les_d3e(monkeypatch):
    echantillon = [
        _produit("cnn-jaune", "jaune"),
        _produit("cnn-gris", "gris"),
    ]

    appels = []

    def fausse_telecharger_image(url):
        appels.append(url)
        return "/tmp/faux_chemin.jpg"

    def faux_predire(chemin):
        return {"categorie": "jaune", "confiance": 0.9}

    monkeypatch.setattr(
        "diagnostic.evaluer_echantillon_groupe.telecharger_image",
        fausse_telecharger_image,
    )
    monkeypatch.setattr(
        "diagnostic.evaluer_echantillon_groupe.predire_categorie",
        faux_predire,
    )
    monkeypatch.setattr(
        "diagnostic.evaluer_echantillon_groupe.Path.unlink",
        lambda self, missing_ok=False: None,
    )

    resultats = evaluer_cnn_direct(echantillon)

    assert len(resultats) == 1
    assert resultats[0]["categorie_attendue"] == "jaune"
    assert appels == ["https://ci.jumia.is/cnn-jaune.jpg"]


def test_image_indisponible_devient_une_erreur_technique_pas_une_mauvaise_classification(monkeypatch):
    echantillon = [_produit("cnn-panne", "vert")]

    def telecharger_qui_echoue(url):
        raise ValueError("Image Jumia introuvable")

    monkeypatch.setattr(
        "diagnostic.evaluer_echantillon_groupe.telecharger_image",
        telecharger_qui_echoue,
    )

    resultats = evaluer_cnn_direct(echantillon)

    assert len(resultats) == 1
    assert resultats[0]["erreur_technique"] != ""
    assert resultats[0]["cnn_correct"] is None
    assert resultats[0]["verdict_cnn"] is None

    paires = paires_cnn(resultats)
    assert paires == []


def test_pas_de_fuite_entre_attendu_et_predit_dans_les_metriques():
    paires_parfaites = [("jaune", "jaune"), ("vert", "vert"), ("bleu", "bleu")]
    paires_toutes_fausses = [("jaune", "vert"), ("vert", "bleu"), ("bleu", "jaune")]
    classes = ["jaune", "vert", "bleu"]

    parfait = calculer_metriques(paires_parfaites, classes)
    fausses = calculer_metriques(paires_toutes_fausses, classes)

    assert parfait["accuracy"] == 1.0
    assert fausses["accuracy"] == 0.0
    assert parfait["macro_f1"] == 1.0
    assert fausses["macro_f1"] == 0.0


def test_matrice_confusion_ne_compte_que_les_classes_connues():
    paires = [("jaune", "jaune"), ("jaune", "vert"), ("vert", "vert")]
    matrice = matrice_confusion(paires, ["jaune", "vert"])

    assert matrice["jaune"]["jaune"] == 1
    assert matrice["jaune"]["vert"] == 1
    assert matrice["vert"]["vert"] == 1
    assert matrice["vert"]["jaune"] == 0


def test_evaluer_hybride_marque_le_statut_deja_vu_ou_nouveau(monkeypatch):
    echantillon = [
        _produit("hybride-vu", "jaune"),
        _produit("hybride-nouveau", "vert"),
    ]

    def fausse_decision(produit):
        return {
            "categorie": "jaune",
            "confiance": 0.8,
            "source": "IA",
            "erreur": None,
        }

    monkeypatch.setattr(
        "diagnostic.evaluer_echantillon_groupe.determiner_verdict",
        lambda produit: fausse_decision(produit),
    )

    resultats = evaluer_hybride(echantillon, deja_vus_liens={"hybride-vu"})

    statuts = {r["lien"]: r["statut"] for r in resultats}
    assert statuts["hybride-vu"] == "deja_vu"
    assert statuts["hybride-nouveau"] == "nouveau"


def test_produit_pour_application_ne_modifie_pas_entree_originale():
    entree = _produit("x", "jaune", mot_cle="bouteille plastique", categorie_jumia=None)
    original = dict(entree)

    produit = produit_pour_application(entree)

    assert entree == original
    assert produit["mot_cle"] == "bouteille plastique"
    assert produit["categorie_jumia"] == ""
