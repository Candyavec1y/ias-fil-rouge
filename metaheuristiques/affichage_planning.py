# ============================================================
# PLANNING OPERATOIRE
# ============================================================
#
# Instance de données destinée ensuite à une métaheuristique
# de placement de patients.
#
# Le planning est défini sur une semaine type :
#
#       Lundi
#       Mardi
#       Mercredi
#       Jeudi
#       Vendredi
#
# avec distinction :
#
#       - semaine PAIRE
#       - semaine IMPAIRE
#       - toutes les semaines
#
# ============================================================


from dataclasses import dataclass, field
from enum import Enum
from datetime import date, time, datetime
from typing import Optional


# ============================================================
# 1. ENUMERATIONS
# ============================================================

class Semaine(Enum):
    """
    Indique sur quelles semaines une vacation est active.
    """

    TOUTES = "toutes"
    PAIRE = "paire"
    IMPAIRE = "impaire"


class TypePlage(Enum):
    """
    Type d'utilisation d'une plage horaire.
    """

    VACATION = "vacation"
    URGENCE = "urgence"
    LIBRE = "libre"
    FERME = "ferme"


# ============================================================
# 2. JOURS
# ============================================================

LUNDI = 0
MARDI = 1
MERCREDI = 2
JEUDI = 3
VENDREDI = 4


NOMS_JOURS = {
    LUNDI: "Lundi",
    MARDI: "Mardi",
    MERCREDI: "Mercredi",
    JEUDI: "Jeudi",
    VENDREDI: "Vendredi",
}


# ============================================================
# 3. CLASSES DE DONNEES
# ============================================================

@dataclass
class Salle:
    id: int
    nom: str


@dataclass
class Chirurgien:
    id: int
    nom: str


@dataclass
class Vacation:
    """
    Une vacation opératoire.

    Exemple :

        Lundi
        Salle 2
        07h45 - 15h30
        JT
        toutes les semaines
    """

    id: int

    jour: int
    salle_id: int

    heure_debut: time
    heure_fin: time

    chirurgien_id: Optional[int]

    semaine: Semaine

    description: str = ""

    type_intervention: Optional[str] = None

    capacite_patients: Optional[int] = None

    def active_pour_semaine(
        self,
        semaine: Semaine
    ) -> bool:

        return (
            self.semaine == Semaine.TOUTES
            or self.semaine == semaine
        )

    @property
    def duree_minutes(self) -> int:

        debut = datetime.combine(
            date.today(),
            self.heure_debut
        )

        fin = datetime.combine(
            date.today(),
            self.heure_fin
        )

        return int(
            (fin - debut).total_seconds() / 60
        )


@dataclass
class PlageSpeciale:
    """
    Plage qui n'est pas une vacation classique.

    Exemple :
        URGENCES
        LIBRE
        FERME
    """

    id: int

    jour: int
    salle_id: int

    heure_debut: time
    heure_fin: time

    type_plage: TypePlage

    semaine: Semaine

    description: str = ""

    def active_pour_semaine(
        self,
        semaine: Semaine
    ) -> bool:

        return (
            self.semaine == Semaine.TOUTES
            or self.semaine == semaine
        )


@dataclass
class Patient:
    """
    Patient à placer par la future métaheuristique.
    """

    id: int

    nom: str

    chirurgien_id: Optional[int] = None

    duree_minutes: int = 0

    type_intervention: Optional[str] = None

    priorite: int = 0

    salle_preferentielle: Optional[int] = None

    urgence: bool = False


@dataclass
class PlacementPatient:
    """
    Représente le placement d'un patient
    dans une vacation.

    Cette classe sera utilisée par la recherche taboue.
    """

    patient_id: int

    vacation_id: int

    jour: int

    salle_id: int

    heure_debut: time

    heure_fin: time


@dataclass
class Planning:
    """
    Instance complète du problème.

    C'est cette structure qui sera donnée
    à la métaheuristique.
    """

    salles: dict[int, Salle]

    chirurgiens: dict[int, Chirurgien]

    vacations: list[Vacation]

    plages_speciales: list[PlageSpeciale]

    patients: list[Patient] = field(
        default_factory=list
    )


