# Deploy-only: static files are pre-built locally via `npm run build`.
# Cloud Build just packages the `out/` directory into an nginx container.
FROM nginx:alpine
COPY out/ /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
