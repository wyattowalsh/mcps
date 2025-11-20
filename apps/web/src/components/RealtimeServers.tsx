'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import type { Server } from '@/lib/db'
import { ServerCard } from './server-card'

interface RealtimeServersProps {
  initialServers: Server[]
}

/**
 * Real-time servers component
 * Subscribes to database changes and updates UI automatically
 */
export default function RealtimeServers({ initialServers }: RealtimeServersProps) {
  const [servers, setServers] = useState(initialServers)
  const supabase = createClient()

  useEffect(() => {
    // Subscribe to real-time changes
    const channel = supabase
      .channel('servers-realtime')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'server',
        },
        (payload) => {
          console.log('Real-time update:', payload)

          if (payload.eventType === 'INSERT') {
            // Add new server to the list
            setServers((current) => [payload.new as Server, ...current])
          } else if (payload.eventType === 'UPDATE') {
            // Update existing server
            setServers((current) =>
              current.map((server) =>
                server.id === (payload.new as Server).id
                  ? (payload.new as Server)
                  : server
              )
            )
          } else if (payload.eventType === 'DELETE') {
            // Remove deleted server
            setServers((current) =>
              current.filter((server) => server.id !== (payload.old as Server).id)
            )
          }
        }
      )
      .subscribe()

    // Cleanup subscription on unmount
    return () => {
      supabase.removeChannel(channel)
    }
  }, [supabase])

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {servers.map((server) => (
        <ServerCard key={server.id} server={server} />
      ))}
    </div>
  )
}
