#!/usr/bin/env python3
"""
run_balloon_solver.py
=====================
CLI / stream wrapper for `balloon_camp_solver.solve`.

Input  : one JSON object on **stdin** (see README).
Success: manifest JSON on **stdout** · exit-code 0
Failure: error JSON on **stderr** · exit-code 1 or 2
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
import random
from typing import List, Any, NoReturn

from vehicle_solver import solve
from transformer import transform_input_payload, transform_output
from vehicle_group_solver import build_clusters


def _emit_error(exc: Exception, exit_code: int) -> NoReturn:
    """Serialize *exc* as one-line JSON to **stderr** and quit."""
    err_payload = {
        "type": type(exc).__name__,
        "message": str(exc),
        "trace": traceback.format_exc(),
    }

    json.dump(err_payload, sys.stderr)
    sys.exit(exit_code)


def _load_stdin_payload() -> dict[str, Any]:
    """Parse a single JSON object from STDIN. Exit 2 on failure."""
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("STDIN payload must be a single JSON object")
        return payload
    except Exception as exc:  # noqa: BLE001
        _emit_error(exc, exit_code=2)  # never returns


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Solve balloon-camp crew assignment")

    # soft-rule weights -------------------------------------------------------
    parser.add_argument(
        "--flight-leg",
        type=int,
        default=None,
        help="Which flight leg to solve for. Accepted values are: [1, 2] ",
    )
    parser.add_argument(
        "--w-second-leg",
        type=int,
        default=20,
        help="Weight for balancing car passengers for the second leg",
    )
    parser.add_argument(
        "--w-pilot-fairness",
        type=int,
        default=1,
        help=(
            "Weight for balancing how many flights each pilot flies "
            "(higher → pilots fly a more equal number of times)."
        ),
    )
    parser.add_argument(
        "--w-passenger-fairness",
        type=int,
        default=20,
        help=(
            "Weight for balancing how many flights each passenger takes "
            "(higher → passengers fly a more equal number of times)."
        ),
    )
    parser.add_argument(
        "--w-nationality-diversity",
        type=int,
        default=3,
        help=(
            "Weight for distributing nationalities evenly across each vehicle "
            "(higher → vehicles are more nationally diverse)."
        ),
    )
    parser.add_argument(
        "--w-vehicle-rotation",
        type=int,
        default=5,
        help=(
            "Weight that penalizes assigning the same passenger to the same vehicle "
            "across multiple flights (higher → more rotation)."
        ),
    )
    parser.add_argument(
        "--w-no-solo-participant",
        type=int,
        default=30,
        help=(
            "Weight that penalizes assignments where a participant is the only human "
            "in a vehicle (higher → discourage solo assignments)."
        ),
    )
    parser.add_argument(
        "--w-cluster-passenger-balance",
        type=int,
        default=7,
        help=(
            "Weight for balancing the number of passengers across predefined "
            "vehicle clusters (higher → clusters receive similar passenger counts)."
        ),
    )
    parser.add_argument(
        "--w-second-leg-overweight",
        type=int,
        default=50,
        help=(
            "Weight that penalizes vehicles whose total passenger weight exceeds "
            "capacity on the second leg (higher → fewer overweight vehicles)."
        ),
    )
    parser.add_argument(
        "--counselor-flight-discount",
        type=int,
        default=1,
        help=(
            "Amount of flights added to a counselor's flight count in order to "
            "prefer participants over counselors."
        ),
    )
    parser.add_argument(
        "--default-person-weight",
        type=int,
        default=80,
        help="Fallback weight in kilograms for people whose weight is unknown.",
    )
    parser.add_argument(
        "--time-limit",
        type=int,
        default=20,
        help="Maximum solver runtime in seconds before timing out.",
    )

    args = parser.parse_args(argv)

    # ---------------------------------------------------------------------#
    # Gather input                                                          #
    # ---------------------------------------------------------------------#
    payload = _load_stdin_payload()
    balloons = payload.get("balloons", [])
    cars = payload.get("cars", [])
    people = payload.get("people", [])
    history = payload.get("history", [])
    groups = payload.get("groups", [])

    # Randomize input order
    random.shuffle(balloons)
    random.shuffle(cars)
    random.shuffle(people)

    try:
        balloons, cars, people, preclusers, frozen, history = transform_input_payload(
            balloons=balloons,
            cars=cars,
            people=people,
            groups=groups,
            history=history,
        )

        cluster = build_clusters(
            balloons=balloons, cars=cars, people=people, precluster=preclusers
        )

        manifest = solve(
            balloons=balloons,
            cars=cars,
            people=people,
            cluster=cluster,
            frozen=frozen,
            past_flights=history,
            leg=args.flight_leg,
            w_pilot_fairness=args.w_pilot_fairness,
            w_passenger_fairness=args.w_passenger_fairness,
            w_no_solo_participant=args.w_no_solo_participant,
            w_cluster_passenger_balance=args.w_cluster_passenger_balance,
            w_vehicle_rotation=args.w_vehicle_rotation,
            w_divers_nationalities=args.w_nationality_diversity,
            w_low_flights_second_leg=args.w_second_leg,
            w_overweight_second_leg=args.w_second_leg_overweight,
            counselor_flight_discount=args.counselor_flight_discount,
            default_person_weight=args.default_person_weight,
            time_limit_s=args.time_limit,
        )

        output = transform_output(manifest, cluster, groups)
        json.dump(output, sys.stdout)
        sys.stdout.write("\n")
        sys.exit(0)

    except Exception as exc:
        _emit_error(exc, exit_code=1)


if __name__ == "__main__":  # pragma: no cover
    main()
