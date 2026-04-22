/**
 * Helpers de types partages pour Storybook CSF 3.0.
 * Story 10.15 code-review MEDIUM-3 : factorisation du cast Storybook v8
 * + Vue SFC typed (DefineSetupFnComponent vs Meta<Args>['component'] = ConcreteComponent<any>).
 * Mutualiser ici evite de disseminer `as unknown as` dans chaque `*.stories.ts`.
 */
import type { Meta } from '@storybook/vue3';

/**
 * Cast d un composant Vue SFC vers le type `component` attendu par Meta<Args>.
 *
 * Storybook v8 declare `Meta<Args>['component']` comme `ConcreteComponent<Args>`
 * ou un type voisin incompatible avec la signature `DefineSetupFnComponent` exposee
 * par les SFC Vue 3 avec props discriminees. Le cast est inerte au runtime
 * (Storybook consomme le composant via render classique) mais reduit la surface
 * `as unknown as` a une seule fonction typee.
 *
 * Usage :
 *   const meta: Meta<ButtonStoryArgs> = {
 *     component: asStorybookComponent<ButtonStoryArgs>(Button),
 *     ...
 *   };
 *
 * A retirer quand Storybook 9 harmonise le typage (tracer dans codemap storybook.md
 * section Upgrade strategy).
 */
export function asStorybookComponent<TArgs>(
  component: unknown,
): Meta<TArgs>['component'] {
  return component as Meta<TArgs>['component'];
}
