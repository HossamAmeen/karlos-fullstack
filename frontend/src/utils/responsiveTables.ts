/**
 * On narrow screens every table is shown as a stack of cards. CSS needs a
 * `data-label` on each cell (taken from the matching header) and a `stack`
 * class on the table. Done globally so each view does not have to care.
 */
function apply(root: ParentNode) {
  root.querySelectorAll('table').forEach((table) => {
    if (table.closest('.print-area') || table.classList.contains('no-stack')) return
    const heads = Array.from(table.querySelectorAll('thead th')).map(
      (th) => th.textContent?.trim() ?? '',
    )
    if (!heads.length) return
    table.classList.add('stack')
    table.querySelectorAll('tbody tr, tfoot tr').forEach((tr) => {
      let col = 0
      Array.from(tr.children).forEach((cell) => {
        if (cell.tagName !== 'TD') return
        cell.setAttribute('data-label', heads[col] ?? '')
        col += Number(cell.getAttribute('colspan') || 1)
      })
    })
  })
}

export function watchTables() {
  let queued = false
  const run = () => {
    queued = false
    apply(document)
  }
  const observer = new MutationObserver(() => {
    if (queued) return
    queued = true
    requestAnimationFrame(run)
  })
  observer.observe(document.body, { childList: true, subtree: true, characterData: true })
  run()
  return () => observer.disconnect()
}
