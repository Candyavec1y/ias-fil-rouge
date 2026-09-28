from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np
import joblib
import pandas as pd

MODELES_DIR = Path("outputs/models_rapide")

CAT_COLS = [
    "type_intervention", "cim_diag_pr", "ccam_1", "sexe",
    "praticien", "anesth_type", "anesth_loco_reg"
]
NUM_COLS = ["age_annees", "annee", "mois", "jour_semaine"]


# =====================================================================
# Recherche dynamique de colonnes
# =====================================================================
def trouver_colonne(mots_cles: List[str], df: pd.DataFrame, min_match: Optional[int] = None) -> Optional[str]:
    if min_match is None:
        min_match = len(mots_cles)

    mots_cles_nettoyes = [
        mot.lower()
        .replace('è', 'e').replace('é', 'e').replace('ê', 'e')
        .replace('à', 'a').replace('â', 'a').replace('ï', 'i')
        .replace('î', 'i').replace('ô', 'o').replace('û', 'u').replace('ç', 'c')
        .replace(' ', '_').replace('(', '').replace(')', '')
        for mot in mots_cles
    ]
    for col in df.columns:
        col_nettoyee = str(col).lower().replace(' ', '_').replace('(', '').replace(')', '')
        matches = sum(1 for mot in mots_cles_nettoyes if mot in col_nettoyee)
        if matches >= min_match:
            return col
    return None


# =====================================================================
# Classe Patient
# =====================================================================
@dataclass
class Patient:
    id: int
    age: int
    sexe: str
    type_intervention: str
    diagnostic: str
    ambulatoire: bool
    duree_bloc: int            # Durée opératoire estimée (en minutes)
    chirurgien_id: int
    urgent: int                # Prédit ou forcé (entre 1 et 10)
    nuits_pre_op: int = 0
    nuits_post_op: int = 0
    date_min: Optional[date] = None


# =====================================================================
# Gestion des modèles
# =====================================================================
_MODELES_CACHE: Optional[Dict[str, Any]] = None

def _get_modeles(repertoire: Path = MODELES_DIR) -> Dict[str, Any]:
    global _MODELES_CACHE
    if _MODELES_CACHE is None:
        _MODELES_CACHE = {
            "clf_capacite": joblib.load(repertoire / "clf_type_capacite.joblib"),
            "reg_bloc": joblib.load(repertoire / "reg_duree_bloc.joblib"),
            "reg_avant": joblib.load(repertoire / "reg_duree_avant.joblib"),
            "reg_apres": joblib.load(repertoire / "reg_duree_apres.joblib"),
            "reg_urgence": joblib.load(repertoire / "reg_urgence.joblib"),
        }
    return _MODELES_CACHE


# =====================================================================
# Création et prédiction individuelle
# =====================================================================
def creer_patient_consultation(
    id_patient: int,
    sexe: str,
    date_naissance: str | date | datetime,
    cim_diag_pr: str,
    ccam_1: str,
    praticien: str,
    anesth_type: str,
    anesth_loco_reg: str,
    interv_type: str,
    cim_assoc_1: Optional[str] = None,
    cim_assoc_2: Optional[str] = None,
    cim_assoc_3: Optional[str] = None,
    cim_assoc_4: Optional[str] = None,
    cim_assoc_5: Optional[str] = None,
    ccam_2: Optional[str] = None,
    ccam_3: Optional[str] = None,
    ccam_4: Optional[str] = None,
    age: Optional[int] = None,
    chirurgien_id: int = 0,
    urgent: Optional[int] = None,
    date_min: Optional[date] = None,
) -> Patient:
    modeles = _get_modeles()

    if isinstance(date_naissance, (date, datetime)):
        dt_naissance = pd.to_datetime(date_naissance)
    else:
        dt_naissance = pd.to_datetime(date_naissance, dayfirst=True)

    dt_ref = pd.Timestamp.now()

    if age is None:
        age_annees = (dt_ref - dt_naissance).days / 365.25
        age_final = int(round(age_annees))
    else:
        age_annees = float(age)
        age_final = int(age)

    features = {
        "type_intervention": str(interv_type),
        "cim_diag_pr": str(cim_diag_pr),
        "ccam_1": str(ccam_1),
        "sexe": str(sexe),
        "praticien": str(praticien),
        "anesth_type": str(anesth_type),
        "anesth_loco_reg": str(anesth_loco_reg),
        "age_annees": age_annees,
        "annee": dt_ref.year,
        "mois": dt_ref.month,
        "jour_semaine": dt_ref.dayofweek,
    }

    df_inf = pd.DataFrame([features])[CAT_COLS + NUM_COLS]
    for c in CAT_COLS:
        df_inf[c] = df_inf[c].astype("category")

    # Inférences
    est_ambulatoire = (modeles["clf_capacite"].predict(df_inf)[0] == "ambulatoire")
    bloc_heures = max(0.0, float(modeles["reg_bloc"].predict(df_inf)[0]))
    duree_bloc_min = int(round(bloc_heures * 60))

    if est_ambulatoire:
        nuits_pre = 0
        nuits_post = 0
    else:
        nuits_pre = int(round(max(0.0, float(modeles["reg_avant"].predict(df_inf)[0]))))
        nuits_post = int(round(max(0.0, float(modeles["reg_apres"].predict(df_inf)[0]))))

    # Prédiction de l'urgence si non fournie manuellement
    if urgent is None:
        pred_urgence = float(modeles["reg_urgence"].predict(df_inf)[0])
        urgence_finale = int(np.clip(round(pred_urgence), 1, 10))
    else:
        urgence_finale = urgent

    return Patient(
        id=id_patient,
        age=age_final,
        sexe=str(sexe),
        type_intervention=str(interv_type),
        diagnostic=str(cim_diag_pr),
        ambulatoire=est_ambulatoire,
        duree_bloc=duree_bloc_min,
        chirurgien_id=chirurgien_id,
        urgent=urgence_finale,
        nuits_pre_op=nuits_pre,
        nuits_post_op=nuits_post,
        date_min=date_min if date_min is not None else dt_ref.date(),
    )


