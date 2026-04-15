/**
 * Helpers pour simuler les reponses SSE du backend chat.
 *
 * Format reel observe dans `app/composables/useChat.ts` (lignes 303-514) :
 *   - Chaque event est une ligne `data: {json}\n\n`
 *   - `event.type` ∈ { 'token', 'done', 'interactive_question',
 *                      'interactive_question_resolved', 'guided_tour',
 *                      'profile_update', 'profile_completion',
 *                      'tool_call_start', 'tool_call_end', 'tool_call_error',
 *                      'document_upload', 'document_status', 'document_analysis',
 *                      'report_suggestion', 'error' }
 *
 * Note dev : la story mentionne des markers HTML `<!--SSE:{...}-->` — c'est
 * le format interne cote LLM/backend AVANT conversion en events SSE. Cote
 * frontend on ne voit QUE les events JSON via `data: ...`. Ces helpers
 * produisent donc le format cote frontend.
 */

export type SSEEventPayload =
  | { type: 'token'; content: string }
  | { type: 'done'; message_id: string }
  | {
      type: 'interactive_question'
      id: string
      conversation_id?: string
      question_type: 'qcu' | 'qcm' | 'qcu_justification' | 'qcm_justification'
      prompt: string
      options: Array<{ id: string; label: string; emoji?: string; description?: string }>
      min_selections?: number
      max_selections?: number
      requires_justification?: boolean
      justification_prompt?: string | null
      module?: string
      created_at?: string
    }
  | {
      type: 'guided_tour'
      tour_id: string
      context: Record<string, unknown>
    }
  | { type: 'error'; content: string }

/**
 * Date fixe utilisee pour tous les `created_at` des fixtures — garantit le
 * determinisme des assertions sur les composants qui rendent du temps relatif.
 */
export const FIXTURE_FROZEN_DATE = '2026-04-14T10:00:00.000Z'

/**
 * Convertit une sequence d'events en string SSE-compatible (UTF-8).
 * Chaque event prend une ligne `data: {json}\n\n` + separateur.
 */
export function sseEventsToString(events: SSEEventPayload[]): string {
  return events.map((evt) => `data: ${JSON.stringify(evt)}\n\n`).join('')
}

/**
 * Convertit un tableau de chunks (chaque chunk = une ou plusieurs lignes data:)
 * en Uint8Array unique pret a passer a `route.fulfill({ body })`.
 *
 * Playwright 1.49 accepte `body: Buffer | string` — on renvoie une string ici
 * pour simplifier (pas besoin de polyfill Buffer cote test, qui tourne en node).
 */
export function createSSEResponse(events: SSEEventPayload[]): {
  body: string
  headers: Record<string, string>
  contentType: string
} {
  return {
    body: sseEventsToString(events),
    headers: {
      'content-type': 'text/event-stream',
      'cache-control': 'no-cache',
      connection: 'keep-alive',
    },
    contentType: 'text/event-stream',
  }
}

// ── Helpers de haut niveau — scenarios pretes pour le parcours Fatou ──

/**
 * Scenario : assistant repond puis affiche un widget de consentement QCU
 * (Oui, montre-moi / Non merci). Matche le pattern 6.3 (consent widget guidage).
 */
export function sseAssistantMessageWithConsent(params: {
  questionId: string
  conversationId: string
  assistantText?: string
  consentPrompt?: string
  messageId: string
}): SSEEventPayload[] {
  const assistantText = params.assistantText
    ?? 'Je vais vous aider. Votre empreinte carbone est de 47.2 tCO2e, principalement liee au transport (62%).'
  const consentPrompt = params.consentPrompt
    ?? 'Voulez-vous voir vos resultats carbone detailles avec le plan de reduction ?'

  return [
    { type: 'token', content: assistantText },
    {
      type: 'interactive_question',
      id: params.questionId,
      conversation_id: params.conversationId,
      question_type: 'qcu',
      prompt: consentPrompt,
      options: [
        { id: 'yes', label: 'Oui, montre-moi' },
        { id: 'no', label: 'Non merci' },
      ],
      min_selections: 1,
      max_selections: 1,
      requires_justification: false,
      justification_prompt: null,
      module: 'chat',
      created_at: FIXTURE_FROZEN_DATE,
    },
    { type: 'done', message_id: params.messageId },
  ]
}

