import { API_BASE_URL, API_VERSION } from '@/config/config'
import { useAuth } from '@/context/AuthContext'
import { paths } from '@/types/openapi'
// import { useAuth0 } from '@auth0/auth0-react'
import { Button, Card, CloseButton, Dialog, Portal, SimpleGrid } from '@chakra-ui/react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createFileRoute, Link } from '@tanstack/react-router'
import { useState } from 'react'

export const Route = createFileRoute('/dashboard/users/')({
  component: RouteComponent,
})

type User = paths["/api/v1/users/{user_id}"]["get"]["responses"]["200"]["content"]["application/json"]

const getUsers = async (token: string | null, token0: string | null = null) => {
    const bearerToken = token ? token : token0
    const res = await fetch(`${API_BASE_URL}/${API_VERSION.v1}/users`, {
        headers: {
            "Authorization": `Bearer ${bearerToken}`
        }
    })
    if (!res.ok) throw new Error("Error fetching data")
    return res.json()
}

const deleteUser = async (payload: {id: string, token: string | null, token0: string | null})  => {
    const { id, token, token0 } = payload
    const bearerToken = token ? token : token0
    const res = await fetch(`${API_BASE_URL}/${API_VERSION.v1}/users/${id}`, {
        method: "DELETE",
        headers: {
        "Authorization": `Bearer ${bearerToken}`,
        },
    })
    if (!res.ok) throw new Error("Failed to delete User")
    return true
}

function RouteComponent() {
    const { token } = useAuth()
    const queryClient = useQueryClient()
    const [idToDelete, setIdToDelete] = useState<string | null>(null)
    
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


    const { data, isLoading, error } = useQuery<User[]>({
        queryKey: ["users"],
        queryFn: () => getUsers(token, null),
        enabled: !!token
    })

    const { mutate, isPending } = useMutation({
        mutationFn: deleteUser,
        onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["policies"] })
      }
    })

    const handleDeleteClick = (id: string) => {
      setIdToDelete(id)
    }

    const confirmDelete = () => {
      if (idToDelete && token) mutate({ id: idToDelete, token, token0: null })
    }

    if (isLoading) return <p> Loading</p>

    if (error) return <p>Error: {error.message}</p>

    return (
        <SimpleGrid columns={{ base: 1, sm: 2, md: 3, lg: 4 }} gap={10}>
        {
            data?.map((user: User) => (
                <Card.Root key={user.id}> 
                    <Link to="/dashboard/users/$userId" params={{ userId: user.id.toString() }} >
                    <Card.Header>{user.username}</Card.Header>
                    <Card.Body>
                        Email: {user.email}
                    </Card.Body>
                    </Link>

                    <Card.Footer>
                    <Dialog.Root role="alertdialog">
                        <Dialog.Trigger asChild>
                        <Button variant="outline" size="sm" onClick={() => handleDeleteClick(user.id.toString())}>
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
                                This will permanently delete User ID: {user.id}
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
                    </Card.Footer>

                </Card.Root>
            ))
        }
        </SimpleGrid>
    )
}
