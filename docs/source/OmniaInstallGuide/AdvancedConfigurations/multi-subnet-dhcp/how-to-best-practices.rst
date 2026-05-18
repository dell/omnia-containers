.. _how-to-multi-subnet-dhcp-best-practices:

Multi-Subnet DHCP Best Practices
================================

Apply operational guidelines and recommendations to ensure reliable, secure, and performant multi-subnet DHCP deployments. These best practices cover planning, configuration, operations, security, and monitoring for rack-based network provisioning.

Planning Best Practices
------------------------

Subnet Allocation Strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~

Plan subnet allocations systematically to avoid conflicts and support growth:

**Use Consistent Subnet Patterns**
- Allocate subnets with a consistent pattern (e.g., odd-numbered third octets)
- Example: ``10.40.1.0/24``, ``10.40.3.0/24``, ``10.40.5.0/24``
- This makes subnet identification and troubleshooting easier

**Document All Allocations**
- Maintain an IP Address Management (IPAM) system
- Record subnet allocations, gateway IPs, and DHCP pool ranges
- Track static IP assignments (gateways, OIM, service nodes)
- Update documentation when allocations change

**Reserve Subnet Ranges for Growth**
- Plan for future rack additions by reserving subnet ranges
- Example: Reserve ``10.40.21.0/24`` through ``10.40.31.0/24`` for future racks
- Avoid using contiguous subnets for unrelated purposes

**Align Subnet Allocation with Rack Numbering**
- Map rack IDs to subnet third octets for clarity
- Example: Rack 1 → ``10.40.1.0/24``, Rack 2 → ``10.40.3.0/24``
- This simplifies physical-to-logical mapping

Rack Topology Design
~~~~~~~~~~~~~~~~~~~~

Design rack topology to optimize network operations:

**Group Related Racks Together**
- Allocate contiguous subnets to racks in the same row or zone
- Example: Row 1 racks use ``10.40.1.0/24`` through ``10.40.9.0/24``
- Simplifies network segmentation and ACL policies

**Consider Physical Network Layout**
- Align subnet allocation with physical switch topology
- Ensure routing paths are optimized for the physical layout
- Minimize hop count between racks and CoreDHCP server

**Plan for Rack Expansion**
- Reserve subnet ranges for additional racks in each row
- Document expansion plans in network design documents
- Update routing and ACL policies when adding racks

DHCP Pool Sizing
~~~~~~~~~~~~~~~

Size DHCP pools appropriately for each subnet:

**Pool Size Guidelines**
- Minimum: 50 IPs for small racks (up to 25 nodes)
- Standard: 100 IPs for medium racks (up to 50 nodes)
- Large: 200 IPs for large racks (up to 100 nodes)

**Reserve Space for Static IPs**
- Reserve IP ranges at the start and end of each subnet for static assignments
- Example: Use ``10.40.1.1-10.40.1.99`` for gateways and static IPs
- Use ``10.40.1.201-10.40.1.254`` for additional static IPs
- DHCP pool: ``10.40.1.100-10.40.1.200``

**Monitor Pool Utilization**
- Track DHCP pool usage per subnet
- Alert when pool utilization exceeds 80%
- Plan to expand pools or add subnets when approaching exhaustion

Configuration Best Practices
---------------------------

Network Specification File Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Manage ``network_spec.yml`` changes systematically:

**Use Version Control**
- Track all changes to ``network_spec.yml`` in version control
- Commit changes with descriptive messages
- Tag releases for rollback capability

**Backup Before Changes**
- Create backups of ``network_spec.yml`` before making changes
- Example: ``cp network_spec.yml network_spec.yml.backup.$(date +%Y%m%d)``
- Keep backups for at least 30 days

**Validate Before Deployment**
- Always run validation playbook before deploying changes
- Fix validation errors before proceeding with deployment
- Document validation results in change records

**Test in Staging Environment**
- Test configuration changes in a staging environment first
- Verify DHCP relay and IP assignment work correctly
- Deploy to production only after successful staging validation

Configuration Validation
~~~~~~~~~~~~~~~~~~~~~~

Validate configuration thoroughly before deployment:

**Subnet Overlap Checks**
- Verify no subnets overlap with each other or the admin network
- Use validation playbook to check for overlaps
- Manually verify CIDR calculations for critical subnets

**DHCP Pool Validation**
- Ensure DHCP pool ranges are within subnet boundaries
- Verify pool ranges do not overlap with static IP ranges
- Check that pool start and end IPs are valid

**Gateway Reachability**
- Verify gateway IPs are reachable from the OIM node
- Test routing to each subnet gateway
- Verify DHCP relay can reach CoreDHCP server

**Configuration Consistency**
- Ensure ``router`` parameter matches ToR switch SVI IP
- Verify VLAN IDs match switch configuration
- Confirm netmask_bits match across all subnets in the same deployment