# ============================================================
# 4. SALLES
# ============================================================

SALLES = {

    1: Salle(
        id=1,
        nom="Salle 1"
    ),

    2: Salle(
        id=2,
        nom="Salle 2"
    ),

    3: Salle(
        id=3,
        nom="Salle 3"
    ),

    4: Salle(
        id=4,
        nom="Salle 4"
    ),

    5: Salle(
        id=5,
        nom="Salle 5"
    ),
}


# ============================================================
# 5. CHIRURGIENS
# ============================================================

CHIRURGIENS = {

    1: Chirurgien(1, "JT"),

    2: Chirurgien(2, "SR"),

    3: Chirurgien(3, "GA"),

    4: Chirurgien(4, "GHREA"),

    5: Chirurgien(5, "DEVOS"),

    6: Chirurgien(6, "MT"),

    7: Chirurgien(7, "DS"),

    8: Chirurgien(8, "RL"),

    9: Chirurgien(9, "FN"),

    10: Chirurgien(10, "TR"),

    11: Chirurgien(11, "CT"),

    12: Chirurgien(12, "MO"),

    13: Chirurgien(13, "CL"),

    14: Chirurgien(14, "DE"),

    15: Chirurgien(15, "DN"),

    16: Chirurgien(16, "JE"),

    17: Chirurgien(17, "LZ"),

    18: Chirurgien(18, "CU"),

    19: Chirurgien(19, "HA"),

    20: Chirurgien(20, "SM"),

    21: Chirurgien(21, "FP"),

    22: Chirurgien(22, "LR"),
}


# ============================================================
# 6. VACATIONS
# ============================================================
#
# IMPORTANT :
#
# semaine = PAIRE
#      -> uniquement semaines paires
#
# semaine = IMPAIRE
#      -> uniquement semaines impaires
#
# semaine = TOUTES
#      -> toutes les semaines
#
# ============================================================

