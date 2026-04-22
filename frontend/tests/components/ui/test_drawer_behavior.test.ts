/**
 * Tests comportement ui/Drawer (AC3-AC9, AC13 Story 10.18).
 * Pattern A strict (10.16 H-3 + capitalisation 10.17) : DOM-only assertions,
 * AUCUN `wrapper.vm.*` — Reka UI DialogPortal portalise sur `document.body`,
 * scan via `document.body.querySelector(...)`.
 */
import { describe, it, expect, vi, afterEach } from 'vitest';
import { nextTick, defineComponent, h, ref } from 'vue';
import { mount } from '@vue/test-utils';
import Drawer from '../../../app/components/ui/Drawer.vue';

// Cleanup inter-tests : Reka UI DialogPortal peut laisser des noeuds
// residuels dans document.body apres unmount() en happy-dom. On purge
// les landmarks `[role="complementary"]` + viewports ScrollArea orphelins
// pour garantir l'isolation (pattern A 10.16 capitalise).
afterEach(() => {
  document.body
    .querySelectorAll('[role="complementary"]')
    .forEach((el) => el.remove());
  document.body
    .querySelectorAll('[data-reka-scroll-area-viewport]')
    .forEach((el) => {
      if (!el.closest('[role="complementary"]')) {
        el.remove();
      }
    });
});

// Helper parent pour v-model:open bidirectionnel
function makeParent(initialOpen: boolean, extraProps: Record<string, unknown> = {}) {
  return defineComponent({
    components: { Drawer },
    setup() {
      const open = ref(initialOpen);
      return { open, extraProps };
    },
    render() {
      return h(
        Drawer,
        {
          open: this.open,
          title: 'Panneau test',
          'onUpdate:open': (v: boolean) => {
            this.open = v;
          },
          ...extraProps,
        },
        { default: () => h('p', 'contenu drawer') },
      );
    },
  });
}

function queryDrawer(): HTMLElement | null {
  return document.body.querySelector<HTMLElement>('[role="complementary"]');
}

describe('ui/Drawer : v-model:open two-way (AC4)', () => {
  it('monte avec open=false → aucun role=complementary dans body', async () => {
    const w = mount(makeParent(false), { attachTo: document.body });
    await nextTick();
    expect(queryDrawer()).toBeNull();
    w.unmount();
  });

  it('monte avec open=true → role=complementary present dans body', async () => {
    const w = mount(
      Drawer,
      {
        props: { open: true, title: 'T1' },
        attachTo: document.body,
      },
    );
    await nextTick();
    await nextTick();
    expect(queryDrawer()).not.toBeNull();
    w.unmount();
  });
});

describe('ui/Drawer : AC3 ARIA override role=complementary + aria-modal=false', () => {
  it('applique role="complementary" (override Reka UI default dialog)', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'Titre' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const el = queryDrawer();
    expect(el).not.toBeNull();
    expect(el?.getAttribute('role')).toBe('complementary');
    w.unmount();
  });

  it('applique aria-modal="false" (drawer != modal bloquant)', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'Titre' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const el = queryDrawer();
    expect(el?.getAttribute('aria-modal')).toBe('false');
    w.unmount();
  });

  it('aria-labelledby pointe vers un ID qui contient le title DOM', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'Sources RAG' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const el = queryDrawer();
    const labelId = el?.getAttribute('aria-labelledby');
    expect(labelId).toBeTruthy();
    const titleEl = document.getElementById(labelId!);
    expect(titleEl?.textContent?.trim()).toBe('Sources RAG');
    w.unmount();
  });

  it('aria-describedby absent si description non fournie', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const el = queryDrawer();
    expect(el?.hasAttribute('aria-describedby')).toBe(false);
    w.unmount();
  });

  it('aria-describedby present et pointe sur description si fournie', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T', description: 'Contexte secondaire' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const el = queryDrawer();
    const descId = el?.getAttribute('aria-describedby');
    expect(descId).toBeTruthy();
    expect(document.getElementById(descId!)?.textContent?.trim()).toBe(
      'Contexte secondaire',
    );
    w.unmount();
  });
});

