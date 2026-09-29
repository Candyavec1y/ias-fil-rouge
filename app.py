"""
Interface chirurgien - planification du bloc opératoire.
Lancer avec :  streamlit run app.py
"""
from datetime import date

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Planification du bloc opératoire", page_icon="", layout="wide")

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
# À aligner avec les valeurs de donnees_hospitalieres.csv
ANESTH_TYPES = ["Générale", "Locorégionale", "Locale", "Sédation", "Aucune"]
INTERV_TYPES = ["Programmée", "Urgente", "Ambulatoire"]


# =====================================================================
# BRANCHEMENT : ces 3 fonctions sont à relier à vos algorithmes
# =====================================================================
def charger_vacations():
    """Planning de l'étape 1 (figé). Renvoie une liste de dicts :
    salle, jour (0 = lundi), debut, fin, praticien.
    -> À remplacer par la lecture de la sortie de metaheuristiques/."""
    d = [
        ("Salle 1", 0, 8, 12, "Dr Martin"), ("Salle 1", 1, 8, 12, "Dr Dupont"),
        ("Salle 1", 2, 14, 18, "Dr Martin"), ("Salle 1", 3, 8, 12, "Dr Bernard"),
        ("Salle 2", 0, 14, 18, "Dr Bernard"), ("Salle 2", 1, 14, 18, "Dr Martin"),
        ("Salle 2", 2, 8, 12, "Dr Dupont"), ("Salle 2", 3, 14, 18, "Dr Martin"),
        ("Salle 3", 0, 8, 12, "Dr Dupont"), ("Salle 3", 1, 8, 12, "Dr Bernard"),
        ("Salle 3", 2, 8, 12, "Dr Martin"), ("Salle 3", 3, 8, 12, "Dr Dupont"),
    ]
    return [dict(salle=s, jour=j, debut=a, fin=b, praticien=p) for s, j, a, b, p in d]


def placer_patients(patients, vacations):
    """Étape 2 : recuit simulé + AGS + tabou.
    Doit renvoyer {id_patient: [proposition1, proposition2]}, chaque proposition
    étant un dict (salle, jour, debut, fin).
    -> Version factice : prend les 2 premières vacations du praticien."""
    res = {}
    for p in patients:
        v = [x for x in vacations if x["praticien"] == p["praticien"]][:2]
        res[p["id"]] = [{k: x[k] for k in ("salle", "jour", "debut", "fin")} for x in v]
    return res


def praticiens():
    return sorted({v["praticien"] for v in charger_vacations()})


# =====================================================================
# État et navigation
# =====================================================================
ss = st.session_state
ss.setdefault("page", "accueil")
ss.setdefault("patients", [])
ss.setdefault("propositions", {})
ss.setdefault("choix", {})


def aller(page):
    ss.page = page


def retour():
    st.button("← Accueil", on_click=aller, args=("accueil",))


def fmt(c):
    return f"{JOURS[c['jour']]} · {c['salle']} · {c['debut']:02d}h-{c['fin']:02d}h"


st.markdown(
    """<style>
    div[data-testid="stButton"] > button[kind="secondary"]:has(p:first-child) {min-height: 3rem;}
    .tuile button {height: 9rem; font-size: 1.4rem; border-radius: 12px;}
    </style>""",
    unsafe_allow_html=True,
)

with st.sidebar:
    ss.medecin = st.selectbox("Praticien connecté", praticiens())


# =====================================================================
# Pages
# =====================================================================
def page_accueil():
    st.title("🏥 Planification du bloc opératoire")
    st.subheader(f"Bonjour {ss.medecin}")
    tuiles = [("  Planning", "planning"), ("  Ajouter un patient", "ajout"),
              ("  Mes patients", "patients"), ("⚙️  Administration", "admin")]
    for i in range(0, 4, 2):
        cols = st.columns(2)
        for col, (label, page) in zip(cols, tuiles[i:i + 2]):
            with col:
                st.markdown('<div class="tuile">', unsafe_allow_html=True)
                st.button(label, key=page, on_click=aller, args=(page,), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)


def page_planning():
    retour()
    st.header("Planning des vacations")
    vac = charger_vacations()
    salles = sorted({v["salle"] for v in vac})
    grille = pd.DataFrame("", index=salles, columns=JOURS)
    for v in vac:
        grille.loc[v["salle"], JOURS[v["jour"]]] = f'{v["praticien"]}  {v["debut"]:02d}h-{v["fin"]:02d}h'
    mien = lambda x: "background-color: #cfe8e4; font-weight: 600" if ss.medecin in x else ""
    st.dataframe(grille.style.map(mien), use_container_width=True)
    st.caption(f"Vos vacations sont surlignées ({ss.medecin}).")