VACATIONS = [

    # ========================================================
    # LUNDI
    # ========================================================

    Vacation(
        id=1,
        jour=LUNDI,
        salle_id=2,
        heure_debut=time(7, 45),
        heure_fin=time(15, 30),
        chirurgien_id=1,
        semaine=Semaine.TOUTES,
        description="JT",
    ),

    Vacation(
        id=2,
        jour=LUNDI,
        salle_id=3,
        heure_debut=time(8, 0),
        heure_fin=time(17, 30),
        chirurgien_id=2,
        semaine=Semaine.TOUTES,
        description="SR",
    ),

    Vacation(
        id=3,
        jour=LUNDI,
        salle_id=3,
        heure_debut=time(8, 0),
        heure_fin=time(13, 0),
        chirurgien_id=4,
        semaine=Semaine.IMPAIRE,
        description="GHREA - semaine impaire",
    ),

    Vacation(
        id=4,
        jour=LUNDI,
        salle_id=3,
        heure_debut=time(10, 0),
        heure_fin=time(15, 30),
        chirurgien_id=5,
        semaine=Semaine.IMPAIRE,
        description="DEVOS - semaine impaire",
    ),

    Vacation(
        id=5,
        jour=LUNDI,
        salle_id=3,
        heure_debut=time(13, 0),
        heure_fin=time(17, 30),
        chirurgien_id=6,
        semaine=Semaine.IMPAIRE,
        description="MT - semaine impaire",
    ),

    Vacation(
        id=6,
        jour=LUNDI,
        salle_id=4,
        heure_debut=time(8, 0),
        heure_fin=time(13, 0),
        chirurgien_id=3,
        semaine=Semaine.PAIRE,
        description="GA - semaine paire - 2 prothèses",
        type_intervention="PROTHESE",
        capacite_patients=2,
    ),

    Vacation(
        id=7,
        jour=LUNDI,
        salle_id=4,
        heure_debut=time(10, 0),
        heure_fin=time(15, 30),
        chirurgien_id=7,
        semaine=Semaine.TOUTES,
        description="DS",
    ),

    Vacation(
        id=8,
        jour=LUNDI,
        salle_id=4,
        heure_debut=time(8, 0),
        heure_fin=time(10, 0),
        chirurgien_id=8,
        semaine=Semaine.IMPAIRE,
        description="RL - semaine impaire",
    ),

    Vacation(
        id=9,
        jour=LUNDI,
        salle_id=5,
        heure_debut=time(8, 0),
        heure_fin=time(15, 30),
        chirurgien_id=9,
        semaine=Semaine.TOUTES,
        description="FN",
    ),


    # ========================================================
    # MARDI
    # ========================================================

    Vacation(
        id=10,
        jour=MARDI,
        salle_id=2,
        heure_debut=time(7, 45),
        heure_fin=time(15, 30),
        chirurgien_id=1,
        semaine=Semaine.TOUTES,
        description="JT",
    ),

    Vacation(
        id=11,
        jour=MARDI,
        salle_id=3,
        heure_debut=time(8, 0),
        heure_fin=time(13, 0),
        chirurgien_id=10,
        semaine=Semaine.TOUTES,
        description="TR",
    ),

    Vacation(
        id=12,
        jour=MARDI,
        salle_id=3,
        heure_debut=time(13, 30),
        heure_fin=time(17, 30),
        chirurgien_id=6,
        semaine=Semaine.TOUTES,
        description="MT",
    ),

    Vacation(
        id=13,
        jour=MARDI,
        salle_id=4,
        heure_debut=time(8, 0),
        heure_fin=time(15, 30),
        chirurgien_id=11,
        semaine=Semaine.TOUTES,
        description="CT",
    ),

    Vacation(
        id=14,
        jour=MARDI,
        salle_id=5,
        heure_debut=time(8, 0),
        heure_fin=time(15, 30),
        chirurgien_id=12,
        semaine=Semaine.TOUTES,
        description="MO",
    ),


    # ========================================================
    # MERCREDI
    # ========================================================

    Vacation(
        id=15,
        jour=MERCREDI,
        salle_id=2,
        heure_debut=time(7, 45),
        heure_fin=time(15, 30),
        chirurgien_id=13,
        semaine=Semaine.TOUTES,
        description="CL",
    ),

    Vacation(
        id=16,
        jour=MERCREDI,
        salle_id=3,
        heure_debut=time(8, 0),
        heure_fin=time(15, 30),
        chirurgien_id=14,
        semaine=Semaine.TOUTES,
        description="DE",
    ),

    Vacation(
        id=17,
        jour=MERCREDI,
        salle_id=4,
        heure_debut=time(8, 0),
        heure_fin=time(13, 0),
        chirurgien_id=15,
        semaine=Semaine.TOUTES,
        description="DN",
    ),

    Vacation(
        id=18,
        jour=MERCREDI,
        salle_id=5,
        heure_debut=time(8, 0),
        heure_fin=time(13, 0),
        chirurgien_id=6,
        semaine=Semaine.PAIRE,
        description="MT - semaine paire",
    ),

    Vacation(
        id=19,
        jour=MERCREDI,
        salle_id=5,
        heure_debut=time(8, 0),
        heure_fin=time(15, 30),
        chirurgien_id=16,
        semaine=Semaine.IMPAIRE,
        description="JE - semaine impaire",
    ),


    # ========================================================
    # JEUDI
    # ========================================================

    Vacation(
        id=20,
        jour=JEUDI,
        salle_id=2,
        heure_debut=time(7, 45),
        heure_fin=time(15, 30),
        chirurgien_id=14,
        semaine=Semaine.TOUTES,
        description="DE",
    ),

    Vacation(
        id=21,
        jour=JEUDI,
        salle_id=3,
        heure_debut=time(8, 0),
        heure_fin=time(15, 30),
        chirurgien_id=2,
        semaine=Semaine.TOUTES,
        description="SR",
    ),

    Vacation(
        id=22,
        jour=JEUDI,
        salle_id=4,
        heure_debut=time(8, 0),
        heure_fin=time(15, 30),
        chirurgien_id=11,
        semaine=Semaine.TOUTES,
        description="CT",
    ),

    Vacation(
        id=23,
        jour=JEUDI,
        salle_id=5,
        heure_debut=time(8, 0),
        heure_fin=time(15, 30),
        chirurgien_id=17,
        semaine=Semaine.TOUTES,
        description="LZ",
    ),


    # ========================================================
    # VENDREDI
    # ========================================================

    Vacation(
        id=24,
        jour=VENDREDI,
        salle_id=2,
        heure_debut=time(7, 45),
        heure_fin=time(13, 0),
        chirurgien_id=13,
        semaine=Semaine.TOUTES,
        description="CL",
    ),

    Vacation(
        id=25,
        jour=VENDREDI,
        salle_id=3,
        heure_debut=time(8, 0),
        heure_fin=time(13, 0),
        chirurgien_id=18,
        semaine=Semaine.TOUTES,
        description="CU",
    ),

    Vacation(
        id=26,
        jour=VENDREDI,
        salle_id=3,
        heure_debut=time(13, 30),
        heure_fin=time(15, 30),
        chirurgien_id=6,
        semaine=Semaine.TOUTES,
        description="MT",
    ),

    Vacation(
        id=27,
        jour=VENDREDI,
        salle_id=4,
        heure_debut=time(8, 0),
        heure_fin=time(13, 0),
        chirurgien_id=19,
        semaine=Semaine.PAIRE,
        description="HA - semaine paire",
    ),

    Vacation(
        id=28,
        jour=VENDREDI,
        salle_id=4,
        heure_debut=time(8, 0),
        heure_fin=time(17, 30),
        chirurgien_id=20,
        semaine=Semaine.IMPAIRE,
        description="SM - semaine impaire",
    ),

    Vacation(
        id=29,
        jour=VENDREDI,
        salle_id=4,
        heure_debut=time(13, 30),
        heure_fin=time(17, 30),
        chirurgien_id=21,
        semaine=Semaine.TOUTES,
        description="FP",
    ),

    Vacation(
        id=30,
        jour=VENDREDI,
        salle_id=5,
        heure_debut=time(8, 0),
        heure_fin=time(13, 0),
        chirurgien_id=22,
        semaine=Semaine.TOUTES,
        description="LR",
    ),
]


