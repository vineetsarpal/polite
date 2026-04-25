import { Button } from '@chakra-ui/react'
import { useAuth0 } from "@auth0/auth0-react"

export default function Auth0Button() {
const { loginWithRedirect, isAuthenticated, logout } = useAuth0()

return (
    isAuthenticated? (
        <Button onClick={() => logout()}>Auth0 Logout</Button>
        ) : (
            <Button onClick={() => loginWithRedirect()}>Auth0 Sign In</Button>
        )
    )
}