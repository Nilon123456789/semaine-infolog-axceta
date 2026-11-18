# Build the Axceta dashboard, then serve with nginx.
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
# Browser on the host talks to cloud published on localhost:8000
ARG VITE_CLOUD_URL=http://localhost:8000
ENV VITE_CLOUD_URL=$VITE_CLOUD_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
