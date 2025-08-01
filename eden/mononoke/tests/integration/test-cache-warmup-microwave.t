# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This software may be used and distributed according to the terms of the
# GNU General Public License found in the LICENSE file in the root
# directory of this source tree.

  $ . "${TEST_FIXTURES}/library.sh"

Setup repository

  $ export CACHE_WARMUP_BOOKMARK="master_bookmark"
  $ export CACHE_WARMUP_MICROWAVE=1
  $ BLOB_TYPE="blob_files" default_setup_drawdag
  A=aa53d24251ff3f54b1b2c29ae02826701b2abeb0079f1bb13b8434b54cd87675
  B=f8c75e41a0c4d29281df765f39de47bca1dcadfdc55ada4ccc2f6df567201658
  C=e32a1e342cdb1e38e88466b4c1a01ae9f410024017aa21dc0a1c5da6b3963bf2

Check that Mononoke booted despite the lack of microwave snapshot

  $ wait_for_mononoke_cache_warmup
  $ grep microwave "$TESTTMP/mononoke.out"
  [WARN] [cache warmup{repo=repo}] microwave: cache warmup failed: "Snapshot is missing"

Kill Mononoke

  $ killandwait "$MONONOKE_PID"
  $ truncate -s 0 "$TESTTMP/mononoke.out"

Delete filenodes

  $ sqlite3 "$TESTTMP/monsql/sqlite_dbs" "DELETE FROM filenodes;";

Regenerate microwave snapshot. This will fail because we have no derived data:

  $ microwave_builder --log-level ERROR blobstore
  * Execution error: Bookmark master_bookmark has no derived data (glob)
  Error: Execution failed
  [1]

Derive data, then regenerate microwave snapshot:

  $ quiet mononoke_admin derived-data -R repo derive --all-types --all-bookmarks
  $ quiet microwave_builder --debug blobstore

Start Mononoke again, check that the microwave snapshot was used

  $ SCUBA="$TESTTMP/scuba.json"
  $ start_and_wait_for_mononoke_server --scuba-log-file "$SCUBA"
  $ wait_for_mononoke_cache_warmup
  $ grep primed "$TESTTMP/mononoke.out"
  [INFO] [cache warmup{repo=repo}] primed filenodes cache with 1 entries
  [WARN] [cache warmup{repo=repo}] microwave: successfully primed cache

Finally, check that we can also generate a snapshot to files

  $ mkdir "$TESTTMP/microwave"
  $ quiet microwave_builder local-path "$TESTTMP/microwave"
  $ ls "$TESTTMP/microwave"
  repo0000.microwave_snapshot_v1

Test that the server warmup metrics are logged
  $ cat "$SCUBA" | summarize_scuba_json "Cache warmup complete" \
  >     .normal.log_tag \
  >     .int.completion_time_us \
  >     .int.poll_count .int.poll_time_us \
  >     .int.max_poll_time_us
  {
    "completion_time_us": *, (glob)
    "log_tag": "Cache warmup complete",
    "max_poll_time_us": *, (glob)
    "poll_count": *, (glob)
    "poll_time_us": * (glob)
  }
