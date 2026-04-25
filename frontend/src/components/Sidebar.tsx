import { Box, Flex, VStack, IconButton, Text, } from '@chakra-ui/react'
import { Link, useMatchRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { LuUsers, LuShield, LuContact, LuFilePlus, LuChevronsLeft, LuChevronsRight } from 'react-icons/lu'

function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false)

  // Use useMatchRoute to detect active routes
  const matchRoute = useMatchRoute()

  // Navigation items with icons
  const navItems = [
    { to: '/dashboard/users', label: 'Users', icon: LuUsers },
    { to: '/dashboard/roles', label: 'Roles', icon: LuShield },
    { to: '/dashboard/contacts', label: 'Contacts', icon: LuContact },
    { to: '/dashboard/policies', label: 'Policies', icon: LuShield },
    { to: '/dashboard/policies/create', label: 'Create a Policy', icon: LuFilePlus },
  ]

  // Toggle collapse state for desktop
  const toggleCollapse = () => setIsCollapsed(!isCollapsed)

  return (
    <>
      {/* Desktop: Sidebar */}
      <Box
        display={{ base: 'none', md: 'block' }}
        position="relative"
        top={0}
        left={0}
        h="100vh"
        w={isCollapsed ? '80px' : '250px'}
        borderRight="1px"
        transition="width 0.2s ease"
        zIndex="docked"
        overflow="hidden"
      >
        {/* Vertical Line Aligned with Toggle Button */}
        {/* <Box
          position="absolute"
          top={0}
          bottom={0}
          right={0}
          w="1px"
          bg={"gray.200"}
          display={{ base: 'none', md: 'block' }}
        /> */}

        <Flex
          direction="column"
          h="full"
          p={isCollapsed ? 2 : 4}
        >
          {/* Collapse Toggle Button */}
          <Flex justify={isCollapsed ? 'center' : 'flex-end'} mb={2}>
            <IconButton
              aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              variant="ghost"
              onClick={toggleCollapse}
              size="sm"
            >
              {isCollapsed ? <LuChevronsRight /> : <LuChevronsLeft />}
            </IconButton>
          </Flex>

          {/* Navigation Items */}
          <VStack align="start" gap={2} flex={1}>
            {navItems.map((item) => {
              const isActive = !!matchRoute({ to: item.to })
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  style={{ width: '100%' }}
                >
                  <Flex
                    align="center"
                    p={3}
                    borderRadius="md"
                    w="100%"
                    fontWeight={isActive ? 'semibold' : 'normal'}
                  >
                    <item.icon size={20} style={{ marginRight: isCollapsed ? 0 : 12 }} />
                    {!isCollapsed && <Text fontSize="md">{item.label}</Text>}
                  </Flex>
                </Link>
              )
            })}
          </VStack>
        </Flex>
      </Box>

      {/* Spacer to prevent content overlap on desktop */}
      <Box
        display={{ base: 'none', md: 'block' }}
        w={isCollapsed ? '80px' : '250px'}
        flexShrink={0}
      />
    </>
  )
}

export default Sidebar