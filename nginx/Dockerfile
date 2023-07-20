FROM ubuntu:22.04

# Atualize o sistema e instale as dependências
RUN apt-get update
RUN apt-get install -y build-essential nano wget apache2-dev unzip libpcre3 libpcre3-dev make perl apache2-utils

RUN wget "http://nginx.org/download/nginx-1.17.7.tar.gz" -O /tmp/nginx-1.17.7.tar.gz
RUN wget "https://github.com/atomx/nginx-http-auth-digest/archive/master.zip" -O /tmp/nginx-http-auth-digest.zip
RUN wget "https://zlib.net/fossils/zlib-1.2.11.tar.gz" -O /tmp/zlib-1.2.11.tar.gz
RUN wget "https://www.openssl.org/source/openssl-1.1.1d.tar.gz" -O /tmp/openssl-1.1.1d.tar.gz

RUN tar zxvf /tmp/nginx-1.17.7.tar.gz -C /usr/local/src/
RUN unzip /tmp/nginx-http-auth-digest.zip -d /usr/local/src/
RUN tar zxvf /tmp/zlib-1.2.11.tar.gz -C /usr/local/src/
RUN tar zxvf /tmp/openssl-1.1.1d.tar.gz -C /usr/local/src/

RUN cd /usr/local/src/nginx-1.17.7 && \
    ./configure --prefix=/etc/nginx --sbin-path=/usr/sbin/nginx --conf-path=/etc/nginx/nginx.conf --error-log-path=/var/log/nginx/error.log --http-log-path=/var/log/nginx/access.log --pid-path=/var/run/nginx.pid --lock-path=/var/run/nginx.lock --http-client-body-temp-path=/var/cache/nginx/client_temp --http-proxy-temp-path=/var/cache/nginx/proxy_temp --http-fastcgi-temp-path=/var/cache/nginx/fastcgi_temp --http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp --http-scgi-temp-path=/var/cache/nginx/scgi_temp --user=nginx --group=nginx --with-openssl=/usr/local/src/openssl-1.1.1d --with-zlib=/usr/local/src/zlib-1.2.11 --with-http_ssl_module --with-http_realip_module --with-http_addition_module --with-http_sub_module --with-http_dav_module --with-http_flv_module --with-http_mp4_module --with-http_gunzip_module --with-http_gzip_static_module --with-http_random_index_module --with-http_secure_link_module --with-http_stub_status_module --with-http_auth_request_module --with-mail --with-mail_ssl_module --with-file-aio --with-http_v2_module --with-cc-opt='-O2 -g -pipe -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -fstack-protector --param=ssp-buffer-size=4 -m64 -mtune=generic' --add-module=../nginx-http-auth-digest-master/ && \
    make && make install

# Copie a configuração padrão do Nginx
RUN rm /etc/nginx/nginx.conf
COPY nginx.conf /etc/nginx/
COPY project.conf /etc/nginx/

RUN groupadd nginx
RUN useradd -g nginx nginx
RUN usermod -s /bin/false nginx

RUN mkdir -p /var/cache/nginx/client_temp

COPY nginx.service /usr/lib/systemd/system/
COPY nginx /etc/logrotate.d/
COPY digest /etc/nginx/
# Expõe a porta 80
EXPOSE 80

# Inicia o serviço do Nginx ao iniciar o contêiner
CMD ["nginx", "-g", "daemon off;"]



