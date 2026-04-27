import { useApiClient, v1 } from '@/lib/apiClient'
import { paths } from '@/types/openapi'
import { Button, Card, CloseButton, Dialog, Portal, SimpleGrid } from '@chakra-ui/react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createFileRoute, Link } from '@tanstack/react-router'
import { Protect } from '@clerk/clerk-react'
import { useState } from 'react'

export const Route = createFileRoute('/dashboard/contacts/')({
  component: RouteComponent,
})

type Contact = paths["/api/v1/contacts/{contact_id}"]["get"]["responses"]["200"]["content"]["application/json"]

function RouteComponent() {
  const api = useApiClient()
  const queryClient = useQueryClient()
  const [idToDelete, setIdToDelete] = useState<string | null>(null)

  const { data, isLoading, error } = useQuery<Contact[]>({
    queryKey: ['contacts'],
    queryFn: () => api.get<Contact[]>(v1('/contacts')),
  })

  const { mutate, isPending } = useMutation({
    mutationFn: (id: string) => api.del(v1(`/contacts/${id}`)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts'] })
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
      {data?.map((contact: Contact) => (
        <Card.Root key={contact.id}>
          <Link to="/dashboard/contacts/$contactId" params={{ contactId: contact.id.toString() }}>
            <Card.Header>{contact.first_name} {contact.last_name}</Card.Header>
            <Card.Body>
              Type: {contact.type}
            </Card.Body>
          </Link>

          <Card.Footer>
            <Protect permission="org:contacts:delete">
              <Dialog.Root role="alertdialog">
                <Dialog.Trigger asChild>
                  <Button variant="outline" size="sm" onClick={() => handleDeleteClick(contact.id.toString())}>
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
                          This will permanently delete Contact ID: {contact.id}
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
