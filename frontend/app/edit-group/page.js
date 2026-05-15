"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import Swal from "sweetalert2";
import { getGroupMembers, searchUser, addUserToGroup } from "@/lib/api";

function EditGroupContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const groupId = searchParams.get("group_id");

  const [members, setMembers] = useState([]);
  const [usernameInput, setUsernameInput] = useState("");
  const [loading, setLoading] = useState(true);

  // ✅ CORREGIDO: Declaramos la variable de entorno al inicio del componente
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const loadMembers = async () => {
    if (!token || !groupId) return;
    setLoading(true);

    try {
      // 1. Obtenemos los miembros (que vienen con ID e is_admin)
      // ✅ CORREGIDO
      const resMembers = await fetch(`${API_URL}/groups/${groupId}/members`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await resMembers.json();
      const membersList = data.members; // [{id: 1, is_admin: true}, ...]

      // 2. Extraemos solo los IDs para buscar sus nombres
      const memberIds = membersList.map(m => m.id);

      // 3. Pedimos los nombres al endpoint de búsqueda masiva
      // ✅ CORREGIDO
      const resNames = await fetch(`${API_URL}/auth/users/by-ids`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(memberIds)
      });
      const usersData = await resNames.json(); // [{id: 1, username: "Jose"}, ...]

      // 4. Creamos el mapa (diccionario) para búsqueda rápida
      const nameMap = {};
      usersData.forEach(u => {
        nameMap[u.id] = u.username;
      });

      // 5. Combinamos la info: ponemos el nombre dentro de cada objeto miembro
      const fullMembers = membersList.map(m => ({
        ...m,
        username: nameMap[m.id] || `Usuario ${m.id}` // Si no hay nombre, mostramos el ID
      }));

      setMembers(fullMembers);
    } catch (err) {
      console.error("Error al cargar nombres de miembros:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMembers();
  }, [groupId]);

  const handleRemoveUser = async (userId) => {
    const result = await Swal.fire({
      title: "¿Eliminar usuario?",
      text: "Esta acción no se puede deshacer",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#dc2626",
      cancelButtonColor: "#334155",
      confirmButtonText: "Sí, eliminar",
      cancelButtonText: "Cancelar",
      background: "#1e293b",
      color: "#e2e8f0"
    });

    if (!result.isConfirmed) return;

    try {
      // ✅ CORREGIDO
      const res = await fetch(`${API_URL}/groups/${groupId}/members/${userId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (res.ok) {
        Swal.fire({ title: "Eliminado", icon: "success", timer: 1500, showConfirmButton: false, background: "#1e293b", color: "#e2e8f0" });
        loadMembers();
      }
    } catch (err) {
      Swal.fire("Error", "No se pudo eliminar", "error");
    }
  };

  const handleAddUser = async () => {
    if (!usernameInput.trim()) return;
    const token = localStorage.getItem("token");

    try {
      // 1. BUSCAR EL USUARIO
      // ✅ CORREGIDO
      const searchRes = await fetch(`${API_URL}/auth/users/search?username=${usernameInput}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });

      if (!searchRes.ok) throw new Error("Error en la búsqueda");

      const searchData = await searchRes.json();

      // Validar si el usuario existe en la lista recibida
      if (searchData.length === 0) {
        Swal.fire({
          title: "No encontrado",
          text: "El usuario no existe",
          icon: "error",
          background: "#1e293b",
          color: "#e2e8f0"
        });
        return;
      }

      // EXTRAER EL ID (del primer elemento de la lista)
      const userId = searchData[0].id;

      // 2. ENVIAR EL ID AL GRUPO
      // ✅ CORREGIDO
      const response = await fetch(`${API_URL}/groups/${groupId}/members`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ user_id: userId }) 
      });

      if (response.ok) {
        Swal.fire({
          title: "Agregado",
          text: "Usuario añadido al grupo",
          icon: "success",
          timer: 2000,
          background: "#1e293b",
          color: "#e2e8f0"
        });
        setUsernameInput(""); // Limpiar input
        loadMembers(); // Recargar lista de miembros
      } else {
        const errorDetail = await response.json();
        throw new Error(errorDetail.detail || "Error al agregar");
      }

    } catch (err) {
      Swal.fire({
        title: "Error",
        text: err.message,
        icon: "error",
        background: "#1e293b",
        color: "#e2e8f0"
      });
    }
  };

  return (
    <div className="group-container">
      <h1>Editar Grupo 👥</h1>

      {/* MIEMBROS */}
      <div className="card">
        <h2>Miembros</h2>
        <div id="membersList">
          {loading ? (
            <p>Cargando miembros...</p>
          ) : (
            members.map((user) => (
              <div key={user.id} className="member">
                <span className={user.is_admin ? "admin" : ""}>
                  {user.username} {user.is_admin ? "(admin)" : ""}
                </span>
                {!user.is_admin && (
                  <button className="remove-btn" onClick={() => handleRemoveUser(user.id)}>
                    ❌
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* AGREGAR USUARIO */}
      <div className="card">
        <h3>Agregar usuario</h3>
        <div className="row">
          <input
            type="text"
            id="usernameInput"
            placeholder="username"
            value={usernameInput}
            onChange={(e) => setUsernameInput(e.target.value)}
          />
          <button onClick={handleAddUser}>Agregar</button>
        </div>
      </div>

      <Link href="/chats">⬅ Volver</Link>
    </div>
  );
}

export default function EditGroupPage() {
  return (
    <Suspense fallback={<div className="container">Cargando...</div>}>
      <EditGroupContent />
    </Suspense>
  );
}