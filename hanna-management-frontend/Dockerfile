# Stage 1: Build the Next.js application
FROM node:20-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
# to leverage Docker cache for dependencies
COPY package*.json ./

# Install dependencies
RUN npm install && npm install react-icons zustand

# Copy the rest of the application code
COPY . .


# Build the Next.js application
# 'next build' creates an optimized production build in the .next directory
RUN npm run build

# Stage 2: Serve the application with a lightweight Node.js runtime
FROM node:20-alpine AS runner

WORKDIR /app

# Set environment variables for Next.js production
ENV NODE_ENV production

# Copy only necessary files from the builder stage
# This includes the built application, public assets, and node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/next.config.ts ./
COPY --from=builder /app/tsconfig.json ./tsconfig.json

# If you have any custom server.js or other root-level files needed for runtime, copy them here.
# For a standard Next.js app, the .next directory contains everything needed.

# Expose the port Next.js runs on
EXPOSE 3000

# Command to run the application
# 'next start' serves the production build
CMD ["npm", "start"]