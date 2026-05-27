#!/bin/bash
# =============================================================================
# create_ldap_user.sh
#
# Creates one or more LDAP users (posixAccount + shadowAccount) in a
# Bitnami OpenLDAP instance.
#
# Reads LDAP server details from omnia_test_config.yml when present.
# Only inputs required: username and password.
#
# Single user:
#   ./create_ldap_user.sh -u <username> -p <password>
#   ./create_ldap_user.sh                     # interactive prompts
#
# Multiple users (batch):
#   ./create_ldap_user.sh --from-file users.txt
#
#   users.txt format (one entry per line, lines starting with # are skipped):
#     username:password
#     ldapuser1:MyP@ss1
#     ldapuser2:MyP@ss2
#
# Optional overrides:
#   --ldap-host    LDAP server IP/hostname   (default: from config or localhost)
#   --ldap-port    LDAP port                 (default: from config or 1389)
#   --domain       LDAP domain               (default: from config or omnia.test)
#   --admin-user   Bind DN username          (default: from config or admin)
#   --admin-pass   Bind DN password          (default: from config, else prompted)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/omnia_test_config.yml"
TMPDIR_LDIF="$(mktemp -d)"
trap 'rm -rf "${TMPDIR_LDIF}"' EXIT

# ─── Colour helpers ──────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
die()     { error "$*"; exit 1; }

# ─── Read a value from omnia_test_config.yml (simple key: "value" parsing) ───
_cfg() {
    local key="$1"
    if [[ -f "${CONFIG_FILE}" ]]; then
        grep -E "^${key}:" "${CONFIG_FILE}" 2>/dev/null \
            | head -1 \
            | sed 's/^[^:]*:[[:space:]]*//' \
            | tr -d '"' \
            | tr -d "'"
    fi
}

# ─── Defaults (from config file when present) ────────────────────────────────
LDAP_HOST="$(_cfg external_ldap_server_ip)"
LDAP_PORT="$(_cfg external_ldap_server_port)"
LDAP_DOMAIN="$(_cfg external_ldap_domain)"
LDAP_ADMIN_USER="$(_cfg external_ldap_bind_username)"
LDAP_ADMIN_PASS="$(_cfg external_ldap_bind_password)"

LDAP_HOST="${LDAP_HOST:-localhost}"
LDAP_PORT="${LDAP_PORT:-1389}"
LDAP_DOMAIN="${LDAP_DOMAIN:-omnia.test}"
LDAP_ADMIN_USER="${LDAP_ADMIN_USER:-admin}"

NEW_USER=""
NEW_PASS=""
UID_OVERRIDE=""
FROM_FILE=""

# ─── Usage ───────────────────────────────────────────────────────────────────
usage() {
    echo -e "${BOLD}Usage:${NC}"
    echo "  $0 -u <username> -p <password> [OPTIONS]"
    echo "  $0 --from-file users.txt [OPTIONS]"
    echo ""
    echo -e "${BOLD}Single user:${NC}"
    echo "  -u, --username    New LDAP username"
    echo "  -p, --password    Password for the new user"
    echo ""
    echo -e "${BOLD}Batch (multiple users):${NC}"
    echo "  --from-file FILE  Path to a file with 'username:password' per line"
    echo "                    (lines starting with # are treated as comments)"
    echo ""
    echo -e "${BOLD}Optional:${NC}"
    echo "  --ldap-host       LDAP server IP/hostname  (default: ${LDAP_HOST})"
    echo "  --ldap-port       LDAP server port         (default: ${LDAP_PORT})"
    echo "  --domain          LDAP domain              (default: ${LDAP_DOMAIN})"
    echo "  --admin-user      Bind DN admin username   (default: ${LDAP_ADMIN_USER})"
    echo "  --admin-pass      Bind DN admin password   (prompted if omitted)"
    echo "  --uid             Force starting UID number (single-user mode only)"
    echo "  -h, --help        Show this help message"
    exit 0
}

# ─── Parse arguments ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        -u|--username)   NEW_USER="$2";        shift 2 ;;
        -p|--password)   NEW_PASS="$2";        shift 2 ;;
        --from-file)     FROM_FILE="$2";       shift 2 ;;
        --ldap-host)     LDAP_HOST="$2";       shift 2 ;;
        --ldap-port)     LDAP_PORT="$2";       shift 2 ;;
        --domain)        LDAP_DOMAIN="$2";     shift 2 ;;
        --admin-user)    LDAP_ADMIN_USER="$2"; shift 2 ;;
        --admin-pass)    LDAP_ADMIN_PASS="$2"; shift 2 ;;
        --uid)           UID_OVERRIDE="$2";    shift 2 ;;
        -h|--help)       usage ;;
        *) die "Unknown option: $1  (use --help for usage)" ;;
    esac