Operational Best Practices
---------------------------

Change Management
~~~~~~~~~~~~~~~~~~

Implement formal change management for network changes:

**Change Request Process**
- Submit change requests for all network configuration changes
- Include impact analysis and rollback plans
- Obtain approval before implementing changes

**Change Windows**
- Schedule network changes during maintenance windows
- Notify affected users of planned changes
- Have on-call support available during change windows

**Rollback Planning**
- Document rollback procedures for each change
- Test rollback procedures in staging
- Ensure backups are available before changes

**Change Documentation**
- Document all changes in change logs
- Include before/after configurations
- Record validation results and issues encountered

Monitoring and Observability
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Monitor multi-subnet DHCP operations proactively:

**DHCP Service Monitoring**
- Monitor CoreDHCP service health and uptime
- Track DHCP request/response rates per subnet
- Alert on DHCP service failures or high error rates

**Subnet Utilization Monitoring**
- Monitor DHCP pool utilization per subnet
- Track IP allocation rates and patterns
- Alert on high utilization or exhaustion

**Network Performance Monitoring**
- Monitor latency between subnets and CoreDHCP server
- Track DHCP response times per subnet
- Monitor network errors and packet loss

**Log Monitoring**
- Monitor CoreDHCP logs for errors and anomalies
- Track DHCP request patterns and unusual activity
- Correlate DHCP logs with network events

Failure Isolation
~~~~~~~~~~~~~~~~~

Implement procedures to isolate and handle failures:

**Rack-Level Isolation**
- Network issues should be contained to individual racks
- Verify that failures in one rack do not affect others
- Test isolation during planned maintenance

**DHCP Relay Failover**
- Configure redundant DHCP relay paths where possible
- Test failover scenarios in staging
- Document failover behavior and recovery procedures

**CoreDHCP High Availability**
- Consider CoreDHCP high-availability configuration for critical deployments
- Plan for CoreDHCP service recovery
- Document manual recovery procedures

Security Best Practices
-----------------------

ACL Policies
~~~~~~~~~~~~

Implement access control lists to restrict network access:

**Restrict DHCP Traffic**
- Allow only DHCP traffic from rack subnets to CoreDHCP server
- Block other traffic from rack subnets to management network
- Example ACL: ``permit udp 10.40.1.0/24 any eq bootpc any eq bootps``

**Limit iDRAC Access**
- Restrict iDRAC access to OOB network only
- Block iDRAC access from Admin network
- Example ACL: ``permit tcp 192.168.0.0/16 any eq 443``

**VLAN Isolation**
- Ensure proper VLAN segregation between rack subnets
- Verify VLAN ACLs prevent unauthorized access
- Document VLAN security policies

VRF Isolation
~~~~~~~~~~~~

Consider VRF (Virtual Routing and Forwarding) for enhanced security:

**VRF for Management Networks**
- Isolate management networks in separate VRFs
- Prevent routing between management and other networks
- Document VRF design and routing policies

**VRF for OOB Networks**
- Isolate OOB/BMC networks in separate VRFs
- Restrict access to iDRAC/BMC interfaces
- Implement VRF-aware firewalls where appropriate

**VRF Routing**
- Configure VRF-aware routing where needed
- Document VRF routing policies and exceptions
- Test VRF connectivity thoroughly

iDRAC Access Control
~~~~~~~~~~~~~~~~~~~

Secure iDRAC/BMC access appropriately:

**Restrict Access Sources**
- Allow iDRAC access only from authorized networks
- Block iDRAC access from public networks
- Use firewall rules to enforce policies

**Implement Authentication**
- Configure iDRAC authentication (LDAP, Active Directory)
- Use strong passwords for local accounts
- Enable account lockout policies

**Audit iDRAC Access**
- Log all iDRAC access attempts
- Monitor for unauthorized access attempts
- Review access logs regularly

Performance Best Practices
-------------------------

Broadcast Domain Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~

Optimize broadcast domains for performance:

**Use /24 Subnets**
- /24 subnets (254 hosts) provide optimal broadcast domain size
- Avoid larger subnets (/23, /22) unless necessary
- Consider /25 subnets (126 hosts) for very small racks

**Monitor Broadcast Traffic**
- Track broadcast traffic per subnet
- Identify and mitigate broadcast storms
- Use storm control on switches if needed

**Optimize ARP Cache**
- Monitor ARP cache size per subnet
- Tune ARP timeout values if necessary
- Consider ARP suppression for large subnets

Routing Optimization
~~~~~~~~~~~~~~~~~~~~

Optimize routing for multi-subnet deployments:

