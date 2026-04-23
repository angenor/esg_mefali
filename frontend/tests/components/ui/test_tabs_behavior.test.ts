/**
 * Tests comportement ui/Tabs (AC7-AC12 Story 10.19).
 *
 * Pattern A strict (10.16 H-3 + 10.17 + 10.18 §4ter.bis) :
 *  - `screen.getByRole` + `user.click/keyboard` (`@testing-library/user-event`),
 *  - AUCUN `wrapper.vm.*`, AUCUN `setValue(...)`.
 *
 * Tabs n'est pas portalise → `screen.*` scanne le wrapper render natif.
 */
import { describe, it, expect, afterEach } from 'vitest';
import { defineComponent, h, ref } from 'vue';
import { render, screen, cleanup } from '@testing-library/vue';
import userEvent from '@testing-library/user-event';
import Tabs from '../../../app/components/ui/Tabs.vue';

afterEach(() => {
  cleanup();
});

const BASE_TABS = [
  { value: 't1', label: 'Onglet 1' },
  { value: 't2', label: 'Onglet 2' },
  { value: 't3', label: 'Onglet 3' },
] as const;

// Helper parent controle pour v-model:modelValue bidirectionnel.
function makeParent(initialValue = 't1', extraProps: Record<string, unknown> = {}) {
  return defineComponent({
    components: { Tabs },
    setup() {
      const modelValue = ref(initialValue);
      return { modelValue, extraProps };
    },
    render() {
      return h(
        Tabs,
        {
          modelValue: this.modelValue,
          tabs: [...BASE_TABS],
          'onUpdate:modelValue': (v: string) => {
            this.modelValue = v;
          },
          ...extraProps,
        },
        {
          'content-t1': () => h('div', { 'data-testid': 'tab-content-t1' }, 'Contenu 1'),
          'content-t2': () => h('div', { 'data-testid': 'tab-content-t2' }, 'Contenu 2'),
          'content-t3': () => h('div', { 'data-testid': 'tab-content-t3' }, 'Contenu 3'),
        },
      );
    },
  });
}

describe('ui/Tabs : AC7 render + v-model', () => {
  it('rend tablist + N triggers + au moins 1 tabpanel', () => {
    render(makeParent('t1'));
    expect(screen.getByRole('tablist')).toBeDefined();
    expect(screen.getAllByRole('tab').length).toBe(BASE_TABS.length);
    expect(screen.getAllByRole('tabpanel').length).toBeGreaterThanOrEqual(1);
  });

  it('clic sur tab 2 → update:modelValue emis avec "t2" + contenu t2 affiche', async () => {
    const user = userEvent.setup();
    render(makeParent('t1'));
    await user.click(screen.getByRole('tab', { name: /onglet 2/i }));
    // Le tabpanel actif doit contenir le texte du slot content-t2
    const activePanel = screen.getByRole('tabpanel');
    expect(activePanel.textContent).toContain('Contenu 2');
  });
});

describe('ui/Tabs : AC8 orientation horizontal + vertical', () => {
  it('orientation horizontal (default) → aria-orientation="horizontal"', () => {
    render(makeParent('t1'));
    const list = screen.getByRole('tablist');
    expect(list.getAttribute('aria-orientation')).toBe('horizontal');
  });

  it('orientation vertical → aria-orientation="vertical"', () => {
    render(makeParent('t1', { orientation: 'vertical' }));
    const list = screen.getByRole('tablist');
    expect(list.getAttribute('aria-orientation')).toBe('vertical');
  });

  it('classes orientation-specifiques appliquees sur tablist', () => {
    const { unmount } = render(makeParent('t1'));
    const horizontalList = screen.getByRole('tablist');
    expect(horizontalList.className).toContain('flex-row');
    unmount();

    render(makeParent('t1', { orientation: 'vertical' }));
    const verticalList = screen.getByRole('tablist');
    expect(verticalList.className).toContain('flex-col');
  });
});

