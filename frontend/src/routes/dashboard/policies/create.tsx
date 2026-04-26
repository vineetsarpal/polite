import { paths } from '@/types/openapi'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'
import { SimpleGrid, Input, Button, Field, Flex, Text, NativeSelect } from '@chakra-ui/react'
import { useApiClient, v1 } from '@/lib/apiClient'
import { Protect } from '@clerk/clerk-react'

export const Route = createFileRoute('/dashboard/policies/create')({
  component: RouteComponent,
})

type FormData = paths["/api/v1/policies/"]["post"]["requestBody"]["content"]["application/json"]
type Contact = paths["/api/v1/contacts/{contact_id}"]["get"]["responses"]["200"]["content"]["application/json"]
type Policy = paths["/api/v1/policies/{policy_id}"]["get"]["responses"]["200"]["content"]["application/json"]

function RouteComponent() {
  const api = useApiClient()
  const { register, handleSubmit } = useForm<FormData>()
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const { data: contacts, isLoading: isLoadingContacts } = useQuery<Contact[]>({
    queryKey: ['contacts'],
    queryFn: () => api.get<Contact[]>(v1('/contacts')),
  })

  const { mutate, isPending, error } = useMutation({
    mutationFn: (data: FormData) => api.post<Policy>(v1('/policies'), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      navigate({ to: '/dashboard/policies' })
    },
  })

  const onSubmit = (data: FormData) => {
    mutate(data)
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <SimpleGrid columns={{ base: 1, sm: 2, md: 3, lg: 4 }} gap={4}>
        <Field.Root>
          <Field.Label>LOB</Field.Label>
          <Input {...register('lob')} />
        </Field.Root>
        <Field.Root>
          <Field.Label>License Plate</Field.Label>
          <Input {...register('license_plate')} />
        </Field.Root>
        <Field.Root>
          <Field.Label>VIN</Field.Label>
          <Input {...register('vin')} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Sum Insured</Field.Label>
          <Input {...register('sum_insured')} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Base Premium</Field.Label>
          <Input {...register('base_premium')} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Net Premium</Field.Label>
          <Input {...register('net_premium')} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Tax</Field.Label>
          <Input {...register('tax')} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Start Date</Field.Label>
          <Input type="date" {...register('start_date')} />
        </Field.Root>
        <Field.Root>
          <Field.Label>End Date</Field.Label>
          <Input type="date" {...register('end_date')} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Policyholder</Field.Label>
          {isLoadingContacts ? (
            <Text>Loading contacts...</Text>
          ) : (
            <NativeSelect.Root>
              <NativeSelect.Field placeholder="Select Policyholder" {...register('policyholder_id')}>
                {contacts?.map((contact: Contact) => (
                  <option key={contact.id} value={contact.id}>
                    {contact.first_name} {contact.last_name}
                  </option>
                ))}
              </NativeSelect.Field>
            </NativeSelect.Root>
          )}
        </Field.Root>
      </SimpleGrid>

      <Flex justifyContent="center" mt={6}>
        <Protect permission="org:policies:create">
          <Button type="submit" loading={isPending}>
            Create Policy
          </Button>
        </Protect>
      </Flex>

      <Text color="red">{error && error.message}</Text>
    </form>
  )
}
