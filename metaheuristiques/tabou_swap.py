from dataclasses import dataclass
from datetime import date, time, timedelta
from typing import List, Dict, Optional, Tuple
import random
import math


# ============================================================
# 1. STRUCTURES DE DONNÉES
# ============================================================

@dataclass
class Patient:
    """
    Représente un patient / une intervention à programmer.
    """

    id: int
    age: int
    sexe: str
    type_intervention: str
    ambulatoire: bool
    duree_operation: float       # minutes
    duree_sejour: int            # nombre de nuits
    diagnostic: str
    chirurgien: str


@dataclass
class Vacation:
    """
    Représente une vacation opératoire.
    """

    id: int
    salle: str
    date: date
    heure_debut: time
    heure_fin: time
    chirurgien: str
    type_intervention: str
    capacite: float              # minutes disponibles

# ============================================================
# 1. STRUCTURES DE DONNÉES
# ============================================================

@dataclass
class Patient:
    id: int
    age: int
    sexe: str
    type_intervention: str
    ambulatoire: bool
    duree_operation: float
    duree_sejour: int
    diagnostic: str
    chirurgien: str


@dataclass
class Vacation:
    id: int
    salle: str
    date: date
    heure_debut: time
    heure_fin: time
    chirurgien: str
    type_intervention: str
    capacite: float


# ============================================================
# 2. RECHERCHE TABOUE (MOUVEMENT SWAP)
# ============================================================