# =====================================================================
# Chargement par lot depuis le CSV
# =====================================================================
def charger_patients_depuis_csv(
    chemin_csv: str | Path = "donnees_hospitalieres.csv",
    n: int = 10,
    random_state: Optional[int] = 42,
) -> List[Patient]:
    df = pd.read_csv(chemin_csv, delimiter=",", encoding="utf-8", on_bad_lines="warn")

    n_echantillon = min(n, len(df))
    if random_state is not None:
        df_sample = df.sample(n=n_echantillon, random_state=random_state)
    else:
        df_sample = df.head(n_echantillon)

    col_naissance = trouver_colonne(["date", "naissance"], df_sample)
    col_sexe = trouver_colonne(["sexe"], df_sample)
    col_diag_pr = trouver_colonne(["cim", "diag", "pr"], df_sample)
    col_ccam_1 = trouver_colonne(["ccam", "1"], df_sample)
    col_praticien = trouver_colonne(["praticien"], df_sample)
    col_anesth_type = trouver_colonne(["anesth", "type"], df_sample)
    col_anesth_loco = trouver_colonne(["anesth", "loco"], df_sample)
    col_interv_type = trouver_colonne(["interv", "type"], df_sample)
    col_id = trouver_colonne(["no", "cas"], df_sample)

    liste_patients: List[Patient] = []

    for idx, (_, row) in enumerate(df_sample.iterrows(), start=1):
        id_patient = int(row[col_id]) if col_id and pd.notna(row[col_id]) else idx

        patient = creer_patient_consultation(
            id_patient=id_patient,
            sexe=str(row[col_sexe]) if col_sexe and pd.notna(row[col_sexe]) else "1",
            date_naissance=row[col_naissance] if col_naissance and pd.notna(row[col_naissance]) else "1980-01-01",
            cim_diag_pr=str(row[col_diag_pr]) if col_diag_pr and pd.notna(row[col_diag_pr]) else "Inconnu",
            ccam_1=str(row[col_ccam_1]) if col_ccam_1 and pd.notna(row[col_ccam_1]) else "Inconnu",
            praticien=str(row[col_praticien]) if col_praticien and pd.notna(row[col_praticien]) else "Inconnu",
            anesth_type=str(row[col_anesth_type]) if col_anesth_type and pd.notna(row[col_anesth_type]) else "Inconnu",
            anesth_loco_reg=str(row[col_anesth_loco]) if col_anesth_loco and pd.notna(row[col_anesth_loco]) else "Inconnu",
            interv_type=str(row[col_interv_type]) if col_interv_type and pd.notna(row[col_interv_type]) else "Inconnu",
            urgent=None,       # Déclenche la prédiction automatique par le ML
            chirurgien_id=0,
        )
        liste_patients.append(patient)

    return liste_patients


def afficher_patients(patients: List[Patient]) -> None:
    print("=" * 115)
    print(f"{'ID':<6} | {'ÂGE':<4} | {'SEXE':<4} | {'INTERVENTION':<30} | {'BLOC (min)':<10} | {'MODE':<12} | {'SÉJOUR (J)':<15} | {'URG':<3}")
    print("-" * 115)

    for p in patients:
        mode = "Ambulatoire" if p.ambulatoire else "Lit classique"
        sejour = "-" if p.ambulatoire else f"{p.nuits_pre_op}j av. / {p.nuits_post_op}j ap."
        interv = (p.type_intervention[:27] + "...") if len(p.type_intervention) > 30 else p.type_intervention

        print(
            f"{p.id:<6} | "
            f"{p.age:<4} | "
            f"{p.sexe:<4} | "
            f"{interv:<30} | "
            f"{p.duree_bloc:<10} | "
            f"{mode:<12} | "
            f"{sejour:<15} | "
            f"{p.urgent:<3}"
        )
    print("=" * 115)


if __name__ == "__main__":
    print("Chargement et prédiction pour 30 patients réels...\n")
    patients_test = charger_patients_depuis_csv(
        chemin_csv="donnees_hospitalieres.csv",
        n=30,
        random_state=42
    )
    afficher_patients(patients_test)