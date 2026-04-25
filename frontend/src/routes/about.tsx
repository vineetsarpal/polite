import { Box, Container } from '@chakra-ui/react'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/about')({
  component: About,
})

function About() {
  return (
    <Box>
      <Container maxW="7xl" py={20} textAlign="center">
          <div className="p-2">Hello from About!</div>
      </Container>
    </Box>
  )
}