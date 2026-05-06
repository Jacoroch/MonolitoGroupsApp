"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { getMyGroups, getMe, getGroupMembers, getMessages } from "@/lib/api";

export default function ChatsPage() {
  const router = useRouter();

  // Estados de UI
  const [menuOpen, setMenuOpen] = useState(false);
  const [membersOpen, setMembersOpen] = useState(false);

  // Estados de Datos
  const [user, setUser] = useState(null);
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [messages, setMessages] = useState([]);
  const [members, setMembers] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [userMap, setUserMap] = useState({});
  const [adminId, setAdminId] = useState(null);

  // Refs para WebSocket y Scroll
  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);

  // 1. Cargar usuario y grupos al entrar
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }

    const initData = async () => {
      try {
        const userData = await getMe(token);
        setUser(userData);
        // Guardamos el ID para identificar mensajes propios
        localStorage.setItem("user_id", userData.id);

        const groupsData = await getMyGroups(token);
        setGroups(groupsData);
      } catch (err) {
        console.error("Error inicializando:", err);
      }
    };

    initData();
  }, [router]);

  // Auto-scroll al final de los mensajes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 2. Seleccionar un grupo y conectar WebSocket
  const selectGroup = async (group) => {
    setSelectedGroup(group);
    const token = localStorage.getItem("token");

    try {
      // 1. Cargar Miembros y generar el Mapa de Usuarios
      const dataMembers = await getGroupMembers(group.id, token);
      setAdminId(dataMembers.admin_id);

      const memberIds = dataMembers.members.map(m => m.id);
      const resUsers = await fetch("http://127.0.0.1:8000/auth/users/by-ids", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(memberIds)
      });

      const usersData = await resUsers.json();
      const newMap = {};
      usersData.forEach(u => { newMap[u.id] = u.username; });
      setUserMap(newMap);
      setMembers(dataMembers.members.map(m => ({ ...m, username: newMap[m.id] || `ID: ${m.id}` })));

      // 2. CARGAR HISTORIAL (Tu nuevo endpoint)
      const resMsgs = await fetch(`http://127.0.0.1:8000/ws/groups/${group.id}/messages?limit=50`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const history = await resMsgs.json();

      // Importante: .reverse() para que el ID 1 aparezca antes que el ID 2
      setMessages(history.reverse());

      // 3. RECONECTAR WEBSOCKET
      if (socketRef.current) socketRef.current.close();

      const wsUrl = `ws://127.0.0.1:8000/ws/groups/${group.id}?token=${token}`;
      socketRef.current = new WebSocket(wsUrl);

      socketRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.action === "new_message") {
          setMessages((prev) => [...prev, data]);
        }
      };

    } catch (err) {
      console.error("Error al cargar el grupo:", err);
    }
  };

  // 3. Enviar Mensaje
  const sendMessage = () => {
    // Verificamos que haya texto y que el socket esté ABIERTO (estado 1)
    if (!newMessage.trim() || !socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.error("El socket no está listo o el mensaje está vacío");
      return;
    }

    const messagePayload = {
      action: "send_message",
      content: newMessage
    };

    socketRef.current.send(JSON.stringify(messagePayload));
    setNewMessage(""); // Limpiar input
  };

  const logout = () => {
    localStorage.clear();
    router.push("/login");
  };

  return (
    <div>
      {/* HEADER */}
      <div className="header">
        <div className="menu-container">
          <button className="menu-btn" onClick={() => setMenuOpen(!menuOpen)}>☰</button>
          <div className={`dropdown ${!menuOpen ? "hidden" : ""}`}>
            <button onClick={() => router.push("/create-group")}>Crear grupo</button>
            <button onClick={logout}>Cerrar sesión</button>
          </div>
        </div>

        <div style={{ fontWeight: "bold" }}>
          {user ? user.username : "Cargando..."}
        </div>

        <h1>GroupsApp</h1>
      </div>

      {/* CONTENEDOR PRINCIPAL */}
      <div className="chat-container">

        {/* PANEL DE GRUPOS */}
        <div className="contacts-panel">
          <div className="contacts-header">Grupos</div>
          <div className="contacts-list">
            {groups.map((group) => (
              <div
                key={group.id}
                className={`contact ${selectedGroup?.id === group.id ? "active" : ""}`}
                onClick={() => selectGroup(group)}
              >
                <div className="avatar"></div>
                <span>{group.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* PANEL DE CHAT */}
        <div className="chat-panel">
          <div className="chat-header">
            <span>{selectedGroup ? selectedGroup.name : "Selecciona un grupo"}</span>

            {selectedGroup && (
              <div className="chat-menu-container">
                <button className="chat-menu-btn" onClick={() => setMembersOpen(!membersOpen)}>☰</button>
                <div className={`members-dropdown ${!membersOpen ? "hidden" : ""}`}>
                  <div className="members-list">
                    {members.map((m) => (
                      <div key={m.id} className="member-item">
                        {m.username} {m.is_admin ? "(admin)" : ""}
                      </div>
                    ))}
                  </div>

                  {/* BOTÓN DE EDICIÓN SOLO PARA EL ADMIN */}
                  {Number(user?.id) === Number(adminId) && (
                    <button
                      className="edit-group-btn"
                      onClick={() => router.push(`/edit-group?group_id=${selectedGroup.id}`)}
                    >
                      Editar grupo
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="chat-messages">
            {messages.map((msg, index) => {
              const isMine = Number(msg.sender_id) === Number(user?.id);

              // BUSCAMOS EL NOMBRE EN EL MAPA USANDO EL ID DEL REMITENTE
              const senderName = userMap[msg.sender_id] || `Usuario ${msg.sender_id}`;

              return (
                <div key={index} className={`message ${isMine ? "sent" : "received"}`}>
                  {!isMine && (
                    <strong className="sender-name">
                      {senderName}
                      <br />
                    </strong>
                  )}
                  <div className="message-content">
                    {msg.content}
                  </div>
                </div>
              );
            })}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input">
            <input
              placeholder="Escribe un mensaje..."
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              disabled={!selectedGroup}
            />
            <button onClick={sendMessage} disabled={!selectedGroup} className="button-chat">Enviar</button>
          </div>
        </div>
      </div>
    </div>
  );
}