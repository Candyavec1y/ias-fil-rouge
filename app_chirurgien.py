"""
Outil de planification du bloc opératoire (interface chirurgien).
Lancer :  streamlit run app_chirurgien.py
Les 3 fonctions marquées TODO en haut de fichier sont à brancher sur vos algorithmes.
"""
import re
from datetime import date, datetime, timedelta

import streamlit as st

st.set_page_config(page_title="Planification du bloc opératoire", page_icon="🏥", layout="wide")

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
PRATICIENS = ["Dr Martin", "Dr Dupont", "Dr Bernard"]
TYPES_INTERVENTION = ["Programmée", "Urgente", "Ambulatoire", "Hospitalisation complète"]
TYPES_ANESTHESIE = ["Générale", "Loco-régionale", "Locale", "Sédation", "Aucune"]

# Interventions standardisées proposées en autocomplétion (saisie libre toujours possible).
INTERVENTIONS = sorted([
    "Ablation de materiel d Osteosynthese Complexe", "Ablation de materiel d Osteosynthese Simple",
    "Arthrodese Arriere Pied", "Arthrodese Cheville",
    "Arthroscopie Epaule Complexe", "Arthroscopie Epaule Simple", "Arthroscopie Genou",
    "Butee Epaule", "Canal Carpien", "Cheville Simple",
    "Ligamentoplastie Genou", "Ligamentoplastie Genou + Arthroscopie",
    "Main Simple", "Ongle Incarne", "Osteosynthese Membre Superieur", "Osteotomie Tibilale Valgisation",
    "Pied Complexe", "Pied Simple",
    "Prothese Totale Epaule", "Prothese Totale Genou", "Prothese Totale Hanche",
    "Prothese UniCompartimentale Genou",
    "Rachis Cervical Simple", "Rachis Lombaire Complexe", "Rachis Lombaire Simple",
    "Reduction Fracture", "Varices",
])

# Formats : CIM-10 = lettre + 2 chiffres (+ point + 1 à 4 caractères) ; CCAM = 4 lettres + 3 chiffres.
RE_CIM = re.compile(r"^[A-Z][0-9]{2}(\.[0-9A-Z]{1,4})?$")
RE_CCAM = re.compile(r"^[A-Z]{4}[0-9]{3}$")


def normaliser_cim(code: str) -> str:
    """M171 -> M17.1 ; m17.1 -> M17.1"""
    c = code.strip().upper().replace(" ", "")
    if len(c) > 3 and "." not in c:
        c = c[:3] + "." + c[3:]
    return c


def normaliser_ccam(code: str) -> str:
    return code.strip().upper().replace(" ", "")


def verifier_codes(cim_principal: str, cim_assoc: list[str], ccam: list[str]):
    """Retourne (codes normalisés, liste d'erreurs)."""
    erreurs, cim_p = [], normaliser_cim(cim_principal)
    if not RE_CIM.match(cim_p):
        erreurs.append(f"CIM principal « {cim_principal} » : format attendu ex. M17.1")
    cim_a = []
    for i, c in enumerate(cim_assoc, start=1):
        if c.strip():
            n = normaliser_cim(c)
            if not RE_CIM.match(n):
                erreurs.append(f"CIM associé {i} « {c} » : format attendu ex. E11.9")
            cim_a.append(n)
    ccam_n = []
    for i, c in enumerate(ccam, start=1):
        if c.strip():
            n = normaliser_ccam(c)
            if not RE_CCAM.match(n):
                erreurs.append(f"CCAM {i} « {c} » : format attendu ex. NFKA010 (4 lettres + 3 chiffres)")
            ccam_n.append(n)
    return cim_p, cim_a, ccam_n, erreurs


def lundi_prochain() -> date:
    d = date.today()
    return d + timedelta(days=(7 - d.weekday()) % 7 or 7)


