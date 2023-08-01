#!/usr/bin/env python3
# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2.

import os

from eden.integration.lib import hgrepo

from .lib.hg_extension_test_base import EdenHgTestCase, hg_test


@hg_test
# pyre-ignore[13]: T62487924
class SymlinkTest(EdenHgTestCase):
    simple_commit: str
    symlink_commit: str
    quasi_symlink_commit: str

    def setup_eden_test(self) -> None:
        self.enable_windows_symlinks = True
        super().setup_eden_test()

    def populate_backing_repo(self, repo: hgrepo.HgRepository) -> None:
        repo.write_file("adir/hello.txt", "hola")
        self.simple_commit = repo.commit("Initial commit.")

        repo.symlink("symlink", os.path.join("adir", "hello.txt"))
        self.symlink_commit = repo.commit("Add symlink pointing to adir/hello.txt")
        repo.update(self.simple_commit)

        repo.write_file("symlink", os.path.join("adir", "hello.txt"))
        self.quasi_symlink_commit = repo.commit(
            "Add symlink lookalike 'pointing' to adir/hello.txt"
        )
        repo.update(self.simple_commit)

    def test_update_to_symlink(self) -> None:
        self.repo.update(self.quasi_symlink_commit)
        self.assertEqual(os.path.join("adir", "hello.txt"), self.read_file("symlink"))
        self.repo.update(self.symlink_commit)
        self.assertEqual("hola", self.read_file("symlink"))

    def test_update_from_symlink(self) -> None:
        self.repo.update(self.symlink_commit)
        self.assertEqual("hola", self.read_file("symlink"))
        self.repo.update(self.quasi_symlink_commit)
        self.assertEqual(os.path.join("adir", "hello.txt"), self.read_file("symlink"))

    def test_show_symlink_commit(self) -> None:
        self.repo.update(self.symlink_commit)
        self.assertEqual(
            self.repo.hg("log", "-r", ".", "--template", "{node}", "--patch"),
            f"""3f0b136eff77afd59a710c48d6e5f178793d08cediff --git a/symlink b/symlink
new file mode 120000
--- /dev/null
+++ b/symlink
@@ -0,0 +1,1 @@
+{os.path.join('adir', 'hello.txt')}
\\ No newline at end of file

""",
        )

    def test_hg_mv_symlink_file(self) -> None:
        self.repo.update(self.symlink_commit)
        self.repo.hg("mv", "symlink", "symbolic_link")
        self.repo.commit("Moving symlink")
        self.assertEqual(self.read_file("symbolic_link"), "hola")
        self.assert_status_empty()
        self.assertEqual(
            self.repo.hg("log", "-r", ".", "--template", "{node}\\n", "--patch"),
            """b80dd1449ad6a2d0ae67936c905fa1e79d9ba65a
diff --git a/symlink b/symbolic_link
rename from symlink
rename to symbolic_link

""",
        )

    def test_modified_symlink_target(self) -> None:
        self.repo.update(self.symlink_commit)
        self.assert_status_empty()
        self.repo.write_file("adir/true_hola.txt", "hola")
        os.remove(self.get_path("symlink"))
        self.repo.symlink("symlink", os.path.join("adir", "true_hola.txt"))
        self.assert_status({"adir/true_hola.txt": "?", "symlink": "M"})
        self.assertEqual(
            self.repo.hg("diff"),
            f"""diff --git a/symlink b/symlink
--- a/symlink
+++ b/symlink
@@ -1,1 +1,1 @@
-{os.path.join('adir', 'hello.txt')}
\\ No newline at end of file
+{os.path.join('adir', 'true_hola.txt')}
\\ No newline at end of file
""",
        )

    def test_symlink_diff(self) -> None:
        self.repo.update(self.symlink_commit)
        os.remove(self.get_path("symlink"))
        self.write_file("symlink", os.path.join("adir", "hello.txt"))
        self.assertEqual(
            self.repo.hg("diff"),
            """diff --git a/symlink b/symlink
old mode 120000
new mode 100644
""",
        )
        self.repo.update(self.quasi_symlink_commit, clean=True)
        os.remove(self.get_path("symlink"))
        self.repo.symlink("symlink", os.path.join("adir", "hello.txt"))
        self.assertEqual(
            self.repo.hg("diff"),
            """diff --git a/symlink b/symlink
old mode 100644
new mode 120000
""",
        )

    def test_directory_listing(self) -> None:
        self.repo.update(self.symlink_commit)
        files = os.scandir(self.mount)
        checkedSymlink = False
        for file in files:
            if file.name == "symlink":
                checkedSymlink = file.is_symlink()
        self.assertTrue(checkedSymlink)

    def test_revert(self) -> None:
        self.repo.update(self.symlink_commit)
        os.remove(self.get_path("symlink"))
        self.assert_status({"symlink": "!"})
        self.repo.hg("revert", "--all")
        self.assert_status_empty()
        self.assertEqual("hola", self.read_file("symlink"))

    def test_manually_restoring_symlink(self) -> None:
        self.repo.update(self.symlink_commit)
        os.remove(self.get_path("symlink"))
        self.assert_status({"symlink": "!"})
        self.repo.symlink("symlink", os.path.join("adir", "hello.txt"))
        self.assert_status_empty()
        self.assertEqual("hola", self.read_file("symlink"))

    def test_hg_update_works_with_symlink_feature(self) -> None:
        # Tests that what didn't work on test_failing_update works with symlinks enabled
        self.repo.update(self.symlink_commit)
        self.repo.symlink("symlink3", os.path.join("adir", "hello.txt"))
        self.repo.commit("Another commit with a symlink")
        self.repo.update(self.simple_commit)
        self.assert_status_empty()

    def test_file_symlink_chain(self) -> None:
        self.repo.symlink("f1", os.path.join("adir", "hello.txt"))
        self.repo.symlink("f2", "f1")
        self.repo.symlink("f3", "f2")
        file_symlink_chain_commit = self.repo.commit(
            "Chain of symlinks pointing to a file in a dir"
        )
        self.assert_status({})
        self.repo.update(self.simple_commit, clean=True)
        self.repo.update(file_symlink_chain_commit)
        self.assertTrue(os.path.isfile(self.get_path("f3")))
        self.assertEqual("hola", self.read_file("f3"))

    def test_dir_symlink_chain(self) -> None:
        self.repo.symlink("d1", "adir", target_is_directory=True)
        self.repo.symlink("d2", "d1", target_is_directory=True)
        self.repo.symlink("d3", "d2", target_is_directory=True)
        self.assertTrue(os.path.isdir(self.get_path("d3")))
        dir_symlink_chain_commit = self.repo.commit(
            "Chain of symlinks pointing to a directory"
        )
        self.assert_status({})
        self.repo.update(self.simple_commit, clean=True)
        self.repo.update(dir_symlink_chain_commit)
        self.assertTrue(os.path.isdir(self.get_path("d3")))
        self.assertEqual("hola", self.read_file(os.path.join("d3", "hello.txt")))

    def test_symlink_cycle(self) -> None:
        self.repo.symlink("s0", "s2")
        self.repo.symlink("s1", "s0")
        self.repo.symlink("s2", "s1")
        cycle_symlink_commit = self.repo.commit(
            "Cycle of symlinks; type should be unresolvable"
        )
        self.assert_status({})
        self.repo.update(self.simple_commit, clean=True)
        self.repo.update(cycle_symlink_commit)
        for i in range(3):
            curpath = self.get_path(f"s{i}")
            self.assertFalse(os.path.isfile(curpath))
            self.assertFalse(os.path.isdir(curpath))
            self.assertEqual(f"s{(i+2)%3}", os.readlink(curpath))

    def test_status_on_dir_symlink(self) -> None:
        self.repo.symlink("dirlink", "adir", target_is_directory=True)
        self.repo.commit("Really simple commit w/ repo")
        self.repo.write_file("adir/hello.txt", "saluton")
        self.assert_status({"adir/hello.txt": "M"})


