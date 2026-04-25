import { paths } from '@/types/openapi'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useForm } from 'react-hook-form'
import { SimpleGrid, Input, Button, Field, Flex, Text, NativeSelect } from '@chakra-ui/react'
import { API_BASE_URL, API_VERSION } from '@/config/config'
import { useAuth } from '@/context/AuthContext'
// import { useAuth0 } from '@auth0/auth0-react'

export const Route = createFileRoute('/dashboard/policies/create')({
  component: RouteComponent,
})

type FormData = paths["/api/v1/policies/"]["post"]["requestBody"]["content"]["application/json"]
type Contact = paths["/api/v1/contacts/{contact_id}"]["get"]["responses"]["200"]["content"]["application/json"]

const fetchContacts = async (token: string | null, token0: string | null) => {
    const bearerToken = token ? token : token0
    const res = await fetch(`${API_BASE_URL}/${API_VERSION.v1}/contacts`, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${bearerToken}`,
        },
    })
    if (!res.ok) {
        const errorResponse = await res.json()
        console.error(errorResponse)
        throw new Error("Failed to fetch contacts")
    }
    return res.json()
}

const createPolicy = async (payload: { data: FormData, token: string | null, token0: string | null }) => {
    const { data, token, token0 } = payload
    const bearerToken = token ? token : token0
    const res = await fetch(`${API_BASE_URL}/${API_VERSION.v1}/policies`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${bearerToken}`,
        },
        body: JSON.stringify(data)
    })
    if (!res.ok) {
        const errorResponse = await res.json()
        console.error(errorResponse)
        throw new Error("Failed to create policy")
    }
    return res.json()
}


function RouteComponent() {
    const { token } = useAuth()
    const { register, handleSubmit } = useForm<FormData>()
    const queryClient = useQueryClient()
    const navigate = useNavigate()

    // // Auth0
    // const { getAccessTokenSilently } = useAuth0()
    // const [auth0Token, setAuth0Token] = useState(null)
    // useEffect(() => {
    //     const fetchAuth0Token = async () => {
    //     const t: string | any = await getAccessTokenSilently()
    //     setAuth0Token(t);
    //   }
    //   fetchAuth0Token()
    // }, [getAccessTokenSilently])

    const { data: contacts, isLoading: isLoadingContacts } = useQuery<Contact[]>({
        queryKey: ['contacts', token], // Invalidate if token changes
        queryFn: () => fetchContacts(token, null), // Assuming 'token' is your primary token, pass auth0Token if needed
        enabled: !!token, // Only run this query if the token is available
    })

    const { mutate, isPending, error } = useMutation({
        mutationFn: createPolicy,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['policies']}),
            navigate({ to: "/dashboard/policies" })
        }
    })

    const onSubmit = (data: FormData) => {
        mutate({ data, token, token0: null})
    }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
        <SimpleGrid columns={{ base: 1, sm: 2, md: 3, lg: 4 }} gap={4}>
            <Field.Root>
                <Field.Label>LOB</Field.Label>
                <Input {...register("lob")} />
            </Field.Root>
            <Field.Root>
                <Field.Label>License Plate</Field.Label>
                <Input {...register("license_plate")} />
            </Field.Root>
            <Field.Root>
                <Field.Label>VIN</Field.Label>
                <Input {...register("vin")} />
            </Field.Root>
            <Field.Root>
                <Field.Label>Sum Insured</Field.Label>
                <Input {...register("sum_insured")} />
            </Field.Root>
            <Field.Root>
                <Field.Label>Base Premium</Field.Label>
                <Input {...register("base_premium")} />
            </Field.Root>
            <Field.Root>
                <Field.Label>Net Premium</Field.Label>
                <Input {...register("net_premium")} />
            </Field.Root>
            <Field.Root>
                <Field.Label>Tax</Field.Label>
                <Input {...register("tax")} />
            </Field.Root>
            <Field.Root>
                <Field.Label>Start Date</Field.Label>
                <Input type='date' {...register("start_date")} />
            </Field.Root>
            <Field.Root>
                <Field.Label>End Date</Field.Label>
                <Input type='date' {...register("end_date")} />
            </Field.Root>
            <Field.Root>
                <Field.Label>Policyholder</Field.Label>
                 {isLoadingContacts ? (
                    <Text>Loading contacts...</Text>
                ) : (
                   <NativeSelect.Root>
                        <NativeSelect.Field placeholder='Select Policyholder' {...register("policyholder_id")}>
                            {contacts?.map((contact: Contact) => (
                                <option key={contact.id} value={contact.id}>{contact.first_name} {contact.last_name}</option>
                            ))}
                        </NativeSelect.Field>   
                   </NativeSelect.Root>
                )}
            </Field.Root>

        </SimpleGrid>

        <Flex justifyContent="center" mt={6}>
            <Button type="submit" loading={isPending}>
                Create Policy
            </Button>
        </Flex>

        <Text color={"red"}>{error && error.message}</Text>
    </form>
  )
}
