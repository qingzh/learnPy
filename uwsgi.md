* nginx 配置
server {
    listen   80;
    server_name xxx.com;

    try_files $uri @uwsgi;
    location @uwsgi  {
        uwsgi_pass 127.0.0.1:3031;
        include uwsgi_params;
        uwsgi_param UWSGI_SCHEME $scheme;
        uwsgi_param SERVER_SOFTWARE nginx/$nginx_version;
    }

    location / {
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:3031;
    }
}