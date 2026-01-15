'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface WebSocketMessage {
    type: string;
    data?: unknown;
    message?: string;
}

export function useWebSocket(url: string) {
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
    const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        setConnectionStatus('connecting');

        try {
            const ws = new WebSocket(url);

            ws.onopen = () => {
                setConnectionStatus('connected');
                console.log('WebSocket connected');
            };

            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    setLastMessage(message);
                } catch (err) {
                    console.error('Failed to parse WebSocket message:', err);
                }
            };

            ws.onclose = () => {
                setConnectionStatus('disconnected');
                console.log('WebSocket disconnected');

                // Auto-reconnect after 3 seconds
                reconnectTimeoutRef.current = setTimeout(() => {
                    connect();
                }, 3000);
            };

            ws.onerror = (error) => {
                setConnectionStatus('error');
                console.error('WebSocket error:', error);
            };

            wsRef.current = ws;
        } catch (err) {
            setConnectionStatus('error');
            console.error('Failed to create WebSocket:', err);
        }
    }, [url]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    }, []);

    const sendMessage = useCallback((message: object) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(message));
        }
    }, []);

    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    return {
        connectionStatus,
        lastMessage,
        sendMessage,
        connect,
        disconnect,
    };
}