class RechercheTaboue:

    def __init__(
        self,
        patients: List[Patient],
        vacations: List[Vacation],
        nombre_lits: int,
        nombre_places_ambulatoires: int,
        nombre_iterations: int = 1000,
        taille_tabou: int = 10,
        taille_voisinage: int = 50,
        nombre_solutions_initiales: int = 5,
        stagnation_max: int = 100,
        seuil_intensification: int = 50,
        nombre_solutions_historique: int = 20,
        taux_diversification: float = 0.10,
        poids_bloc: float = 0.50,
        poids_hebergement: float = 0.50,
        seed: Optional[int] = 42
    ):
        self.patients = patients
        self.vacations = vacations
        self.nombre_lits = nombre_lits
        self.nombre_places_ambulatoires = nombre_places_ambulatoires

        self.nombre_iterations = nombre_iterations
        self.taille_tabou = taille_tabou
        self.taille_voisinage = taille_voisinage
        self.nombre_solutions_initiales = nombre_solutions_initiales
        self.stagnation_max = stagnation_max
        self.seuil_intensification = seuil_intensification
        self.nombre_solutions_historique = nombre_solutions_historique
        self.taux_diversification = taux_diversification
        self.poids_bloc = poids_bloc
        self.poids_hebergement = poids_hebergement

        if not math.isclose(poids_bloc + poids_hebergement, 1.0):
            raise ValueError("Les poids de la fonction objectif doivent sommer à 1.")

        if seed is not None:
            random.seed(seed)

        self.patients_dict = {p.id: p for p in patients}
        self.vacations_dict = {v.id: v for v in vacations}

    def compatible(self, patient: Patient, vacation: Vacation) -> bool:
        if patient.chirurgien != vacation.chirurgien:
            return False
        if patient.type_intervention != vacation.type_intervention:
            return False
        if patient.duree_operation > vacation.capacite:
            return False
        return True

    def vacations_compatibles(self, patient: Patient) -> List[Vacation]:
        return [v for v in self.vacations if self.compatible(patient, v)]

    def calculer_charges(self, solution: Dict[int, int]) -> Dict[int, float]:
        charges = {v.id: 0.0 for v in self.vacations}
        for patient_id, vacation_id in solution.items():
            patient = self.patients_dict[patient_id]
            charges[vacation_id] += patient.duree_operation
        return charges

    def occupation_hebergement(self, solution: Dict[int, int]) -> Tuple[Dict[date, int], Dict[date, int]]:
        occupation_lits = {}
        occupation_ambulatoire = {}

        for patient_id, vacation_id in solution.items():
            patient = self.patients_dict[patient_id]
            vacation = self.vacations_dict[vacation_id]
            jour_operation = vacation.date

            if patient.ambulatoire:
                occupation_ambulatoire.setdefault(jour_operation, 0)
                occupation_ambulatoire[jour_operation] += 1
            else:
                for nuit in range(patient.duree_sejour):
                    jour = jour_operation + timedelta(days=nuit)
                    occupation_lits.setdefault(jour, 0)
                    occupation_lits[jour] += 1

        return occupation_lits, occupation_ambulatoire

    def faisable(self, solution: Dict[int, int]) -> bool:
        if len(solution) != len(self.patients):
            return False

        for patient_id, vacation_id in solution.items():
            patient = self.patients_dict[patient_id]
            vacation = self.vacations_dict[vacation_id]
            if not self.compatible(patient, vacation):
                return False

        charges = self.calculer_charges(solution)
        for vacation_id, charge in charges.items():
            capacite = self.vacations_dict[vacation_id].capacite
            if charge > capacite:
                return False

        occupation_lits, occupation_ambulatoire = self.occupation_hebergement(solution)

        for jour, occupation in occupation_lits.items():
            if occupation > self.nombre_lits:
                return False

        for jour, occupation in occupation_ambulatoire.items():
            if occupation > self.nombre_places_ambulatoires:
                return False

        return True

    def construire_solution_initiale(self, randomisation: bool = True) -> Dict[int, int]:
        solution = {}
        charges = {v.id: 0.0 for v in self.vacations}

        patients_tries = sorted(
            self.patients,
            key=lambda p: (len(self.vacations_compatibles(p)), -p.duree_operation)
        )

        for patient in patients_tries:
            vacations_possibles = []
            for vacation in self.vacations:
                if not self.compatible(patient, vacation):
                    continue
                nouvelle_charge = charges[vacation.id] + patient.duree_operation
                if nouvelle_charge <= vacation.capacite:
                    vacations_possibles.append(vacation)

            if not vacations_possibles:
                raise ValueError(f"Impossible de construire une solution initiale faisable pour le patient {patient.id}.")

            if randomisation:
                vacations_possibles.sort(key=lambda v: v.capacite - charges[v.id] - patient.duree_operation)
                nombre_choix = min(3, len(vacations_possibles))
                vacation = random.choice(vacations_possibles[:nombre_choix])
            else:
                vacation = min(vacations_possibles, key=lambda v: v.capacite - charges[v.id] - patient.duree_operation)

            solution[patient.id] = vacation.id
            charges[vacation.id] += patient.duree_operation

        return solution

    def critere_bloc(self, solution: Dict[int, int]) -> float:
        charges = self.calculer_charges(solution)
        taux = []
        for vacation in self.vacations:
            if vacation.capacite <= 0:
                continue
            taux.append(charges[vacation.id] / vacation.capacite)

        if not taux:
            return 0.0

        moyenne = sum(taux) / len(taux)
        variance = sum((t - moyenne) ** 2 for t in taux) / len(taux)
        return variance

    def critere_hebergement(self, solution: Dict[int, int]) -> float:
        occupation_lits, _ = self.occupation_hebergement(solution)
        occupations = list(occupation_lits.values())
        if not occupations:
            return 0.0

        moyenne = sum(occupations) / len(occupations)
        variance = sum((occ - moyenne) ** 2 for occ in occupations) / len(occupations)
        return variance

    def normaliser(self, valeur: float, minimum: float, maximum: float) -> float:
        if maximum <= minimum:
            return 0.0
        return (valeur - minimum) / (maximum - minimum)

    def evaluation(self, solution: Dict[int, int], bornes: Optional[Dict[str, Tuple[float, float]]] = None) -> float:
        if not self.faisable(solution):
            return float("inf")

        score_bloc = self.critere_bloc(solution)
        score_hebergement = self.critere_hebergement(solution)

        if bornes is not None:
            score_bloc = self.normaliser(score_bloc, bornes["bloc"][0], bornes["bloc"][1])
            score_hebergement = self.normaliser(score_hebergement, bornes["hebergement"][0], bornes["hebergement"][1])

        score = self.poids_bloc * score_bloc + self.poids_hebergement * score_hebergement
        return score

    # ========================================================
    # MODIFICATION PRINCIPALE : MOUVEMENT SWAP (ÉCHANGE)
    # ========================================================

    def appliquer_mouvement(
        self,
        solution: Dict[int, int],
        p1_id: int,
        p2_id: int
    ) -> Dict[int, int]:
        """
        Échange les vacations de deux patients (mouvement Swap).
        """
        nouvelle_solution = solution.copy()
        vac1 = nouvelle_solution[p1_id]
        vac2 = nouvelle_solution[p2_id]
        
        nouvelle_solution[p1_id] = vac2
        nouvelle_solution[p2_id] = vac1
        
        return nouvelle_solution

    def generer_voisinage(
        self,
        solution: Dict[int, int],
        nombre_voisins: Optional[int] = None
    ):
        if nombre_voisins is None:
            nombre_voisins = self.taille_voisinage

        mouvements_possibles = []
        patients_ids = list(solution.keys())

        # Parcourir toutes les paires uniques de patients
        for i in range(len(patients_ids)):
            for j in range(i + 1, len(patients_ids)):
                p1_id = patients_ids[i]
                p2_id = patients_ids[j]

                vac1 = solution[p1_id]
                vac2 = solution[p2_id]

                # Inutile d'échanger s'ils sont dans la même vacation
                if vac1 == vac2:
                    continue

                mouvement = (p1_id, p2_id, vac1, vac2)
                mouvements_possibles.append(mouvement)

        if len(mouvements_possibles) <= nombre_voisins:
            mouvements_selectionnes = mouvements_possibles
        else:
            mouvements_selectionnes = random.sample(mouvements_possibles, nombre_voisins)

        voisins = []
        for mouvement in mouvements_selectionnes:
            p1_id, p2_id, vac1, vac2 = mouvement
            voisin = self.appliquer_mouvement(solution, p1_id, p2_id)

            if self.faisable(voisin):
                voisins.append((voisin, mouvement))

        return voisins

    def generer_voisins_diversifies(
        self,
        solution: Dict[int, int],
        nombre_voisins: int
    ):
        charges = self.calculer_charges(solution)
        vacations_triees = sorted(
            self.vacations,
            key=lambda v: charges[v.id] / v.capacite if v.capacite > 0 else float("inf")
        )
        vacations_cibles_ids = {v.id for v in vacations_triees[:max(1, len(vacations_triees) // 3)]}

        mouvements = []
        patients_ids = list(solution.keys())

        for i in range(len(patients_ids)):
            for j in range(i + 1, len(patients_ids)):
                p1_id = patients_ids[i]
                p2_id = patients_ids[j]

                vac1 = solution[p1_id]
                vac2 = solution[p2_id]

                if vac1 == vac2:
                    continue

                # On privilégie les échanges impliquant au moins une vacation sous-utilisée
                if vac1 not in vacations_cibles_ids and vac2 not in vacations_cibles_ids:
                    continue

                voisin = self.appliquer_mouvement(solution, p1_id, p2_id)
                if self.faisable(voisin):
                    mouvement = (p1_id, p2_id, vac1, vac2)
                    mouvements.append((voisin, mouvement))

        if len(mouvements) > nombre_voisins:
            mouvements = random.sample(mouvements, nombre_voisins)

        return mouvements

    def intensifier(self, historique_solutions: List[Tuple[float, Dict[int, int]]]):
        if not historique_solutions:
            return None
        classement = sorted(historique_solutions, key=lambda x: x[0])
        meilleures = classement[:self.nombre_solutions_historique]
        _, solution = random.choice(meilleures)
        return solution.copy()

    def recherche_taboue_unique(self, solution_initiale: Dict[int, int]):
        solution_courante = solution_initiale.copy()
        bornes = None
        score_courant = self.evaluation(solution_courante, bornes)
        meilleure_solution = solution_courante.copy()
        meilleur_score = score_courant

        liste_taboue = []
        historique_solutions = [(score_courant, solution_courante.copy())]
        iterations_sans_amelioration = 0
        historique_scores = []

        for iteration in range(self.nombre_iterations):
            nombre_voisins_diversification = int(self.taille_voisinage * self.taux_diversification)
            nombre_voisins_normaux = self.taille_voisinage - nombre_voisins_diversification

            voisins_normaux = self.generer_voisinage(solution_courante, nombre_voisins_normaux)
            voisins_diversifies = self.generer_voisins_diversifies(solution_courante, nombre_voisins_diversification)
            voisins = voisins_normaux + voisins_diversifies

            if not voisins:
                break

            meilleur_voisin = None
            meilleur_voisin_score = float("inf")
            meilleur_mouvement = None

            for voisin, mouvement in voisins:
                score = self.evaluation(voisin, bornes)
                est_tabou = mouvement in liste_taboue

                if est_tabou:
                    if score >= meilleur_score:
                        continue

                if score < meilleur_voisin_score:
                    meilleur_voisin = voisin
                    meilleur_voisin_score = score
                    meilleur_mouvement = mouvement

            if meilleur_voisin is None:
                break

            solution_courante = meilleur_voisin
            score_courant = meilleur_voisin_score

            # Pour un mouvement de type Swap, on peut stocker le mouvement ou ses paires inversées dans la liste taboue
            liste_taboue.append(meilleur_mouvement)
            if len(liste_taboue) > self.taille_tabou:
                liste_taboue.pop(0)

            amelioration = False
            if score_courant < meilleur_score:
                meilleure_solution = solution_courante.copy()
                meilleur_score = score_courant
                iterations_sans_amelioration = 0
                amelioration = True
            else:
                iterations_sans_amelioration += 1

            historique_solutions.append((score_courant, solution_courante.copy()))
            historique_solutions = sorted(historique_solutions, key=lambda x: x[0])[:self.nombre_solutions_historique]

            historique_scores.append({
                "iteration": iteration + 1,
                "score": score_courant,
                "meilleur_score": meilleur_score,
                "mouvement": meilleur_mouvement,
                "amelioration": amelioration,
                "taille_tabou": len(liste_taboue),
                "stagnation": iterations_sans_amelioration
            })

            if iterations_sans_amelioration >= self.seuil_intensification:
                solution_intensifiee = self.intensifier(historique_solutions)
                if solution_intensifiee is not None:
                    solution_courante = solution_intensifiee
                    score_courant = self.evaluation(solution_courante, bornes)
                    liste_taboue = []
                    iterations_sans_amelioration = 0

            if iterations_sans_amelioration >= self.stagnation_max:
                break

        return meilleure_solution, meilleur_score, historique_scores

    def optimiser(self):
        meilleure_solution_globale = None
        meilleur_score_global = float("inf")
        historique_global = []

        for numero_solution in range(self.nombre_solutions_initiales):
            solution_initiale = self.construire_solution_initiale(randomisation=True)
            meilleure_solution, meilleur_score, historique = self.recherche_taboue_unique(solution_initiale)

            historique_global.append({
                "solution_initiale": numero_solution + 1,
                "score_final": meilleur_score,
                "historique": historique
            })

            if meilleur_score < meilleur_score_global:
                meilleure_solution_globale = meilleure_solution.copy()
                meilleur_score_global = meilleur_score

        return meilleure_solution_globale, meilleur_score_global, historique_global
    
from datetime import date, time

# ============================================================
ot_patients = [
    # --- Orthopédie (Dr A et Dr B) ---
    Patient(id=1, age=65, sexe="M", type_intervention="Prothèse genou", ambulatoire=False, duree_operation=120.0, duree_sejour=4, diagnostic="Gonarthrose", chirurgien="Dr A"),
    Patient(id=2, age=70, sexe="F", type_intervention="Prothèse genou", ambulatoire=False, duree_operation=150.0, duree_sejour=5, diagnostic="Gonarthrose sévère", chirurgien="Dr A"),
    Patient(id=3, age=58, sexe="M", type_intervention="Prothèse genou", ambulatoire=False, duree_operation=120.0, duree_sejour=3, diagnostic="Gonarthrose", chirurgien="Dr A"),
    
    Patient(id=4, age=62, sexe="F", type_intervention="Prothèse hanche", ambulatoire=False, duree_operation=110.0, duree_sejour=4, diagnostic="Coxarthrose", chirurgien="Dr B"),
    Patient(id=5, age=75, sexe="M", type_intervention="Prothèse hanche", ambulatoire=False, duree_operation=130.0, duree_sejour=6, diagnostic="Coxarthrose sévère", chirurgien="Dr B"),

    # --- Chirurgie Viscérale / Digestive (Dr C et Dr D) ---
    Patient(id=6, age=25, sexe="M", type_intervention="Appendicectomie", ambulatoire=True, duree_operation=60.0, duree_sejour=0, diagnostic="Appendicite aiguë", chirurgien="Dr C"),
    Patient(id=7, age=30, sexe="F", type_intervention="Appendicectomie", ambulatoire=True, duree_operation=90.0, duree_sejour=0, diagnostic="Appendicite", chirurgien="Dr C"),
    Patient(id=8, age=45, sexe="M", type_intervention="Appendicectomie", ambulatoire=False, duree_operation=90.0, duree_sejour=2, diagnostic="Appendicite compliquée", chirurgien="Dr C"),
    
    Patient(id=9, age=50, sexe="F", type_intervention="Cholecystectomie", ambulatoire=True, duree_operation=75.0, duree_sejour=0, diagnostic="Lithiase biliaire", chirurgien="Dr D"),
    Patient(id=10, age=40, sexe="M", type_intervention="Cholecystectomie", ambulatoire=False, duree_operation=90.0, duree_sejour=2, diagnostic="Colique hépatique", chirurgien="Dr D"),
]

patients = ot_patients

vacations = [
    # Vacations pour Dr A (Prothèse genou) - Réparties sur 2 jours
    Vacation(id=1, salle="Salle 1", date=date(2026, 6, 1), heure_debut=time(8, 0), heure_fin=time(14, 0), chirurgien="Dr A", type_intervention="Prothèse genou", capacite=360.0),
    Vacation(id=2, salle="Salle 1", date=date(2026, 6, 3), heure_debut=time(8, 0), heure_fin=time(14, 0), chirurgien="Dr A", type_intervention="Prothèse genou", capacite=360.0),

    # Vacation pour Dr B (Prothèse hanche)
    Vacation(id=3, salle="Salle 2", date=date(2026, 6, 1), heure_debut=time(8, 0), heure_fin=time(14, 0), chirurgien="Dr B", type_intervention="Prothèse hanche", capacite=360.0),

    # Vacations pour Dr C (Appendicectomie)
    Vacation(id=4, salle="Salle 3", date=date(2026, 6, 1), heure_debut=time(8, 0), heure_fin=time(13, 0), chirurgien="Dr C", type_intervention="Appendicectomie", capacite=300.0),
    Vacation(id=5, salle="Salle 3", date=date(2026, 6, 2), heure_debut=time(8, 0), heure_fin=time(13, 0), chirurgien="Dr C", type_intervention="Appendicectomie", capacite=300.0),

    # Vacation pour Dr D (Cholecystectomie)
    Vacation(id=6, salle="Salle 4", date=date(2026, 6, 2), heure_debut=time(8, 0), heure_fin=time(13, 0), chirurgien="Dr D", type_intervention="Cholecystectomie", capacite=300.0),
]
        
recherche = RechercheTaboue(
    patients=ot_patients,
    vacations=vacations,

    nombre_lits=30,
    nombre_places_ambulatoires=10,

    nombre_iterations=1000,
    taille_tabou=10,
    taille_voisinage=50,
    nombre_solutions_initiales=5,

    stagnation_max=100,
    seuil_intensification=50,

    nombre_solutions_historique=20,
    taux_diversification=0.10,

    poids_bloc=0.50,
    poids_hebergement=0.50,

    seed=42
)
solution, score, historique = recherche.optimiser()

print("====================================")
print("MEILLEURE SOLUTION")
print("====================================")

print("Score :", score)

for patient_id, vacation_id in solution.items():

    print(
        f"Patient {patient_id} "
        f"-> Vacation {vacation_id}"
    )