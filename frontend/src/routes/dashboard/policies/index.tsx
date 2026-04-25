import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Button, Card, SimpleGrid, CloseButton, Dialog, Portal } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { paths } from "@/types/openapi"
import { API_BASE_URL, API_VERSION } from "@/config/config"

import { createFileRoute } from '@tanstack/react-router'
import { useState } from "react"
import { useAuth } from "@/context/AuthContext"
// import { useAuth0 } from "@auth0/auth0-react"

export const Route = createFileRoute('/dashboard/policies/')({
  component: RouteComponent,
})

type Policy = paths["/api/v1/policies/{policy_id}"]["get"]["responses"]["200"]["content"]["application/json"]

const getPolicies = async (token: string | null, token0: string | null) => {
    const bearerToken = token ? token : token0
    const res = await fetch(`${API_BASE_URL}/${API_VERSION.v1}/policies`, {
        headers: {
          "Authorization": `Bearer ${bearerToken}`,
        },
    })

    if (!res.ok) throw new Error("Error fetching data!")
    return res.json()
}

const deletePolicy = async (payload: {id: string, token: string | null, token0: string | null})  => {
  const { id, token, token0 } = payload
  const bearerToken = token ? token : token0
  const res = await fetch(`${API_BASE_URL}/${API_VERSION.v1}/policies/${id}`, {
    method: "DELETE",
    headers: {
      "Authorization": `Bearer ${bearerToken}`,
    },
  })
  if (!res.ok) throw new Error("Failed to delete policy")
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


    const { data, isLoading, error } = useQuery<Policy[]>({
        queryKey: ['policies'],
        queryFn: () => getPolicies(token, null),
        staleTime: 5000, // cache query for these many milisecs
        enabled: !!token
    })

    const { mutate, isPending } = useMutation({
      mutationFn: deletePolicy,
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
        data?.map((policy: Policy) => (
              <Card.Root key={policy.id}> 
                <Link to="/dashboard/policies/$policyId" params={{ policyId: policy.id.toString() }} >
                  <Card.Header>Policy ID: {policy.id}</Card.Header>
                  <Card.Body>
                      Sum Insured: {policy.sum_insured}
                      <br />
                      Net Premium: {policy.net_premium}
                  </Card.Body>
                </Link>

                <Card.Footer>
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
                </Card.Footer>

              </Card.Root>
        ))
      }
    </SimpleGrid>
  )
}