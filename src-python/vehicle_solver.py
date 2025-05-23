"""Balloon‑camp crew optimiser
================================
A single‐slot (one flight) solver with:
• **Hard rules**
  – exactly one qualified operator per occupied vehicle
  – every passenger (incl. operator) occupies a seat
  – seat‑capacity and optional max‑weight per vehicle
  – each person appears in ≤ 1 vehicle and operates ≤ 1 vehicle
  – optional *frozen* assignments (operator / passenger / absent)
• **Soft rules** (linear objective)
  – give airtime to low‑flight pilots (w_fair)
  – prefer low‑flight passengers in balloons (w_low_flights)
  – reward mixed nationalities in each vehicle (w_diversity)
  – discourage putting someone in the same vehicle again (w_new_vehicle)

All weights are user‑tunable kwargs.

Dependencies: `ortools>=9.9`.  Run the smoke‑test at bottom to verify.
"""

from itertools import product, combinations
from collections import defaultdict
from typing import List, Dict, Any, Optional

from ortools.sat.python import cp_model


# ---------------------------------------------------------------------------
# Main one-leg solver (sequential-leg workflow)
# ---------------------------------------------------------------------------
def solve(
    balloons: List[Dict[str, Any]],
    cars: List[Dict[str, Any]],
    people: List[Dict[str, Any]],
    cluster: Optional[Dict[str, List[str]]] = None,
    *,
    frozen: Optional[List[Dict[str, str]]] = None,
    past_flights: Optional[List[Dict[str, Any]]] = None,
    leg: int = None,
    # soft weights
    # Defaults are overwritten by command-line args
    w_fair: int = 1,
    w_low_flights: int = 20,
    w_diversity: int = 3,
    w_new_vehicle: int = 5,
    w_second_leg: int = 20,
    # misc
    default_person_weight: int = 70,
    time_limit_s: int = 30,
):
    """Solve a *single* leg; call once per flight."""
    frozen = frozen or []

    if leg is not None and leg > 1:
        if len(past_flights) == 0:
            raise ValueError("Flight history must be provided for multi-leg flights")
        if cluster is None:
            raise ValueError("Cluster must be provided for multi-leg flights")

    # ------------------------------------------------------------------
    # 0. Fast look-ups
    # ------------------------------------------------------------------
    vehicles = [dict(**b, kind="balloon") for b in balloons] + [
        dict(**c, kind="car") for c in cars
    ]

    people_by_id = {p["id"]: p for p in people}
    vehicles_by_id = {v["id"]: v for v in vehicles}

    person_ids = list(people_by_id)
    vehicle_ids = list(vehicles_by_id)

    weight = {
        p: people_by_id[p].get("weight", default_person_weight) for p in person_ids
    }
    flights_so_far = {p: people_by_id[p]["flights"] for p in person_ids}
    nationality = {p: people_by_id[p]["nationality"] for p in person_ids}
    is_counselor = {
        p: people_by_id[p].get("role", "participant") == "counselor" for p in person_ids
    }

    capacity = {v: vehicles_by_id[v]["capacity"] for v in vehicle_ids}
    kind = {v: vehicles_by_id[v]["kind"] for v in vehicle_ids}
    allowed_op = {v: set(vehicles_by_id[v]["allowed_operators"]) for v in vehicle_ids}
    max_weight = {v: vehicles_by_id[v].get("max_weight", -1) for v in vehicle_ids}

    # ------------------------------------------------------------------
    # 0.b  Historic “fresh vehicle” map
    # ------------------------------------------------------------------
    seen = defaultdict(set)
    if past_flights:
        for fl in past_flights:
            for grp in fl["groups"]:
                bid = grp["balloon"]["id"]
                seen[grp["balloon"]["operator"]].add(bid)
                for p in grp["balloon"]["passengers"]:
                    seen[p].add(bid)
                for car in grp["cars"]:
                    cid = car["id"]
                    seen[car["operator"]].add(cid)
                    for p in car["passengers"]:
                        seen[p].add(cid)

    # ------------------------------------------------------------------
    # 1. CP-SAT model
    # ------------------------------------------------------------------
    model = cp_model.CpModel()

    op = {  # operator‑selection vars
        (p, v): model.NewBoolVar(f"op_{p}_{v}")
        for p, v in product(person_ids, vehicle_ids)
    }
    pax = {  # passenger‑seat vars (operator counts as passenger)
        (p, v): model.NewBoolVar(f"pax_{p}_{v}")
        for p, v in product(person_ids, vehicle_ids)
    }

    # ------------------------------------------------------------------
    # 2. Hard constraints
    # ------------------------------------------------------------------
    # 2.1 each person exactly one seat / one operator role
    for p in person_ids:
        model.Add(sum(pax[p, v] for v in vehicle_ids) == 1)  # seat exactly once
        model.Add(sum(op[p, v] for v in vehicle_ids) <= 1)  # ≤1 operator role

    # 2.2 operator ⇒ passenger + operator eligibility
    for p, v in product(person_ids, vehicle_ids):
        model.AddImplication(op[p, v], pax[p, v])
        if p not in allowed_op[v]:
            model.Add(op[p, v] == 0)

    # 2.3 capacity limit
    for v in vehicle_ids:
        model.Add(sum(pax[p, v] for p in person_ids) <= capacity[v])

    # 2.4 weight limit
    for v in vehicle_ids:
        if max_weight[v] > 0:
            model.Add(sum(weight[p] * pax[p, v] for p in person_ids) <= max_weight[v])

    # 2.5 occupancy flag & exactly‑one operator if occupied
    for v in vehicle_ids:
        occ = model.NewBoolVar(f"occ_{v}")
        seats = sum(pax[p, v] for p in person_ids)
        model.Add(seats >= 1).OnlyEnforceIf(occ)
        model.Add(seats == 0).OnlyEnforceIf(occ.Not())
        model.Add(sum(op[p, v] for p in person_ids) == 1).OnlyEnforceIf(occ)
        model.Add(sum(op[p, v] for p in person_ids) == 0).OnlyEnforceIf(occ.Not())

    # 2.6 frozen seats
    for lock in frozen:
        p, v = lock["person"], lock["vehicle"]
        if lock["role"] == "operator":
            model.Add(op[p, v] == 1)
            model.Add(pax[p, v] == 1)
        elif lock["role"] == "passenger":
            model.Add(pax[p, v] == 1)
            model.Add(op[p, v] == 0)
        else:
            raise ValueError("unknown role")

    # 2.7 stay-in-cluster after leg-0
    if leg is not None and leg > 1:
        # take cluster from *previous* leg (last entry)
        prev = past_flights[-1]
        allowed = defaultdict(set)

        for grp in prev["groups"]:
            cluster_vids = {grp["balloon"]["id"]} | {car["id"] for car in grp["cars"]}
            # operator + passengers
            ids = (
                {grp["balloon"]["operator"]}
                | set(grp["balloon"]["passengers"])
                | {car["operator"] for car in grp["cars"]}
                | {p for car in grp["cars"] for p in car["passengers"]}
            )
            for pid in ids:
                allowed[pid].update(cluster_vids)

        for p in person_ids:
            for v in vehicle_ids:
                if not allowed.get(p):
                    raise ValueError(
                        f"Person {people_by_id[p]["name"]} not allowed in any vehicle"
                    )
                if v not in allowed.get(p, set()):
                    model.Add(pax[p, v] == 0)

    # ------------------------------------------------------------------
    # 3. Objective
    # ------------------------------------------------------------------
    objective_terms = []
    max_flights = max(flights_so_far.values()) + 1

    # 3.1 pilot fairness
    for p, v in product(person_ids, vehicle_ids):
        if p in allowed_op[v]:
            bonus = max_flights - flights_so_far[p]
            objective_terms.append(-w_fair * bonus * op[p, v])

    # 3.2 low-flight pax in balloons  (participants > counselors)
    for p, v in product(person_ids, vehicle_ids):
        if kind[v] == "balloon":
            bonus = max_flights - flights_so_far[p]
            if is_counselor[p]:
                bonus *= 0.5  # halve importance
            objective_terms.append(-w_low_flights * bonus * pax[p, v])

    # 3.3 diversity
    for v in vehicle_ids:
        for p1, p2 in combinations(person_ids, 2):
            if nationality[p1] == nationality[p2]:
                continue
            pair = model.NewBoolVar(f"mix_{p1}_{p2}_{v}")
            model.AddMinEquality(pair, [pax[p1, v], pax[p2, v]])
            objective_terms.append(-w_diversity * pair)

    # 3.4 fresh vehicle (passengers only)
    for p, v in product(person_ids, vehicle_ids):
        if v not in seen[p]:
            objective_terms.append(-w_new_vehicle * (pax[p, v] - op[p, v]))

    # 3.5 soft cluster balance
    if leg is not None and leg == 1:
        future_seats = sum(b["capacity"] for b in balloons)
        sorted_f = sorted(flights_so_far.values())
        cutoff = (
            sorted_f[-1]
            if future_seats >= len(sorted_f)
            else sorted_f[future_seats - 1]
        )
        low = {p: int(flights_so_far[p] <= cutoff) for p in person_ids}

        for b in balloons:
            bid = b["id"]
            target = b["capacity"]

            car_ids = cluster[bid]

            # how many low-flight pax we actually placed in those cars
            low_in_cars = sum(low[p] * pax[p, v] for v in car_ids for p in person_ids)

            short = model.NewIntVar(0, target, f"short_{bid}")
            model.Add(short >= target - low_in_cars)

            objective_terms.append(+w_second_leg * short)

    model.Minimize(sum(objective_terms))

    # ------------------------------------------------------------------
    # 4. Solve
    # ------------------------------------------------------------------
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = 8

    if solver.Solve(model) not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("No feasible assignment")

    # ------------------------------------------------------------------
    # 5. Manifest
    # ------------------------------------------------------------------
    manifest = {v: {"operator": None, "passengers": []} for v in vehicle_ids}
    for p, v in product(person_ids, vehicle_ids):
        if solver.BooleanValue(op[p, v]):
            manifest[v]["operator"] = p
            continue
        if solver.BooleanValue(pax[p, v]):
            manifest[v]["passengers"].append(p)

    return manifest
