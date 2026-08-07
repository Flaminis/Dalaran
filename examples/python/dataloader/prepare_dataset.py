"""Download a LeRobot dataset from HuggingFace Hub and prepare it for the dataloader.

This script:
1. Downloads a LeRobot dataset from HuggingFace Hub.
2. Loads it into Dalaran via the built-in LeRobot importer (`log_file_from_path`).
3. Splits the resulting archive into one DLR per episode.
4. Registers the per-episode RRDs to a catalog server instance.

"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from huggingface_hub import snapshot_download

import dalaran as dl

DEFAULT_REPO_ID = "dalaran/so101-pick-and-place"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "data"
APPLICATION_ID = "lerobot"

_EPISODE_RE = re.compile(r"^(episode_)(\d+)$")


def _zero_pad_episode_id(rec_id: str, width: int = 5) -> str:
    """Turn `episode_1` into `episode_00001` so segments sort lexicographically."""
    m = _EPISODE_RE.match(rec_id)
    if m:
        return f"{m.group(1)}{int(m.group(2)):0{width}d}"
    return rec_id


def download_dataset(repo_id: str, dest: Path) -> Path:
    """Download a LeRobot dataset from HuggingFace Hub into *dest* and return its path."""
    print(f"Downloading {repo_id} to {dest} …")
    local_dir = snapshot_download(repo_id=repo_id, repo_type="dataset", local_dir=dest)
    return Path(local_dir)


def lerobot_to_combined_dlr(dataset_dir: Path, combined_dlr: Path) -> None:
    """Use Dalaran's built-in LeRobot importer to turn the dataset into a single DLR."""
    print(f"Converting {dataset_dir} -> {combined_dlr}")
    with dl.RecordingStream(APPLICATION_ID) as rec:
        rec.save(str(combined_dlr))
        rec.log_file_from_path(str(dataset_dir))


def split_into_episode_rrds(combined_dlr: Path, dlr_dir: Path) -> list[Path]:
    """Split a combined DLR archive into one DLR per episode.

    Returns the paths of the written per-episode RRDs.
    """
    dlr_dir.mkdir(parents=True, exist_ok=True)

    reader = dl.experimental.RrdReader(str(combined_dlr))
    recordings = reader.recordings()
    print(f"Archive contains {len(recordings)} recordings")

    episode_paths: list[Path] = []
    for entry in recordings:
        store = reader.store(store=entry)
        # Skip metadata-only recordings (e.g. the "root" recording that only carries properties).
        if not store.schema().entity_paths():
            continue

        episode_id = _zero_pad_episode_id(entry.recording_id)
        dlr_path = dlr_dir / f"{episode_id}.dlr"

        with dl.RecordingStream(APPLICATION_ID, recording_id=episode_id, send_properties=False) as rec:
            rec.save(str(dlr_path))
            rec.send_chunks(store)
        episode_paths.append(dlr_path)
        print(f"  wrote {dlr_path} ({dlr_path.stat().st_size / (1024 * 1024):.1f} MB)")

    return episode_paths


def register_to_catalog(
    dlr_paths: list[Path],
    *,
    catalog_url: str,
    dataset_name: str,
) -> None:
    """Register per-episode RRDs to a catalog server instance.

    Uses absolute file:// URIs so the catalog can read the RRDs directly from the local filesystem.
    """
    print(f"\nRegistering {len(dlr_paths)} episodes to {catalog_url} as dataset '{dataset_name}' …")
    client = dl.catalog.CatalogClient(catalog_url)
    dataset = client.create_dataset(dataset_name, exist_ok=True)

    uris = [f"file://{p.resolve()}" for p in dlr_paths]
    on_duplicate = dl.catalog.OnDuplicateSegmentLayer(dl.catalog.OnDuplicateSegmentLayer.REPLACE)
    dataset.register(uris, on_duplicate=on_duplicate).wait()
    print("  registration done")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--repo-id",
        default=DEFAULT_REPO_ID,
        help=f"HuggingFace dataset repo id (default: {DEFAULT_REPO_ID}).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to store downloaded dataset and output RRDs (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--catalog-url",
        default="dalaran+http://127.0.0.1:51234",
        help="Dalaran catalog URL to register episodes with. Pass an empty string to skip registration.",
    )
    parser.add_argument(
        "--dataset-name",
        default=None,
        help="Name of the dataset to create/use in the catalog (default: derived from --repo-id).",
    )
    parser.add_argument(
        "--keep-combined",
        action="store_true",
        help="Keep the intermediate combined DLR after splitting (useful for debugging).",
    )
    args = parser.parse_args()

    output_dir = args.output_dir
    repo_slug = args.repo_id.replace("/", "_")
    dataset_dir = output_dir / "lerobot" / repo_slug
    dlr_dir = output_dir / "rrds" / repo_slug
    combined_dlr = output_dir / f"{repo_slug}_combined.dlr"

    download_dataset(args.repo_id, dataset_dir)
    lerobot_to_combined_dlr(dataset_dir, combined_dlr)
    episode_paths = split_into_episode_rrds(combined_dlr, dlr_dir)

    if not args.keep_combined:
        combined_dlr.unlink()

    print(f"\nWrote {len(episode_paths)} per-episode RRDs to {dlr_dir}")

    if args.catalog_url:
        dataset_name = args.dataset_name or repo_slug
        register_to_catalog(episode_paths, catalog_url=args.catalog_url, dataset_name=dataset_name)


if __name__ == "__main__":
    main()
