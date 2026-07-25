document.documentElement.classList.add("js");

const respecterMouvementReduit = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
);

function definirMouvementReduit() {
    document.documentElement.dataset.mouvementReduit =
        respecterMouvementReduit.matches ? "true" : "false";
}

definirMouvementReduit();

if (respecterMouvementReduit.addEventListener) {
    respecterMouvementReduit.addEventListener("change", definirMouvementReduit);
} else {
    respecterMouvementReduit.addListener(definirMouvementReduit);
}

const carousel = document.querySelector("[data-carousel]");

if (carousel) {
    const slides = [...carousel.querySelectorAll("[data-slide]")];
    const indicateurs = [
        ...carousel.querySelectorAll("[data-carousel-indicateur]"),
    ];
    const boutonPause = carousel.querySelector("[data-carousel-pause]");
    const statut = carousel.querySelector("[data-carousel-statut]");
    const dureeAffichage = 3000;
    const dureeTransition = 900;
    let indexActuel = 0;
    let minuteur = null;
    let finTransition = null;
    let transitionEnCours = false;
    let pauseUtilisateur = false;
    let pauseInteraction = false;

    function animationAutorisee() {
        return !respecterMouvementReduit.matches;
    }

    function arreterMinuteur() {
        if (minuteur !== null) {
            window.clearTimeout(minuteur);
            minuteur = null;
        }
    }

    function programmerSuivant() {
        arreterMinuteur();

        if (
            pauseUtilisateur
            || pauseInteraction
            || !animationAutorisee()
            || document.hidden
        ) {
            return;
        }

        minuteur = window.setTimeout(() => {
            afficherSlide((indexActuel + 1) % slides.length);
        }, dureeAffichage);
    }

    function mettreAJourPause() {
        boutonPause.classList.toggle("est-en-pause", pauseUtilisateur);
        boutonPause.setAttribute("aria-pressed", String(pauseUtilisateur));
        boutonPause.setAttribute(
            "aria-label",
            pauseUtilisateur
                ? "Reprendre l’animation"
                : "Mettre l’animation en pause"
        );
    }

    function appliquerTheme(slide) {
        document.body.style.setProperty("--fond-accueil", slide.dataset.fond);
        document.body.style.setProperty("--texte-accueil", slide.dataset.texte);
        document.body.dataset.bacActif = slide.dataset.couleur;
    }

    function afficherSlide(nouvelIndex, annoncer = true) {
        if (transitionEnCours || nouvelIndex === indexActuel) {
            programmerSuivant();
            return;
        }

        const ancienneSlide = slides[indexActuel];
        const nouvelleSlide = slides[nouvelIndex];
        const dureeEffective = animationAutorisee() ? dureeTransition : 0;

        arreterMinuteur();
        transitionEnCours = true;
        ancienneSlide.classList.remove("est-active", "entre-par-le-haut");
        ancienneSlide.classList.add("sort-vers-le-bas");
        ancienneSlide.setAttribute("aria-hidden", "true");

        nouvelleSlide.classList.remove("sort-vers-le-bas");
        nouvelleSlide.classList.add("est-active", "entre-par-le-haut");
        nouvelleSlide.setAttribute("aria-hidden", "false");

        indicateurs[indexActuel].classList.remove("est-actif");
        indicateurs[indexActuel].setAttribute("aria-current", "false");
        indicateurs[nouvelIndex].classList.add("est-actif");
        indicateurs[nouvelIndex].setAttribute("aria-current", "true");

        indexActuel = nouvelIndex;
        appliquerTheme(nouvelleSlide);

        if (annoncer) {
            const nom = nouvelleSlide.querySelector("h1, h2").textContent;
            statut.textContent = `${nom}, élément ${nouvelIndex + 1} sur ${slides.length}`;
        }

        window.clearTimeout(finTransition);
        finTransition = window.setTimeout(() => {
            ancienneSlide.classList.remove("sort-vers-le-bas");
            nouvelleSlide.classList.remove("entre-par-le-haut");
            transitionEnCours = false;
            programmerSuivant();
        }, dureeEffective);
    }

    indicateurs.forEach((indicateur, index) => {
        indicateur.addEventListener("click", () => afficherSlide(index));
    });

    boutonPause.addEventListener("click", () => {
        pauseUtilisateur = !pauseUtilisateur;
        mettreAJourPause();
        programmerSuivant();
    });

    carousel.addEventListener("mouseenter", () => {
        pauseInteraction = true;
        arreterMinuteur();
    });

    carousel.addEventListener("mouseleave", () => {
        pauseInteraction = false;
        programmerSuivant();
    });

    carousel.addEventListener("focusin", () => {
        pauseInteraction = true;
        arreterMinuteur();
    });

    carousel.addEventListener("focusout", (evenement) => {
        if (!carousel.contains(evenement.relatedTarget)) {
            pauseInteraction = false;
            programmerSuivant();
        }
    });

    document.addEventListener("visibilitychange", programmerSuivant);
    respecterMouvementReduit.addEventListener?.("change", programmerSuivant);

    appliquerTheme(slides[0]);
    mettreAJourPause();
    programmerSuivant();
}

const dialogueRecherche = document.querySelector(".recherche-dialogue");

if (dialogueRecherche) {
    const boutonsOuverture = document.querySelectorAll("[data-open-search]");
    const boutonFermeture = dialogueRecherche.querySelector(
        "[data-close-search]"
    );
    const champRecherche = dialogueRecherche.querySelector(
        "[data-search-input]"
    );
    const suggestions = dialogueRecherche.querySelector(
        "[data-search-suggestions]"
    );
    const formulaire = dialogueRecherche.querySelector("form");

    function ouvrirRecherche() {
        if (!dialogueRecherche.open) {
            dialogueRecherche.showModal();
        }
        window.requestAnimationFrame(() => champRecherche.focus());
    }

    boutonsOuverture.forEach((bouton) => {
        bouton.addEventListener("click", (evenement) => {
            evenement.preventDefault();
            ouvrirRecherche();
        });
    });

    boutonFermeture.addEventListener("click", () => {
        dialogueRecherche.close();
    });

    dialogueRecherche.addEventListener("click", (evenement) => {
        if (evenement.target === dialogueRecherche) {
            dialogueRecherche.close();
        }
    });

    const boutonsSuggestions = suggestions.querySelectorAll(
        "[data-suggestion]"
    );

    function mettreAJourSuggestions() {
        const saisie = champRecherche.value.trim().toLocaleLowerCase("fr");
        let nombreCorrespondances = 0;

        boutonsSuggestions.forEach((bouton) => {
            const proposition = bouton.dataset.suggestion.toLocaleLowerCase("fr");
            const correspond = saisie.length >= 2 && proposition.includes(saisie);

            bouton.hidden = !correspond;
            nombreCorrespondances += correspond ? 1 : 0;
        });

        suggestions.hidden = saisie.length < 2 || nombreCorrespondances === 0;
    }

    champRecherche.addEventListener("input", mettreAJourSuggestions);

    boutonsSuggestions.forEach((bouton) => {
        bouton.addEventListener("click", () => {
            champRecherche.value = bouton.dataset.suggestion;
            formulaire.requestSubmit();
        });
    });

    mettreAJourSuggestions();

    if (window.location.hash === "#recherche") {
        ouvrirRecherche();
    }
}