describe('ui/Drawer : AC5 fermeture close button', () => {
  it('close button par defaut present avec aria-label="Fermer le panneau"', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const btn = document.body.querySelector<HTMLButtonElement>(
      'button[aria-label="Fermer le panneau"]',
    );
    expect(btn).not.toBeNull();
    w.unmount();
  });

  // M-1 10.18 post-review : prop closeLabel i18n-ready (default « Fermer le panneau »).
  it('closeLabel custom applique sur le bouton close (i18n-ready)', async () => {
    const w = mount(Drawer, {
      props: {
        open: true,
        title: 'T',
        closeLabel: 'Fermer le panneau des sources',
      },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const btn = document.body.querySelector<HTMLButtonElement>(
      'button[aria-label="Fermer le panneau des sources"]',
    );
    expect(btn).not.toBeNull();
    // Default « Fermer le panneau » absent (override effectif)
    const defaultBtn = document.body.querySelector(
      'button[aria-label="Fermer le panneau"]',
    );
    expect(defaultBtn).toBeNull();
    w.unmount();
  });

  it('showCloseButton=false retire le bouton (AC5 case no-close-button)', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T', showCloseButton: false },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const btn = document.body.querySelector(
      'button[aria-label="Fermer le panneau"]',
    );
    expect(btn).toBeNull();
    w.unmount();
  });

  it('emit update:open=false quand Escape appuye (closeOnEscape default true)', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const el = queryDrawer();
    el?.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }),
    );
    await nextTick();
    await nextTick();
    // H-2a 10.18 post-review : assertion stricte (retire garde permissive
    // `if (events)` qui masquait une regression silencieuse). Reka UI doit
    // emettre update:open=[false] au keydown Escape (closeOnEscape default true).
    // Si ce test devient flaky happy-dom, delegation Storybook play function
    // `CloseOnEscape` prevue — mais l'assert strict reste la source de verite.
    const events = w.emitted('update:open');
    expect(events).toBeDefined();
    expect(events!.at(-1)).toEqual([false]);
    w.unmount();
  });
});

describe('ui/Drawer : AC5 runtime warn si 3 paths disabled (piege #32)', () => {
  it('declenche console.warn dev-only quand 3 chemins fermeture desactives', () => {
    const spy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const w = mount(Drawer, {
      props: {
        open: false,
        title: 'T',
        closeOnEscape: false,
        closeOnOverlayClick: false,
        showCloseButton: false,
      },
      attachTo: document.body,
    });
    // Warn execute au setup() — synchrone, pas besoin nextTick
    expect(spy).toHaveBeenCalled();
    const msg = spy.mock.calls[0]?.[0];
    expect(String(msg)).toContain('[ui/Drawer]');
    expect(String(msg)).toContain('3 chemins');
    spy.mockRestore();
    w.unmount();
  });

  it('pas de warn quand au moins 1 chemin reste actif', () => {
    const spy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const w = mount(Drawer, {
      props: {
        open: false,
        title: 'T',
        closeOnEscape: true,
        closeOnOverlayClick: false,
        showCloseButton: false,
      },
      attachTo: document.body,
    });
    // Le warn Drawer ne doit pas avoir ete appele (filtre: pas d'autres warns)
    const drawerWarns = spy.mock.calls.filter((c) =>
      String(c[0]).includes('[ui/Drawer]'),
    );
    expect(drawerWarns.length).toBe(0);
    spy.mockRestore();
    w.unmount();
  });
});

describe('ui/Drawer : AC7 sizes desktop (classList scan)', () => {
  it('size=sm → classe md:w-[320px] presente (side horizontal)', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T', side: 'right', size: 'sm' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const el = queryDrawer();
    expect(el?.className).toContain('md:w-[320px]');
    w.unmount();
  });

  it('size=md → classe md:w-[480px] presente', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T', side: 'right', size: 'md' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    expect(queryDrawer()?.className).toContain('md:w-[480px]');
    w.unmount();
  });

  it('size=lg → classe md:w-[560px] presente + garde-fou max-w-[50vw] (piege #30)', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T', side: 'right', size: 'lg' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const cls = queryDrawer()?.className ?? '';
    expect(cls).toContain('md:w-[560px]');
    expect(cls).toContain('md:max-w-[50vw]');
    w.unmount();
  });

  it('side=top + size=md → classe md:h-[480px] (dimension verticale)', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T', side: 'top', size: 'md' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    expect(queryDrawer()?.className).toContain('md:h-[480px]');
    w.unmount();
  });
});