describe('ui/Tabs : AC9 activation automatic vs manual', () => {
  it("activation 'automatic' (default) : ArrowRight → modelValue change immediat", async () => {
    const user = userEvent.setup();
    render(makeParent('t1'));
    const t1 = screen.getByRole('tab', { name: /onglet 1/i });
    t1.focus();
    await user.keyboard('{ArrowRight}');
    // Assertion stricte leçon 21 : le tabpanel actif a le contenu de t2
    const panel = screen.getByRole('tabpanel');
    expect(panel.textContent).toContain('Contenu 2');
  });

  it("activation 'manual' : ArrowRight → focus bouge mais modelValue inchange", async () => {
    const user = userEvent.setup();
    render(makeParent('t1', { activationMode: 'manual' }));
    const t1 = screen.getByRole('tab', { name: /onglet 1/i });
    t1.focus();
    await user.keyboard('{ArrowRight}');
    // Le focus est sur t2 mais modelValue reste t1 → panel affiche Contenu 1
    const panel = screen.getByRole('tabpanel');
    expect(panel.textContent).toContain('Contenu 1');
  });

  it("activation 'manual' + Enter → modelValue change apres activation explicite", async () => {
    const user = userEvent.setup();
    render(makeParent('t1', { activationMode: 'manual' }));
    const t1 = screen.getByRole('tab', { name: /onglet 1/i });
    t1.focus();
    await user.keyboard('{ArrowRight}');
    await user.keyboard('{Enter}');
    const panel = screen.getByRole('tabpanel');
    expect(panel.textContent).toContain('Contenu 2');
  });
});

describe('ui/Tabs : AC10 ARIA attributes', () => {
  it('chaque tab a aria-selected (true/false) + role="tab"', () => {
    render(makeParent('t1'));
    const tabs = screen.getAllByRole('tab');
    // Premier tab selectionne
    expect(tabs[0].getAttribute('aria-selected')).toBe('true');
    // Les suivants non-selectionnes
    expect(tabs[1].getAttribute('aria-selected')).toBe('false');
    expect(tabs[2].getAttribute('aria-selected')).toBe('false');
    // Tous les tabs portent role="tab" (sanity)
    tabs.forEach((t) => expect(t.getAttribute('role')).toBe('tab'));
  });

  it('tabpanel actif a aria-labelledby pointant le tab', () => {
    render(makeParent('t1'));
    const panel = screen.getByRole('tabpanel');
    const labelledby = panel.getAttribute('aria-labelledby');
    expect(labelledby).not.toBeNull();
    expect(document.getElementById(labelledby!)).not.toBeNull();
  });

  it('prop label → aria-label present sur tablist', () => {
    render(makeParent('t1', { label: 'Navigation principale' }));
    expect(screen.getByRole('tablist').getAttribute('aria-label')).toBe(
      'Navigation principale',
    );
  });
});

describe('ui/Tabs : AC11 keyboard navigation horizontal', () => {
  it('ArrowRight depuis t1 → focus sur t2', async () => {
    const user = userEvent.setup();
    render(makeParent('t1'));
    const t1 = screen.getByRole('tab', { name: /onglet 1/i });
    t1.focus();
    await user.keyboard('{ArrowRight}');
    const t2 = screen.getByRole('tab', { name: /onglet 2/i });
    expect(document.activeElement).toBe(t2);
  });

  it('ArrowLeft depuis t1 → cycle infini vers tN (dernier)', async () => {
    const user = userEvent.setup();
    render(makeParent('t1'));
    const t1 = screen.getByRole('tab', { name: /onglet 1/i });
    t1.focus();
    await user.keyboard('{ArrowLeft}');
    const t3 = screen.getByRole('tab', { name: /onglet 3/i });
    expect(document.activeElement).toBe(t3);
  });

  it('Home depuis tN → focus sur t1', async () => {
    const user = userEvent.setup();
    render(makeParent('t3'));
    const t3 = screen.getByRole('tab', { name: /onglet 3/i });
    t3.focus();
    await user.keyboard('{Home}');
    const t1 = screen.getByRole('tab', { name: /onglet 1/i });
    expect(document.activeElement).toBe(t1);
  });

  it('End depuis t1 → focus sur dernier tab', async () => {
    const user = userEvent.setup();
    render(makeParent('t1'));
    const t1 = screen.getByRole('tab', { name: /onglet 1/i });
    t1.focus();
    await user.keyboard('{End}');
    const t3 = screen.getByRole('tab', { name: /onglet 3/i });
    expect(document.activeElement).toBe(t3);
  });
});

describe('ui/Tabs : AC11 keyboard navigation vertical', () => {
  it('orientation vertical : ArrowDown remplace ArrowRight', async () => {
    const user = userEvent.setup();
    render(makeParent('t1', { orientation: 'vertical' }));
    const t1 = screen.getByRole('tab', { name: /onglet 1/i });
    t1.focus();
    await user.keyboard('{ArrowDown}');
    const t2 = screen.getByRole('tab', { name: /onglet 2/i });
    expect(document.activeElement).toBe(t2);
  });

  it('orientation vertical : ArrowUp remplace ArrowLeft (cycle)', async () => {
    const user = userEvent.setup();
    render(makeParent('t1', { orientation: 'vertical' }));
    const t1 = screen.getByRole('tab', { name: /onglet 1/i });
    t1.focus();
    await user.keyboard('{ArrowUp}');
    const t3 = screen.getByRole('tab', { name: /onglet 3/i });
    expect(document.activeElement).toBe(t3);
  });
});

