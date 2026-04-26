import { useAuth, useOrganization, RedirectToSignIn, RedirectToCreateOrganization } from '@clerk/clerk-react'
import Sidebar from '@/components/Sidebar'
import { useColorModeValue } from '@/components/ui/color-mode'
import { Grid, GridItem, Box, Flex, Spinner } from '@chakra-ui/react'
import { createFileRoute, Outlet } from '@tanstack/react-router'

export const Route = createFileRoute('/dashboard')({
  component: DashboardLayout,
})

function DashboardLayout() {
  const { isLoaded: authLoaded, isSignedIn } = useAuth()
  const { isLoaded: orgLoaded, organization } = useOrganization()

  const bgMain = useColorModeValue('', 'gray.950')
  const bgSide = useColorModeValue('gray.50', '')

  if (!authLoaded || !orgLoaded) {
    return (
      <Flex h="100vh" align="center" justify="center">
        <Spinner />
      </Flex>
    )
  }

  if (!isSignedIn) {
    return <RedirectToSignIn />
  }

  if (!organization) {
    return <RedirectToCreateOrganization />
  }

  return (
    <>
      <Grid
        templateColumns={{ base: '1fr', md: 'auto 1fr' }}
      >
        <GridItem
          as="aside"
          w={{ base: 0, md: 'auto' }}
          borderRight={{ base: 'none', md: '1px' }}
          borderColor={{ base: 'transparent', md: 'gray.200' }}
          overflowY="auto"
          display={{ base: 'none', md: 'block' }}
          bg={bgSide}
        >
          <Sidebar />
        </GridItem>

        <GridItem
          as="main"
          p={{ base: 4, md: 10 }}
          overflow="auto"
          bg={bgMain}
          borderRadius={"2xl"}
          mr={2}
          mb={2}
        >
          <Box maxW="container.xl" mx="auto">
            <Outlet />
          </Box>
        </GridItem>
      </Grid>
    </>
  )
}
