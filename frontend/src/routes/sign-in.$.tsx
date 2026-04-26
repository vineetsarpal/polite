import { SignIn } from '@clerk/clerk-react'
import { createFileRoute } from '@tanstack/react-router'
import { Center } from '@chakra-ui/react'

export const Route = createFileRoute('/sign-in/$')({
  component: RouteComponent,
})

function RouteComponent() {
  return (
    <Center minH="100vh" py={10}>
      <SignIn routing="path" path="/sign-in" signUpUrl="/sign-up" />
    </Center>
  )
}
