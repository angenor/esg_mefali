import type { ParsedSegment, RichBlockType } from '~/types/richblocks'

const BLOCK_TYPES: ReadonlySet<string> = new Set([
  'chart', 'mermaid', 'table', 'gauge', 'progress', 'timeline',
])

// BUG-V3-001 : MiniMax double parfois l'appel `ask_interactive_question` en
// écrivant aussi les arguments JSON en texte. Le tool est bien appelé (SSE
// `interactive_question` émis, widget rendu via InteractiveQuestionHost) mais
// le JSON orphelin pollue la bulle. Ce filtre supprime ces JSON-fuites avant
// le rendu markdown.
//
// Garde-fous anti faux positif :
// - Le match doit être isolé : début de ligne + (fin de ligne OU fin texte).
//   Un contenu pédagogique dans un bloc de code ``` est préservé (traité en
//   amont par le parser code-block).
// - Les blocs triple-backticks (chart/mermaid/...) ne sont pas concernés —
//   ils sont traités plus bas par codeBlockRegex.
const WIDGET_JSON_LEAK_REGEX = /^\s*\{\s*"question_type"\s*:\s*"(?:qcu|qcm)(?:_justification)?"[\s\S]*?"options"\s*:\s*\[[\s\S]*?\]\s*\}\s*$/gm

function stripWidgetJsonLeak(text: string): string {
  return text.replace(WIDGET_JSON_LEAK_REGEX, '').trim()
}

/**
 * Parse le contenu d'un message en segments texte et blocs visuels.
 * Gère les blocs incomplets pendant le streaming.
 */
export function useMessageParser() {
  function pushText(segments: ParsedSegment[], raw: string): void {
    const cleaned = stripWidgetJsonLeak(raw)
    if (cleaned) {
      segments.push({ type: 'text', content: cleaned, isComplete: true })
    }
  }

  function parse(content: string): ParsedSegment[] {
    const segments: ParsedSegment[] = []
    const codeBlockRegex = /```(\w+)\n([\s\S]*?)(?:```|$)/g
    let lastIndex = 0
    let match: RegExpExecArray | null = null

    while ((match = codeBlockRegex.exec(content)) !== null) {
      const blockType = match[1] ?? ''
      const blockContent = match[2] ?? ''
      const fullMatch = match[0]

      // Texte avant le bloc
      if (match.index > lastIndex) {
        pushText(segments, content.slice(lastIndex, match.index))
      }

      if (BLOCK_TYPES.has(blockType)) {
        // Verifier si le bloc est complet (se termine par ```)
        const isComplete = fullMatch.endsWith('```')
        segments.push({
          type: blockType as RichBlockType,
          content: blockContent.trim(),
          isComplete,
        })
      } else {
        // Bloc de code standard (non visuel) — traiter comme texte
        pushText(segments, fullMatch)
      }

      lastIndex = match.index + fullMatch.length
    }

    // Texte apres le dernier bloc
    if (lastIndex < content.length) {
      const remaining = content.slice(lastIndex)
      // Verifier s'il y a un bloc incomplet en cours (ouvert sans fermeture)
      const incompleteMatch = remaining.match(/```(\w+)\n?([\s\S]*)$/)
      if (incompleteMatch && incompleteMatch[1] && BLOCK_TYPES.has(incompleteMatch[1])) {
        // Texte avant le bloc incomplet
        pushText(segments, remaining.slice(0, incompleteMatch.index))
        segments.push({
          type: incompleteMatch[1] as RichBlockType,
          content: (incompleteMatch[2] || '').trim(),
          isComplete: false,
        })
      } else {
        pushText(segments, remaining)
      }
    }

    // Si aucun segment, retourner le contenu brut (toujours filtré BUG-V3-001)
    if (segments.length === 0) {
      pushText(segments, content)
    }

    return segments
  }

  return { parse }
}
