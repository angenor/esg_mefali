// Types des blocs visuels (Rich Blocks) pour le rendu dans le chat

export interface ChartBlockData {
  type: 'bar' | 'line' | 'pie' | 'doughnut' | 'radar' | 'polarArea'
  data: {
    labels: string[]
    datasets: Array<{
      label: string
      data: number[]
      backgroundColor?: string | string[]
      borderColor?: string | string[]
      [key: string]: unknown
    }>
  }
  options?: Record<string, unknown>
}

export interface TableBlockData {
  headers: string[]
  rows: Array<Array<string | number>>
  highlightColumn?: number
  sortable?: boolean
}

export interface GaugeBlockData {
  value: number
  max: number
  label: string
  thresholds: Array<{ limit: number; color: string }>
  unit?: string
}

export interface ProgressBlockData {
  items: Array<{
    label: string
    value: number
    max: number
    color?: string
  }>
}

export interface TimelineBlockData {
  events: Array<{
    date: string
    title: string
    status: 'done' | 'in_progress' | 'todo'
    description?: string
  }>
}

export type RichBlockType = 'chart' | 'mermaid' | 'table' | 'gauge' | 'progress' | 'timeline'

export interface ParsedSegment {
  type: 'text' | RichBlockType
  content: string
  isComplete: boolean
}
