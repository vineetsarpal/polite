import { Button, Flex, Heading, HStack, Spacer, Text } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { ColorModeButton, useColorModeValue } from "@/components/ui/color-mode"
import AuthButton from "./AuthButton"
import { useQuery } from "@tanstack/react-query"
import { useAuth } from "@/context/AuthContext"
import { userService } from "@/services/userService"
// import Auth0Button from "./Auth0Button"
// import { useAuth0 } from "@auth0/auth0-react"

function Navbar() {
    const { isLoggedIn, token } = useAuth()
    // const { user: auth0User, isAuthenticated  } = useAuth0()
    const bgNav = useColorModeValue('gray.50','')

    const { data } = useQuery({
        queryKey: ["currentUser", token],
        queryFn: () => userService.getCurrentUser(token),
        staleTime: 5 * 60 * 1000,
        enabled: isLoggedIn && !!token,
    })

  return (
    <Flex as={"nav"} px={10} py={2} gap={2} alignItems={"center"} wrap={"wrap"} bg={isLoggedIn ? bgNav : ''}>
        <HStack gap={10}>
            <Link to="/"  activeProps={{ className: 'font-bold' }} activeOptions={{ exact: true }}>
                <Heading size="3xl" fontWeight="bold">Polite</Heading>
            </Link> 
            <Link to="/about"  activeProps={{ className: 'font-bold' }} activeOptions={{ exact: true }}>
                About
            </Link>
        </HStack>
    
        <Spacer />

        <HStack gap={5}>
            {(isLoggedIn) && 
                <Link to='/dashboard'>
                    <Button variant={"solid"} rounded="full">Dashboard</Button>
                </Link>
            }   
            {isLoggedIn && <Text>Welcome, {data?.username} </Text>}
            {/* {isAuthenticated && <Text>Welcome, {auth0User?.name} </Text>} */}

            <AuthButton />
            {/* {!isLoggedIn && <Auth0Button />} */}
            <ColorModeButton />
        </HStack>
    </Flex>
  )
}

export default Navbar