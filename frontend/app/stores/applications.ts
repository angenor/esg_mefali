import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface SectionsProgress {
  total: number
  generated: number
  validated: number
}

export interface ApplicationSummary {
  id: string
  fund_name: string
  intermediary_name: string | null
  target_type: string
  status: string
  status_label: string
  sections_progress: SectionsProgress
  created_at: string
  updated_at: string
}

export interface FundInfo {
  id: string
  name: string
  organization: string
}

export interface IntermediaryInfo {
  id: string
  name: string
  contact_email: string | null
  contact_phone: string | null
  physical_address: string | null
}

export interface SectionData {
  title: string
  content: string | null
  status: string
  updated_at: string | null
}

export interface ChecklistItem {
  key: string
  name: string
  status: string
  document_id: string | null
  required_by: string
}

export interface ApplicationDetail {
  id: string
  fund: FundInfo
  intermediary: IntermediaryInfo | null
  match: { id: string; compatibility_score: number } | null
  target_type: string
  status: string
  status_label: string
  sections: Record<string, SectionData>
  checklist: ChecklistItem[]
  intermediary_prep: Record<string, unknown> | null
  simulation: Record<string, unknown> | null
  created_at: string
  updated_at: string
  submitted_at: string | null
}

export const useApplicationsStore = defineStore('applications', () => {
  const applications = ref<ApplicationSummary[]>([])
  const applicationsTotal = ref(0)
  const currentApplication = ref<ApplicationDetail | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const activeTab = ref<string>('sections')

  const hasApplications = computed(() => applications.value.length > 0)

  function setApplications(data: ApplicationSummary[], total: number) {
    applications.value = data
    applicationsTotal.value = total
  }

  function setCurrentApplication(data: ApplicationDetail | null) {
    currentApplication.value = data
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  function setError(value: string | null) {
    error.value = value
  }

  function setActiveTab(tab: string) {
    activeTab.value = tab
  }

  function updateSection(sectionKey: string, data: Partial<SectionData>) {
    if (currentApplication.value && currentApplication.value.sections[sectionKey]) {
      currentApplication.value = {
        ...currentApplication.value,
        sections: {
          ...currentApplication.value.sections,
          [sectionKey]: {
            ...currentApplication.value.sections[sectionKey],
            ...data,
          },
        },
      }
    }
  }

  function reset() {
    applications.value = []
    applicationsTotal.value = 0
    currentApplication.value = null
    loading.value = false
    error.value = null
    activeTab.value = 'sections'
  }

  return {
    applications,
    applicationsTotal,
    currentApplication,
    loading,
    error,
    activeTab,
    hasApplications,
    setApplications,
    setCurrentApplication,
    setLoading,
    setError,
    setActiveTab,
    updateSection,
    reset,
  }
})
