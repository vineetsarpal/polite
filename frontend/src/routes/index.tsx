import { useAuth } from "@/context/AuthContext";
// import { useAuth0 } from "@auth0/auth0-react";
import {
  Box,
  Button,
  Container,
  Heading,
  Stack,
  Text,
  VStack,
} from "@chakra-ui/react";

import { createFileRoute, Link } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: Index,
})

function Index() {
    const { isLoggedIn } = useAuth()
    // const { isAuthenticated } = useAuth0()

    function Feature({ title, description }: { title: string, description: string}) {
      return (
        <VStack gap={2} maxW="sm">
          <Heading size="sm">{title}</Heading>
          <Text>{description}</Text>
        </VStack>
      )
    }
  
  return (
    <Box>
      <Container maxW="7xl" py={20} textAlign="center">
        <VStack gap={6}>
          <Heading fontSize={{ base: "3xl", md: "5xl" }}>
            Simplify Your Insurance Operations
          </Heading>
          <Text fontSize={{ base: "md", md: "lg" }} color="gray.600">
            A modern web app for managing your Policies
          </Text>
          <Stack
            direction={{ base: "column", sm: "row" }}
            gap={4}
            mt={4}
            justify="center"
          >

            {!isLoggedIn ? (
              <Link to="/login">
                <Button colorScheme="gray" size="lg">Get Started</Button>
              </Link>
              ) : (
                <Link to="/dashboard">
                  <Button size="lg">Dashboard</Button>
                </Link>
              )
            }

            <Link to="/about">
              <Button variant="outline" size="lg">
                Learn More
              </Button>
            </Link>
          </Stack>
        </VStack>
      </Container>

      <Box py={10}>
        <Container maxW="7xl">
          <Heading size="md" mb={6} textAlign="center">
            Key Features
          </Heading>
          <Stack
            direction={{ base: "column", md: "row" }}
            gap={8}
            justify="center"
          >
            <Feature
              title="Policy Management"
              description="Easily create, edit, and manage insurance policies."
            />
            <Feature
              title="User Access Control"
              description="Authenticate users and assign roles with ease."
            />
            <Feature
              title="Secure & Fast"
              description="Built with FastAPI and React for speed and security."
            />
          </Stack>
        </Container>
      </Box>
    </Box>
  )
}