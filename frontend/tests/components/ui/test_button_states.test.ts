import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import Button from '../../../app/components/ui/Button.vue';

describe('ui/Button : states loading / disabled / click / keyboard (AC4+AC5)', () => {
  let warnSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    warnSpy.mockRestore();
  });

  it('click emis 1 fois en state default', async () => {
    const w = mount(Button, { slots: { default: 'Go' } });
    await w.find('button').trigger('click');
    expect(w.emitted('click')).toHaveLength(1);
    expect(w.emitted('click')?.[0]?.[0]).toBeInstanceOf(MouseEvent);
    w.unmount();
  });

  it('loading=true : aria-busy="true" + disabled + spinner rendu + texte invisible', async () => {
    const w = mount(Button, {
      props: { loading: true },
      slots: { default: 'Signer' },
    });
    const btn = w.find('button');
    expect(btn.attributes('aria-busy')).toBe('true');
    expect(btn.attributes('disabled')).toBeDefined();
    // Spinner present
    expect(w.find('svg.animate-spin').exists()).toBe(true);
    // Texte wrap span contient classe invisible
    const textSpans = w.findAll('span');
    const labelSpan = textSpans.find((s) => s.text() === 'Signer');
    expect(labelSpan?.classes()).toContain('invisible');
    // Click bloque
    await btn.trigger('click');
    expect(w.emitted('click')).toBeUndefined();
    w.unmount();
  });

  it('disabled=true : aria-disabled="true" + click bloque', async () => {
    const w = mount(Button, {
      props: { disabled: true },
      slots: { default: 'Nope' },
    });
    const btn = w.find('button');
    expect(btn.attributes('aria-disabled')).toBe('true');
    expect(btn.attributes('disabled')).toBeDefined();
    await btn.trigger('click');
    expect(w.emitted('click')).toBeUndefined();
    w.unmount();
  });

  it('disabled=true : keyboard Enter + Space ne declenche pas click (native button)', async () => {
    const w = mount(Button, {
      props: { disabled: true },
      slots: { default: 'Nope' },
    });
    const btn = w.find('button');
    await btn.trigger('keydown', { key: 'Enter' });
    await btn.trigger('keyup', { key: ' ' });
    expect(w.emitted('click')).toBeUndefined();
    w.unmount();
  });

  it('iconOnly=true sans ariaLabel vide : console.warn appele', () => {
    mount(Button, {
      props: { iconOnly: true, ariaLabel: '   ' },
      slots: { iconLeft: '<span>i</span>' },
    });
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('iconOnly=true requires non-empty ariaLabel'),
    );
  });

  it('slot default vide + non iconOnly + pas ariaLabel : console.warn appele', () => {
    mount(Button, { props: {} });
    expect(warnSpy).toHaveBeenCalledWith(
      expect.stringContaining('no visible label'),
    );
  });

  it('iconOnly=true AVEC ariaLabel non vide : pas de warning', () => {
    mount(Button, {
      props: { iconOnly: true, ariaLabel: 'Fermer' },
      slots: { iconLeft: '<span>x</span>' },
    });
    expect(warnSpy).not.toHaveBeenCalled();
  });
});
