from __future__ import annotations

import argparse

import dalaran as dl
import dalaran.blueprint as dlb


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple benchmark for many transforms over time & space.")
    dl.script_add_args(parser)

    parser.add_argument("--branching-factor", type=int, default=2, help="How many children each node has")
    parser.add_argument("--hierarchy-depth", type=int, default=10, help="How many levels of hierarchy we want")
    parser.add_argument(
        "--transforms-every-n-levels", type=int, default=2, help="At which level in the hierarchies we add transforms"
    )
    parser.add_argument(
        "--num-timestamps",
        type=int,
        default=100,
        help="Number of timestamps to log. Stamps shift for each entity a bit.",
    )
    parser.add_argument("--transforms-only", action="store_true", help="If set, don't log a point at each leaf")
    parser.add_argument(
        "--num-views", type=int, default=6, help="Number of 3D views to create (each will use a different origin)"
    )

    args = parser.parse_args()

    dl.script_setup(args, "dalaran_example_benchmark_many_transforms")
    dl.set_time("sim_time", duration=0)

    entity_paths = []
    call_id = 0

    def log_hierarchy(entity_path: str, level: int) -> None:
        nonlocal call_id
        call_id += 1
        entity_paths.append(entity_path)

        # Add a transform at every 'transforms_every_n_levels' level except root
        if level > 0 and level % args.transforms_every_n_levels == 0:
            # Add a static transform that has to be combined in to stress the per-timestamp transform resolve.
            dl.log(
                entity_path,
                # Have to be careful to not override all other transforms, therefore, use `from_fields`.
                dl.Transform3D.from_fields(
                    mat3x3=[
                        [1.0 + level * 0.1, 0.0, 0.0],
                        [0.0, 1.0 + level * 0.1, 0.0],
                        [0.0, 0.0, 1.0 + level * 0.1],
                    ]
                ),
                static=True,
            )

            # Add a transform that changes for each timestamp.
            for i in range(args.num_timestamps):
                call_id_factor = call_id * 0.02
                dl.set_time("sim_time", duration=i + call_id_factor)
                dl.log(
                    entity_path,
                    dl.Transform3D(
                        translation=[i * 0.1 * level + call_id_factor, call_id_factor * level, 0.0],
                        rotation_axis_angle=dl.RotationAxisAngle(axis=(0.0, 1.0, 0.0), degrees=i * 0.1),
                    ),
                )

        if level == args.hierarchy_depth:
            if not args.transforms_only:
                # Log a single point at the leaf
                dl.set_time("sim_time", duration=0)
                dl.log(entity_path, dl.Points3D([[0.0, 0.0, 0.0]]))
            return

        for i in range(args.branching_factor):
            child_path = f"{entity_path}/{i}_at_{level}"
            log_hierarchy(child_path, level + 1)

    log_hierarchy("root", 0)

    # All views display all entities.
    dl.send_blueprint(
        dlb.Blueprint(
            dlb.Grid(
                contents=[dlb.Spatial3DView(origin=path, contents="/**") for path in entity_paths[: args.num_views]]
            ),
            collapse_panels=True,  # Collapse panels, so perf is mostly about the data & the views.
        )
    )


if __name__ == "__main__":
    main()