**Centralize CoreDHCP Server**
- Place CoreDHCP server centrally in network topology
- Minimize hop count to all subnets
- Use ECMP for load balancing where possible

**Route Aggregation**
- Use route summarization to reduce routing table size
- Aggregate contiguous subnets where possible
- Document aggregation policies

**Monitor Routing Performance**
- Track routing table size and growth
- Monitor routing convergence times
- Optimize routing protocols for large deployments

DHCP Pool Sizing
~~~~~~~~~~~~~~

Size DHCP pools appropriately for performance:

**Avoid Oversized Pools**
- Large pools increase DHCP scan time
- Size pools based on actual node count
- Monitor pool utilization and adjust as needed

**Pool Placement Within Subnet**
- Place DHCP pools in the middle of subnet range
- Avoid pool edges near network/broadcast addresses
- Reserve space at subnet boundaries for static IPs

**Monitor Pool Performance**
- Track DHCP lease times and renewal patterns
- Monitor pool fragmentation
- Adjust pool sizes based on usage patterns

Capacity Planning
-----------------

Subnet Capacity Planning
~~~~~~~~~~~~~~~~~~~~~~

Plan for subnet capacity and growth:

**Monitor Subnet Utilization**
- Track IP utilization per subnet
- Project growth based on historical trends
- Plan subnet additions before exhaustion

**Reserve Expansion Capacity**
- Reserve subnet ranges for future expansion
- Document expansion plans in capacity planning documents
- Update capacity plans quarterly

**Plan for Rack Additions**
- Document procedures for adding new racks
- Include subnet allocation, routing, and ACL updates
- Test addition procedures in staging

DHCP Pool Capacity Planning
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Plan for DHCP pool capacity:

**Monitor Pool Utilization**
- Track pool utilization per subnet
- Alert when utilization exceeds 80%
- Plan pool expansions before exhaustion

**Pool Expansion Strategies**
- Increase pool size within subnet (if space available)
- Add additional subnets for expansion
- Consider /23 subnets for very large racks

**Load Balancing Considerations**
- Distribute nodes evenly across subnets
- Avoid overloading individual pools
- Monitor pool balance across subnets

Monitoring and Alerting
----------------------

Key Metrics to Monitor
~~~~~~~~~~~~~~~~~~~~~~~

Monitor these metrics for multi-subnet DHCP health:

**DHCP Service Metrics**
- CoreDHCP service uptime
- DHCP request rate per subnet
- DHCP response time per subnet
- DHCP error rate per subnet

**Network Metrics**
- Latency between subnets and CoreDHCP server
- Packet loss per subnet
- Routing table size
- Broadcast traffic per subnet

**Pool Utilization Metrics**
- DHCP pool utilization per subnet
- IP allocation rate per subnet
- Lease renewal rate per subnet
- Pool fragmentation per subnet

Alert Thresholds
~~~~~~~~~~~~~~~~

Configure appropriate alert thresholds:

**DHCP Service Alerts**
- Alert if CoreDHCP service is down
- Alert if DHCP error rate exceeds 5%
- Alert if DHCP response time exceeds 2 seconds

**Network Alerts**
- Alert if packet loss exceeds 1%
- Alert if latency exceeds 100ms
- Alert if routing table size exceeds expected limits

**Pool Utilization Alerts**
- Alert if pool utilization exceeds 80%
- Alert if pool utilization exceeds 90% (critical)
- Alert if pool exhaustion is imminent

Log Analysis
~~~~~~~~~~~

Analyze logs proactively to identify issues:

**DHCP Log Analysis**
- Monitor CoreDHCP logs for errors
- Track unusual DHCP request patterns
- Correlate DHCP logs with network events

**Network Log Analysis**
- Monitor switch logs for DHCP relay issues
- Track routing log entries
- Analyze ACL log entries for security events

**Correlation**
- Correlate DHCP logs with network logs
- Identify root causes of issues
- Document common patterns and resolutions

Documentation
-------------

Maintain comprehensive documentation:

**Network Topology Documentation**
- Document rack layout and subnet allocations
- Include switch configurations and routing policies
- Update documentation when topology changes

**Configuration Documentation**
- Document all ``network_spec.yml`` configurations
- Include parameter descriptions and examples
- Maintain change logs for configuration updates

**Operational Documentation**
- Document operational procedures
- Include troubleshooting procedures
- Maintain runbooks for common tasks

**Security Documentation**
- Document security policies and ACL configurations
- Include iDRAC access control policies
- Maintain security incident response procedures

Next Steps
----------

For configuration procedures, see :doc:`how-to-configuration`.

For network architecture details, see :doc:`concept-network-architecture`.

For troubleshooting assistance, see :doc:`../../troubleshootingguide/multi-subnet-dhcp`.

For an overview of multi-subnet DHCP, see :doc:`concept-overview`.
