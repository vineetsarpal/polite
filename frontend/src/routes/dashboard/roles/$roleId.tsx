import { API_BASE_URL, API_VERSION } from '@/config/config'
import { paths } from '@/types/openapi'
import { Box, Button, Checkbox, Flex, Heading, HStack, Spacer, Tabs, Text, VStack } from '@chakra-ui/react'
import { Toaster, toaster } from '@/components/ui/toaster'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { LuUser, LuSquareCheck } from 'react-icons/lu'

import { createFileRoute } from '@tanstack/react-router'


export const Route = createFileRoute('/dashboard/roles/$roleId')({
  component: RouteComponent,
})

type Role = paths["/api/v1/roles/{role_id}"]["get"]["responses"]["200"]["content"]["application/json"]
type Permission = paths["/api/v1/permissions/{permission_id}"]["get"]["responses"]["200"]["content"]["application/json"]

interface PermissionWithAssignment extends Permission {
    assigned: boolean
}

const getRole = async (id: string) => {
    const res = await fetch(`${API_BASE_URL}/${API_VERSION.v1}/roles/${id}`)
    if (!res.ok) throw new Error("Error fetching data!")
    return res.json()
}

const getRolePermissions = async (roleId: string | any) => {
    const res = await fetch(`${API_BASE_URL}/${API_VERSION.v1}/roles/${roleId}/permissions`)
    if (!res.ok) throw new Error("Error fetching data!")
    return res.json()
}

function RouteComponent() {
    const { roleId } = Route.useParams()
    const [editMode, setEditMode] = useState(false)
    const [permissions, setPermissions] = useState<PermissionWithAssignment[]>([])
    const [initialPermissions, setInitialPermissions] = useState<PermissionWithAssignment[]>([])
    const queryClient = useQueryClient()

    const { data: roleData, isLoading, error } = useQuery<Role>({
        queryKey: ["roles", roleId],
        queryFn: () => getRole(roleId),
        enabled: !!roleId
    })

    const { data: permissionData } = useQuery<PermissionWithAssignment[]>({
        queryKey: ["permissions", roleId],
        queryFn: () => getRolePermissions(roleId),
        enabled: !!roleId
    })

    // Initialize roles state when roleData loads
    useEffect(() => {
        if (permissionData) {
            setPermissions(permissionData)
            setInitialPermissions(permissionData)
        }
    }, [permissionData])

     // Mutation for saving changes
    const updateRolesMutation = useMutation({
        mutationFn: async (selectedPermissionIds: number[]) => {
            const res = await fetch(
                `${API_BASE_URL}/${API_VERSION.v1}/roles/${roleData?.id}/permissions`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(selectedPermissionIds)
                }
            );
            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.detail || "Failed to update roles")
            }
            return res.json();
        },
        onSuccess: () => {
            toaster.create({
                title: "Role Permissions updated successfully",
                type: "success",
            })
            queryClient.invalidateQueries({ queryKey: ["permissions", roleId] });
            setEditMode(false)
        },
        onError: (error) => {
            toaster.create({
                title: error,
                type: "error",
            })
        },
    })

     // Handle checkbox change
    const handleCheckboxChange = (permissionId: number) => {
        setPermissions(prev => prev.map(permission => permission.id === permissionId ? { ...permission, assigned: !permission.assigned } : permission))
    }

    // Handle cancel button click
    const handleCancel = () => {
        setPermissions(initialPermissions)
        setEditMode(false)
    }

    // Save permissions to backend
    const handleSave = () => {
        if (!roleData?.id) {
            alert(`Role ID ${roleData?.id} not available to save permissions.`);
            return
        }
        const selectedPermissionIds = permissions.filter(p => p.assigned).map(p => p.id);
        updateRolesMutation.mutate(selectedPermissionIds);
    }

    if (isLoading || !roleData) return <p>Loading...</p>

    if (error) return <p>Error: {error.message}</p>

    return (
    <>
      <Toaster />
      <Box
            p={6}
            borderWidth="1px"
            borderRadius="lg"
            shadow="md"
            w="100%"
            maxW="md"
            mx="auto"
        >
            <Tabs.Root defaultValue="details" variant="plain">
                <Tabs.List bg="bg.muted" rounded="lg" p="1">
                    <Tabs.Trigger value="details">
                        <LuUser />
                        Role Details
                    </Tabs.Trigger>
                    <Tabs.Trigger value="permissions">
                        <LuSquareCheck />
                        Permissions
                    </Tabs.Trigger>
                    <Tabs.Indicator rounded="md" />
                </Tabs.List>

                <Tabs.Content value="details">
                    <VStack gap={5} align="stretch" mt={4}>
                        <Heading as="h2" size="lg" mb={2}>
                            Role Details
                        </Heading>
                        <Text>
                            Name: {roleData?.name || 'Loading Role...'}
                        </Text>
                    </VStack>
                </Tabs.Content>

                <Tabs.Content value="permissions">
                    <VStack gap={5} align="stretch" mt={4}>
                        <Text fontSize="lg" fontWeight="semibold" mb={3}>
                            Manage Permissions
                        </Text>
                        {permissions && permissions.length > 0 ? (
                            <VStack align="flex-start" gap={3}>
                                {permissions.map((permission: PermissionWithAssignment) => (
                                    <HStack key={permission.id} width="100%">
                                        <Checkbox.Root
                                            checked={permission.assigned}
                                            onCheckedChange={() => handleCheckboxChange(permission.id)}
                                            id={`permission-${permission.id}`}
                                            disabled={!editMode}
                                        >
                                            <Checkbox.HiddenInput />
                                            <Checkbox.Control
                                                borderRadius="md"
                                                borderWidth="2px"
                                            />
                                            <Checkbox.Label ml={2}>
                                                <Text fontSize="md">
                                                    {permission.name}
                                                </Text>
                                            </Checkbox.Label>
                                        </Checkbox.Root>
                                    </HStack>
                                ))}
                            </VStack>
                        ) : (
                            <Text fontStyle="italic">
                                No permissions available to assign.
                            </Text>
                        )}
                        <Spacer />
                        <Flex justifyContent="center" mt={6}>
                            {editMode ? (
                                <HStack w="100%" gap={4}>
                                    <Button
                                        onClick={handleSave}
                                        loading={updateRolesMutation.isPending}
                                        loadingText="Saving..."
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
                                <Button onClick={() => setEditMode(true)} w="100%" disabled={roleData?.name==="admin"}>
                                    Edit
                                </Button>
                            )}
                        </Flex>
                    </VStack>
                </Tabs.Content>
            </Tabs.Root>
        </Box>
    </>
  )
}
