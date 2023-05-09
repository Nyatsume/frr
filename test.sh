set -x
vtysh -c "conf t" \
-c "router isis 1" \
-c "srv6 locator loc1"
