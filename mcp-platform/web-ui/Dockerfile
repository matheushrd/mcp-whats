# Use a imagem base nginx:alpine
FROM nginx:alpine

# Instale curl
# A diretiva USER root garante que temos permissão para instalar pacotes.
# A imagem nginx:alpine já roda como root por padrão para essas operações.
RUN apk add --no-cache curl

# Copie seus arquivos da interface web
# Certifique-se que os caminhos estão corretos em relação à raiz do contexto do build (mcp-platform/web-ui/)
COPY index.html /usr/share/nginx/html/
# Se você tiver styles.css e script.js, descomente e ajuste os caminhos se necessário:
COPY styles.css /usr/share/nginx/html/
COPY script.js /usr/share/nginx/html/

# Copie sua configuração customizada do Nginx
# Certifique-se que o arquivo nginx.conf existe no seu diretório web-ui
COPY nginx.conf /etc/nginx/nginx.conf

# A porta 80 já é exposta pela imagem base do Nginx
# O CMD padrão da imagem base do Nginx é "nginx -g daemon off;", que é o que queremos.
