rm /tmp/in.pcap
nsenter -a -t $(cat /tmp/topotests/isis_srv6_topo1.test_isis_srv6_topo1/r3.pid) tcpdump -nni eth1 -vvv -w /tmp/in.pcap
