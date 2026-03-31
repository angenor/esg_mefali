import { ref } from 'vue'
import type { Conversation, Message, PaginatedResponse } from '~/types'
import type { ProfileUpdateEvent, CompletionResponse } from '~/types/company'
import { useAuthStore } from '~/stores/auth'
import { useCompanyStore } from '~/stores/company'

export function useChat() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const companyStore = useCompanyStore()
  const apiBase = config.public.apiBase

  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const messages = ref<Message[]>([])
  const isStreaming = ref(false)
  const streamingContent = ref('')
  const error = ref('')
  const documentProgress = ref<{
    documentId: string
    filename: string
    status: 'uploaded' | 'extracting' | 'analyzing' | 'done' | 'error'
  } | null>(null)
  const reportSuggestion = ref<{
    assessmentId: string
    message: string
  } | null>(null)

  function getHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      ...(authStore.accessToken
        ? { Authorization: `Bearer ${authStore.accessToken}` }
        : {}),
    }
  }

  async function fetchConversations(): Promise<void> {
    const response = await fetch(`${apiBase}/chat/conversations`, {
      headers: getHeaders(),
    })
    if (!response.ok) throw new Error('Erreur lors du chargement des conversations')
    const data: PaginatedResponse<Conversation> = await response.json()
    conversations.value = data.items
  }

  async function createConversation(title?: string): Promise<Conversation> {
    const response = await fetch(`${apiBase}/chat/conversations`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(title ? { title } : {}),
    })
    if (!response.ok) throw new Error('Erreur lors de la création de la conversation')
    const conversation: Conversation = await response.json()
    conversations.value = [conversation, ...conversations.value]
    return conversation
  }

  async function selectConversation(conversation: Conversation): Promise<void> {
    currentConversation.value = conversation
    await fetchMessages(conversation.id)
  }

  async function fetchMessages(conversationId: string): Promise<void> {
    const response = await fetch(
      `${apiBase}/chat/conversations/${conversationId}/messages`,
      { headers: getHeaders() },
    )
    if (!response.ok) throw new Error('Erreur lors du chargement des messages')
    const data: PaginatedResponse<Message> = await response.json()
    messages.value = data.items
  }

  async function sendMessage(content: string, file?: File): Promise<void> {
    if (!currentConversation.value) return

    error.value = ''
    isStreaming.value = true
    streamingContent.value = ''
    documentProgress.value = null

    // Ajouter le message utilisateur localement
    const displayContent = file
      ? `${content || 'Analyse ce document'}\n📎 ${file.name}`
      : content
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: displayContent,
      created_at: new Date().toISOString(),
    }
    messages.value = [...messages.value, userMessage]

    try {
      // Construire la requete : multipart si fichier, sinon Form data
      const formData = new FormData()
      formData.append('content', content || (file ? `Analyse ce document : ${file.name}` : ''))
      if (file) {
        formData.append('file', file)
      }

      const headers: Record<string, string> = {}
      if (authStore.accessToken) {
        headers.Authorization = `Bearer ${authStore.accessToken}`
      }

      const response = await fetch(
        `${apiBase}/chat/conversations/${currentConversation.value.id}/messages`,
        {
          method: 'POST',
          headers,
          body: formData,
        },
      )

      if (!response.ok) {
        throw new Error('Erreur lors de l\'envoi du message')
      }

      // Lire le flux SSE
      const reader = response.body!.getReader()
      const decoder = new TextDecoder()

      // Ajouter un message assistant vide pour le streaming
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: '',
        created_at: new Date().toISOString(),
      }
      messages.value = [...messages.value, assistantMessage]

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const jsonStr = line.slice(6)

          try {
            const event = JSON.parse(jsonStr) as {
              type: string
              content?: string
              message_id?: string
              field?: string
              value?: string | number | boolean
              label?: string
              identity_completion?: number
              esg_completion?: number
              overall_completion?: number
              document_id?: string
              filename?: string
              status?: string
              summary?: string
              document_type?: string
              assessment_id?: string
            }

            if (event.type === 'token' && event.content) {
              streamingContent.value += event.content
              // Mettre a jour le dernier message assistant
              const lastIdx = messages.value.length - 1
              messages.value = messages.value.map((msg, idx) =>
                idx === lastIdx
                  ? { ...msg, content: streamingContent.value }
                  : msg,
              )
            } else if (event.type === 'done' && event.message_id) {
              // Mettre a jour l'ID du message avec l'ID persiste
              const lastIdx = messages.value.length - 1
              messages.value = messages.value.map((msg, idx) =>
                idx === lastIdx
                  ? { ...msg, id: event.message_id! }
                  : msg,
              )
              documentProgress.value = null
            } else if (event.type === 'document_upload') {
              // Document recu
              documentProgress.value = {
                documentId: event.document_id!,
                filename: event.filename!,
                status: 'uploaded',
              }
            } else if (event.type === 'document_status') {
              // Progression document
              if (documentProgress.value) {
                documentProgress.value = {
                  ...documentProgress.value,
                  status: event.status as 'extracting' | 'analyzing' | 'error',
                }
              }
            } else if (event.type === 'document_analysis') {
              // Analyse terminee
              if (documentProgress.value) {
                documentProgress.value = {
                  ...documentProgress.value,
                  status: 'done',
                }
              }
            } else if (event.type === 'profile_update' && event.field) {
              // Mise a jour du profil extraite du chat
              const update: ProfileUpdateEvent = {
                field: event.field,
                value: event.value!,
                label: event.label || event.field,
              }
              companyStore.addProfileUpdate(update)
              companyStore.updateProfileField(event.field, event.value)
            } else if (event.type === 'profile_completion') {
              // Mise a jour de la completion
              companyStore.setCompletion({
                identity_completion: event.identity_completion!,
                esg_completion: event.esg_completion!,
                overall_completion: event.overall_completion!,
                identity_fields: { filled: [], missing: [] },
                esg_fields: { filled: [], missing: [] },
              })
            } else if (event.type === 'report_suggestion' && event.assessment_id) {
              reportSuggestion.value = {
                assessmentId: event.assessment_id,
                message: event.message || 'Votre evaluation ESG est terminee ! Generez un rapport PDF.',
              }
            } else if (event.type === 'error') {
              error.value = event.content || 'Erreur du service IA'
            }
          } catch {
            // Ignorer les lignes qui ne sont pas du JSON valide
          }
        }
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Erreur inconnue'
    } finally {
      isStreaming.value = false
      streamingContent.value = ''
    }
  }

  async function deleteConversation(conversationId: string): Promise<void> {
    const response = await fetch(
      `${apiBase}/chat/conversations/${conversationId}`,
      { method: 'DELETE', headers: getHeaders() },
    )
    if (!response.ok) throw new Error('Erreur lors de la suppression')
    conversations.value = conversations.value.filter(c => c.id !== conversationId)
    if (currentConversation.value?.id === conversationId) {
      currentConversation.value = null
      messages.value = []
    }
  }

  async function renameConversation(conversationId: string, title: string): Promise<void> {
    const response = await fetch(
      `${apiBase}/chat/conversations/${conversationId}`,
      {
        method: 'PATCH',
        headers: getHeaders(),
        body: JSON.stringify({ title }),
      },
    )
    if (response.status === 429) {
      error.value = 'Trop de requêtes. Veuillez patienter quelques instants.'
      return
    }
    if (!response.ok) throw new Error('Erreur lors du renommage')
    const updated: Conversation = await response.json()
    conversations.value = conversations.value.map(c =>
      c.id === conversationId ? updated : c,
    )
    if (currentConversation.value?.id === conversationId) {
      currentConversation.value = updated
    }
  }

  const searchQuery = ref('')

  const filteredConversations = computed(() => {
    const query = searchQuery.value.trim().toLowerCase()
    if (!query) return conversations.value
    return conversations.value.filter(c =>
      c.title.toLowerCase().includes(query),
    )
  })

  return {
    conversations,
    currentConversation,
    messages,
    isStreaming,
    streamingContent,
    error,
    searchQuery,
    filteredConversations,
    documentProgress,
    reportSuggestion,
    fetchConversations,
    createConversation,
    selectConversation,
    fetchMessages,
    sendMessage,
    deleteConversation,
    renameConversation,
  }
}
