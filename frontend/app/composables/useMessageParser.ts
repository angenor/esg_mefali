import type { ParsedSegment, RichBlockType } from '~/types/richblocks'

const BLOCK_TYPES: ReadonlySet<string> = new Set([
  'chart', 'mermaid', 'table', 'gauge', 'progress', 'timeline',
])

/**
 * Parse le contenu d'un message en segments texte et blocs visuels.
 * Gère les blocs incomplets pendant le streaming.
 */
export function useMessageParser() {
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
        const textBefore = content.slice(lastIndex, match.index)
        if (textBefore.trim()) {
          segments.push({ type: 'text', content: textBefore, isComplete: true })
        }
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
        segments.push({ type: 'text', content: fullMatch, isComplete: true })
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
        const textBefore = remaining.slice(0, incompleteMatch.index)
        if (textBefore.trim()) {
          segments.push({ type: 'text', content: textBefore, isComplete: true })
        }
        segments.push({
          type: incompleteMatch[1] as RichBlockType,
          content: (incompleteMatch[2] || '').trim(),
          isComplete: false,
        })
      } else if (remaining.trim()) {
        segments.push({ type: 'text', content: remaining, isComplete: true })
      }
    }

    // Si aucun segment, retourner le contenu brut
    if (segments.length === 0 && content.trim()) {
      segments.push({ type: 'text', content, isComplete: true })
    }

    return segments
  }

  return { parse }
}
