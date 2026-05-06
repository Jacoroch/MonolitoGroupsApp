const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://0.0.0.0:8000";

/**
 * UTILS: Manejo de respuestas para evitar repetir código
 */
async function handleResponse(res, errorMessage) {
  if (!res.ok) {
    // Intentamos extraer el detalle del error del backend (FastAPI suele enviarlo en 'detail')
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || errorMessage);
  }
  return res.json();
}

/**
 * AUTH: Registro y Autenticación
 */

// 1. Registro de nuevo usuario
export async function registerRequest(data) {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  return handleResponse(res, "Error en el registro");
}

// 2. Login (IMPORTANTE: Recibe FormData para ser compatible con OAuth2/FastAPI)
export async function loginRequest(formData) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    // No ponemos Content-Type manual aquí, el navegador lo pone automáticamente al enviar FormData
    body: formData 
  });
  return handleResponse(res, "Credenciales incorrectas");
}

// 3. Obtener mi propia información
export async function getMe(token) {
  const res = await fetch(`${API_URL}/auth/me`, {
    headers: { 
      "Authorization": `Bearer ${token}` 
    }
  });
  return handleResponse(res, "No se pudo obtener la información del usuario");
}

/**
 * GROUPS: Manejo de grupos y miembros
 */
export async function getMyGroups(token) {
  const res = await fetch(`${API_URL}/groups/my-groups`, {
    headers: { 
      "Authorization": `Bearer ${token}` 
    }
  });
  return handleResponse(res, "Error cargando tus grupos");
}

export async function createGroup(data, token) {
  const res = await fetch(`${API_URL}/groups/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify(data)
  });
  return handleResponse(res, "Error creando el grupo");
}

export async function getGroupMembers(groupId, token) {
  const res = await fetch(`${API_URL}/groups/${groupId}/members`, {
    headers: { 
      "Authorization": `Bearer ${token}` 
    }
  });
  return handleResponse(res, "Error cargando miembros del grupo");
}

/**
 * USERS: Búsqueda y gestión
 */

// Busca usuarios por nombre (Recuerda que devuelve una lista [])
export async function searchUser(username, token) {
  const res = await fetch(`${API_URL}/auth/users/search?username=${username}`, {
    headers: {
      "Authorization": `Bearer ${token}`
    }
  });
  return handleResponse(res, "Usuario no encontrado");
}

// Agrega un usuario al grupo
export async function addUserToGroup(groupId, userId, token) {
  const res = await fetch(`${API_URL}/groups/${groupId}/members`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ user_id: userId })
  });
  return handleResponse(res, "Error agregando usuario al grupo");
}

/**
 * MESSAGES: Historial de chat
 */
export async function getMessages(groupId, token) {
  const res = await fetch(`${API_URL}/ws/groups/${groupId}/messages`, {
    headers: { 
      "Authorization": `Bearer ${token}` 
    }
  });
  return handleResponse(res, "Error cargando el historial de mensajes");
}