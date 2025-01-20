docker network inspect my_local_network >/dev/null 2>&1 || docker network create --driver bridge my_local_network &&
docker build -t secure-messenger . &&
sudo docker run --network my_local_network -it --rm secure-messenger "$@"