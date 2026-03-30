FROM node:22-slim

WORKDIR /app

# Installer les dépendances
COPY package.json package-lock.json* ./
RUN npm install

# Copier le code source
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
