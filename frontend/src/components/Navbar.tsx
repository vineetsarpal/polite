import { Button, Flex, Heading, HStack, Spacer } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { ColorModeButton } from "@/components/ui/color-mode"
import { OrganizationSwitcher, UserButton, SignedIn, SignedOut } from "@clerk/clerk-react"

function Navbar() {
  return (
    <Flex as={"nav"} px={10} py={2} gap={2} alignItems={"center"} wrap={"wrap"}>
      <HStack gap={10}>
        <Link to="/" activeProps={{ className: 'font-bold' }} activeOptions={{ exact: true }}>
          <Heading size="3xl" fontWeight="bold">Polite</Heading>
        </Link>
        <Link to="/about" activeProps={{ className: 'font-bold' }} activeOptions={{ exact: true }}>
          About
        </Link>
      </HStack>

      <Spacer />

      <HStack gap={5}>
        <SignedIn>
          <Link to="/dashboard">
            <Button variant={"solid"} rounded="full">Dashboard</Button>
          </Link>
          <OrganizationSwitcher
            afterCreateOrganizationUrl="/dashboard"
            afterSelectOrganizationUrl="/dashboard"
          />
          <UserButton afterSignOutUrl="/sign-in" />
        </SignedIn>
        <SignedOut>
          <Link to="/sign-in">
            <Button size="sm" variant="ghost">Sign in</Button>
          </Link>
          <Link to="/sign-up">
            <Button size="sm">Sign up</Button>
          </Link>
        </SignedOut>
        <ColorModeButton />
      </HStack>
    </Flex>
  )
}

export default Navbar
