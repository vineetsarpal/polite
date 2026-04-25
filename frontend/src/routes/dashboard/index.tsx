import { Box, Text } from '@chakra-ui/react'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/dashboard/')({
  component: RouteComponent,
})

function RouteComponent() {
  return (
     <Box>
      <Text>Welcome to your Dashboard!</Text>
    </Box>
  )
}
