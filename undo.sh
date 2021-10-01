set -x

vtysh <<EOF
conf te
router isis 1
 segment-routing srv6
  no locator test
EOF

vtysh -c 'sh run isisd'
