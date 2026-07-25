document.documentElement.classList.add("js");

const respecterMouvementReduit = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
);

function definirMouvementReduit() {
    document.documentElement.dataset.mouvementReduit =
        respecterMouvementReduit.matches ? "true" : "false";
}

definirMouvementReduit();
respecterMouvementReduit.addEventListener("change", definirMouvementReduit);