# ---------------------------------------------------------------------------
# TODO 1 : remplacer par le planning de vacations produit par l'étape 1
#          (recuit simulé + AGS + tabou). Format attendu : liste de dicts.
# ---------------------------------------------------------------------------
def charger_planning_vacations() -> list[dict]:
    return [
        {"jour": 0, "salle": 1, "praticien": "Dr Martin", "debut": "08:00", "fin": "12:00"},
        {"jour": 1, "salle": 1, "praticien": "Dr Dupont", "debut": "08:00", "fin": "12:00"},
        {"jour": 2, "salle": 1, "praticien": "Dr Martin", "debut": "14:00", "fin": "18:00"},
        {"jour": 3, "salle": 1, "praticien": "Dr Bernard", "debut": "08:00", "fin": "12:00"},
        {"jour": 0, "salle": 2, "praticien": "Dr Bernard", "debut": "14:00", "fin": "18:00"},
        {"jour": 1, "salle": 2, "praticien": "Dr Martin", "debut": "14:00", "fin": "18:00"},
        {"jour": 2, "salle": 2, "praticien": "Dr Dupont", "debut": "08:00", "fin": "12:00"},
        {"jour": 3, "salle": 2, "praticien": "Dr Martin", "debut": "14:00", "fin": "18:00"},
        {"jour": 0, "salle": 3, "praticien": "Dr Dupont", "debut": "08:00", "fin": "12:00"},
        {"jour": 1, "salle": 3, "praticien": "Dr Bernard", "debut": "08:00", "fin": "12:00"},
        {"jour": 2, "salle": 3, "praticien": "Dr Martin", "debut": "08:00", "fin": "12:00"},
        {"jour": 3, "salle": 3, "praticien": "Dr Dupont", "debut": "08:00", "fin": "12:00"},
    ]


# ---------------------------------------------------------------------------
# TODO 2 : remplacer par l'appel à vos algorithmes de placement.
#          Entrée : le patient (dict) + le planning. Sortie : 2 propositions.
#          Ici : placeholder qui prend les 2 premières vacations du praticien.
# ---------------------------------------------------------------------------
def proposer_creneaux(patient: dict, planning: list[dict]) -> list[dict]:
    lundi = lundi_prochain()
    vacs = [v for v in planning if v["praticien"] == patient["praticien"]]
    vacs.sort(key=lambda v: (v["jour"], v["debut"]))
    propositions = []
    for v in vacs[:2]:
        debut = datetime.strptime(v["debut"], "%H:%M")
        fin = debut + timedelta(minutes=150)
        propositions.append({
            "date": lundi + timedelta(days=v["jour"]),
            "debut": debut.strftime("%H:%M"),
            "fin": fin.strftime("%H:%M"),
            "salle": v["salle"],
            "praticien": v["praticien"],
            "lit_ok": True,
            "sspi_ok": True,
        })
    return propositions


# ---------------------------------------------------------------------------
# TODO 3 : enregistrer le créneau choisi (fichier, base de données…)
#          pour que les prochains placements en tiennent compte.
# ---------------------------------------------------------------------------
def valider_creneau(patient: dict, creneau: dict) -> None:
    patient["statut"] = "Planifié"
    patient["creneau"] = creneau


