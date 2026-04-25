import { Button, Field, Flex, HStack, Input, SimpleGrid } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { paths } from "@/types/openapi"
import { useEffect, useState } from "react"
import { useForm } from "react-hook-form"
import { API_BASE_URL, API_VERSION } from "@/config/config"
import { useAuth } from "@/context/AuthContext"
// import { useAuth0 } from "@auth0/auth0-react"

import { createFileRoute, useNavigate } from '@tanstack/react-router'

export const Route = createFileRoute('/dashboard/contacts/$contactId')({
  component: RouteComponent,
})

type Contact = paths["/api/v1/contacts/{contact_id}"]["get"]["responses"]["200"]["content"]["application/json"]
type UpdatePayload = paths["/api/v1/contacts/{contact_id}"]["put"]["requestBody"]["content"]["application/json"]

const getContact = async (id: string, token: string | null) => {
    const bearerToken = token
    const res = await fetch(`${API_BASE_URL}/${API_VERSION.v1}/contacts/${id}`, {
        headers: {
            "Authorization": `Bearer ${bearerToken}`
        }
    })
    if (!res.ok) throw new Error("Error fetching data!")
    return res.json()
}

const updatePolicy = async (payload : { id: string, data: UpdatePayload, token: string | null, token0: string | null }) => {
    const { id, data, token, token0 } = payload
    const bearerToken = token ? token : token0
    const res = await fetch(`${API_BASE_URL}/${API_VERSION.v1}/contacts/${id}`, {
        method: 'PUT',
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${bearerToken}`,
        },
        body: JSON.stringify(data),
    })
    if (!res.ok) throw new Error("Error updating policy!")
    return res.json()
}

function RouteComponent() {
    const { token } = useAuth()
    const [editMode, setEditMode] = useState(false)
    const { contactId } = Route.useParams()
    const queryClient = useQueryClient()
    const navigate = useNavigate()

    //  // Auth0
    // const { getAccessTokenSilently } = useAuth0()
    // const [auth0Token, setAuth0Token] = useState(null)
    // useEffect(() => {
    //     const fetchAuth0Token = async () => {
    //     const t: string | any = await getAccessTokenSilently()
    //     setAuth0Token(t);
    //   }
    //   fetchAuth0Token()
    // }, [getAccessTokenSilently])

    const { data, isLoading, error } = useQuery<Contact>({
        queryKey: ["policies", contactId],
        queryFn: () => getContact(contactId, token),
    })

    // const toDateInputFormat = (dateString: string) => {
    //     const date = new Date(dateString)
    //     return date.toISOString()
    // }

    const { register, handleSubmit, reset } = useForm<UpdatePayload>({
        defaultValues: data 
    })

    // Reset the form when the data is loaded or updated
    useEffect(() => {
        reset(data)
    }, [data, reset])

    const { mutate } = useMutation({
        mutationFn: updatePolicy,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['contacts', contactId] });
            navigate({ to: `/contacts/${contactId}`})
            setEditMode(false)
        }
    })

    const onSubmit = (formData: UpdatePayload) => {
        mutate({ id: contactId, data: formData, token, token0: null })
    }

    if (isLoading || !data) return <p>Loading...</p>

    if (error) return <p>Error: {error.message}</p>

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
        <SimpleGrid columns={{ base: 1, sm: 2, md: 3, lg: 4 }} gap={4}>
            <Field.Root>
                <Field.Label>First Name</Field.Label>
                <Input {...register("first_name")} disabled={!editMode} />
            </Field.Root>
            <Field.Root>
                <Field.Label>Last Name</Field.Label>
                <Input {...register("last_name")} disabled={!editMode} />
            </Field.Root>
            <Field.Root>
                <Field.Label>Type</Field.Label>
                <Input {...register("type")} disabled={true} />
            </Field.Root>
            <Field.Root>
                <Field.Label>DOB</Field.Label>
                <Input {...register("dob")} disabled={!editMode} />
            </Field.Root>
            <Field.Root>
                <Field.Label>Email</Field.Label>
                <Input {...register("email")} disabled={!editMode} />
            </Field.Root>
        </SimpleGrid>

        <Flex justifyContent="center" mt={6}>
            {editMode ? (
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
                ) : (
                <Button alignSelf="flex-end" onClick={() => setEditMode(true)}>Edit</Button>
            )}
        </Flex>
    </form>
  )
}