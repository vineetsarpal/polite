import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Card, SimpleGrid, CloseButton, Dialog, Portal } from '@chakra-ui/react'
import { Link } from '@tanstack/react-router'
import { paths } from '@/types/openapi'
import { useApiClient, v1 } from '@/lib/apiClient'
import { Protect } from '@clerk/clerk-react'
import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'

export const Route = createFileRoute('/dashboard/policies/')({
  component: RouteComponent,
})

type Policy = paths["/api/v1/policies/{policy_id}"]["get"]["responses"]["200"]["content"]["application/json"]

function RouteComponent() {
  const api = useApiClient()
  const queryClient = useQueryClient()
  const [idToDelete, setIdToDelete] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery<Policy[]>({
    queryKey: ['policies'],
    queryFn: () => api.get<Policy[]>(v1('/policies')),
    staleTime: 5000,
  })

  const { mutate, isPending } = useMutation({
    mutationFn: (id: string) => api.del(v1(`/policies/${id}`)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] })
    },
  })

  const handleDeleteClick = (id: string) => {
    setIdToDelete(id)
  }

  const confirmDelete = () => {
    if (idToDelete) mutate(idToDelete)
  }

  if (isLoading) return <p>Loading</p>

  if (error) return <p>Error: {error.message}</p>

  return (
    <SimpleGrid columns={{ base: 1, sm: 2, md: 3, lg: 4 }} gap={10}>
      {data?.map((policy: Policy) => (
        <Card.Root key={policy.id}>
          <Link to="/dashboard/policies/$policyId" params={{ policyId: policy.id.toString() }}>
            <Card.Header>Policy ID: {policy.id}</Card.Header>
            <Card.Body>
              Sum Insured: {policy.sum_insured}
              <br />
              Net Premium: {policy.net_premium}
            </Card.Body>
          </Link>

          <Card.Footer>
            <Protect permission="org:policies:delete">
              <Dialog.Root role="alertdialog">
                <Dialog.Trigger asChild>
                  <Button variant="outline" size="sm" onClick={() => handleDeleteClick(policy.id.toString())}>
                    Delete
                  </Button>
                </Dialog.Trigger>
                <Portal>
                  <Dialog.Backdrop />
                  <Dialog.Positioner>
                    <Dialog.Content>
                      <Dialog.Header>
                        <Dialog.Title>Are you sure?</Dialog.Title>
                      </Dialog.Header>
                      <Dialog.Body>
                        <p>
                          This will permanently delete Policy ID: {policy.id}
                        </p>
                      </Dialog.Body>
                      <Dialog.Footer>
                        <Dialog.ActionTrigger asChild>
                          <Button variant="outline">Cancel</Button>
                        </Dialog.ActionTrigger>
                        <Button colorPalette="red" onClick={confirmDelete} loading={isPending}>Delete</Button>
                      </Dialog.Footer>
                      <Dialog.CloseTrigger asChild>
                        <CloseButton size="sm" />
                      </Dialog.CloseTrigger>
                    </Dialog.Content>
                  </Dialog.Positioner>
                </Portal>
              </Dialog.Root>
            </Protect>
          </Card.Footer>
        </Card.Root>
      ))}
    </SimpleGrid>
  )
}