@hg_test
# pyre-ignore[13]: T62487924
class SymlinkWindowsDisabledTest(EdenHgTestCase):
    initial_commit: str

    def setup_eden_test(self) -> None:
        # This should allow us to make the backing repo symlink-enabled. The working copy one will be disabled later.
        self.enable_windows_symlinks = True
        super().setup_eden_test()

    def populate_backing_repo(self, repo: hgrepo.HgRepository) -> None:
        repo.write_file("contents1", "c1\n")
        repo.write_file("contents2", "c2\n")
        repo.symlink("symlink", "contents1")
        self.initial_commit = repo.commit("Initial commit.")
        # We only want the backing repo to be symlink-enabled
        self.enable_windows_symlinks = False

    def test_changed_symlink_shows_up_in_status(self) -> None:
        self.repo.symlink("symlink", "contents2")
        self.assertEqual("c2\n", self.read_file("symlink"))

        self.assert_status({"symlink": "M"})

    def test_symlink_replacement(self) -> None:
        # We need another commit since integration tests clone the entire repo
        # as present in the backing repo, so symlink is actually a symlink
        self.repo.symlink("symlink2", "contents2")
        self.assertEqual("c2\n", self.read_file("symlink2"))
        symlink_commit = self.repo.commit("Another commit with a symlink")

        self.repo.update(self.initial_commit, clean=True)
        self.repo.update(symlink_commit, clean=True)
        # After coming back to the newly created commit, symlink2 should be a regular file
        self.assertEqual("contents2", self.read_file("symlink2"))
        os.remove(self.get_path("symlink2"))
        symlink_commit = self.repo.symlink("symlink2", "contents2")
        # This used to fail when we weren't properly calculating the SHA1 of symlinks on Windows
        self.assert_status_empty()

    def test_status_empty_after_fresh_clone(self) -> None:
        self.assert_status_empty()
        self.assertEqual("contents1", self.read_file("symlink"))
        self.assertFalse(os.path.islink(self.get_path("symlink")))
        self.assert_status_empty()

    def test_disabled_symlinks_update(self) -> None:
        self.repo.symlink("symlink2", "contents2")
        self.repo.commit("Another commit with a symlink")
        # There shouldn't be issues when updating now that the SHA1 is being properly calculated and everything symlink related is gated
        self.repo.update(self.initial_commit)
        self.assert_status_empty()
        self.assertEqual("contents1", self.read_file("symlink"))

    def test_modified_fake_symlink_target(self) -> None:
        self.assert_status_empty()
        os.remove(self.get_path("symlink"))
        self.repo.symlink("symlink", "contents2")
        self.assert_status({"symlink": "M"})
        self.assertEqual(
            self.repo.hg("diff", "--git"),
            """diff --git a/symlink b/symlink
--- a/symlink
+++ b/symlink
@@ -1,1 +1,1 @@
-contents1
\\ No newline at end of file
+contents2
\\ No newline at end of file
""",
        )