# ============================================================
# 7. PLAGES SPECIALES
# ============================================================

PLAGES_SPECIALES = [

    # ----------------------------
    # LUNDI
    # ----------------------------

    PlageSpeciale(
        id=100,
        jour=LUNDI,
        salle_id=4,
        heure_debut=time(13, 0),
        heure_fin=time(15, 30),
        type_plage=TypePlage.URGENCE,
        semaine=Semaine.PAIRE,
        description="URGENCES - semaine paire",
    ),

    # ----------------------------
    # MARDI
    # ----------------------------

    PlageSpeciale(
        id=101,
        jour=MARDI,
        salle_id=3,
        heure_debut=time(13, 30),
        heure_fin=time(15, 30),
        type_plage=TypePlage.URGENCE,
        semaine=Semaine.TOUTES,
        description="URGENCES",
    ),

    # ----------------------------
    # MERCREDI
    # ----------------------------

    PlageSpeciale(
        id=102,
        jour=MERCREDI,
        salle_id=4,
        heure_debut=time(13, 0),
        heure_fin=time(15, 30),
        type_plage=TypePlage.URGENCE,
        semaine=Semaine.TOUTES,
        description="URGENCES",
    ),

    PlageSpeciale(
        id=103,
        jour=MERCREDI,
        salle_id=5,
        heure_debut=time(13, 0),
        heure_fin=time(15, 30),
        type_plage=TypePlage.URGENCE,
        semaine=Semaine.TOUTES,
        description="URGENCES",
    ),

    # ----------------------------
    # VENDREDI
    # ----------------------------

    PlageSpeciale(
        id=104,
        jour=VENDREDI,
        salle_id=2,
        heure_debut=time(13, 30),
        heure_fin=time(15, 30),
        type_plage=TypePlage.URGENCE,
        semaine=Semaine.TOUTES,
        description="URGENCES",
    ),

    PlageSpeciale(
        id=105,
        jour=VENDREDI,
        salle_id=5,
        heure_debut=time(13, 30),
        heure_fin=time(17, 30),
        type_plage=TypePlage.LIBRE,
        semaine=Semaine.TOUTES,
        description="LIBRE",
    ),
]