# ---------------------------------------------------------------------------
# Style et état
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
:root { --bleu:#1f4e5f; --bleu-clair:#e6eef1; --ligne:#cfd9de; }
h1, h2, h3 { color: var(--bleu); }
.tuiles div[data-testid="stButton"] > button { min-height: 130px; font-size: 1.25rem; border:1px solid var(--ligne); }
.grille { border-collapse: collapse; width: 100%; }
.grille th, .grille td { border: 1px solid var(--ligne); padding: 10px 12px; text-align: left; vertical-align: top; }
.grille th { background: var(--bleu); color: #fff; font-weight: 600; }
.grille td.salle { background: var(--bleu-clair); color: #16303a; font-weight: 600; width: 90px; }
.grille td.moi { background: #d8ecdf; color: #16303a; }
.grille td.moi small { color: #3d5560; }
.grille td small { color: #8fa0a8; }
.carte-ok, .carte-ok * { color: #16303a !important; }
.carte-ok { border-left: 6px solid #2e8b57; padding: 8px 16px; background:#eef7f1; }
</style>
""",
    unsafe_allow_html=True,
)

ss = st.session_state
ss.setdefault("page", "accueil")
ss.setdefault("patients", [])
ss.setdefault("patient_courant", None)
ss.setdefault("propositions", [])
ss.setdefault("planning", charger_planning_vacations())


def aller(page: str) -> None:
    ss.page = page


def bouton_retour() -> None:
    st.button("← Accueil", on_click=aller, args=("accueil",))


with st.sidebar:
    st.markdown("### 🏥 Bloc opératoire")
    ss.praticien = st.selectbox("Praticien connecté", PRATICIENS)  # TODO : remplacer par votre authentification
    st.caption("Sélection de démonstration : à remplacer par la connexion réelle.")


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def page_accueil() -> None:
    st.title("Planification du bloc opératoire")
    st.subheader(f"Bonjour {ss.praticien}")
    st.markdown('<div class="tuiles">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.button("📅  Planning", on_click=aller, args=("planning",), use_container_width=True)
    c2.button("👤  Ajouter un patient", on_click=aller, args=("ajout",), use_container_width=True)
    c3, c4 = st.columns(2)
    c3.button("👥  Mes patients", on_click=aller, args=("patients",), use_container_width=True)
    c4.button("⚙️  Administration", on_click=aller, args=("admin",), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def page_planning() -> None:
    bouton_retour()
    lundi = lundi_prochain()
    st.title("Planning des vacations")
    st.write(f"Semaine du {lundi:%d/%m/%Y} au {lundi + timedelta(days=6):%d/%m/%Y}")
    salles = sorted({v["salle"] for v in ss.planning})
    html = "<table class='grille'><tr><th></th>" + "".join(f"<th>{j}</th>" for j in JOURS) + "</tr>"
    for s in salles:
        html += f"<tr><td class='salle'>Salle {s}</td>"
        for j in range(len(JOURS)):
            v = next((x for x in ss.planning if x["salle"] == s and x["jour"] == j), None)
            if v:
                cls = "moi" if v["praticien"] == ss.praticien else ""
                html += f"<td class='{cls}'>{v['praticien']}<br><small>{v['debut']} – {v['fin']}</small></td>"
            else:
                html += "<td></td>"
        html += "</tr>"
    st.markdown(html + "</table>", unsafe_allow_html=True)
    st.caption(f"Vos vacations sont en vert ({ss.praticien}).")

    planifies = [p for p in ss.patients if p["statut"] == "Planifié"]
    if planifies:
        st.subheader("Patients planifiés")
        st.dataframe(
            [{
                "Patient": f"{p['prenom']} {p['nom']}",
                "Date": p["creneau"]["date"].strftime("%d/%m/%Y"),
                "Horaire": f"{p['creneau']['debut']} – {p['creneau']['fin']}",
                "Salle": p["creneau"]["salle"],
                "Praticien": p["creneau"]["praticien"],
            } for p in planifies],
            hide_index=True, use_container_width=True,
        )


def page_ajout() -> None:
    bouton_retour()
    st.title("Ajouter un patient")
    with st.form("form_patient"):
        st.subheader("Informations du patient")
        c1, c2 = st.columns(2)
        nom = c1.text_input("Nom")
        prenom = c2.text_input("Prénom")
        c1, c2 = st.columns(2)
        naissance = c1.date_input("Date de naissance", value=date(1970, 1, 1),
                                  min_value=date(1900, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
        sexe = c2.radio("Sexe", ["Femme", "Homme"], horizontal=True)
        entree = st.date_input("Date d'entrée à l'hôpital", value=lundi_prochain(), format="DD/MM/YYYY")

        st.subheader("Diagnostic")
        cim_principal = st.text_input("CIM principal", placeholder="ex. M17.1")
        cols = st.columns(5)
        cim_assoc = [cols[i].text_input(f"CIM associé {i + 1}") for i in range(5)]

        st.subheader("Intervention")
        cols = st.columns(4)
        ccam = [cols[i].text_input(f"CCAM {i + 1}", placeholder="ex. NFKA010") for i in range(4)]
        try:  # Streamlit >= 1.44 : tape pour filtrer + saisie libre acceptée
            intervention = st.selectbox(
                "Intervention", INTERVENTIONS, index=None, accept_new_value=True,
                placeholder="Commencez à taper (ex. Prothese Totale Genou)",
            ) or ""
        except TypeError:  # anciennes versions : suggestions seulement
            intervention = st.selectbox(
                "Intervention", INTERVENTIONS, index=None,
                placeholder="Commencez à taper (ex. Prothese Totale Genou)",
            ) or ""
        c1, c2, c3 = st.columns(3)
        type_interv = c1.selectbox("Type d'intervention", TYPES_INTERVENTION)
        anesth_type = c2.selectbox("Type d'anesthésie", TYPES_ANESTHESIE)
        anesth_loco = c3.checkbox("Anesthésie loco-régionale")

        envoye = st.form_submit_button("Trouver des créneaux", type="primary")

    if envoye:
        if not (nom.strip() and prenom.strip() and cim_principal.strip() and intervention.strip()):
            st.error("Renseignez au minimum le nom, le prénom, le CIM principal et l'intervention.")
            return
        cim_p, cim_a, ccam_n, erreurs = verifier_codes(cim_principal, cim_assoc, ccam)
        if erreurs:
            st.error("Corrigez les codes suivants :\n\n" + "\n".join(f"- {e}" for e in erreurs))
            return
        age = entree.year - naissance.year - ((entree.month, entree.day) < (naissance.month, naissance.day))
        patient = {
            "nom": nom.strip(), "prenom": prenom.strip(), "age": age, "sexe": sexe,
            "date_naissance": naissance, "date_entree": entree,
            "cim_principal": cim_p, "cim_assoc": cim_a,
            "ccam": ccam_n, "intervention": intervention.strip(),
            "type_intervention": type_interv, "anesth_type": anesth_type, "anesth_loco_reg": anesth_loco,
            "praticien": ss.praticien, "statut": "À placer", "creneau": None,
        }
        with st.spinner("Recherche des meilleurs créneaux…"):
            propositions = proposer_creneaux(patient, ss.planning)
        if not propositions:
            st.error("Aucun créneau compatible n'a été trouvé pour ce patient.")
            return
        ss.patients.append(patient)
        ss.patient_courant = patient
        ss.propositions = propositions
        ss.page = "proposition"
        st.rerun()


def choisir(creneau: dict) -> None:
    valider_creneau(ss.patient_courant, creneau)
    ss.page = "confirmation"


def page_proposition() -> None:
    p = ss.patient_courant
    st.title("Proposition de planification")
    st.write(f"**Patient :** {p['prenom']} {p['nom']}  \n**Intervention :** {p['intervention']}  \n**Praticien :** {p['praticien']}")
    st.write(f"{len(ss.propositions)} créneaux compatibles ont été trouvés.")
    cols = st.columns(len(ss.propositions))
    for i, (col, c) in enumerate(zip(cols, ss.propositions), start=1):
        with col, st.container(border=True):
            st.subheader(f"Proposition {i}")
            st.markdown(
                f"📅 {c['date']:%d/%m/%Y}  \n🕐 {c['debut']} – {c['fin']}  \n"
                f"🏥 Salle {c['salle']}  \n👨‍⚕️ {c['praticien']}"
            )
            st.write(f"Lit disponible : {'✓' if c['lit_ok'] else '✗'}")
            st.write(f"SSPI disponible : {'✓' if c['sspi_ok'] else '✗'}")
            st.button("Choisir ce créneau", key=f"choix{i}", on_click=choisir, args=(c,),
                      type="primary", use_container_width=True)
    st.button("← Modifier le patient", on_click=aller, args=("ajout",))


def page_confirmation() -> None:
    p = ss.patient_courant
    c = p["creneau"]
    st.markdown(
        f"<div class='carte-ok'><h3>✓ Patient planifié</h3>"
        f"<b>{p['prenom']} {p['nom']}</b><br>"
        f"📅 {c['date']:%d/%m/%Y}<br>🕐 {c['debut']} – {c['fin']}<br>"
        f"🏥 Salle {c['salle']}<br>👨‍⚕️ {c['praticien']}<br><br>"
        f"Le créneau a été ajouté au planning.</div>",
        unsafe_allow_html=True,
    )
    st.write("")
    st.button("Voir le planning", on_click=aller, args=("planning",), type="primary")
    st.button("Ajouter un autre patient", on_click=aller, args=("ajout",))


def page_patients() -> None:
    bouton_retour()
    st.title("Mes patients")
    mes = [p for p in ss.patients if p["praticien"] == ss.praticien]
    if not mes:
        st.info("Aucun patient pour le moment. Utilisez « Ajouter un patient » pour commencer.")
        return
    st.dataframe(
        [{
            "Patient": f"{p['prenom']} {p['nom']}", "Âge": p["age"], "Intervention": p["intervention"],
            "Statut": p["statut"],
            "Créneau": (f"{p['creneau']['date']:%d/%m/%Y} {p['creneau']['debut']} · Salle {p['creneau']['salle']}"
                        if p["creneau"] else "—"),
        } for p in mes],
        hide_index=True, use_container_width=True,
    )


def page_admin() -> None:
    bouton_retour()
    st.title("Administration")
    st.info("À définir (gestion des praticiens, des salles, régénération du planning des vacations…).")


PAGES = {
    "accueil": page_accueil, "planning": page_planning, "ajout": page_ajout,
    "proposition": page_proposition, "confirmation": page_confirmation,
    "patients": page_patients, "admin": page_admin,
}
PAGES[ss.page]()