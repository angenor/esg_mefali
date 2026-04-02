import { describe, expect, it } from 'vitest'
import { normalizeTimeline } from '~/utils/normalizeTimeline'

// ── T043: Parse correctement {"events": [...]} ─────────────────────────

describe('T043: Format canonique events', () => {
  it('parse un bloc timeline avec events', () => {
    const input = {
      events: [
        { date: 'Mois 1-2', title: 'Action 1', status: 'done', description: 'Detail' },
        { date: 'Mois 3-6', title: 'Action 2', status: 'in_progress' },
        { date: 'Mois 7-12', title: 'Action 3', status: 'todo' },
      ],
    }
    const result = normalizeTimeline(input)
    expect(result).not.toBeNull()
    expect(result!.events).toHaveLength(3)
    expect(result!.events[0]).toEqual({
      date: 'Mois 1-2',
      title: 'Action 1',
      status: 'done',
      description: 'Detail',
    })
    expect(result!.events[2].status).toBe('todo')
  })
})

// ── T044: Parse correctement {"phases": [...]} comme alias ──────────────

describe('T044: Alias phases', () => {
  it('parse un bloc timeline avec phases comme alias de events', () => {
    const input = {
      title: "Plan d'action 12 mois",
      phases: [
        { name: 'Court terme (0-3 mois)', actions: ['Action 1', 'Action 2'] },
        { name: 'Moyen terme (3-6 mois)', actions: ['Action 3'] },
        { name: 'Long terme (6-12 mois)', actions: ['Action 4'] },
      ],
    }
    const result = normalizeTimeline(input)
    expect(result).not.toBeNull()
    expect(result!.events).toHaveLength(3)
    // name → title
    expect(result!.events[0].title).toBe('Court terme (0-3 mois)')
    // Pas de date explicite → ''
    expect(result!.events[0].date).toBe('')
    // Pas de status → defaut 'todo'
    expect(result!.events[0].status).toBe('todo')
  })

  it('parse items comme alias de events', () => {
    const input = {
      items: [
        { date: 'Semaine 1-2', title: 'Preparation', description: 'Documents' },
        { date: 'Semaine 3-4', title: 'Montage', description: 'Dossier' },
      ],
    }
    const result = normalizeTimeline(input)
    expect(result).not.toBeNull()
    expect(result!.events).toHaveLength(2)
    expect(result!.events[0].title).toBe('Preparation')
  })

  it('parse steps comme alias de events', () => {
    const input = {
      steps: [
        { date: 'Etape 1', title: 'Demarrage', status: 'done' },
      ],
    }
    const result = normalizeTimeline(input)
    expect(result).not.toBeNull()
    expect(result!.events).toHaveLength(1)
  })
})

// ── T045: Parse les variantes de champs (period, name, state) ───────────

describe('T045: Aliases de champs', () => {
  it('period → date', () => {
    const input = {
      events: [{ period: 'Mois 1', title: 'Action', status: 'todo' }],
    }
    const result = normalizeTimeline(input)
    expect(result!.events[0].date).toBe('Mois 1')
  })

  it('timeframe → date', () => {
    const input = {
      events: [{ timeframe: '6 mois', title: 'Action', status: 'todo' }],
    }
    const result = normalizeTimeline(input)
    expect(result!.events[0].date).toBe('6 mois')
  })

  it('name → title', () => {
    const input = {
      events: [{ date: 'Mois 1', name: 'Mon action', status: 'done' }],
    }
    const result = normalizeTimeline(input)
    expect(result!.events[0].title).toBe('Mon action')
  })

  it('label → title', () => {
    const input = {
      events: [{ date: 'Mois 1', label: 'Mon action', status: 'done' }],
    }
    const result = normalizeTimeline(input)
    expect(result!.events[0].title).toBe('Mon action')
  })

  it('state → status', () => {
    const input = {
      events: [{ date: 'Mois 1', title: 'Action', state: 'in_progress' }],
    }
    const result = normalizeTimeline(input)
    expect(result!.events[0].status).toBe('in_progress')
  })

  it('details → description', () => {
    const input = {
      events: [{ date: 'Mois 1', title: 'Action', status: 'todo', details: 'Info' }],
    }
    const result = normalizeTimeline(input)
    expect(result!.events[0].description).toBe('Info')
  })

  it('content → description', () => {
    const input = {
      events: [{ date: 'Mois 1', title: 'Action', status: 'todo', content: 'Info' }],
    }
    const result = normalizeTimeline(input)
    expect(result!.events[0].description).toBe('Info')
  })
})

// ── T046: Affiche erreur quand ni events ni phases ──────────────────────

describe('T046: Pas de cle reconnue', () => {
  it('retourne null quand aucune cle reconnue', () => {
    const input = { data: [{ date: 'Mois 1', title: 'Action' }] }
    const result = normalizeTimeline(input)
    expect(result).toBeNull()
  })

  it('retourne null quand events est vide', () => {
    const input = { events: [] }
    const result = normalizeTimeline(input)
    expect(result).toBeNull()
  })

  it('retourne null pour un objet vide', () => {
    const result = normalizeTimeline({})
    expect(result).toBeNull()
  })
})

// ── T047: Utilise "todo" par defaut quand status absent ─────────────────

describe('T047: Status par defaut', () => {
  it('status absent → todo', () => {
    const input = {
      events: [{ date: 'Mois 1', title: 'Action' }],
    }
    const result = normalizeTimeline(input)
    expect(result!.events[0].status).toBe('todo')
  })

  it('status invalide → todo', () => {
    const input = {
      events: [{ date: 'Mois 1', title: 'Action', status: 'unknown_status' }],
    }
    const result = normalizeTimeline(input)
    expect(result!.events[0].status).toBe('todo')
  })
})

// ── T048: Gere le JSON invalide sans crash ──────────────────────────────

describe('T048: Entrees invalides', () => {
  it('retourne null pour null', () => {
    const result = normalizeTimeline(null)
    expect(result).toBeNull()
  })

  it('retourne null pour une string', () => {
    const result = normalizeTimeline('not an object')
    expect(result).toBeNull()
  })

  it('retourne null pour un nombre', () => {
    const result = normalizeTimeline(42)
    expect(result).toBeNull()
  })

  it('ignore les evenements sans date ni titre', () => {
    const input = {
      events: [
        { status: 'done' }, // Pas de date ni titre → ignore
        { date: 'Mois 1', title: 'Action', status: 'todo' },
      ],
    }
    const result = normalizeTimeline(input)
    expect(result!.events).toHaveLength(1)
    expect(result!.events[0].title).toBe('Action')
  })

  it('ignore les entrees non-objet dans events', () => {
    const input = {
      events: [
        'not an object',
        null,
        { date: 'Mois 1', title: 'Action' },
      ],
    }
    const result = normalizeTimeline(input)
    expect(result!.events).toHaveLength(1)
  })
})
