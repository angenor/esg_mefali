import type { TimelineBlockData } from '~/types/richblocks'

/**
 * Normalise un objet JSON brut en TimelineBlockData canonique.
 *
 * Accepte les variantes de cle pour la liste d'evenements :
 *   events (canonique), phases, items, steps
 *
 * Accepte les aliases de champs par evenement :
 *   date ← period, timeframe
 *   title ← name, label
 *   status ← state (defaut: "todo")
 *   description ← details, content
 */
export function normalizeTimeline(raw: unknown): TimelineBlockData | null {
  if (typeof raw !== 'object' || raw === null) {
    return null
  }

  const obj = raw as Record<string, unknown>

  // Resoudre la liste d'evenements avec priorite
  const eventList =
    obj.events ?? obj.phases ?? obj.items ?? obj.steps

  if (!Array.isArray(eventList) || eventList.length === 0) {
    return null
  }

  const events: TimelineBlockData['events'] = []

  for (const item of eventList) {
    if (typeof item !== 'object' || item === null) continue

    const entry = item as Record<string, unknown>

    const date = (entry.date ?? entry.period ?? entry.timeframe) as string | undefined
    const title = (entry.title ?? entry.name ?? entry.label) as string | undefined

    // Ignorer les evenements sans date ET sans titre
    if (!date && !title) continue

    const rawStatus = (entry.status ?? entry.state) as string | undefined
    const status = (['done', 'in_progress', 'todo'].includes(rawStatus ?? '')
      ? rawStatus
      : 'todo') as 'done' | 'in_progress' | 'todo'

    const description = (entry.description ?? entry.details ?? entry.content) as string | undefined

    events.push({
      date: date ?? '',
      title: title ?? '',
      status,
      ...(description ? { description } : {}),
    })
  }

  if (events.length === 0) {
    return null
  }

  return { events }
}