describe('ui/Tabs : AC11 disabled tab skip', () => {
  it("tab disabled → skip dans la navigation keyboard", async () => {
    const user = userEvent.setup();
    const TABS_WITH_DISABLED = [
      { value: 't1', label: 'Onglet 1' },
      { value: 't2', label: 'Onglet 2', disabled: true },
      { value: 't3', label: 'Onglet 3' },
    ];
    render(Tabs, {
      props: {
        modelValue: 't1',
        tabs: TABS_WITH_DISABLED,
      },
    });
    const t1 = screen.getByRole('tab', { name: /onglet 1/i });
    t1.focus();
    await user.keyboard('{ArrowRight}');
    const t3 = screen.getByRole('tab', { name: /onglet 3/i });
    expect(document.activeElement).toBe(t3);
  });
});

describe('ui/Tabs : AC12 forceMount lazy vs eager', () => {
  it('forceMount default false : un seul tabpanel rendu (l\'actif)', () => {
    render(makeParent('t1'));
    // Pattern: seul le tabpanel actif est dans le DOM (lazy mount Reka UI).
    // Assertion stricte leçon 21 : queryByTestId null avant changement de tab.
    expect(screen.queryByTestId('tab-content-t2')).toBeNull();
    expect(screen.getByTestId('tab-content-t1')).toBeDefined();
  });

  it('forceMount true : tous les tabpanels rendus simultanement', () => {
    render(makeParent('t1', { forceMount: true }));
    expect(screen.getByTestId('tab-content-t1')).toBeDefined();
    expect(screen.getByTestId('tab-content-t2')).toBeDefined();
    expect(screen.getByTestId('tab-content-t3')).toBeDefined();
  });

  it('lazy : clic sur t2 → content-t2 monte apres switch', async () => {
    const user = userEvent.setup();
    render(makeParent('t1'));
    expect(screen.queryByTestId('tab-content-t2')).toBeNull();
    await user.click(screen.getByRole('tab', { name: /onglet 2/i }));
    expect(screen.getByTestId('tab-content-t2')).toBeDefined();
  });

  it('M-5 piège #37 : forceMount omis ≡ forceMount=false (lazy)', () => {
    // M-5 / Leçon 24 §4quinquies — Reka UI traite forceMount comme prop-presence.
    // Notre wrapper mappe explicitement `false → undefined` pour neutraliser ce
    // piège. Test : omission + false produisent le meme comportement (lazy).
    render(makeParent('t1'));
    expect(screen.queryByTestId('tab-content-t2')).toBeNull();
    expect(screen.queryByTestId('tab-content-t3')).toBeNull();
  });

  it('M-5 piège #37 : forceMount=false explicite equivalent a omission (lazy)', () => {
    render(makeParent('t1', { forceMount: false }));
    // Verif comportement equivalent a omission : un seul tabpanel monte.
    expect(screen.queryByTestId('tab-content-t2')).toBeNull();
    expect(screen.queryByTestId('tab-content-t3')).toBeNull();
    expect(screen.getByTestId('tab-content-t1')).toBeDefined();
  });

  it('M-5 piège #37 : forceMount=true explicite active le mode eager', () => {
    // forceMount true → tous les tabpanels rendus (piège inverse : boolean
    // true est le seul equivalent fonctionnel de prop-presence chez Reka UI).
    render(makeParent('t1', { forceMount: true }));
    expect(screen.getByTestId('tab-content-t2')).toBeDefined();
    expect(screen.getByTestId('tab-content-t3')).toBeDefined();
  });
});

describe('ui/Tabs : AC7 icon slot + aria-hidden', () => {
  it('tab.icon → rendered avec aria-hidden="true"', () => {
    const FakeIcon = defineComponent({
      render() {
        return h('span', { class: 'fake-icon', 'data-testid': 'icon-t1' });
      },
    });
    render(Tabs, {
      props: {
        modelValue: 't1',
        tabs: [
          { value: 't1', label: 'Onglet 1', icon: FakeIcon },
          { value: 't2', label: 'Onglet 2' },
        ],
      },
    });
    const icon = screen.getByTestId('icon-t1');
    // L'icone est rendue avec aria-hidden sur son wrapper component
    // (class `aria-hidden="true"` passe au component). Le component racine
    // (span.fake-icon) porte l'attribut via fallthrough.
    expect(icon.getAttribute('aria-hidden')).toBe('true');
  });
});
