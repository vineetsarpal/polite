import { createFileRoute } from '@tanstack/react-router'
import { Protect } from '@clerk/clerk-react'
import { Box, Text } from '@chakra-ui/react'

export const Route = createFileRoute('/dashboard/policies/update')({
  component: RouteComponent,
})

function RouteComponent() {
  return (
    <Protect permission="org:policies:update">
      <Box>
        <Text>Hello "/policies/update"!</Text>
      </Box>
    </Protect>
  )
}