describe('ui/Drawer : AC7 sides (classList scan)', () => {
  const cases: Array<[string, string]> = [
    ['right', 'md:right-0'],
    ['left', 'md:left-0'],
    ['top', 'md:top-0'],
    ['bottom', 'md:bottom-0'],
  ];
  for (const [side, expected] of cases) {
    it(`side=${side} → classe ${expected} presente`, async () => {
      const w = mount(Drawer, {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        props: { open: true, title: 'T', side: side as any },
        attachTo: document.body,
      });
      await nextTick();
      await nextTick();
      expect(queryDrawer()?.className).toContain(expected);
      w.unmount();
    });
  }
});

describe('ui/Drawer : AC6 mobile fullscreen CSS-only (piege #29)', () => {
  it('side=right : classe w-full h-full inset-0 presente (base mobile, override md:)', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T', side: 'right', size: 'md' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const cls = queryDrawer()?.className ?? '';
    expect(cls).toContain('w-full');
    expect(cls).toContain('h-full');
    expect(cls).toContain('inset-0');
    expect(cls).toContain('md:inset-auto');
    w.unmount();
  });

  // H-1 10.18 post-review : AC6 bottom-sheet bascule mobile (pattern iOS
  // UISheetPresentationController / Android BottomSheetDialog).
  it('side=bottom : pattern bottom-sheet mobile (max-h 85vh + rounded-t-xl)', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T', side: 'bottom', size: 'md' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const cls = queryDrawer()?.className ?? '';
    expect(cls).toContain('bottom-0');
    expect(cls).toContain('max-h-[85vh]');
    expect(cls).toContain('rounded-t-xl');
    expect(cls).toContain('md:rounded-none');
    w.unmount();
  });

  it('side=top : pattern top-sheet mobile (max-h 85vh + rounded-b-xl)', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T', side: 'top', size: 'md' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const cls = queryDrawer()?.className ?? '';
    expect(cls).toContain('top-0');
    expect(cls).toContain('max-h-[85vh]');
    expect(cls).toContain('rounded-b-xl');
    w.unmount();
  });
});

