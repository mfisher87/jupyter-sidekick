import {
  ILayoutRestorer,
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import { ICommandPalette } from '@jupyterlab/apputils';
import { ILauncher } from '@jupyterlab/launcher';
import { LabIcon } from '@jupyterlab/ui-components';

import acpSvgStr from '../style/icons/acp.svg';
import { AcpChatPanel } from './widget';

const OPEN = 'jupyter-acp:open';
const MOVE_LEFT = 'jupyter-acp:move-left';
const MOVE_RIGHT = 'jupyter-acp:move-right';
const MOVE_MAIN = 'jupyter-acp:move-main';

export const acpIcon = new LabIcon({
  name: 'jupyter-acp:icon',
  svgstr: acpSvgStr
});

const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyter-acp:plugin',
  description: 'Zed-style ACP chat for JupyterLab.',
  autoStart: true,
  optional: [ICommandPalette, ILauncher, ILayoutRestorer],
  activate: (
    app: JupyterFrontEnd,
    palette: ICommandPalette | null,
    launcher: ILauncher | null,
    restorer: ILayoutRestorer | null
  ) => {
    let panel: AcpChatPanel | null = null;

    const ensurePanel = (): AcpChatPanel => {
      if (panel === null || panel.isDisposed) {
        panel = new AcpChatPanel();
        panel.id = 'jupyter-acp-panel';
        panel.title.icon = acpIcon;
        panel.title.label = 'ACP Chat';
        panel.title.caption = 'ACP Chat';
        panel.title.closable = true; // closable when floated into the main area
      }
      return panel;
    };

    // Relocate (and reveal) the single chat panel into the given shell area.
    // Re-adding an existing widget to a different area moves it there, so the
    // chat can live in the left/right sidebar or be popped out as a main tab —
    // letting the file browser stay open alongside it.
    const reveal = (area: 'left' | 'right' | 'main'): void => {
      const p = ensurePanel();
      const options = area === 'main' ? {} : { rank: 900 };
      app.shell.add(p, area, options);
      app.shell.activateById(p.id);
    };

    // Default home: the left sidebar.
    reveal('left');
    if (restorer && panel) {
      restorer.add(panel, 'jupyter-acp-panel');
    }

    app.commands.addCommand(OPEN, {
      label: 'ACP Chat',
      caption: 'Open the ACP chat panel',
      icon: acpIcon,
      execute: () => app.shell.activateById(ensurePanel().id)
    });
    app.commands.addCommand(MOVE_LEFT, {
      label: 'ACP Chat: Move to Left Sidebar',
      execute: () => reveal('left')
    });
    app.commands.addCommand(MOVE_RIGHT, {
      label: 'ACP Chat: Move to Right Sidebar',
      execute: () => reveal('right')
    });
    app.commands.addCommand(MOVE_MAIN, {
      label: 'ACP Chat: Move to Main Area',
      execute: () => reveal('main')
    });

    if (palette) {
      for (const command of [OPEN, MOVE_LEFT, MOVE_RIGHT, MOVE_MAIN]) {
        palette.addItem({ command, category: 'AI' });
      }
    }
    if (launcher) {
      launcher.add({ command: OPEN, category: 'Other', rank: 1 });
    }
  }
};

export default plugin;
