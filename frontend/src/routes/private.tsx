import { API_BASE_URL } from '@/config/config'
import { useAuth0 } from '@auth0/auth0-react'
import { useQuery } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'

export const Route = createFileRoute('/private')({
  component: RouteComponent,
})


const itsPrivate = async (token0: string | null) => {
    const bearerToken = token0
    const res = await  fetch(`${API_BASE_URL}/private`, {
        headers: {
            "Authorization": `Bearer ${bearerToken}`
        }
    }) 
    if (!res.ok) throw new Error("Error fetching data!")
    const data = await res.json()
    return data?.user
}


function RouteComponent() {
    // Auth0
    const { getAccessTokenSilently, user } = useAuth0()
    const [auth0Token, setAuth0Token] = useState(null)
    useEffect(() => {
        const fetchAuth0Token = async () => {
            const t: string | any = await getAccessTokenSilently()
            setAuth0Token(t)
        }
        fetchAuth0Token()
    }, [getAccessTokenSilently])
    
    const { data } = useQuery({
        queryKey: ["private"],
        queryFn: () => itsPrivate(auth0Token),
        enabled: !!auth0Token
    }) 

    return (
        <div>
            Hello { data?.sub }
            <br />
            Hey there { user?.email }
        </div>
    )
}
