import { Button } from '@chakra-ui/react'
import { Link, useNavigate } from '@tanstack/react-router'
import { useAuth } from '@/context/AuthContext'

export default function AuthButton() {
  const { isLoggedIn, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate({ to: '/'})
  }

  return isLoggedIn ? (
    <Button onClick={handleLogout} variant="outline">
      Sign Out
    </Button>
  ) : (
      <Link to='/login'>
        <Button variant={"solid"}>Sign In</Button>
      </Link>
  )
}