done

# ─── Validate --from-file is not mixed with -u / -p ─────────────────────────
if [[ -n "${FROM_FILE}" && ( -n "${NEW_USER}" || -n "${NEW_PASS}" ) ]]; then
    die "--from-file cannot be used together with -u / -p."
fi
if [[ -n "${FROM_FILE}" ]]; then
    [[ -f "${FROM_FILE}" ]] || die "File not found: ${FROM_FILE}"
fi

# ─── Interactive prompts (single-user mode, no --from-file) ──────────────────
if [[ -z "${FROM_FILE}" ]]; then
    if [[ -z "${NEW_USER}" ]]; then
        echo -ne "${BOLD}Enter new LDAP username: ${NC}"
        read -r NEW_USER
    fi
    if [[ -z "${NEW_PASS}" ]]; then
        echo -ne "${BOLD}Enter password for '${NEW_USER}': ${NC}"
        read -rs NEW_PASS
        echo
        echo -ne "${BOLD}Confirm password: ${NC}"
        read -rs PASS_CONFIRM
        echo
        [[ "${NEW_PASS}" == "${PASS_CONFIRM}" ]] || die "Passwords do not match."
    fi
    [[ -n "${NEW_USER}" ]] || die "Username cannot be empty."
    [[ -n "${NEW_PASS}" ]] || die "Password cannot be empty."
fi

if [[ -z "${LDAP_ADMIN_PASS}" ]]; then
    echo -ne "${BOLD}Enter LDAP admin password (cn=${LDAP_ADMIN_USER}): ${NC}"
    read -rs LDAP_ADMIN_PASS
    echo
fi
[[ -n "${LDAP_ADMIN_PASS}" ]] || die "Admin password cannot be empty."

# ─── Derived LDAP values ─────────────────────────────────────────────────────
# Convert "omnia.test" -> "dc=omnia,dc=test"
DC_STRING="$(echo "${LDAP_DOMAIN}" | awk -F'.' '{for(i=1;i<=NF;i++) printf "dc=%s%s", $i, (i<NF)?",":""; print ""}')"
BIND_DN="cn=${LDAP_ADMIN_USER},${DC_STRING}"
LDAP_URI="ldap://${LDAP_HOST}:${LDAP_PORT}"

info "LDAP URI    : ${LDAP_URI}"
info "Base DN     : ${DC_STRING}"
info "Bind DN     : ${BIND_DN}"
echo

# ─── Check ldapadd / ldappasswd / ldapsearch are available ───────────────────
for cmd in ldapadd ldappasswd ldapsearch; do
    command -v "${cmd}" &>/dev/null || die "'${cmd}' not found. Install ldap-utils (Debian/Ubuntu) or openldap-clients (RHEL)."
done

# ─── Verify admin bind works before doing anything ───────────────────────────
info "Verifying admin bind to ${LDAP_URI} ..."
if ! ldapsearch -x -H "${LDAP_URI}" \
        -D "${BIND_DN}" -w "${LDAP_ADMIN_PASS}" \
        -b "${DC_STRING}" -s base "(objectClass=*)" dn &>/dev/null; then
    die "Admin bind failed. Check --ldap-host, --ldap-port, --domain, --admin-user, --admin-pass."
fi
success "Admin bind OK."

# ─── Ensure ou=People and ou=Groups exist (done once) ───────────────────────
_ensure_ou() {
    local ou_name="$1"
    local ou_dn="ou=${ou_name},${DC_STRING}"
    local check
    check="$(ldapsearch -x -H "${LDAP_URI}" \
        -D "${BIND_DN}" -w "${LDAP_ADMIN_PASS}" \
        -b "${ou_dn}" -s base "(objectClass=*)" dn 2>/dev/null || true)"
    if ! echo "${check}" | grep -q "dn:"; then
        info "Creating OU: ${ou_dn}"
        local ou_ldif="${TMPDIR_LDIF}/ou_${ou_name}.ldif"
        cat > "${ou_ldif}" <<LDIF
dn: ${ou_dn}
objectClass: organizationalUnit
ou: ${ou_name}
LDIF
        ldapadd -x -H "${LDAP_URI}" \
            -D "${BIND_DN}" -w "${LDAP_ADMIN_PASS}" \
            -f "${ou_ldif}" &>/dev/null \
            || warn "Could not create ou=${ou_name} (may already exist)."
        success "OU '${ou_name}' is ready."
    else
        info "OU '${ou_name}' already exists."
    fi
}