# ============================================================
# 8. PATIENTS
# ============================================================
#
# Pour l'instant on laisse vide.
#
# Tu pourras ensuite charger tes vrais patients ici.
#
# Exemple :
#
# Patient(
#     id=1,
#     nom="Patient 001",
#     chirurgien_id=1,
#     duree_minutes=120,
#     type_intervention="PROTHESE",
#     priorite=2
# )
#
# ============================================================

PATIENTS = []


# ============================================================
# 9. CREATION DE L'INSTANCE
# ============================================================

INSTANCE = Planning(

    salles=SALLES,

    chirurgiens=CHIRURGIENS,

    vacations=VACATIONS,

    plages_speciales=PLAGES_SPECIALES,

    patients=PATIENTS
)


# ============================================================
# 10. DETERMINATION DE LA SEMAINE
# ============================================================

def type_semaine(
    date_reference: date
) -> Semaine:
    """
    Retourne PAIRE ou IMPAIRE à partir
    du numéro ISO de la semaine.
    """

    numero = date_reference.isocalendar().week

    if numero % 2 == 0:
        return Semaine.PAIRE

    return Semaine.IMPAIRE


# ============================================================
# 11. VACATIONS ACTIVES
# ============================================================

def vacations_actives(
    planning: Planning,
    semaine: Semaine
) -> list[Vacation]:

    return [

        vacation

        for vacation in planning.vacations

        if vacation.active_pour_semaine(semaine)
    ]


# ============================================================
# 12. PLAGES SPECIALES ACTIVES
# ============================================================

def plages_speciales_actives(
    planning: Planning,
    semaine: Semaine
) -> list[PlageSpeciale]:

    return [

        plage

        for plage in planning.plages_speciales

        if plage.active_pour_semaine(semaine)
    ]


# ============================================================
# 13. VACATIONS COMPATIBLES AVEC UN PATIENT
# ============================================================

def vacations_compatibles(
    planning: Planning,
    patient: Patient,
    semaine: Semaine
) -> list[Vacation]:
    """
    Retourne les vacations dans lesquelles
    le patient pourrait potentiellement être placé.

    Cette fonction servira directement à la métaheuristique.
    """

    resultat = []

    vacations = vacations_actives(
        planning,
        semaine
    )

    for vacation in vacations:

        # ----------------------------------------------------
        # 1. Vérification du chirurgien
        # ----------------------------------------------------

        if patient.chirurgien_id is not None:

            if vacation.chirurgien_id != patient.chirurgien_id:
                continue

        # ----------------------------------------------------
        # 2. Vérification de la salle
        # ----------------------------------------------------

        if patient.salle_preferentielle is not None:

            if (
                vacation.salle_id
                != patient.salle_preferentielle
            ):
                continue

        # ----------------------------------------------------
        # 3. Vérification du type d'intervention
        # ----------------------------------------------------

        if (
            patient.type_intervention is not None
            and vacation.type_intervention is not None
        ):

            if (
                patient.type_intervention
                != vacation.type_intervention
            ):
                continue

        # ----------------------------------------------------
        # 4. Vérification de la durée
        # ----------------------------------------------------

        if (
            vacation.duree_minutes
            < patient.duree_minutes
        ):
            continue

        # ----------------------------------------------------
        # 5. La vacation est compatible
        # ----------------------------------------------------

        resultat.append(vacation)

    return resultat