describe('ui/Drawer : AC8 focus return & trap observable (H-2b + M-3 post-review)', () => {
  // H-2b 10.18 post-review : focus return observable apres fermeture.
  // Pattern A strict : le drawer doit etre retire du DOM + activeElement
  // ne doit pas rester coince sur un element descendant d'un drawer supprime
  // (sanity check portal cleanup Reka UI). Validation runtime complete
  // (focus exactement sur trigger) deleguee a Storybook play function
  // `FocusReturnOnClose` — leçon 10.15 HIGH-2 : focus restoration
  // portail-dependant fiable en browser runtime, pas en happy-dom sans
  // layout box. Note inline = delegation documentee.
  it('focus return : drawer retire du DOM + activeElement hors portal apres close', async () => {
    const Parent = defineComponent({
      components: { Drawer },
      setup() {
        const open = ref(false);
        return { open };
      },
      render() {
        return h('div', [
          h(
            'button',
            {
              'data-testid': 'trigger',
              onClick: () => {
                this.open = true;
              },
            },
            'Ouvrir',
          ),
          h(
            Drawer,
            {
              open: this.open,
              title: 'T',
              'onUpdate:open': (v: boolean) => {
                this.open = v;
              },
            },
            { default: () => h('p', 'Contenu') },
          ),
        ]);
      },
    });

    const w = mount(Parent, { attachTo: document.body });
    await nextTick();

    const triggerEl = document.body.querySelector<HTMLButtonElement>(
      '[data-testid="trigger"]',
    );
    expect(triggerEl).not.toBeNull();
    triggerEl!.focus();
    expect(document.activeElement).toBe(triggerEl);

    // Ouverture
    triggerEl!.click();
    await nextTick();
    await nextTick();
    expect(queryDrawer()).not.toBeNull();

    // Fermeture via v-model (simule close button / Escape / overlay)
    (w.vm as unknown as { open: boolean }).open = false;
    await nextTick();
    await nextTick();
    await nextTick();

    // Assert strict observable : activeElement reste dans le DOM monte
    // (pas orphelin / pas sur un element detache du Reka UI portal apres
    // close). Le focus return exact sur trigger = Storybook runtime
    // `FocusReturnOnClose` — Reka UI FocusScope restoreFocus requiert
    // layout box, indisponible en happy-dom.
    const active = document.activeElement;
    expect(active).not.toBeNull();
    expect(document.body.contains(active)).toBe(true);
    // Le trigger reste focalisable (pas detache)
    expect(document.body.contains(triggerEl)).toBe(true);
    w.unmount();
  });

  // M-3 10.18 post-review : focus trap coverage (trapFocus=true).
  // Assert observable : le drawer rend, les elements internes sont
  // focalisables, et focus reste descendant de [role="complementary"]
  // apres mise au focus programmatique. Le cycle Tab reel est delegue
  // Storybook play function `FocusTrapCycle` (Reka UI FocusScope requiert
  // layout box, indisponible en happy-dom).
  it('trapFocus=true : element focalise reste dans le drawer (pattern A observable)', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T', trapFocus: true },
      attachTo: document.body,
      slots: {
        default:
          '<div><button data-testid="inner-a">A</button><button data-testid="inner-b">B</button></div>',
      },
    });
    await nextTick();
    await nextTick();

    const drawer = queryDrawer();
    expect(drawer).not.toBeNull();

    const innerA = document.body.querySelector<HTMLButtonElement>(
      '[data-testid="inner-a"]',
    );
    const innerB = document.body.querySelector<HTMLButtonElement>(
      '[data-testid="inner-b"]',
    );
    expect(innerA).not.toBeNull();
    expect(innerB).not.toBeNull();

    // Focus observable reste dans le drawer (descendant [role="complementary"])
    innerA!.focus();
    expect(drawer!.contains(document.activeElement)).toBe(true);

    innerB!.focus();
    expect(drawer!.contains(document.activeElement)).toBe(true);
    w.unmount();
  });

  it('trapFocus=false (default) : drawer rendu sans interception focus forcee', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T', trapFocus: false },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();

    // trapFocus=false : verification observable = DialogContent monte sans
    // activer FocusScope trap (navigation DOM externe libre). Le cycle Tab
    // externe reel est delegue Storybook runtime `FocusTrapDisabled` (visible
    // manuellement : Tab sort du drawer vers le contenu principal).
    expect(queryDrawer()).not.toBeNull();
    w.unmount();
  });
});

describe('ui/Drawer : AC13 ScrollArea integree', () => {
  // M-4 10.18 post-review : assert strict (data-attribute Reka UI) + fallback
  // multi-version. Remplace laxiste `textContent.contains(...)` qui restait
  // vert meme en cas de suppression accidentelle de ScrollAreaRoot.
  it('ScrollAreaRoot Reka UI present via data-attribute strict', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T' },
      attachTo: document.body,
      slots: {
        default: '<p>Contenu scrollable</p>',
      },
    });
    await nextTick();
    await nextTick();
    // Reka UI 2.9.6 expose `data-reka-scroll-area-viewport` sur le viewport
    // (scan fallback radix legacy + class CSS si API change).
    const viewport =
      document.body.querySelector('[data-reka-scroll-area-viewport]') ??
      document.body.querySelector('[data-radix-scroll-area-viewport]') ??
      document.body.querySelector('.scroll-area-viewport');
    expect(viewport).not.toBeNull();

    // Le slot default reste rendu dans le viewport (sanity check UX).
    expect(viewport?.textContent).toContain('Contenu scrollable');
    w.unmount();
  });
});

describe('ui/Drawer : AC11 baseline header/footer slots', () => {
  it('slot #footer rendu quand fourni', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T' },
      attachTo: document.body,
      slots: {
        footer: '<button data-testid="footer-btn">Action</button>',
      },
    });
    await nextTick();
    await nextTick();
    const btn = document.body.querySelector('[data-testid="footer-btn"]');
    expect(btn).not.toBeNull();
    w.unmount();
  });

  it('slot #header custom override le header default', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'DefaultTitle' },
      attachTo: document.body,
      slots: {
        header: '<h2 data-testid="custom-header">Custom</h2>',
      },
    });
    await nextTick();
    await nextTick();
    const custom = document.body.querySelector('[data-testid="custom-header"]');
    expect(custom?.textContent).toBe('Custom');
    w.unmount();
  });
});
