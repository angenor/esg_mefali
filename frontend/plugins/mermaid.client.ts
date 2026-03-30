import mermaid from 'mermaid'

export default defineNuxtPlugin(() => {
  mermaid.initialize({
    startOnLoad: false,
    theme: 'default',
  })

  return {
    provide: {
      mermaid,
    },
  }
})
