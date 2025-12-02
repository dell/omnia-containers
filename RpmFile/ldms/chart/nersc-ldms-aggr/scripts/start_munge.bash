#!/bin/bash
echo "[--] START MUNGED"
if [ -z "$1" ]; then
  echo "USAGE: $0 <conf file>"
  exit 1
fi
CONF_FILE="$1"
echo "[>>] Show CONF_FILE:$CONF_FILE"
cat $CONF_FILE
echo "[>>] Source CONF_FILE:$CONF_FILE"
source $CONF_FILE
echo "[>>] Stop running munged: $MUNGE_PID_FILES"
if [ -f  "$MUNGE_PID_FILE" ]; then
  echo "[>>] kill munged"
  kill -9 $(cat $MUNGE_PID_FILE)
else
  echo "[OK] No munged"
fi
echo "[>>] Find munge key: $MUNGE_KEY_FILE"
if [ -f "$MUNGE_KEY_FILE" ]; then
  echo "OK[] Munge key does exist."
else
  echo "[!!] Munge key does not exist. Exit!"
  exit 1
fi
echo "[--] Setup Files, Dirs, and perms"
if [ ! -d "$MUNGE_RUN_DIR" ]; then
  echo "[>>] Make Running directory: $MUNGE_RUN_DIR"
  mkdir "$MUNGE_RUN_DIR"
else
  echo "[OK] Found Running directory: $MUNGE_RUN_DIR"
fi
if [ ! -d "$MUNGE_LOG_DIR" ]; then
  echo "[>>] Make munge log dir: $MUNGE_LOG_DIR"
  mkdir -p "$MUNGE_LOG_DIR"
else
  echo "[OK] Found munge log dir: $MUNGE_LOG_DIR"
fi
echo "Fix Perms"
chown -v munge:munge /var/lib/munge $MUNGE_LOG_DIR
chown -v munge:root $MUNGE_RUN_DIR
chmod -v 0711 /var/lib/munge
chmod -v 0700 $MUNGE_LOG_DIR
echo "[>>] Vars
Bin File:    $MUNGED_BIN
Key File:    $MUNGE_KEY_FILE
Pid File:    $MUNGE_PID_FILE
Socket File: $MUNGE_SOCKET_FILE
Log File:    $MUNGE_LOG_File
"
echo "[>>] Start Munge"
$MUNGED_BIN \
  --verbose \
  --force \
  --num-threads=256 \
  --key-file $MUNGE_KEY_FILE \
  --log-file $MUNGE_LOG_FILE \
  --seed-file /var/lib/munge/munged.seed \
  --socket $MUNGE_SOCKET_FILE \
  --pid-file $MUNGE_PID_FILE
echo "[>>] List running Munged"
ps -elf |grep $(cat $MUNGE_PID_FILE)
echo "[>>] Test1: munge|unmune"
munge -n --socket=$MUNGE_SOCKET_FILE |unmunge --socket=$MUNGE_SOCKET_FILE
echo "[>>] Test2:  munge|unmune"
echo "PASS" | munge --socket=$MUNGE_SOCKET_FILE |unmunge --socket=$MUNGE_SOCKET_FILE
if [ $? -ne 0 ]; then
    echo "[!!] Failed to munge |unmunge"
    kill -9 $(cat $MUNGE_PID_FILE)
    exit 1
fi
