import { Box, Text, CloseButton, Flex } from '@chakra-ui/react'
import { useState } from 'react'

export const TopBanner = () => {
  const [isVisible, setIsVisible] = useState(true)

  // Handle closing the banner
  const handleClose = () => {
    setIsVisible(false)
    // localStorage.setItem('bannerDismissed', 'true')
  }

//   useEffect(() => {
//     if (localStorage.getItem('bannerDismissed') === 'true') {
//       setIsVisible(false)
//     }
//   }, [])

  if (!isVisible) return null

  return (
    <Box
      position="relative"
      top={0}
      left={0}
      right={0}
      p={1}
      zIndex="banner"
      textAlign="center"
      boxShadow="sm"
    >
      <Flex
        align="center"
        justify="center"
        maxW="container.xl"
        maxH={"4"}
        mx="auto"
        px={{ base: 4, md: 0 }}
      >
        <Text fontSize={{ base: 'xs', md: 'sm' }} fontWeight="medium">
          This website is in beta mode. We're testing features and making improvements. You may encounter bugs or incomplete functionality.{' '}
          {/* <Link
            href="mailto:feedback@yourwebsite.com"
            color="blue.600"
            textDecoration="underline"
            _hover={{ color: 'blue.800' }}
          >
            Share your feedback
          </Link>
          {' '}to help us improve! */}
        </Text>
        <CloseButton
          size="sm"
          onClick={handleClose}
          ml={4}
        />
      </Flex>
    </Box>
  )
}