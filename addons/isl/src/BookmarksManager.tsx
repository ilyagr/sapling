/**
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */

import {Bookmark} from './Bookmark';
import {bookmarksDataStorage} from './BookmarksData';
import {Column} from './ComponentUtils';
import {DropdownFields} from './DropdownFields';
import {useCommandEvent} from './ISLShortcuts';
import {Kbd} from './Kbd';
import {Tooltip} from './Tooltip';
import {Checkbox} from './components/Checkbox';
import {T} from './i18n';
import {dagWithPreviews} from './previews';
import {spacing} from './tokens.stylex';
import * as stylex from '@stylexjs/stylex';
import {VSCodeButton} from '@vscode/webview-ui-toolkit/react';
import {atom, useAtom, useAtomValue} from 'jotai';
import {Icon} from 'shared/Icon';
import {KeyCode, Modifier} from 'shared/KeyboardShortcuts';

const styles = stylex.create({
  bookmarkGroup: {
    alignItems: 'flex-start',
    marginInline: spacing.pad,
  },
});

export function BookmarksManagerMenu() {
  const additionalToggles = useCommandEvent('ToggleBookmarksManagerDropdown');
  return (
    <Tooltip
      component={dismiss => <BookmarksManager dismiss={dismiss} />}
      trigger="click"
      placement="bottom"
      group="topbar"
      title={
        <T replace={{$shortcut: <Kbd keycode={KeyCode.M} modifiers={[Modifier.ALT]} />}}>
          Bookmarks Manager ($shortcut)
        </T>
      }
      additionalToggles={additionalToggles}>
      <VSCodeButton appearance="icon" data-testid="bulk-actions-button">
        <Icon icon="bookmark" />
      </VSCodeButton>
    </Tooltip>
  );
}

const remoteBookmarks = atom(get => {
  const dag = get(dagWithPreviews);
  return dag.getBatch(dag.public_().toArray()).flatMap(commit => commit.remoteBookmarks);
});

function BookmarksManager(_props: {dismiss: () => void}) {
  const bookmarks = useAtomValue(remoteBookmarks);
  const [bookmarksData, setBookmarksData] = useAtom(bookmarksDataStorage);
  return (
    <DropdownFields
      title={<T>Bookmarks Manager</T>}
      icon="bookmark"
      data-testid="bookmarks-manager-dropdown">
      <strong>
        <T>Remote Bookmarks</T>
      </strong>
      <Column xstyle={styles.bookmarkGroup}>
        {bookmarks.map(bookmark => (
          <Checkbox
            key={bookmark}
            checked={!bookmarksData.hiddenRemoteBookmarks.includes(bookmark)}
            onChange={checked => {
              const shouldBeDeselected = !checked;
              let hiddenRemoteBookmarks = bookmarksData.hiddenRemoteBookmarks;
              if (shouldBeDeselected) {
                hiddenRemoteBookmarks = [...hiddenRemoteBookmarks, bookmark];
              } else {
                hiddenRemoteBookmarks = hiddenRemoteBookmarks.filter(b => b !== bookmark);
              }
              setBookmarksData({...bookmarksData, hiddenRemoteBookmarks});
            }}>
            <Bookmark key={bookmark}>{bookmark}</Bookmark>
          </Checkbox>
        ))}
      </Column>
    </DropdownFields>
  );
}
