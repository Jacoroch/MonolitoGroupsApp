import { useEffect, useRef } from "react";

export function useChatSocket(groupId, token, onMessage) {
  const socketRef = useRef(null);

  useEffect(() => {
    if (!groupId) return;

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";

    const socket = new WebSocket(
      `${protocol}://localhost:8000/ws/groups/${groupId}?token=${token}`
    );

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.action === "new_message") {
        onMessage(data);
      }
    };

    socketRef.current = socket;

    return () => socket.close();
  }, [groupId, token]);

  const sendMessage = (content) => {
    if (!socketRef.current) return;

    socketRef.current.send(
      JSON.stringify({
        action: "send_message",
        content
      })
    );
  };

  return { sendMessage };
}