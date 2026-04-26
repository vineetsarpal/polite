import { OrganizationProfile } from '@clerk/clerk-react'
import { createFileRoute } from '@tanstack/react-router'
import { Box, Heading } from '@chakra-ui/react'

export const Route = createFileRoute('/dashboard/organization')({
  component: RouteComponent,
})

function RouteComponent() {
  return (
    <Box p={6}>
      <Heading size="lg" mb={4}>Organization</Heading>
      <OrganizationProfile routing="path" path="/dashboard/organization" />
    </Box>
  )
}
