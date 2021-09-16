vtysh -c "conf t" \
-c "router isis 1" \
-c "srv6 locator loc1"
vtysh -c "show isis segment-routing srv6"
vtysh -c "show segment-routing srv6 loc json"
