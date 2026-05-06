"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createGroup, addUserToGroup } from "@/lib/api";

export default function CreateGroupPage() {
  const router = useRouter();

  const [token, setToken] = useState(null);
  const [groupData, setGroupData] = useState({ name: "", description: "" });
  const [currentGroupId, setCurrentGroupId] = useState(null);
  
  const [searchUsername, setSearchUsername] = useState("");
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedUsers, setSelectedUsers] = useState([]);
  
  const [groupMsg, setGroupMsg] = useState({ text: "", type: "" });
  const [userMsg, setUserMsg] = useState({ text: "", type: "" });

  useEffect(() => {
    const t = localStorage.getItem("token");
    if (!t) {
      router.push("/login");
      return;
    }
    setToken(t);
  }, [router]);

  const showMessage = (setter, text, type) => {
    setter({ text, type });
    setTimeout(() => setter({ text: "", type: "" }), 3000);
  };

  // 🧱 CREAR GRUPO
  const handleCreateGroup = async (e) => {
    e.preventDefault();
    try {
      const res = await createGroup(groupData, token);
      setCurrentGroupId(res.id);
      showMessage(setGroupMsg, "Grupo creado correctamente ✅", "success");
    } catch (err) {
      showMessage(setGroupMsg, "Error creando grupo", "error");
    }
  };

  // 🔍 BUSCAR USUARIO (Adaptado al formato de array del backend)
  const handleSearchUser = async () => {
    if (!searchUsername.trim()) return;
    try {
      // Usamos el endpoint de búsqueda que devuelve un array: [{"id":2,"username":"a"}]
      const response = await fetch(`http://127.0.0.1:8000/auth/users/search?username=${searchUsername}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      
      const data = await response.json();

      if (response.ok && data.length > 0) {
        setSelectedUser(data[0]); // Tomamos el primer resultado
      } else {
        setSelectedUser(null);
        showMessage(setUserMsg, "No encontrado ❌", "error");
      }
    } catch (err) {
      setSelectedUser(null);
      showMessage(setUserMsg, "Error en la búsqueda", "error");
    }
  };

  // ➕ AGREGAR A LISTA TEMPORAL
  const addUserToList = () => {
    if (!selectedUser) {
      showMessage(setUserMsg, "Busca un usuario primero", "error");
      return;
    }
    if (selectedUsers.find(u => u.id === selectedUser.id)) {
      showMessage(setUserMsg, "Usuario ya agregado", "error");
      return;
    }
    setSelectedUsers([...selectedUsers, selectedUser]);
    setSelectedUser(null);
    setSearchUsername("");
  };

  const removeUserFromList = (id) => {
    setSelectedUsers(selectedUsers.filter(u => u.id !== id));
  };

  // 🚀 AGREGAR TODOS AL BACKEND
  const addAllUsersToGroup = async () => {
    if (!currentGroupId) {
      showMessage(setUserMsg, "Primero crea el grupo", "error");
      return;
    }
    if (selectedUsers.length === 0) {
      showMessage(setUserMsg, "No hay usuarios seleccionados", "error");
      return;
    }

    try {
      for (const user of selectedUsers) {
        await addUserToGroup(currentGroupId, user.id, token);
      }
      showMessage(setUserMsg, "Usuarios agregados correctamente ✅", "success");
      setSelectedUsers([]);
    } catch (err) {
      showMessage(setUserMsg, "Error agregando algunos usuarios", "error");
    }
  };

  return (
    <div className="group-container">
      <h1>Crear Grupo 👥</h1>

      {/* SECCIÓN 1: DATOS DEL GRUPO */}
      <div className="card">
        <h2>Datos del grupo</h2>
        <form onSubmit={handleCreateGroup}>
          <input
            type="text"
            placeholder="Nombre del grupo"
            required
            value={groupData.name}
            onChange={e => setGroupData({ ...groupData, name: e.target.value })}
          />
          <input
            type="text"
            placeholder="Descripción"
            required
            value={groupData.description}
            onChange={e => setGroupData({ ...groupData, description: e.target.value })}
          />
          <button type="submit">Crear Grupo</button>
          
          {groupMsg.text && (
            <div className={`message ${groupMsg.type}`} style={{ display: 'block' }}>
              {groupMsg.text}
            </div>
          )}
        </form>
      </div>

      {/* SECCIÓN 2: AGREGAR MIEMBROS */}
      <div className="card">
        <h2>Agregar miembros 🔍</h2>
        <div className="row">
          <input
            type="text"
            placeholder="Buscar username"
            value={searchUsername}
            onChange={e => setSearchUsername(e.target.value)}
          />
          <button onClick={handleSearchUser}>Buscar</button>
          <button className="secondary-btn" onClick={addUserToList}>➕</button>
        </div>

        <p id="searchResult">
          {selectedUser ? `Encontrado: ${selectedUser.username}` : ""}
        </p>

        <h3>Usuarios seleccionados:</h3>
        <div id="userList">
          {selectedUsers.map(user => (
            <div key={user.id} className="user-item">
              <span>{user.username}</span>
              <button className="remove-btn" onClick={() => removeUserFromList(user.id)}>❌</button>
            </div>
          ))}
        </div>

        <button style={{ marginTop: "10px" }} onClick={addAllUsersToGroup}>
          Agregar todos al grupo
        </button>

        {userMsg.text && (
          <div className={`message ${userMsg.type}`} style={{ display: 'block' }}>
            {userMsg.text}
          </div>
        )}
      </div>

      <Link href="/chats" className="back-link">
        ⬅ Volver
      </Link>
    </div>
  );
}