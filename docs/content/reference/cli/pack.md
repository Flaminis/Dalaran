---
title: dalaran-pack and dalaran-unpack
order: 3
---

A `.dlrpack` bundle is how you hand a reproducible recording to someone else. It is a plain zip
containing a `manifest.json`, the `.dlr` recordings, any `.dbl` blueprints, and arbitrary
attachments such as calibration files or notes.

```sh
dalaran-pack drive.dlrpack drive_01.dlr drive_02.dlr \
    --blueprint overview.dbl \
    --attach calibration.yaml \
    --tag lidar --tag outdoor \
    --description "Two laps around the parking lot"
```

```txt
my_session.dlrpack
├── manifest.json
├── recordings/drive_01.dlr
├── blueprints/overview.dbl
└── attachments/calibration.yaml
```

## Inspect, verify, extract

```sh
dalaran-unpack drive.dlrpack --inspect     # print the manifest, extract nothing
dalaran-unpack drive.dlrpack --verify      # validate every checksum, exit 1 on mismatch
dalaran-unpack drive.dlrpack -d ./unpacked # extract (verifying first)
```

Extraction verifies checksums before writing anything, refuses to overwrite existing files unless
`--force` is given, and rejects any archive member that would escape the destination directory.
Pass `--no-verify` to extract a bundle you already know is damaged.

## The manifest

```json
{
  "schema_version": 1,
  "kind": "dalaran.bundle",
  "created_at": "2025-01-31T12:00:00Z",
  "dalaran_version": "0.36.0",
  "description": "Two laps around the parking lot",
  "tags": ["lidar", "outdoor"],
  "files": [
    {
      "path": "recordings/drive_01.dlr",
      "role": "recording",
      "source_name": "drive_01.dlr",
      "size_bytes": 1048576,
      "sha256": "…",
      "recording": {
        "fourcc": "RRF2",
        "encoded_version": "0.36.0",
        "entity_paths": ["/world/points"],
        "timelines": ["log_time"],
        "time_ranges": { "log_time": null },
        "complete": true
      }
    }
  ]
}
```

Recordings are summarized while packing: the stream header is parsed for the magic bytes and the
encoding version, and entity paths and timeline names are recovered from the Arrow schema metadata
where it is readable. `complete` tells you whether that scan found anything.

## Integrity

Every member is hashed with SHA-256 at pack time. `--verify` re-hashes each one and reports, per
file, a size mismatch, a checksum mismatch, a member declared in the manifest but missing from the
archive, or a member smuggled into the archive without being declared. Any of those makes the
command exit with `1`.

## From Python

```python
from dalaran.tools.bundle import create_bundle, extract_bundle, verify_bundle

create_bundle("drive.dlrpack", ["drive_01.dlr"], tags=["lidar"])
assert verify_bundle("drive.dlrpack") == []
extract_bundle("drive.dlrpack", "./unpacked")
```
