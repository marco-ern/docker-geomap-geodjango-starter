# Etapa 1: build de la app Vue
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

# Recibir la variable en build
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY . .
RUN npm run build

# Etapa 2: Nginx para servir estáticos
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Opcional: si vas a usar proxy hacia Django ajustas nginx.conf después
# COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]