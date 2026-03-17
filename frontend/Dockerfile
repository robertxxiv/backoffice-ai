FROM node:22-alpine

WORKDIR /app/frontend

COPY frontend/package.json ./package.json
COPY frontend/package-lock.json ./package-lock.json
RUN npm ci

COPY frontend ./

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