# ============================================================
# 14. AFFICHAGE COMPLET
# ============================================================

def afficher_planning(
    planning: Planning,
    semaine: Semaine,
    titre: str = "PLANNING"
):
    """
    Affiche TOUS les jours :

        Lundi
        Mardi
        Mercredi
        Jeudi
        Vendredi

    pour une semaine paire ou impaire.
    """

    print()
    print("=" * 120)
    print(
        f"{titre} - SEMAINE {semaine.value.upper()}"
    )
    print("=" * 120)

    vacations = vacations_actives(
        planning,
        semaine
    )

    plages_speciales = plages_speciales_actives(
        planning,
        semaine
    )

    # ========================================================
    # BOUCLE SUR LES 5 JOURS
    # ========================================================

    for jour in range(5):

        print()
        print()
        print("#" * 120)
        print(
            f"# {NOMS_JOURS[jour].upper():^116} #"
        )
        print("#" * 120)

        # ----------------------------------------------------
        # Boucle sur les salles
        # ----------------------------------------------------

        for salle in planning.salles.values():

            print()
            print(
                f"  {'-' * 110}"
            )

            print(
                f"  {salle.nom}"
            )

            print(
                f"  {'-' * 110}"
            )

            elements = []

            # ------------------------------------------------
            # Vacations
            # ------------------------------------------------

            for vacation in vacations:

                if (
                    vacation.jour == jour
                    and vacation.salle_id == salle.id
                ):

                    elements.append(
                        (
                            vacation.heure_debut,
                            vacation.heure_fin,
                            "VACATION",
                            vacation
                        )
                    )

            # ------------------------------------------------
            # Urgences / libres
            # ------------------------------------------------

            for plage in plages_speciales:

                if (
                    plage.jour == jour
                    and plage.salle_id == salle.id
                ):

                    elements.append(
                        (
                            plage.heure_debut,
                            plage.heure_fin,
                            plage.type_plage.value.upper(),
                            plage
                        )
                    )

            # ------------------------------------------------
            # Aucun élément
            # ------------------------------------------------

            if not elements:

                print(
                    "      Aucun élément programmé."
                )

                continue

            # ------------------------------------------------
            # Tri chronologique
            # ------------------------------------------------

            elements.sort(
                key=lambda x: x[0]
            )

            # ------------------------------------------------
            # Affichage
            # ------------------------------------------------

            for (
                heure_debut,
                heure_fin,
                type_element,
                element
            ) in elements:

                debut = heure_debut.strftime(
                    "%H:%M"
                )

                fin = heure_fin.strftime(
                    "%H:%M"
                )

                # --------------------------------------------
                # VACATION
                # --------------------------------------------

                if type_element == "VACATION":

                    if (
                        element.chirurgien_id
                        is not None
                    ):

                        chirurgien = (
                            planning.chirurgiens[
                                element.chirurgien_id
                            ].nom
                        )

                    else:

                        chirurgien = "-"

                    print(
                        f"      "
                        f"{debut} - {fin}"
                        f"   "
                        f"{chirurgien:<10}"
                        f"   "
                        f"{element.description}"
                    )

                # --------------------------------------------
                # URGENCE / LIBRE / FERME
                # --------------------------------------------

                else:

                    print(
                        f"      "
                        f"{debut} - {fin}"
                        f"   "
                        f"{type_element:<10}"
                        f"   "
                        f"{element.description}"
                    )

    # ========================================================
    # FIN
    # ========================================================

    print()
    print("=" * 120)

    print(
        f"FIN DU PLANNING - "
        f"SEMAINE {semaine.value.upper()}"
    )

    print("=" * 120)


# ============================================================
# 15. AFFICHAGE DES DEUX SEMAINES
# ============================================================

def afficher_deux_semaines(
    planning: Planning
):
    """
    Affiche successivement :

        1. semaine paire
        2. semaine impaire

    Très pratique pour vérifier visuellement
    les alternances du planning.
    """

    afficher_planning(
        planning,
        Semaine.PAIRE,
        "PLANNING"
    )

    print("\n\n")

    afficher_planning(
        planning,
        Semaine.IMPAIRE,
        "PLANNING"
    )


