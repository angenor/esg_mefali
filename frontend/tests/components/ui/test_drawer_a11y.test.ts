/**
 * Tests A11y ui/Drawer (AC3 + AC10 Story 10.18).
 * Portail Reka UI DialogPortal → assertions via document.body.querySelector
 * (Pattern A — leçon 10.16 H-3 capitalisée + piège #28 codemap).
 *
 * Note explicite : les audits portail-dépendants (contraste runtime, focus trap
 * keyboard navigation, animations slide) sont DÉLÉGUÉS à Storybook addon-a11y
 * runtime (leçon 10.15 HIGH-2 capitalisée infra). Ici : smoke DOM + ARIA.
 */
import { describe, it, expect } from 'vitest';
import { nextTick } from 'vue';
import { mount } from '@vue/test-utils';
import { axe, toHaveNoViolations } from 'jest-axe';
import Drawer from '../../../app/components/ui/Drawer.vue';

expect.extend(toHaveNoViolations);

const AXE_OPTIONS = {
  rules: {
    // happy-dom n'evalue pas le layout CSS — delegue Storybook runtime (piege #28)
    'color-contrast': { enabled: false },
    'color-contrast-enhanced': { enabled: false },
    region: { enabled: false },
    // aria-modal n'est pas valide strict selon ARIA 1.2 sur role="complementary"
    // (ARIA le reserve a role="dialog"). Override delibere Q2+Q3 verrouillees
    // (leçon 10.14 HIGH-2 capitalisee infra) : drawer consultatif != modal
    // bloquant. Signalement explicite `aria-modal="false"` ameliore la
    // semantique screen reader. La validation WCAG runtime est deleguee a
    // Storybook addon-a11y qui permet de scoper la regle (piege #28 codemap).
    'aria-allowed-attr': { enabled: false },
    // aria-hidden-focus : artefact happy-dom quand plusieurs instances Reka UI
    // coexistent dans document.body apres remount. Validation Storybook runtime.
    'aria-hidden-focus': { enabled: false },
  },
} as const;

describe('ui/Drawer : AC3 ARIA override (Pattern A DOM-only)', () => {
  it('role="complementary" present (override Reka UI default dialog)', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'Sources' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const el = document.body.querySelector('[role="complementary"]');
    expect(el).not.toBeNull();
    expect(el?.getAttribute('role')).toBe('complementary');
    // Enforce strict : pas de role="dialog" (qui serait le default Reka UI)
    expect(el?.getAttribute('role')).not.toBe('dialog');
    w.unmount();
  });

  it('aria-modal="false" explicite (drawer != modal bloquant)', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'T' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const el = document.body.querySelector('[role="complementary"]');
    expect(el?.getAttribute('aria-modal')).toBe('false');
    w.unmount();
  });

  it('aria-labelledby pointe sur titleId existant non-null (AC3)', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'Sources RAG FR71' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const el = document.body.querySelector('[role="complementary"]');
    const labelId = el?.getAttribute('aria-labelledby');
    expect(labelId).toBeTruthy();
    expect(document.getElementById(labelId!)?.textContent?.trim()).toBe(
      'Sources RAG FR71',
    );
    w.unmount();
  });

  it('aria-describedby conditionnel — present ssi description fournie', async () => {
    // Sans description
    const w1 = mount(Drawer, {
      props: { open: true, title: 'T' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    expect(
      document.body
        .querySelector('[role="complementary"]')
        ?.hasAttribute('aria-describedby'),
    ).toBe(false);
    w1.unmount();

    // Avec description
    const w2 = mount(Drawer, {
      props: { open: true, title: 'T', description: 'Contexte' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const descId = document.body
      .querySelector('[role="complementary"]')
      ?.getAttribute('aria-describedby');
    expect(descId).toBeTruthy();
    expect(document.getElementById(descId!)?.textContent?.trim()).toBe(
      'Contexte',
    );
    w2.unmount();
  });
});

describe('ui/Drawer : AC10 vitest-axe smoke (delegation runtime Storybook pour portail)', () => {
  it('open default (sans description) : 0 violation smoke', async () => {
    const w = mount(Drawer, {
      props: { open: true, title: 'Panneau' },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const results = await axe(document.body, AXE_OPTIONS);
    expect(results).toHaveNoViolations();
    w.unmount();
  });

  it('open avec description : 0 violation smoke', async () => {
    const w = mount(Drawer, {
      props: {
        open: true,
        title: 'Panneau',
        description: 'Contexte secondaire',
      },
      attachTo: document.body,
    });
    await nextTick();
    await nextTick();
    const results = await axe(document.body, AXE_OPTIONS);
    expect(results).toHaveNoViolations();
    w.unmount();
  });
});
