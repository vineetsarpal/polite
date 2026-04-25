import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/dashboard/policies/update')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/policies/update"!</div>
}