_ensure_ou "People"
_ensure_ou "Groups"

# ─── Fetch current max UID/GID from LDAP once (shared across batch) ───────────
info "Fetching existing UID/GID range from LDAP ..."
_EXISTING_UIDS="$(ldapsearch -x -H "${LDAP_URI}" \
    -D "${BIND_DN}" -w "${LDAP_ADMIN_PASS}" \
    -b "ou=People,${DC_STRING}" "(uidNumber=*)" uidNumber 2>/dev/null \
    | grep "^uidNumber:" | awk '{print $2}' | sort -n || true)"
_EXISTING_GIDS="$(ldapsearch -x -H "${LDAP_URI}" \
    -D "${BIND_DN}" -w "${LDAP_ADMIN_PASS}" \
    -b "ou=Groups,${DC_STRING}" "(gidNumber=*)" gidNumber 2>/dev/null \
    | grep "^gidNumber:" | awk '{print $2}' | sort -n || true)"

_MAX_UID=2999
if [[ -n "${_EXISTING_UIDS}" ]]; then
    _MAX_UID="$(echo "${_EXISTING_UIDS}" | tail -1)"
fi
_MAX_GID=2999
if [[ -n "${_EXISTING_GIDS}" ]]; then
    _MAX_GID="$(echo "${_EXISTING_GIDS}" | tail -1)"
fi
info "Highest UID in LDAP: ${_MAX_UID}  |  Highest GID in LDAP: ${_MAX_GID}"

# ─── Core function: create a single LDAP user ────────────────────────────────
# Args: $1=username  $2=password  $3=uid_override (empty = auto)
# Uses and updates global _MAX_UID / _MAX_GID counters.
# Returns 0 on success, 1 on skip (already exists), 2 on error.
_create_one_user() {
    local usr="$1"
    local pwd="$2"
    local uid_force="$3"

    local user_dn="uid=${usr},ou=People,${DC_STRING}"
    local group_dn="cn=${usr},ou=Groups,${DC_STRING}"

    # Check for duplicate
    local existing
    existing="$(ldapsearch -x -H "${LDAP_URI}" \
        -D "${BIND_DN}" -w "${LDAP_ADMIN_PASS}" \
        -b "ou=People,${DC_STRING}" "(uid=${usr})" dn 2>/dev/null || true)"
    if echo "${existing}" | grep -q "dn:"; then
        warn "User '${usr}' already exists — skipping."
        return 1
    fi

    # Assign UID/GID
    local next_uid next_gid
    if [[ -n "${uid_force}" ]]; then
        next_uid="${uid_force}"
        next_gid="${uid_force}"
    else
        next_uid=$(( _MAX_UID + 1 ))
        next_gid=$(( _MAX_GID + 1 ))
        _MAX_UID=${next_uid}
        _MAX_GID=${next_gid}
    fi

    info "Creating user '${usr}'  UID=${next_uid}  GID=${next_gid} ..."

    # User LDIF
    local user_ldif="${TMPDIR_LDIF}/user_${usr}.ldif"
    cat > "${user_ldif}" <<LDIF
dn: ${user_dn}
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
uid: ${usr}
cn: ${usr}
sn: ${usr}
uidNumber: ${next_uid}
gidNumber: ${next_gid}
homeDirectory: /home/${usr}
loginShell: /bin/bash
shadowLastChange: 0
shadowMax: 99999
shadowWarning: 7
LDIF

    # Group LDIF
    local group_ldif="${TMPDIR_LDIF}/group_${usr}.ldif"
    cat > "${group_ldif}" <<LDIF
dn: ${group_dn}
objectClass: posixGroup
cn: ${usr}
gidNumber: ${next_gid}
memberUid: ${usr}
LDIF

    # Add user
    if ! ldapadd -x -H "${LDAP_URI}" \
            -D "${BIND_DN}" -w "${LDAP_ADMIN_PASS}" \
            -f "${user_ldif}" &>/dev/null; then
        error "ldapadd failed for '${usr}'."
        return 2
    fi

    # Add group
    if ! ldapadd -x -H "${LDAP_URI}" \
            -D "${BIND_DN}" -w "${LDAP_ADMIN_PASS}" \
            -f "${group_ldif}" &>/dev/null; then
        warn "Group entry for '${usr}' could not be added (user was still created)."
    fi

    # Set password
    if ! ldappasswd -x -H "${LDAP_URI}" \
            -D "${BIND_DN}" -w "${LDAP_ADMIN_PASS}" \
            -s "${pwd}" \
            "${user_dn}" &>/dev/null; then
        error "ldappasswd failed for '${usr}'. User entry exists but password was NOT set."
        return 2
    fi

    success "User '${usr}' created  (UID=${next_uid} | GID=${next_gid} | DN: ${user_dn})"
    return 0
}