def page_ajout():
    retour()
    st.header("Ajouter un patient")
    with st.form("form_patient", clear_on_submit=True):
        st.subheader("Informations du patient")
        c1, c2 = st.columns(2)
        nom, prenom = c1.text_input("Nom"), c2.text_input("Prénom")
        c1, c2, c3 = st.columns(3)
        naissance = c1.date_input("Date de naissance", value=None, min_value=date(1900, 1, 1),
                                  max_value=date.today(), format="DD/MM/YYYY")
        sexe = c2.radio("Sexe", ["Femme", "Homme"], horizontal=True)
        entree = c3.date_input("Date d'entrée à l'hôpital", value=None, format="DD/MM/YYYY")

        st.subheader("Diagnostic")
        cim_p = st.text_input("CIM principal")
        cols = st.columns(5)
        cim_a = [cols[i].text_input(f"CIM associé {i + 1}") for i in range(5)]

        st.subheader("Actes")
        cols = st.columns(4)
        ccam = [cols[i].text_input(f"CCAM {i + 1}") for i in range(4)]

        st.subheader("Intervention")
        c1, c2, c3, c4 = st.columns(4)
        prat = c1.selectbox("Praticien", praticiens(), index=praticiens().index(ss.medecin))
        anesth = c2.selectbox("Type d'anesthésie", ANESTH_TYPES)
        loco = c3.selectbox("Anesthésie loco-régionale", ["Non", "Oui"])
        interv = c4.selectbox("Type d'intervention", INTERV_TYPES)

        if st.form_submit_button("Enregistrer le patient", type="primary"):
            if not (nom and prenom and naissance and entree and cim_p):
                st.error("Renseignez au minimum : nom, prénom, dates de naissance et d'entrée, CIM principal.")
            else:
                ss.patients.append(dict(
                    id=len(ss.patients) + 1, nom=nom, prenom=prenom, sexe=sexe,
                    naissance=naissance, entree=entree,
                    age=(entree - naissance).days // 365, praticien=prat,
                    cim_principal=cim_p, cim_associes=[c for c in cim_a if c],
                    ccam=[c for c in ccam if c], anesth_type=anesth,
                    loco_reg=loco, interv_type=interv,
                ))
                st.success(f"Patient {prenom} {nom} enregistré.")


def page_patients():
    retour()
    st.header("Mes patients")
    mes = [p for p in ss.patients if p["praticien"] == ss.medecin]
    if not mes:
        st.info("Aucun patient pour le moment. Ajoutez-en un depuis l'accueil.")
        return
    st.dataframe(pd.DataFrame(mes)[["id", "nom", "prenom", "age", "sexe", "entree", "cim_principal", "interv_type"]],
                 hide_index=True, use_container_width=True)
    if st.button("Lancer le placement", type="primary"):
        with st.spinner("Recherche des meilleurs créneaux..."):
            ss.propositions.update(placer_patients(mes, charger_vacations()))
        aller("choix")
        st.rerun()


def page_choix():
    retour()
    st.header("Choisir un créneau")
    mes = [p for p in ss.patients if p["praticien"] == ss.medecin and p["id"] in ss.propositions]
    if not mes:
        st.info("Aucune proposition. Lancez d'abord le placement depuis « Mes patients ».")
        return
    for p in mes:
        props = ss.propositions[p["id"]]
        with st.container(border=True):
            st.markdown(f"**{p['prenom']} {p['nom']}**, {p['age']} ans, {p['cim_principal']}")
            if ss.choix.get(p["id"]):
                st.success(f"Créneau validé : {fmt(ss.choix[p['id']])}")
                continue
            sel = st.radio("Créneaux proposés", range(len(props)), format_func=lambda i, pr=props: fmt(pr[i]),
                           key=f"radio_{p['id']}")
            if st.button("Valider ce créneau", key=f"ok_{p['id']}"):
                ss.choix[p["id"]] = props[sel]
                st.rerun()


def page_admin():
    retour()
    st.header("Administration")
    st.info("À définir (gestion des praticiens, des salles, export du planning).")


{"accueil": page_accueil, "planning": page_planning, "ajout": page_ajout,
 "patients": page_patients, "choix": page_choix, "admin": page_admin}[ss.page]()