/**
 * Scenario : apres acceptation du consentement, le serveur emet un marker
 * guided_tour qui declenche useGuidedTour.startTour(tour_id, context).
 */
export function sseGuidedTourAcceptanceResponse(params: {
  tourId: string
  context: Record<string, unknown>
  assistantText?: string
  messageId: string
}): SSEEventPayload[] {
  const assistantText = params.assistantText
    ?? 'Parfait, je vous guide vers vos resultats carbone detailles.'

  return [
    { type: 'token', content: assistantText },
    {
      type: 'guided_tour',
      tour_id: params.tourId,
      context: params.context,
    },
    { type: 'done', message_id: params.messageId },
  ]
}

// ── Helpers story 8.2 — parcours Moussa (/financing) ──────────────────

/**
 * Scenario : assistant repond a une question contextuelle posee sur `/financing`
 * puis propose un guidage via widget QCU de consentement.
 *
 * Le contenu du token cite volontairement **4 fonds** (count) et les noms des
 * 3 premiers (GCF, BOAD, SUNREF) — les assertions AC3 sont des regex qui
 * tolerent l'une ou l'autre formulation. Si ce helper est renomme ou que le
 * contenu est modifie, **mettre a jour** les regex de `8-2-parcours-moussa.spec.ts`.
 */
export function sseAssistantMessageWithConsentOnFinancing(params: {
  questionId: string
  conversationId: string
  messageId: string
  matchesCount?: number
  topFundNames?: string[]
  consentPrompt?: string
}): SSEEventPayload[] {
  const matchesCount = params.matchesCount ?? 4
  const topFunds = params.topFundNames ?? ['GCF Agriculture Resilient', 'BOAD Ligne PME Verte', 'SUNREF Cacao Durable']
  const consentPrompt = params.consentPrompt
    ?? 'Voulez-vous que je vous guide dans le catalogue des fonds ?'
  const assistantText
    = `J'ai identifie ${matchesCount} fonds verts compatibles avec votre cooperative cacao en Cote d'Ivoire : `
      + `${topFunds.join(', ')} et d'autres options complementaires. `
      + 'Vous pouvez consulter le catalogue complet sur cette page /financing.'

  return [
    { type: 'token', content: assistantText },
    {
      type: 'interactive_question',
      id: params.questionId,
      conversation_id: params.conversationId,
      question_type: 'qcu',
      prompt: consentPrompt,
      options: [
        { id: 'yes', label: 'Oui, montre-moi' },
        { id: 'no', label: 'Non merci' },
      ],
      min_selections: 1,
      max_selections: 1,
      requires_justification: false,
      justification_prompt: null,
      module: 'financing',
      created_at: FIXTURE_FROZEN_DATE,
    },
    { type: 'done', message_id: params.messageId },
  ]
}

/**
 * Scenario : utilisateur REFUSE le guidage — le serveur emet UN seul token
 * d'accuse de reception, SANS marker `guided_tour` ni `interactive_question`.
 *
 * L'absence de relance automatique est volontaire : AC4 de la story 8.2
 * verifie que le chat reste fonctionnel et qu'aucun Driver.js ne demarre.
 */
export function sseRefusalAcknowledgement(params: {
  messageId: string
  assistantText?: string
}): SSEEventPayload[] {
  const assistantText = params.assistantText
    ?? 'Pas de souci, je reste a votre disposition. Si vous avez d\'autres questions, n\'hesitez pas.'

  return [
    { type: 'token', content: assistantText },
    { type: 'done', message_id: params.messageId },
  ]
}
