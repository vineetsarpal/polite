import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/permissions/')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/permissions/"!</div>
}
