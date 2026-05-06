"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { registerRequest, loginRequest } from "@/lib/api";
import { parseJwt } from "@/lib/auth";

export default function SignupPage() {
  const router = useRouter();

  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: ""
  });

  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const [showPass, setShowPass] = useState(false);
  const [showPass2, setShowPass2] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");
    setSuccess(false);

    // Validación básica de contraseñas
    if (form.password !== form.confirmPassword) {
      setError("Las contraseñas no coinciden");
      return;
    }

    try {
      // 1. Petición de Registro
      await registerRequest({
        username: form.username,
        email: form.email,
        password: form.password
      });

      setSuccess(true);

      // 2. Login automático tras registro exitoso
      // Usamos FormData porque el loginRequest espera Oauth2 (password flow)
      const loginData = new FormData();
      loginData.append("username", form.username);
      loginData.append("password", form.password);

      const data = await loginRequest(loginData);

      const token = data.access_token;
      const decoded = parseJwt(token);

      // 3. Guardar en localStorage (Consistente con tu sistema de chats)
      localStorage.setItem("token", token);
      localStorage.setItem("user_id", decoded.sub);
      
      // Opcional: Guardar el objeto user completo si tu decoded lo trae
      localStorage.setItem("user", JSON.stringify({
        id: decoded.sub,
        username: form.username
      }));

      // Redirección rápida
      setTimeout(() => {
        router.push("/chats");
      }, 1000);

    } catch (err) {
      // Manejo de errores del backend (ej: usuario ya existe)
      setError(err.message || "Error al crear la cuenta");
    }
  };

  return (
    <div className="container">
      <div className="card">
        <h1>Crear cuenta</h1>

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <input
              type="text"
              placeholder="Usuario"
              required
              value={form.username}
              onChange={(e) =>
                setForm({ ...form, username: e.target.value })
              }
            />
          </div>

          <div className="input-group">
            <input
              type="email"
              placeholder="Correo electrónico"
              required
              value={form.email}
              onChange={(e) =>
                setForm({ ...form, email: e.target.value })
              }
            />
          </div>

          <div className="input-group">
            <input
              type={showPass ? "text" : "password"}
              placeholder="Contraseña"
              required
              value={form.password}
              onChange={(e) =>
                setForm({ ...form, password: e.target.value })
              }
            />
            <span
              className="toggle-pass"
              onClick={() => setShowPass(!showPass)}
              style={{ cursor: "pointer" }}
            >
              {showPass ? "🙈" : "👁️"}
            </span>
          </div>

          <div className="input-group">
            <input
              type={showPass2 ? "text" : "password"}
              placeholder="Confirmar contraseña"
              required
              value={form.confirmPassword}
              onChange={(e) =>
                setForm({ ...form, confirmPassword: e.target.value })
              }
            />
            <span
              className="toggle-pass"
              onClick={() => setShowPass2(!showPass2)}
              style={{ cursor: "pointer" }}
            >
              {showPass2 ? "🙈" : "👁️"}
            </span>
          </div>

          <button type="submit">Registrarse</button>

          {error && <div className="message error" style={{ display: 'block' }}>{error}</div>}
          {success && (
            <div className="message success" style={{ display: 'block' }}>
              Cuenta creada correctamente. Iniciando sesión...
            </div>
          )}
        </form>

        <div className="link">
          ¿Ya tienes cuenta? <a href="/login">Inicia sesión</a>
        </div>
      </div>
    </div>
  );
}