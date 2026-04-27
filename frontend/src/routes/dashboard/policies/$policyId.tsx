import { Button, Field, Flex, HStack, Input, SimpleGrid } from '@chakra-ui/react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { paths } from '@/types/openapi'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useApiClient, v1 } from '@/lib/apiClient'
import { Protect } from '@clerk/clerk-react'
import { createFileRoute, useNavigate } from '@tanstack/react-router'

export const Route = createFileRoute('/dashboard/policies/$policyId')({
  component: RouteComponent,
})

type Policy = paths["/api/v1/policies/{policy_id}"]["get"]["responses"]["200"]["content"]["application/json"]
type UpdatePayload = paths["/api/v1/policies/{policy_id}"]["put"]["requestBody"]["content"]["application/json"]

function RouteComponent() {
  const { policyId } = Route.useParams()
  const api = useApiClient()
  const [editMode, setEditMode] = useState(false)
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery<Policy>({
    queryKey: ['policies', policyId],
    queryFn: () => api.get<Policy>(v1(`/policies/${policyId}`)),
  })

  const toDateInputFormat = (dateString: string) => {
    const date = new Date(dateString)
    return date.toISOString().split('T')[0]
  }

  const { register, handleSubmit, reset } = useForm<UpdatePayload>({
    defaultValues: data
      ? {
          ...data,
          start_date: toDateInputFormat(data.start_date),
          end_date: toDateInputFormat(data.end_date),
        }
      : {},
  })

  useEffect(() => {
    if (data) {
      const formatted = {
        ...data,
        start_date: toDateInputFormat(data.start_date),
        end_date: toDateInputFormat(data.end_date),
      }
      reset(formatted)
    }
  }, [data, reset])

  const { mutate } = useMutation({
    mutationFn: (formData: UpdatePayload) =>
      api.put<Policy>(v1(`/policies/${policyId}`), formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies', policyId] })
      navigate({ to: `/dashboard/policies/${policyId}` })
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
          <Field.Label>LOB</Field.Label>
          <Input {...register('lob')} disabled={true} />
        </Field.Root>
        <Field.Root>
          <Field.Label>License Plate</Field.Label>
          <Input {...register('license_plate')} disabled={!editMode} />
        </Field.Root>
        <Field.Root>
          <Field.Label>VIN</Field.Label>
          <Input {...register('vin')} disabled={!editMode} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Sum Insured</Field.Label>
          <Input {...register('sum_insured')} disabled={!editMode} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Base Premium</Field.Label>
          <Input {...register('base_premium')} disabled={!editMode} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Net Premium</Field.Label>
          <Input {...register('net_premium')} disabled={!editMode} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Tax</Field.Label>
          <Input {...register('tax')} disabled={!editMode} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Start Date</Field.Label>
          <Input type="date" {...register('start_date')} disabled={true} />
        </Field.Root>
        <Field.Root>
          <Field.Label>End Date</Field.Label>
          <Input type="date" {...register('end_date')} disabled={true} />
        </Field.Root>
        <Field.Root>
          <Field.Label>Policyholder ID</Field.Label>
          <Input {...register('policyholder_id')} disabled={!editMode} />
        </Field.Root>
      </SimpleGrid>

      <Flex justifyContent="center" mt={6}>
        {editMode ? (
          <Protect permission="org:policies:update">
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
