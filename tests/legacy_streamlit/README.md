# Tests hérités — interface Streamlit (obsolète)

Ces tests concernent les modules `app/chatbot.py`, `app/dashboard.py` et
`app/ecoscore.py`, qui appartenaient à l'ancienne interface Streamlit du
projet, remplacée par l'interface Flask.

Ils sont conservés ici à titre d'historique uniquement et ne sont **pas**
exécutés par la suite de tests actuelle (voir `pytest.ini` à la racine du
projet, qui exclut ce dossier par défaut).

Si l'équipe décide de réintégrer ces fonctionnalités (chatbot, tableau de
bord, éco-score) dans l'application Flask, ces tests devront être réécrits
pour correspondre à la nouvelle architecture.