#require no-eden

  $ enable amend morestatus rebase
  $ setconfig rebase.experimental.inmemory=true
  $ setconfig drawdag.defaultfiles=false

Make sure we minimize content fetches:
  $ newserver server
  $ drawdag <<EOS
  >      # C/four = four
  >      # B/two = 2
  > C B  # B/three = three
  > |/   # B/one = (removed)
  > A    # A/one = one
  >      # A/two = two
  > EOS

  $ newclientrepo client test:server
  $ LOG=file_fetches=trace,tree_fetches=trace hg rebase -q -r $B -d $C
  TRACE tree_fetches: attrs=["content"] keys=["@0d27acda", "@b941fe6c", "@e6f8ae7d"]
  TRACE file_fetches: attrs=["header"] keys=["three"]
  TRACE file_fetches: attrs=["header"] keys=["three"]
  TRACE file_fetches: attrs=["history"] length=Some(1) keys=["three", "two"]

Make sure we batch tree fetches well:
  $ newserver server2
  $ drawdag <<EOS
  > E C  # C/a/b/c2/file = C
  > | |  # D/a/b/c2/unrelated = D
  > D B  # E/a/b/c3/file = D
  > |/   # B/a/b/c1/file = B
  > A    # A/a/b/c2/file = A
  >      # A/a/b/c1/file = A
  > EOS

  $ newclientrepo client2 test:server2
  $ hg pull -qr $C
FIXME: we don't need to prefetch anything for D:
  $ LOG=file_fetches=trace,tree_fetches=trace hg rebase -q -s $B -d $E
  TRACE tree_fetches: attrs=["content"] keys=["@0578004a", "@1d3af747", "@1e081eaa", "@3b9f2e11", "@e2120c7c"]
  TRACE tree_fetches: attrs=["content"] keys=["a@05099e49", "a@1da49c91", "a@82fb1620", "a@bc26d404", "a@ce774d7e"]
  TRACE tree_fetches: attrs=["content"] keys=["a/b@693cd354", "a/b@7f83a148", "a/b@99574908", "a/b@d48eda77", "a/b@ee58f75d"]
  TRACE tree_fetches: attrs=["content"] keys=["a/b/c1@0c8dfc95", "a/b/c1@82bbf75d", "a/b/c2@0c8dfc95", "a/b/c2@1570ca89", "a/b/c2@e98395d2", "a/b/c3@cefe4a92"]
  TRACE file_fetches: attrs=["history"] length=Some(1) keys=["a/b/c1/file"]
  TRACE tree_fetches: attrs=["content"] keys=["@a2e501c5"]
  TRACE tree_fetches: attrs=["content"] keys=["a@b6b00943"]
  TRACE tree_fetches: attrs=["content"] keys=["a/b@98da63d7"]
  TRACE file_fetches: attrs=["history"] length=Some(1) keys=["a/b/c2/file"]

Make sure we batch fetch content for files needing merge:
  $ newserver server3
  $ drawdag <<EOS
  >      # C/bar = 2\n2\n3\n
  >      # C/foo = b\nb\nc\n
  > C B  # B/bar = 1\n2\n4\n
  > |/   # B/foo = a\nb\nd\n
  > A    # A/bar = 1\n2\n3\n
  >      # A/foo = a\nb\nc\n
  > EOS

  $ newclientrepo client3 test:server3
  $ LOG=file_fetches=trace,tree_fetches=trace hg rebase -q -r $B -d $C
  TRACE tree_fetches: attrs=["content"] keys=["@52df54bd", "@9e73d36f", "@c0749e87"]
  TRACE file_fetches: attrs=["content", "header", "aux"] keys=["bar", "bar", "foo", "foo"]
  TRACE file_fetches: attrs=["content", "header"] keys=["bar"]
  TRACE file_fetches: attrs=["content", "header"] keys=["bar"]
  TRACE file_fetches: attrs=["history"] length=Some(1) keys=["bar"]
  TRACE file_fetches: attrs=["content", "header"] keys=["foo"]
  TRACE file_fetches: attrs=["content", "header"] keys=["foo"]
  TRACE file_fetches: attrs=["history"] length=Some(1) keys=["foo"]
  TRACE file_fetches: attrs=["content", "header"] keys=["bar"]
  TRACE file_fetches: attrs=["history"] length=Some(1) keys=["bar"]
  TRACE file_fetches: attrs=["content", "header"] keys=["foo"]
  TRACE file_fetches: attrs=["history"] length=Some(1) keys=["foo"]
  TRACE file_fetches: attrs=["history"] length=Some(1) keys=["bar"]
  TRACE file_fetches: attrs=["history"] length=Some(1) keys=["foo"]
