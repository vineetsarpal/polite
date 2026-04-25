import { API_BASE_URL, API_VERSION } from '@/config/config'
import { paths } from '@/types/openapi'
import { Box, Button, Checkbox, Flex, Heading, HStack, Spacer, Text, VStack } from '@chakra-ui/react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'

export const Route = createFileRoute('/dashboard/users/$userId')({
  component: RouteComponent,
})

type User = paths["/api/v1/users/{user_id}"]["get"]["responses"]["200"]["content"]["application/json"]
type Role = paths["/api/v1/roles/{role_id}"]["get"]["responses"]["200"]["content"]["application/json"]

interface RoleWithAssignment extends Role {
    assigned: boolean
}

const getUser = async (id: string) => {
    const res = await fetch(`${API_BASE_URL}/${API_VERSION.v1}/users/${id}`)
    if (!res.ok) throw new Error("Error fetching data!")
    return res.json()
}

const getUserRoles = async (userId: string | any) => {
    const res = await fetch(`${API_BASE_URL}/${API_VERSION.v1}/users/${userId}/roles`)
    if (!res.ok) throw new Error("Error fetching data!")
    return res.json()
}

function RouteComponent() {
    const { userId } = Route.useParams()
    const [editMode, setEditMode] = useState(false)
    const [roles, setRoles] = useState<RoleWithAssignment[]>([])
    const [initialRoles, setInitialRoles] = useState<RoleWithAssignment[]>([])
    const queryClient = useQueryClient()


    const { data: userData, isLoading, error } = useQuery<User>({
        queryKey: ["users", userId],
        queryFn: () => getUser(userId),
        enabled: !!userId
    })

    const { data: roleData } = useQuery<RoleWithAssignment[]>({
        queryKey: ["roles", userId],
        queryFn: () => getUserRoles(userId),
        enabled: !!userId
    })

    // Initialize roles state when roleData loads
    useEffect(() => {
        if (roleData) {
            setRoles(roleData)
            setInitialRoles(roleData)
        }
    }, [roleData])

     // Mutation for saving changes
    const updateRolesMutation = useMutation({
        mutationFn: async (selectedRoleIds: number[]) => {
            const res = await fetch(
                `${API_BASE_URL}/${API_VERSION.v1}/users/${userData?.id}/roles`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(selectedRoleIds)
                }
            );
            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.detail || "Failed to update roles")
            }
            return res.json();
        },
        onSuccess: () => {
            alert("Roles updated successfully!")
            // Invalidate the 'roles' query to refetch fresh data from the backend
            // This ensures that if the user navigates away and comes back, or if another part
            // of the app relies on this data, it's always up-to-date with the backend.
            queryClient.invalidateQueries({ queryKey: ["roles", userId] });
        },
        onError: (error) => {
            alert(`Error: ${error.message}`)
        },
    })

     // Handle checkbox change
    const handleCheckboxChange = (roleId: number) => {
        setRoles(prev => prev.map(role => role.id === roleId ? { ...role, assigned: !role.assigned } : role))
    }

    // Handle cancel button click
    const handleCancel = () => {
        setRoles(initialRoles)
        setEditMode(false)
    }

    // Save roles to backend
    const handleSave = () => {
        if (!userData?.id) {
            alert(`User ID ${userData?.id} not available to save roles.`);
            return;
        }
        const selectedRoleIds = roles.filter(r => r.assigned).map(r => r.id);
        updateRolesMutation.mutate(selectedRoleIds);
    }

    if (isLoading || !userData) return <p>Loading...</p>

    if (error) return <p>Error: {error.message}</p>

    return (
    <Box
      p={6}
      borderWidth="1px"
      borderRadius="lg"
      shadow="md"
      w="100%"
      maxW="md"
      mx="auto" 
    >
      <VStack gap={5} align="stretch">
        <Heading as="h2" size="lg"  mb={2}>
          User Details
        </Heading>
        <Text>
          Name: {userData?.full_name || 'Loading User...'}
        </Text>

        {/* Roles Section */}
        <Box>
          <Text fontSize="lg" fontWeight="semibold" mb={3}>
            Manage Roles
          </Text>
          {roles && roles.length > 0 ? (
            <VStack align="flex-start" gap={3}>
              {roles.map((role: RoleWithAssignment) => {
                return (
                // Use Checkbox.Root for each individual checkbox
                <HStack key={role.id} width="100%">
                  <Checkbox.Root
                    // The 'checked' prop controls the state
                    checked={role.assigned}
                    // The 'onCheckedChange' event handler
                    onCheckedChange={() => handleCheckboxChange(role.id)}
                    id={`role-${role.id}`} // Good for accessibility, links to the label
                    disabled={!editMode}
                  >
                    <Checkbox.HiddenInput />

                    <Checkbox.Control
                        borderRadius="md" // Rounded corners for the box
                        borderWidth="2px"
                    >
                    </Checkbox.Control>

                    {/* The label text */}
                    <Checkbox.Label  ml={2}>
                      <Text fontSize="md">
                        {role.name}
                      </Text>
                    </Checkbox.Label>
                  </Checkbox.Root>
                </HStack>
              )})}
            </VStack>
          ) : (
            <Text fontStyle="italic">
              No roles available to assign.
            </Text>
          )}
        </Box>

        <Spacer />

        <Flex justifyContent="center" mt={6}>
          {editMode ? (
              <HStack w={"100%"} gap={4}>
                  <Button
                    onClick={handleSave}
                    loading={isLoading}
                    loadingText="Saving.."
                    flex={1}
                  >
                    Save
                  </Button>
                  <Button
                      variant="outline"
                      onClick={handleCancel}
                      flex={1}
                  >
                      Cancel
                  </Button>
              </HStack>
              ) : (
              <Button onClick={() => setEditMode(true)} w={"100%"}>Edit</Button>
          )}
        </Flex>
        
      </VStack>
    </Box>
  )
}
