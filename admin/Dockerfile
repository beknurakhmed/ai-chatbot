FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# Build — Next.js reads NEXT_PUBLIC_* from .env.local at build time
RUN npm run build

EXPOSE 3001

CMD ["npm", "start"]
