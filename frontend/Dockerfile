FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

EXPOSE 2000

# Expose host to 0.0.0.0 for Docker container port mapping
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
