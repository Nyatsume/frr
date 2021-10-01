set -x

vtysh <<EOF
conf te
router isis 1
 segment-routing srv6
  locator loc1
EOF

vtysh -c 'sh run isisd'
