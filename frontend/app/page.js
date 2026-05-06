import Link from "next/link";

export default function Home() {
  return (
    <div className="container">
      <div className="card">

        <h1>GroupsApp</h1>
        <p>Conéctate y chatea en grupo</p>

        <Link href="/login">
          <button className="login-btn">Iniciar Sesión</button>
        </Link>

        <Link href="/signup">
          <button className="signup-btn">Registrarse</button>
        </Link>

      </div>
    </div>
  );
}