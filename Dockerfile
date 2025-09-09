FROM nginx:alpine

# Удалим дефолтный индекс, чтобы не мешал
RUN rm -f /usr/share/nginx/html/*

# Копируем только то, что прошло через .dockerignore
COPY . /usr/share/nginx/html/

# По умолчанию nginx слушает 80
EXPOSE 80
