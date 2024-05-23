/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

import type {CommitInfo} from '../../types';

import {Tooltip} from '../../Tooltip';
import {tracker} from '../../analytics';
import {Button} from '../../components/Button';
import {T, t} from '../../i18n';
import {SplitCommitIcon} from '../../icons/SplitCommitIcon';
import {uncommittedChangesWithPreviews} from '../../previews';
import {useConfirmUnsavedEditsBeforeSplit} from './ConfirmUnsavedEditsBeforeSplit';
import {editingStackIntentionHashes} from './stackEditState';
import {useAtomValue, useSetAtom} from 'jotai';

/** Button to open split UI for the current commit. Expected to be shown on the head commit.
 * Loads that one commit in the split UI. */
export function SplitButton({
  commit,
  ...rest
}: {commit: CommitInfo} & React.ComponentProps<typeof Button>) {
  const confirmUnsavedEditsBeforeSplit = useConfirmUnsavedEditsBeforeSplit();
  const setEditStackIntentionHashes = useSetAtom(editingStackIntentionHashes);

  const uncommittedChanges = useAtomValue(uncommittedChangesWithPreviews);
  const hasUncommittedChanges = uncommittedChanges.length > 0;

  const onClick = async () => {
    if (!(await confirmUnsavedEditsBeforeSplit([commit], 'split'))) {
      return;
    }
    setEditStackIntentionHashes(['split', new Set([commit.hash])]);
    tracker.track('SplitOpenFromHeadCommit');
  };
  return (
    <Tooltip
      title={hasUncommittedChanges ? t('Cannot currently split with uncommitted changes') : ''}
      trigger={hasUncommittedChanges ? 'hover' : 'disabled'}>
      <Button onClick={onClick} disabled={hasUncommittedChanges} {...rest}>
        <SplitCommitIcon />
        <T>Split</T>
      </Button>
    </Tooltip>
  );
}
