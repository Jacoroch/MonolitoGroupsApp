# 1. Imagen base
FROM node:20-slim

# 2. Directorio de trabajo
WORKDIR /app

# 3. Gestión de dependencias
COPY package*.json ./

# Instalamos TODAS las dependencias (necesitamos Tailwind para el build)
RUN npm cache clean --force && npm install

# 4. Copiar el código fuente
COPY . .

# 5. Construimos la aplicación de Next.js
RUN npm run build

# 6. AHORA SÍ, declaramos el entorno de producción para el tiempo de ejecución
ENV NODE_ENV=production

# 7. Exponer el puerto
EXPOSE 3000

CMD ["npm", "start"]