# ============================================================
# 16. AFFICHAGE D'UN PATIENT ET DE SES POSSIBILITES
# ============================================================

def afficher_possibilites_patient(
    planning: Planning,
    patient: Patient,
    semaine: Semaine
):
    """
    Affiche toutes les vacations compatibles
    avec un patient.

    C'est exactement ce que la future recherche
    taboue pourra utiliser pour construire
    les voisins.
    """

    print()
    print("=" * 100)

    print(
        f"PATIENT : {patient.nom}"
    )

    print(
        f"SEMAINE : {semaine.value}"
    )

    print("=" * 100)

    compatibles = vacations_compatibles(
        planning,
        patient,
        semaine
    )

    if not compatibles:

        print(
            "Aucune vacation compatible."
        )

        return

    for vacation in compatibles:

        chirurgien = (
            planning.chirurgiens[
                vacation.chirurgien_id
            ].nom
            if vacation.chirurgien_id is not None
            else "-"
        )

        salle = planning.salles[
            vacation.salle_id
        ].nom

        print(
            f"{NOMS_JOURS[vacation.jour]:<10}"
            f"| {salle:<10}"
            f"| {vacation.heure_debut.strftime('%H:%M')}"
            f" - "
            f"{vacation.heure_fin.strftime('%H:%M')}"
            f"| {chirurgien:<8}"
            f"| {vacation.description}"
        )


# ============================================================
# 17. EXEMPLE DE PATIENT
# ============================================================
#
# Cette partie est uniquement un exemple.
#
# Elle montre comment la future métaheuristique pourra
# interroger les possibilités d'un patient.
#
# ============================================================

PATIENT_TEST = Patient(

    id=1,

    nom="Patient TEST",

    chirurgien_id=1,

    duree_minutes=120,

    type_intervention=None,

    priorite=1
)


# ============================================================
# 18. PROGRAMME PRINCIPAL
# ============================================================

if __name__ == "__main__":

    # ========================================================
    # A. INFORMATIONS GENERALES
    # ========================================================

    print()
    print("=" * 100)
    print("INSTANCE DU PLANNING OPERATOIRE")
    print("=" * 100)

    print()
    print(
        f"Nombre de salles       : "
        f"{len(INSTANCE.salles)}"
    )

    print(
        f"Nombre de chirurgiens  : "
        f"{len(INSTANCE.chirurgiens)}"
    )

    print(
        f"Nombre de vacations    : "
        f"{len(INSTANCE.vacations)}"
    )

    print(
        f"Nombre de plages spéciales : "
        f"{len(INSTANCE.plages_speciales)}"
    )

    # ========================================================
    # B. AFFICHAGE SEMAINE PAIRE
    # ========================================================

    afficher_planning(
        INSTANCE,
        Semaine.PAIRE,
        "PLANNING OPERATOIRE"
    )

    # ========================================================
    # C. AFFICHAGE SEMAINE IMPAIRE
    # ========================================================
    #
    # Décommente cette partie si tu veux afficher également
    # la semaine impaire.
    #
    # ========================================================

    afficher_planning(
        INSTANCE,
        Semaine.IMPAIRE,
        "PLANNING OPERATOIRE"
    )

    # ========================================================
    # D. TEST DE DETERMINATION D'UNE SEMAINE
    # ========================================================

    date_test = date(
        2026,
        9,
        22
    )

    semaine_test = type_semaine(
        date_test
    )

    print()
    print("=" * 100)

    print(
        f"La date "
        f"{date_test.strftime('%d/%m/%Y')}"
        f" correspond à une semaine "
        f"{semaine_test.value}."
    )

    print("=" * 100)

    # ========================================================
    # E. TEST DES POSSIBILITES D'UN PATIENT
    # ========================================================

    afficher_possibilites_patient(
        INSTANCE,
        PATIENT_TEST,
        Semaine.PAIRE
    )