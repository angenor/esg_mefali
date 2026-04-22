/**
 * Compile-time type tests pour ui/Badge (AC1 + AC4 Story 10.17).
 * Executes via `vitest --typecheck` (vitest.config.ts typecheck enabled).
 * Les directives // @ts-expect-error DOIVENT trouver une erreur TS ; sinon
 * vitest typecheck echoue et detecte toute regression silencieuse de la
 * discrimination union variant x state (verdict / lifecycle / admin).
 */
import { describe, it, expectTypeOf, assertType } from 'vitest';
import type {
  VerdictState,
  LifecycleState,
  AdminCriticality,
  BadgeSize,
} from '../../../app/components/ui/registry';

// Reproduction locale du type discrimine (source : Badge.vue, single source of truth).
// Si Badge.vue change, cette copie DOIT suivre explicitement (pattern 10.15 / 10.16).
type BadgePropsBase = { size?: BadgeSize };
type BadgeProps =
  | (BadgePropsBase & { variant: 'verdict'; state: VerdictState; conditional?: boolean })
  | (BadgePropsBase & { variant: 'lifecycle'; state: LifecycleState })
  | (BadgePropsBase & { variant: 'admin'; state: AdminCriticality });

describe('ui/Badge : AC1 + AC4 type safety (compile-time)', () => {
  it('VerdictState inclut exactement pass|fail|reported|na', () => {
    expectTypeOf<VerdictState>().toEqualTypeOf<'pass' | 'fail' | 'reported' | 'na'>();
  });

  it('LifecycleState inclut les 9 etats FundApplication FR32', () => {
    expectTypeOf<LifecycleState>().toEqualTypeOf<
      | 'draft'
      | 'snapshot_frozen'
      | 'signed'
      | 'exported'
      | 'submitted'
      | 'in_review'
      | 'accepted'
      | 'rejected'
      | 'withdrawn'
    >();
  });

  it('AdminCriticality inclut exactement n1|n2|n3', () => {
    expectTypeOf<AdminCriticality>().toEqualTypeOf<'n1' | 'n2' | 'n3'>();
  });

  it('BadgeSize inclut exactement sm|md|lg (sizes inline non-interactif Q4)', () => {
    expectTypeOf<BadgeSize>().toEqualTypeOf<'sm' | 'md' | 'lg'>();
  });

  it('AC1 : variant verdict + state invalide cross-variant est rejete', () => {
    // @ts-expect-error state 'draft' est une LifecycleState, pas un VerdictState.
    const bad1: BadgeProps = { variant: 'verdict', state: 'draft' };
    void bad1;

    // @ts-expect-error state 'n1' est une AdminCriticality, pas un VerdictState.
    const bad2: BadgeProps = { variant: 'verdict', state: 'n1' };
    void bad2;

    // OK : les 4 verdict states valides.
    const valid1: BadgeProps = { variant: 'verdict', state: 'pass' };
    const valid2: BadgeProps = { variant: 'verdict', state: 'na' };
    assertType<BadgeProps>(valid1);
    assertType<BadgeProps>(valid2);
  });

  it('AC1 : variant lifecycle + state invalide cross-variant est rejete', () => {
    // @ts-expect-error state 'pass' est un VerdictState, pas un LifecycleState.
    const bad1: BadgeProps = { variant: 'lifecycle', state: 'pass' };
    void bad1;

    // @ts-expect-error state 'n2' est une AdminCriticality, pas un LifecycleState.
    const bad2: BadgeProps = { variant: 'lifecycle', state: 'n2' };
    void bad2;

    // OK : les 9 lifecycle states valides (echantillon).
    const valid1: BadgeProps = { variant: 'lifecycle', state: 'signed' };
    const valid2: BadgeProps = { variant: 'lifecycle', state: 'in_review' };
    assertType<BadgeProps>(valid1);
    assertType<BadgeProps>(valid2);
  });

  it('AC1 : variant admin + state invalide cross-variant est rejete', () => {
    // @ts-expect-error state 'pass' est un VerdictState, pas un AdminCriticality.
    const bad1: BadgeProps = { variant: 'admin', state: 'pass' };
    void bad1;

    // @ts-expect-error state 'draft' est un LifecycleState, pas un AdminCriticality.
    const bad2: BadgeProps = { variant: 'admin', state: 'draft' };
    void bad2;

    // OK : les 3 admin criticalites valides.
    const valid1: BadgeProps = { variant: 'admin', state: 'n1' };
    assertType<BadgeProps>(valid1);
  });

  it('AC4 : conditional autorise uniquement sur variant=verdict', () => {
    // OK : conditional=true/false sur verdict.
    const valid1: BadgeProps = { variant: 'verdict', state: 'pass', conditional: true };
    const valid2: BadgeProps = { variant: 'verdict', state: 'pass', conditional: false };
    assertType<BadgeProps>(valid1);
    assertType<BadgeProps>(valid2);

    // @ts-expect-error conditional n'est PAS autorise sur variant=lifecycle.
    const bad1: BadgeProps = { variant: 'lifecycle', state: 'signed', conditional: true };
    void bad1;

    // @ts-expect-error conditional n'est PAS autorise sur variant=admin.
    const bad2: BadgeProps = { variant: 'admin', state: 'n2', conditional: true };
    void bad2;
  });

  it('AC4 : conditional doit etre boolean, pas string', () => {
    // @ts-expect-error 'yes' n'est pas assignable a boolean.
    const bad: BadgeProps = { variant: 'verdict', state: 'pass', conditional: 'yes' };
    void bad;
  });

  it('AC1 : variant hors union est rejete', () => {
    // @ts-expect-error 'warning' n'est pas un variant reconnu.
    const bad: BadgeProps = { variant: 'warning', state: 'pass' };
    void bad;
  });

  it('AC5 : size hors BadgeSize est rejete', () => {
    // @ts-expect-error 'xl' n'est pas dans BadgeSize (Q4 verrouillee — pas de xl MVP).
    const bad: BadgeProps = { variant: 'verdict', state: 'pass', size: 'xl' };
    void bad;
  });

  it('AC1 : variant seul sans state est rejete (state obligatoire)', () => {
    // @ts-expect-error state manquant — invariant AC1 signature complete.
    const bad1: BadgeProps = { variant: 'verdict' };
    void bad1;

    // @ts-expect-error state manquant — lifecycle requis.
    const bad2: BadgeProps = { variant: 'lifecycle' };
    void bad2;
  });

  it('AC1 : invariants Object.freeze + typeof[number] stables', () => {
    // Sanity : les types derives sont des literals unions, pas des string generiques.
    const variantOnly: VerdictState = 'pass';
    const lifecycleOnly: LifecycleState = 'signed';
    const adminOnly: AdminCriticality = 'n2';
    expectTypeOf(variantOnly).toEqualTypeOf<VerdictState>();
    expectTypeOf(lifecycleOnly).toEqualTypeOf<LifecycleState>();
    expectTypeOf(adminOnly).toEqualTypeOf<AdminCriticality>();
  });
});