# ─── Batch mode ──────────────────────────────────────────────────────────────
if [[ -n "${FROM_FILE}" ]]; then
    TOTAL=0; CREATED=0; SKIPPED=0; FAILED=0
    echo
    echo -e "${BOLD}── Batch mode: reading users from '${FROM_FILE}' ──${NC}"
    echo

    while IFS= read -r line || [[ -n "${line}" ]]; do
        # Skip blank lines and comments
        [[ -z "${line}" || "${line}" =~ ^[[:space:]]*# ]] && continue

        # Expect username:password
        if [[ "${line}" != *:* ]]; then
            warn "Skipping malformed line (expected 'username:password'): ${line}"
            (( FAILED++ )) || true
            continue
        fi

        b_user="${line%%:*}"
        b_pass="${line#*:}"
        b_user="$(echo "${b_user}" | xargs)"   # trim whitespace
        b_pass="$(echo "${b_pass}" | xargs)"

        if [[ -z "${b_user}" || -z "${b_pass}" ]]; then
            warn "Skipping line with empty username or password: ${line}"
            (( FAILED++ )) || true
            continue
        fi

        (( TOTAL++ )) || true
        _create_one_user "${b_user}" "${b_pass}" ""
        rc=$?
        if   [[ ${rc} -eq 0 ]]; then (( CREATED++ )) || true
        elif [[ ${rc} -eq 1 ]]; then (( SKIPPED++ )) || true
        else                          (( FAILED++  )) || true
        fi
    done < "${FROM_FILE}"

    echo
    echo -e "${BOLD}── Batch summary ─────────────────────────────────────${NC}"
    echo -e "  Total in file : ${TOTAL}"
    echo -e "  ${GREEN}Created${NC}       : ${CREATED}"
    echo -e "  ${YELLOW}Skipped${NC}       : ${SKIPPED}  (already existed)"
    echo -e "  ${RED}Failed${NC}        : ${FAILED}"
    echo
    [[ ${FAILED} -gt 0 ]] && exit 1 || exit 0
fi

# ─── Single-user mode ────────────────────────────────────────────────────────
_create_one_user "${NEW_USER}" "${NEW_PASS}" "${UID_OVERRIDE}" || {
    rc=$?
    [[ ${rc} -eq 1 ]] && die "User '${NEW_USER}' already exists in LDAP."
    die "Failed to create user '${NEW_USER}'."
}

# ─── Final verification (single-user mode only) ───────────────────────────────
VERIFY="$(ldapsearch -x -H "${LDAP_URI}" \
    -D "${BIND_DN}" -w "${LDAP_ADMIN_PASS}" \
    -b "ou=People,${DC_STRING}" "(uid=${NEW_USER})" \
    uid uidNumber gidNumber homeDirectory 2>/dev/null)"
if echo "${VERIFY}" | grep -q "uid: ${NEW_USER}"; then
    FINAL_UID="$(echo "${VERIFY}" | grep '^uidNumber:' | awk '{print $2}')"
    FINAL_GID="$(echo "${VERIFY}" | grep '^gidNumber:' | awk '{print $2}')"
    echo
    echo -e "${GREEN}${BOLD}========================================${NC}"
    echo -e "${GREEN}${BOLD}  LDAP user created successfully!${NC}"
    echo -e "${GREEN}${BOLD}========================================${NC}"
    echo -e "  ${BOLD}Username${NC}  : ${NEW_USER}"
    echo -e "  ${BOLD}DN${NC}        : uid=${NEW_USER},ou=People,${DC_STRING}"
    echo -e "  ${BOLD}UID/GID${NC}   : ${FINAL_UID} / ${FINAL_GID}"
    echo -e "  ${BOLD}Home${NC}      : /home/${NEW_USER}"
    echo -e "  ${BOLD}Shell${NC}     : /bin/bash"
    echo -e "  ${BOLD}LDAP URI${NC}  : ${LDAP_URI}"
    echo
else
    die "User '${NEW_USER}' was not found in LDAP after creation. Manual inspection required."
fi
