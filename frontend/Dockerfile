# 1. Imagen base: Usamos la versión estable de Node (Alpine para que sea ligero)
FROM node:18-alpine

# 2. Variables de entorno
# Establecemos el entorno como producción para optimizar Next.js
ENV NODE_ENV=production

# 3. Directorio de trabajo
WORKDIR /app

# 4. Gestión de dependencias
# Copiamos package.json y package-lock.json primero
COPY package*.json ./

# Instalamos las dependencias (usando npm ci para instalaciones limpias y exactas)
RUN npm install

# 5. Copiar el código fuente y construir la app
COPY . .

# Construimos la aplicación de Next.js
RUN npm run build

# 6. Exponer el puerto que usa Next.js (por defecto 3000)
EXPOSE 3000

# Al igual que en tu back, si usarás docker-compose, el comando se puede definir allá.
# Pero dejamos este por defecto para que el contenedor pueda correr solo:
CMD ["npm", "start"]