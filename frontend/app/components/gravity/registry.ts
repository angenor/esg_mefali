/**
 * Registre central des composants a gravite juridique/emotionnelle maximale.
 * Pattern CCC-9 frozen tuple (heritage Story 10.8+10.10+10.11+10.12+10.13).
 * Source unique pour : tests comptage, docs storybook.md, Storybook toolbar.
 * Invariant : GRAVITY_COMPONENT_REGISTRY.length === 6 (test enforcement).
 */

export interface GravityComponentEntry {
  readonly name: string;
  readonly fr: string;
  readonly states: readonly string[];
}

export const GRAVITY_COMPONENT_REGISTRY = Object.freeze([
  Object.freeze({
    name: 'SignatureModal',
    fr: 'FR40',
    states: Object.freeze(['initial', 'ready', 'signing', 'signed', 'error']),
  }),
  Object.freeze({
    name: 'SourceCitationDrawer',
    fr: 'FR71',
    states: Object.freeze(['closed', 'opening', 'open', 'loading', 'error', 'closing']),
  }),
  Object.freeze({
    name: 'ReferentialComparisonView',
    fr: 'FR26',
    states: Object.freeze(['loading', 'loaded', 'partial', 'error']),
  }),
  Object.freeze({
    name: 'ImpactProjectionPanel',
    fr: 'Q11+Q14',
    states: Object.freeze(['computing', 'computed-safe', 'computed-blocked', 'published']),
  }),
  Object.freeze({
    name: 'SectionReviewCheckpoint',
    fr: 'FR41',
    states: Object.freeze(['locked', 'in-progress', 'all-reviewed', 'exporting', 'exported']),
  }),
  Object.freeze({
    name: 'SgesBetaBanner',
    fr: 'FR44',
    states: Object.freeze([
      'beta-pending-review',
      'beta-review-requested',
      'beta-review-validated',
      'beta-review-rejected',
      'post-beta-ga',
    ]),
  }),
] as const) satisfies readonly GravityComponentEntry[];

export type GravityComponentName =
  (typeof GRAVITY_COMPONENT_REGISTRY)[number]['name'];
