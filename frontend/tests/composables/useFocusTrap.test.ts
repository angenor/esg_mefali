import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useFocusTrap } from '~/composables/useFocusTrap'

// Helper : creer un conteneur avec des elements focusables
function createContainer(...buttonLabels: string[]): HTMLDivElement {
  const container = document.createElement('div')
  for (const label of buttonLabels) {
    const btn = document.createElement('button')
    btn.textContent = label
    container.appendChild(btn)
  }
  document.body.appendChild(container)
  return container
}

describe('useFocusTrap', () => {
  let container: HTMLDivElement

  afterEach(() => {
    document.body.innerHTML = ''
  })

  describe('Tab cycle les elements focusables', () => {
    it('Tab sur le dernier element revient au premier', async () => {
      container = createContainer('Btn1', 'Btn2', 'Btn3')
      const containerRef = ref<HTMLElement | null>(container)
      const { activate, deactivate } = useFocusTrap(containerRef)

      activate()
      await nextTick()

      const buttons = container.querySelectorAll('button')
      // Le focus est sur le premier element apres activation
      expect(document.activeElement).toBe(buttons[0])

      // Placer le focus sur le dernier
      buttons[2].focus()
      expect(document.activeElement).toBe(buttons[2])

      // Tab sur le dernier → doit revenir au premier
      const event = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })
      Object.defineProperty(event, 'shiftKey', { value: false })
      const preventDefaultSpy = vi.spyOn(event, 'preventDefault')
      document.dispatchEvent(event)

      expect(preventDefaultSpy).toHaveBeenCalled()
      expect(document.activeElement).toBe(buttons[0])

      deactivate()
    })

    it('Shift+Tab sur le premier element va au dernier', async () => {
      container = createContainer('Btn1', 'Btn2', 'Btn3')
      const containerRef = ref<HTMLElement | null>(container)
      const { activate, deactivate } = useFocusTrap(containerRef)

      activate()
      await nextTick()

      const buttons = container.querySelectorAll('button')
      // Focus est sur le premier (activation)
      expect(document.activeElement).toBe(buttons[0])

      // Shift+Tab sur le premier → doit aller au dernier
      const event = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, shiftKey: true })
      const preventDefaultSpy = vi.spyOn(event, 'preventDefault')
      document.dispatchEvent(event)

      expect(preventDefaultSpy).toHaveBeenCalled()
      expect(document.activeElement).toBe(buttons[2])

      deactivate()
    })
  })

  describe('elements focusables recalcules dynamiquement', () => {
    it('detecte un nouveau bouton ajoute pendant que le trap est actif', async () => {
      container = createContainer('Btn1', 'Btn2')
      const containerRef = ref<HTMLElement | null>(container)
      const { activate, deactivate } = useFocusTrap(containerRef)

      activate()
      await nextTick()

      // Ajouter un nouveau bouton
      const newBtn = document.createElement('button')
      newBtn.textContent = 'Btn3'
      container.appendChild(newBtn)

      // Placer le focus sur le nouveau dernier element
      newBtn.focus()
      expect(document.activeElement).toBe(newBtn)

      // Tab sur le nouveau dernier → doit revenir au premier
      const event = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })
      Object.defineProperty(event, 'shiftKey', { value: false })
      const preventDefaultSpy = vi.spyOn(event, 'preventDefault')
      document.dispatchEvent(event)

      expect(preventDefaultSpy).toHaveBeenCalled()
      const buttons = container.querySelectorAll('button')
      expect(document.activeElement).toBe(buttons[0])

      deactivate()
    })

    it('detecte un bouton supprime pendant que le trap est actif', async () => {
      container = createContainer('Btn1', 'Btn2', 'Btn3')
      const containerRef = ref<HTMLElement | null>(container)
      const { activate, deactivate } = useFocusTrap(containerRef)

      activate()
      await nextTick()

      // Supprimer le dernier bouton
      const buttons = container.querySelectorAll('button')
      container.removeChild(buttons[2])

      // Placer le focus sur le nouveau dernier (Btn2)
      buttons[1].focus()
      expect(document.activeElement).toBe(buttons[1])

      // Tab → doit revenir au premier
      const event = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })
      Object.defineProperty(event, 'shiftKey', { value: false })
      const preventDefaultSpy = vi.spyOn(event, 'preventDefault')
      document.dispatchEvent(event)

      expect(preventDefaultSpy).toHaveBeenCalled()
      expect(document.activeElement).toBe(buttons[0])

      deactivate()
    })
  })

  describe('activation et desactivation', () => {
    it('activate met isActive a true et focus le premier element', async () => {
      container = createContainer('Btn1')
      const containerRef = ref<HTMLElement | null>(container)
      const { activate, deactivate, isActive } = useFocusTrap(containerRef)

      expect(isActive.value).toBe(false)

      activate()
      await nextTick()

      expect(isActive.value).toBe(true)
      expect(document.activeElement).toBe(container.querySelector('button'))

      deactivate()
    })

    it('deactivate met isActive a false et ne piege plus le focus', async () => {
      container = createContainer('Btn1', 'Btn2')
      const containerRef = ref<HTMLElement | null>(container)
      const { activate, deactivate, isActive } = useFocusTrap(containerRef)

      activate()
      await nextTick()
      deactivate()

      expect(isActive.value).toBe(false)

      // Tab ne devrait plus etre piege
      const buttons = container.querySelectorAll('button')
      buttons[1].focus()
      const event = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })
      const preventDefaultSpy = vi.spyOn(event, 'preventDefault')
      document.dispatchEvent(event)

      // preventDefault ne devrait PAS etre appele — le trap est desactive
      expect(preventDefaultSpy).not.toHaveBeenCalled()
    })

    it('ne fait rien si containerRef est null', async () => {
      const containerRef = ref<HTMLElement | null>(null)
      const { activate, deactivate } = useFocusTrap(containerRef)

      // Ne doit pas planter
      activate()
      await nextTick()
      deactivate()
    })
  })

  describe('ignore les touches non-Tab', () => {
    it('ne piege pas Enter ou Space', async () => {
      container = createContainer('Btn1', 'Btn2')
      const containerRef = ref<HTMLElement | null>(container)
      const { activate, deactivate } = useFocusTrap(containerRef)

      activate()
      await nextTick()

      const event = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true })
      const preventDefaultSpy = vi.spyOn(event, 'preventDefault')
      document.dispatchEvent(event)

      expect(preventDefaultSpy).not.toHaveBeenCalled()

      deactivate()
    })
  })
})
