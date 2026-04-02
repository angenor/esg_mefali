import { describe, expect, it } from 'vitest'
import { useMessageParser } from '~/composables/useMessageParser'

const { parse } = useMessageParser()

// ── T016: Blocs incomplets post-streaming ─────────────────────────

describe('T016: Blocs incomplets rendent le contenu post-streaming', () => {
  it('un bloc gauge complet (avec ```) a isComplete=true', () => {
    const content = '```gauge\n{"value":72,"max":100,"label":"Score ESG"}\n```'
    const segments = parse(content)
    const gauge = segments.find(s => s.type === 'gauge')
    expect(gauge).toBeDefined()
    expect(gauge!.isComplete).toBe(true)
    expect(gauge!.content).toContain('"value":72')
  })

  it('un bloc gauge incomplet (sans ```) a isComplete=false mais contenu valide', () => {
    const content = '```gauge\n{"value":72,"max":100,"label":"Score ESG"}'
    const segments = parse(content)
    const gauge = segments.find(s => s.type === 'gauge')
    expect(gauge).toBeDefined()
    expect(gauge!.isComplete).toBe(false)
    // Le contenu JSON est quand même disponible pour un rendu fallback
    expect(gauge!.content).toContain('"value":72')
  })

  it('un bloc progress incomplet contient le JSON partiel', () => {
    const content = 'Voici le résultat :\n```progress\n{"items":[{"label":"E","value":65,"max":100}]}'
    const segments = parse(content)
    const progress = segments.find(s => s.type === 'progress')
    expect(progress).toBeDefined()
    expect(progress!.isComplete).toBe(false)
    expect(progress!.content).toContain('"items"')
  })
})
