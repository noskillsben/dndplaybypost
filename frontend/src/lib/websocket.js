import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { API_URL } from './config';

function createWebSocketStore() {
    const { subscribe, set, update } = writable({
        isConnected: false,
        messages: [],
        error: null,
        users: []
    });

    let socket = null;
    let reconnectTimer = null;
    let campaignId = null;

    const connect = (id) => {
        if (!browser) return;

        campaignId = id;
        const token = localStorage.getItem('token');

        if (!token) {
            update(s => ({ ...s, error: 'No authentication token found' }));
            return;
        }

        // Always use relative path based on window.location for WebSockets
        // This ensures we go through the same proxy/ingress as the page
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsUrl = `${protocol}//${host}/api/campaigns/${id}/ws?token=${token}`;

        console.log('[WebSocket] Attempting to connect to:', wsUrl);

        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log('WebSocket connected');
            update(s => ({ ...s, isConnected: true, error: null }));
            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
                reconnectTimer = null;
            }
        };

        socket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                handleMessage(message);
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
            }
        };

        socket.onclose = (event) => {
            console.log('[WebSocket] Disconnected. Code:', event.code, 'Reason:', event.reason, 'Clean:', event.wasClean);
            update(s => ({ ...s, isConnected: false }));
            socket = null;

            // Attempt reconnect if not closed cleanly
            if (event.code !== 1000 && event.code !== 1008) {
                console.log('[WebSocket] Will attempt reconnect in 3 seconds...');
                reconnectTimer = setTimeout(() => connect(campaignId), 3000);
            }
        };

        socket.onerror = (error) => {
            console.error('[WebSocket] Error:', error);
            update(s => ({ ...s, error: 'Connection error' }));
        };
    };

    const disconnect = () => {
        if (socket) {
            socket.close(1000, 'User disconnected');
            socket = null;
        }
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
        set({
            isConnected: false,
            messages: [],
            error: null,
            users: []
        });
    };

    const sendMessage = (content, characterId = null, isIc = true, diceExpression = null) => {
        if (!socket || socket.readyState !== WebSocket.OPEN) {
            console.error('WebSocket not connected');
            return;
        }

        const payload = {
            type: 'message',
            content,
            character_id: characterId,
            is_ic: isIc,
            dice_expression: diceExpression
        };

        socket.send(JSON.stringify(payload));
    };

    const handleMessage = (message) => {
        update(state => {
            switch (message.type) {
                case 'message':
                    return {
                        ...state,
                        messages: [...state.messages, message.data]
                    };
                case 'user_joined':
                    // Add user if not already in list
                    if (!state.users.find(u => u.user_id === message.data.user_id)) {
                        return {
                            ...state,
                            users: [...state.users, message.data]
                        };
                    }
                    return state;
                case 'user_left':
                    return {
                        ...state,
                        users: state.users.filter(u => u.user_id !== message.data.user_id)
                    };
                case 'error':
                    return {
                        ...state,
                        error: message.data.message
                    };
                default:
                    return state;
            }
        });
    };

    return {
        subscribe,
        connect,
        disconnect,
        sendMessage
    };
}

export const campaignChat = createWebSocketStore();
