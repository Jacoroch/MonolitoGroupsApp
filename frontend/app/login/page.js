"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { loginRequest } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();

  const [form, setForm] = useState({
    username: "",
    password: ""
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    // Previene el refresco de página y el "?" en la URL
    e.preventDefault();
    
    setLoading(true);
    setError("");

    try {
      // Usamos la URLSearchParams directamente para cumplir con OAuth2 de FastAPI
      const formData = new URLSearchParams();
      formData.append("username", form.username);
      formData.append("password", form.password);
      formData.append("grant_type", "password");

      const res = await fetch("http://127.0.0.1:8000/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded"
        },
        body: formData
      });

      const data = await res.json();

      if (res.ok) {
        // Guardamos el token para las peticiones en /chats
        localStorage.setItem("token", data.access_token);
        
        console.log("Login exitoso, redirigiendo...");
        router.push("/chats");
      } else {
        setError(data.detail || "Usuario o contraseña incorrectos");
      }

    } catch (err) {
      console.error("Error:", err);
      setError("Error de conexión con el servidor");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="card">
        <h1>Iniciar Sesión</h1>

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <input
              type="text"
              placeholder="Usuario"
              required
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
            />
          </div>

          <div className="input-group">
            <input
              type="password"
              placeholder="Contraseña"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </div>

          <button type="submit" disabled={loading}>
            {loading ? "Cargando..." : "Entrar"}
          </button>

          {error && (
            <div className="error">
              {error}
            </div>
          )}
        </form>

        <div className="link">
          ¿No tienes cuenta? <a href="/signup">Regístrate</a>
        </div>
      </div>
    </div>
  );
}