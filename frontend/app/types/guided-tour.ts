// frontend/app/types/guided-tour.ts

/**
 * Types du systeme de guidage visuel (parcours guides Driver.js).
 * Consomme par lib/guided-tours/registry.ts et composables/useGuidedTour.ts.
 */

export interface GuidedTourPopover {
  title: string
  description: string
  side?: 'top' | 'bottom' | 'left' | 'right'
  countdown?: number
}

export interface GuidedTourStep {
  /** Route cible si l'etape necessite une navigation (ex: '/carbon/results') */
  route?: string
  /** Selecteur CSS — TOUJOURS au format [data-guide-target="xxx"] */
  selector: string
  /** Configuration du popover Driver.js */
  popover: GuidedTourPopover
}

export interface GuidedTourEntryStep {
  /** Selecteur de l'element sidebar a pointer avant navigation */
  selector: string
  /** Configuration du popover avec countdown optionnel */
  popover: GuidedTourPopover
  /** Route vers laquelle naviguer apres le countdown */
  targetRoute: string
}

export interface GuidedTourDefinition {
  /** Identifiant unique — convention show_[module]_[page] en snake_case */
  id: string
  /** Etapes du parcours dans l'ordre d'affichage */
  steps: GuidedTourStep[]
  /** Etape d'entree optionnelle pour les parcours multi-pages (navigation initiale) */
  entryStep?: GuidedTourEntryStep
}

/** Contexte dynamique envoye par le LLM pour personnaliser les textes */
export type TourContext = Record<string, unknown>

/** Etats de la machine a etats du parcours guide */
export type TourState =
  | 'idle'
  | 'loading'
  | 'ready'
  | 'navigating'
  | 'waiting_dom'
  | 'highlighting'
  | 'complete'
  | 'interrupted'
