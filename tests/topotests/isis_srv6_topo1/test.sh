source /etc/fdk-local.bash
fdk-enter-ctx r1.pid ip -6 route | grep seg6local
fdk-enter-ctx r2.pid ip -6 route | grep seg6local
fdk-enter-ctx r3.pid ip -6 route | grep seg6local
fdk-enter-ctx r4.pid ip -6 route | grep seg6local
