#! /bin/bash

sleep_until_minute

# Start the router ------------------------------
source ../../../utils/set_up_environment
${ROUTER} --config ./router_5.conf

