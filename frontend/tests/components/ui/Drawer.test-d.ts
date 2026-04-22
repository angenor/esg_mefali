/**
 * Compile-time type tests pour ui/Drawer (AC1 Story 10.18).
 * Execute via `vitest --typecheck` (vitest.config.ts typecheck enabled).
 *
 * Pattern byte-identique 10.15 HIGH-1 + 10.16 + 10.17 (compile-time enforcement).
 * Portee : union `side` / `size` + props obligatoires (`open`, `title`) +
 *          boolean strict (pas de coercion string/number).
 */
import { describe, it, expectTypeOf } from 'vitest';
import type {
  DrawerSide,
  DrawerSize,
} from '../../../app/components/ui/registry';

// Signature publique Drawer reflet byte-identique de DrawerProps (Drawer.vue).
// Declaree localement pour eviter import d'un .vue en typecheck (stable, verifie
// cote runtime par test_drawer_behavior : `open` + `title` requis).
interface DrawerProps {
  open: boolean;
  title: string;
  description?: string;
  side?: DrawerSide;
  size?: DrawerSize;
  trapFocus?: boolean;
  closeOnEscape?: boolean;
  closeOnOverlayClick?: boolean;
  showCloseButton?: boolean;
  closeLabel?: string;
}

describe('ui/Drawer : AC1 type safety (compile-time)', () => {
  it('DrawerSide inclut exactement right|left|top|bottom', () => {
    expectTypeOf<DrawerSide>().toEqualTypeOf<
      'right' | 'left' | 'top' | 'bottom'
    >();
  });

  it('DrawerSize inclut exactement sm|md|lg', () => {
    expectTypeOf<DrawerSize>().toEqualTypeOf<'sm' | 'md' | 'lg'>();
  });

  it('side "invalid" hors union est rejete', () => {
    // @ts-expect-error side hors union canonique right|left|top|bottom
    const bad: DrawerProps = { open: true, title: 'T', side: 'invalid' };
    void bad;
  });

  it('side "center" est rejete (drawer est toujours bord, pas centre)', () => {
    // @ts-expect-error drawer positionne sur un bord uniquement
    const bad: DrawerProps = { open: true, title: 'T', side: 'center' };
    void bad;
  });

  it('size "xl" hors union est rejete', () => {
    // @ts-expect-error size hors union sm|md|lg
    const bad: DrawerProps = { open: true, title: 'T', size: 'xl' };
    void bad;
  });

  it('size "SM" casse est rejete (minuscule requis)', () => {
    // @ts-expect-error union literale minuscule
    const bad: DrawerProps = { open: true, title: 'T', size: 'SM' };
    void bad;
  });

  it('title manquant est rejete (requis pour aria-labelledby AC3)', () => {
    // @ts-expect-error title requis
    const bad: DrawerProps = { open: true };
    void bad;
  });

  it('open manquant est rejete (requis pour v-model:open)', () => {
    // @ts-expect-error open requis
    const bad: DrawerProps = { title: 'T' };
    void bad;
  });

  it('open "true" string est rejete (boolean strict)', () => {
    // @ts-expect-error boolean strict pas de coercion string
    const bad: DrawerProps = { open: 'true', title: 'T' };
    void bad;
  });

  it('trapFocus "yes" string est rejete (boolean strict)', () => {
    // @ts-expect-error boolean strict
    const bad: DrawerProps = { open: true, title: 'T', trapFocus: 'yes' };
    void bad;
  });

  it('closeOnEscape 1 number est rejete (boolean strict)', () => {
    // @ts-expect-error boolean strict
    const bad: DrawerProps = { open: true, title: 'T', closeOnEscape: 1 };
    void bad;
  });

  it('description number est rejete (string requis)', () => {
    // @ts-expect-error string requis
    const bad: DrawerProps = { open: true, title: 'T', description: 123 };
    void bad;
  });

  it('showCloseButton null est rejete (boolean strict, pas null)', () => {
    // @ts-expect-error boolean strict, null non-autorise sur boolean optional
    const bad: DrawerProps = { open: true, title: 'T', showCloseButton: null };
    void bad;
  });

  it('DrawerProps minimal (open + title) compile', () => {
    const good: DrawerProps = { open: false, title: 'Panneau' };
    expectTypeOf(good).toMatchTypeOf<DrawerProps>();
  });

  it('closeLabel number est rejete (string requis — M-1 10.18 post-review)', () => {
    // @ts-expect-error string requis
    const bad: DrawerProps = { open: true, title: 'T', closeLabel: 123 };
    void bad;
  });

  it('closeLabel null est rejete (string strict, pas null)', () => {
    // @ts-expect-error string strict, null non-autorise
    const bad: DrawerProps = { open: true, title: 'T', closeLabel: null };
    void bad;
  });

  it('DrawerProps complet avec toutes les props compile', () => {
    const good: DrawerProps = {
      open: true,
      title: 'Sources',
      description: 'Citations RAG',
      side: 'right',
      size: 'md',
      trapFocus: false,
      closeOnEscape: true,
      closeOnOverlayClick: true,
      showCloseButton: true,
      closeLabel: 'Fermer le panneau des sources',
    };
    expectTypeOf(good).toMatchTypeOf<DrawerProps>();
  });
});
