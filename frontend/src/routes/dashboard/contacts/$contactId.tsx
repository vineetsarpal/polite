import { Button, Field, Flex, HStack, Input, SimpleGrid } from '@chakra-ui/react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { paths } from '@/types/openapi'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useApiClient, v1 } from '@/lib/apiClient'
import { Protect } from '@clerk/clerk-react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'

export const Route = createFileRoute('/dashboard/contacts/$contactId')({
  component: RouteComponent,
})

type Contact = paths["/api/v1/contacts/{contact_id}"]["get"]["responses"]["200"]["content"]["application/json"]
type UpdatePayload = paths["/api/v1/contacts/{contact_id}"]["put"]["requestBody"]["content"]["application/json"]

function RouteComponent() {
  const api = useApiClient()
  const [editMode, setEditMode] = useState(false)
  const { contactId } = Route.useParams()
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery<Contact>({
    queryKey: ['contacts', contactId],
    queryFn: () => api.get<Contact>(v1(`/contacts/${contactId}`)),
  })

  const { register, handleSubmit, reset } = useForm<UpdatePayload>({
    defaultValues: data,
  })

  useEffect(() => {
    reset(data)
  }, [data, reset])

  const { mutate } = useMutation({
    mutationFn: (formData: UpdatePayload) =>
      api.put<Contact>(v1(`/contacts/${contactId}`), formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contacts', contactId] })
      navigate({ to: `/dashboard/contacts/${contactId}` })
      setEditMode(false)
    },
  })

  const onSubmit = (formData: UpdatePayload) => {
    mutate(formData)
  }

  if (isLoading || !data) return <p>Loading...</p>

  if (error) return <p>Error: {error.message}</p>

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <SimpleGrid columns={{ base: 1, sm: 2, md: 3, lg: 4 }} gap={4}>
        <Field.Root>
          <Field.Label>First Name</Field.Label>
          <Input {...register('first_name')} disabled={!editMode} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Last Name</Field.Label>
          <Input {...register('last_name')} disabled={!editMode} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Type</Field.Label>
          <Input {...register('type')} disabled={true} />
        </Field.Root>
        <Field.Root>
          <Field.Label>DOB</Field.Label>
          <Input {...register('dob')} disabled={!editMode} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Email</Field.Label>
          <Input {...register('email')} disabled={!editMode} />
        </Field.Root>
      </SimpleGrid>

      <Flex justifyContent="center" mt={6}>
        {editMode ? (
          <Protect permission="org:contacts:update">
            <HStack justify="flex-end">
              <Button type="submit" colorScheme="blue">Save</Button>
              <Button
                variant="outline"
                onClick={() => {
                  reset()
                  setEditMode(false)
                }}
              >
                Cancel
              </Button>
            </HStack>
          </Protect>
        ) : (
          <Button alignSelf="flex-end" onClick={() => setEditMode(true)}>Edit</Button>
        )}
      </Flex>
    </form>
  )
}
