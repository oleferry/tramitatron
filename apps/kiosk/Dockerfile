# Imagen de DESARROLLO del kiosco (servidor Vite con proxy hacia api y
# device-agent). La imagen de producción (build estático + kiosk mode) llegará
# con el hardening de la fase 5.
FROM node:22-alpine

WORKDIR /srv

COPY package.json package-lock.json ./
RUN npm ci --no-fund --no-audit

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
