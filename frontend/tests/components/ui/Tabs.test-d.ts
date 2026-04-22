/**
 * Compile-time type tests pour ui/Tabs (AC7 Story 10.19).
 * Pattern byte-identique 10.15-10.18 HIGH-1 compile-time enforcement.
 */
import { describe, it, expectTypeOf } from 'vitest';
import type { Component } from 'vue';
import type {
  TabsActivationMode,
  TabsOrientation,
} from '../../../app/components/ui/registry';

// Signature publique reflet byte-identique de TabsProps (Tabs.vue).
// Declaree localement pour eviter import d'un .vue en typecheck.
interface TabItem {
  value: string;
  label: string;
  icon?: Component;
  disabled?: boolean;
}

interface TabsProps {
  modelValue: string;
  tabs: TabItem[];
  orientation?: TabsOrientation;
  activationMode?: TabsActivationMode;
  forceMount?: boolean;
  label?: string;
}

describe('ui/Tabs : AC7 type safety (compile-time)', () => {
  it("TabsOrientation inclut exactement 'horizontal' | 'vertical'", () => {
    expectTypeOf<TabsOrientation>().toEqualTypeOf<'horizontal' | 'vertical'>();
  });

  it("TabsActivationMode inclut exactement 'automatic' | 'manual'", () => {
    expectTypeOf<TabsActivationMode>().toEqualTypeOf<
      'automatic' | 'manual'
    >();
  });

  it('TabsProps minimal (modelValue + tabs) valide', () => {
    const ok: TabsProps = {
      modelValue: 't1',
      tabs: [{ value: 't1', label: 'Onglet 1' }],
    };
    void ok;
  });

  it("orientation: 'invalid' est rejete (hors union)", () => {
    // @ts-expect-error orientation hors union horizontal | vertical
    const bad: TabsProps = {
      modelValue: 't1',
      tabs: [],
      orientation: 'invalid',
    };
    void bad;
  });

  it("activationMode: 'hybrid' est rejete", () => {
    // @ts-expect-error activationMode hors union automatic | manual
    const bad: TabsProps = {
      modelValue: 't1',
      tabs: [],
      activationMode: 'hybrid',
    };
    void bad;
  });

  it('tabs sans value/label est rejete', () => {
    // @ts-expect-error tabs[0] manque value + label requis
    const bad: TabsProps = {
      modelValue: 't1',
      tabs: [{ foo: 'bar' }],
    };
    void bad;
  });

  it('modelValue: 42 est rejete (string requis)', () => {
    // @ts-expect-error modelValue doit etre string
    const bad: TabsProps = {
      modelValue: 42,
      tabs: [],
    };
    void bad;
  });

  it("forceMount: 'yes' est rejete (boolean strict)", () => {
    // @ts-expect-error forceMount doit etre boolean
    const bad: TabsProps = {
      modelValue: 't1',
      tabs: [],
      forceMount: 'yes',
    };
    void bad;
  });

  it("tabs[0].icon: 'string' est rejete (Component requis)", () => {
    // @ts-expect-error icon doit etre Component, pas string
    const bad: TabsProps = {
      modelValue: 't1',
      tabs: [{ value: 't1', label: 'O1', icon: 'ChevronDown' }],
    };
    void bad;
  });

  it('modelValue manquant est rejete (requis)', () => {
    // @ts-expect-error modelValue requis
    const bad: TabsProps = {
      tabs: [],
    };
    void bad;
  });
});
