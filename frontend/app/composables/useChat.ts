import { ref } from 'vue'
import type { Conversation, Message, PaginatedResponse } from '~/types'
import { useAuthStore } from '~/stores/auth'

export function useChat() {
  const config = useRuntimeConfig()
  const authStore = useAuthStore()
  const apiBase = config.public.apiBase

  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const messages = ref<Message[]>([])
  const isStreaming = ref(false)
  const streamingContent = ref('')
  const error = ref('')

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

  async function sendMessage(content: string): Promise<void> {
    if (!currentConversation.value) return

    error.value = ''
    isStreaming.value = true
    streamingContent.value = ''

    // Ajouter le message utilisateur localement
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }
    messages.value = [...messages.value, userMessage]

    try {
      const response = await fetch(
        `${apiBase}/chat/conversations/${currentConversation.value.id}/messages`,
        {
          method: 'POST',
          headers: getHeaders(),
          body: JSON.stringify({ content }),
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
            }

            if (event.type === 'token' && event.content) {
              streamingContent.value += event.content
              // Mettre à jour le dernier message assistant
              const lastIdx = messages.value.length - 1
              messages.value = messages.value.map((msg, idx) =>
                idx === lastIdx
                  ? { ...msg, content: streamingContent.value }
                  : msg,
              )
            } else if (event.type === 'done' && event.message_id) {
              // Mettre à jour l'ID du message avec l'ID persisté
              const lastIdx = messages.value.length - 1
              messages.value = messages.value.map((msg, idx) =>
                idx === lastIdx
                  ? { ...msg, id: event.message_id! }
                  : msg,
              )
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
    fetchConversations,
    createConversation,
    selectConversation,
    fetchMessages,
    sendMessage,
    deleteConversation,
    renameConversation,
  }
}
