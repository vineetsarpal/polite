import { SignUp } from '@clerk/clerk-react'
import { createFileRoute } from '@tanstack/react-router'
import { Center } from '@chakra-ui/react'

export const Route = createFileRoute('/sign-up')({
  component: RouteComponent,
})

function RouteComponent() {
  return (
    <Center minH="100vh" py={10}>
      <SignUp routing="path" path="/sign-up" signInUrl="/sign-in" />
    </Center>
  )
}
