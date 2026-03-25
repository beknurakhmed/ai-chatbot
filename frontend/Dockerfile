FROM node:22-alpine

WORKDIR /app

# Install deps
COPY package.json package-lock.json* ./
RUN npm install

# Copy app
COPY . .

# Build
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
